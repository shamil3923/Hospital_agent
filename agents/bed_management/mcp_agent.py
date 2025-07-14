"""
Bed Management Agent with MCP Integration
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import logging
from datetime import datetime

from ..shared.llm_config import llm_config
from ..shared.vector_store import vector_store
from .mcp_tools import (
    get_bed_occupancy_status,
    get_available_beds,
    get_critical_bed_alerts,
    get_patient_discharge_predictions,
    update_bed_status,
    cleanup_mcp_tools
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the bed management agent"""
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    user_query: str
    context: str
    tools_used: List[str]
    final_response: str


class MCPBedManagementAgent:
    """Bed Management Agent with MCP integration"""
    
    def __init__(self, use_mcp: bool = True):
        self.use_mcp = use_mcp
        self.llm = llm_config.get_llm(temperature=0.1)
        
        # Use MCP tools
        self.tools = [
            get_bed_occupancy_status,
            get_available_beds,
            get_critical_bed_alerts,
            get_patient_discharge_predictions,
            update_bed_status
        ]
        
        self.tool_node = ToolNode(self.tools)
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "gather_context")
        workflow.add_edge("gather_context", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _analyze_query(self, state: AgentState) -> AgentState:
        """Analyze user query to determine intent"""
        user_query = state["user_query"]
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing a user query for a hospital bed management system.
            
            Determine the user's intent and extract key information:
            - What type of information are they looking for?
            - Are they asking about specific wards, bed types, or patients?
            - Do they want to perform any actions (like updating bed status)?
            
            Respond with a brief analysis of the query intent."""),
            ("human", user_query)
        ])
        
        try:
            chain = analysis_prompt | self.llm
            analysis = chain.invoke({"query": user_query})
            
            state["messages"].append(AIMessage(content=f"Query analysis: {analysis.content}"))
            logger.info(f"Analyzed query: {user_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            state["messages"].append(AIMessage(content="Query analysis completed"))
        
        return state
    
    def _gather_context(self, state: AgentState) -> AgentState:
        """Gather relevant context from knowledge base"""
        user_query = state["user_query"]
        
        try:
            # Get relevant context from vector store
            context = vector_store.get_context_for_query(user_query, max_context_length=800)
            state["context"] = context
            
            logger.info(f"Gathered context for query: {user_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            state["context"] = ""
        
        return state
    
    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute relevant tools based on query analysis"""
        user_query = state["user_query"].lower()
        tools_used = []
        
        try:
            # Determine which tools to use based on query content
            if any(keyword in user_query for keyword in ["status", "occupancy", "capacity", "overview"]):
                result = get_bed_occupancy_status.invoke({})
                state["messages"].append(AIMessage(content=f"Bed occupancy data: {result}"))
                tools_used.append("get_bed_occupancy_status")
            
            if any(keyword in user_query for keyword in ["available", "vacant", "free", "empty"]):
                # Extract ward or bed type if mentioned
                ward = None
                bed_type = None
                if "icu" in user_query:
                    ward = "ICU"
                elif "emergency" in user_query or "er" in user_query:
                    ward = "Emergency"
                elif "general" in user_query:
                    ward = "General"
                
                result = get_available_beds.invoke({"ward": ward, "bed_type": bed_type})
                state["messages"].append(AIMessage(content=f"Available beds: {result}"))
                tools_used.append("get_available_beds")
            
            if any(keyword in user_query for keyword in ["alert", "critical", "warning", "urgent", "problem"]):
                result = get_critical_bed_alerts.invoke({})
                state["messages"].append(AIMessage(content=f"Critical alerts: {result}"))
                tools_used.append("get_critical_bed_alerts")
            
            if any(keyword in user_query for keyword in ["discharge", "prediction", "upcoming", "expected"]):
                result = get_patient_discharge_predictions.invoke({})
                state["messages"].append(AIMessage(content=f"Discharge predictions: {result}"))
                tools_used.append("get_patient_discharge_predictions")
            
            # Check for bed status update requests
            if any(keyword in user_query for keyword in ["update", "change", "set", "mark"]):
                # This would need more sophisticated parsing in a real implementation
                # For now, we'll just note that an update was requested
                state["messages"].append(AIMessage(content="Bed status update requested - please provide specific bed number and new status"))
                tools_used.append("update_bed_status_requested")
            
            # If no specific tools were triggered, get general status
            if not tools_used:
                result = get_bed_occupancy_status.invoke({})
                state["messages"].append(AIMessage(content=f"General bed status: {result}"))
                tools_used.append("get_bed_occupancy_status")
            
            state["tools_used"] = tools_used
            
        except Exception as e:
            logger.error(f"Error executing tools: {e}")
            state["messages"].append(AIMessage(content=f"Error retrieving data: {str(e)}"))
            state["tools_used"] = []
        
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response using LLM with context and tool results"""
        user_query = state["user_query"]
        context = state.get("context", "")
        messages = state["messages"]
        tools_used = state.get("tools_used", [])
        
        # Extract tool results from messages
        tool_results = []
        for msg in messages:
            if isinstance(msg, AIMessage) and any(tool in msg.content for tool in ["occupancy data", "Available beds", "Critical alerts", "Discharge predictions"]):
                tool_results.append(msg.content)
        
        response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Bed Management Agent for a hospital using MCP (Model Context Protocol) tools. Your role is to:

1. Provide accurate, actionable information about bed occupancy and availability
2. Identify critical issues and provide recommendations
3. Help optimize patient flow and bed utilization
4. Communicate clearly with medical staff

Context from knowledge base:
{context}

Tool results (via MCP):
{tool_results}

Tools used: {tools_used}

Based on the user query and available data, provide a comprehensive, helpful response. 
Include specific numbers, recommendations, and next steps when appropriate.
Be professional but conversational. Mention that you're using MCP for real-time data access."""),
            ("human", user_query)
        ])
        
        try:
            chain = response_prompt | self.llm
            response = chain.invoke({
                "context": context,
                "tool_results": "\n".join(tool_results),
                "tools_used": ", ".join(tools_used)
            })
            
            state["final_response"] = response.content
            state["messages"].append(AIMessage(content=response.content))
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["final_response"] = "I apologize, but I encountered an error while processing your request. Please try again."
        
        return state
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent workflow"""
        initial_state = AgentState(
            messages=[],
            user_query=query,
            context="",
            tools_used=[],
            final_response=""
        )
        
        try:
            # Run the workflow
            final_state = self.graph.invoke(initial_state)
            
            return {
                "response": final_state["final_response"],
                "tools_used": final_state["tools_used"],
                "timestamp": datetime.now().isoformat(),
                "agent": "mcp_bed_management_agent",
                "mcp_enabled": self.use_mcp
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try again.",
                "tools_used": [],
                "timestamp": datetime.now().isoformat(),
                "agent": "mcp_bed_management_agent",
                "mcp_enabled": self.use_mcp,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup MCP resources"""
        if self.use_mcp:
            await cleanup_mcp_tools()
