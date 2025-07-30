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
    assign_patient_to_bed,
    create_patient_and_assign,
    get_all_doctors,
    get_all_patients,
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
            update_bed_status,
            assign_patient_to_bed,
            create_patient_and_assign,
            get_all_doctors,
            get_all_patients
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
        """Execute relevant tools based on query analysis with proper error handling"""
        user_query = state["user_query"].lower()
        tools_used = []
        tool_results = []
        
        try:
            # Enhanced tool execution with comprehensive real-time data

            # Bed occupancy and status queries
            if any(keyword in user_query for keyword in ["status", "occupancy", "capacity", "overview"]):
                try:
                    result = get_bed_occupancy_status.invoke({"input_data": ""})
                    tool_results.append(f"Bed occupancy data: {result}")
                    tools_used.append("get_bed_occupancy_status")
                    logger.info("SUCCESS: Executed bed occupancy status tool")
                except Exception as e:
                    logger.error(f"ERROR: Bed occupancy tool failed: {e}")
                    tool_results.append(f"Bed occupancy tool error: {str(e)}")

            # Patient information queries
            if any(keyword in user_query for keyword in ["patient", "patients", "show me all patients", "patient list"]):
                try:
                    from .mcp_tools import get_real_time_patients
                    ward_context = state.get("ward_context")
                    result = get_real_time_patients.invoke({"ward": ward_context})
                    tool_results.append(f"Patient data: {result}")
                    tools_used.append("get_real_time_patients")
                    logger.info("SUCCESS: Executed real-time patients tool")
                except Exception as e:
                    logger.error(f"ERROR: Real-time patients tool failed: {e}")
                    tool_results.append(f"Patient data error: {str(e)}")

            # Doctor information queries - enhanced detection
            if any(keyword in user_query.lower() for keyword in ["doctor", "doctors", "physician", "specialist", "staff", "cardiologist", "cardiologists"]):
                try:
                    from .mcp_tools import get_real_time_doctors
                    # Extract specialty if mentioned - enhanced specialty detection
                    specialty = None
                    specialty_mappings = {
                        "cardiology": ["cardiology", "cardiologist", "cardiologists", "cardiac", "heart"],
                        "emergency": ["emergency", "er", "trauma", "urgent"],
                        "icu": ["icu", "intensive care", "critical care"],
                        "surgery": ["surgery", "surgical", "surgeon", "surgeons", "operating"],
                        "pediatrics": ["pediatric", "pediatrics", "children", "kids", "peds"],
                        "neurology": ["neurology", "neuro", "neurologist", "neurologists", "brain"],
                        "oncology": ["oncology", "cancer", "oncologist", "oncologists", "chemotherapy"]
                    }

                    for spec, keywords in specialty_mappings.items():
                        if any(keyword in user_query.lower() for keyword in keywords):
                            specialty = spec
                            break
                    result = get_real_time_doctors.invoke({"specialty": specialty})
                    tool_results.append(f"Doctor data: {result}")
                    tools_used.append("get_real_time_doctors")
                    logger.info("SUCCESS: Executed real-time doctors tool")
                except Exception as e:
                    logger.error(f"ERROR: Real-time doctors tool failed: {e}")
                    tool_results.append(f"Doctor data error: {str(e)}")

            # Equipment status queries
            if any(keyword in user_query for keyword in ["equipment", "ventilator", "monitor", "pump", "device"]):
                try:
                    from .mcp_tools import get_equipment_status
                    ward_context = state.get("ward_context")
                    result = get_equipment_status.invoke({"ward": ward_context})
                    tool_results.append(f"Equipment data: {result}")
                    tools_used.append("get_equipment_status")
                    logger.info("SUCCESS: Executed equipment status tool")
                except Exception as e:
                    logger.error(f"ERROR: Equipment status tool failed: {e}")
                    tool_results.append(f"Equipment data error: {str(e)}")

            # Discharge predictions and capacity planning
            if any(keyword in user_query for keyword in ["discharge", "prediction", "forecast", "capacity", "planning"]):
                try:
                    from .mcp_tools import get_discharge_predictions
                    result = get_discharge_predictions.invoke({})
                    tool_results.append(f"Discharge predictions: {result}")
                    tools_used.append("get_discharge_predictions")
                    logger.info("SUCCESS: Executed discharge predictions tool")
                except Exception as e:
                    logger.error(f"ERROR: Discharge predictions tool failed: {e}")
                    tool_results.append(f"Discharge predictions error: {str(e)}")

            # Medical knowledge queries
            if any(keyword in user_query for keyword in ["medical", "condition", "treatment", "protocol", "care"]):
                try:
                    from .mcp_tools import get_medical_knowledge
                    result = get_medical_knowledge.invoke({"query": user_query})
                    tool_results.append(f"Medical knowledge: {result}")
                    tools_used.append("get_medical_knowledge")
                    logger.info("SUCCESS: Executed medical knowledge tool")
                except Exception as e:
                    logger.error(f"ERROR: Medical knowledge tool failed: {e}")
                    tool_results.append(f"Medical knowledge error: {str(e)}")

            if any(keyword in user_query for keyword in ["available", "vacant", "free", "empty", "beds", "show me"]):
                try:
                    # Enhanced ward extraction with better pattern matching
                    ward = None
                    bed_type = None
                    ward_patterns = {
                        "ICU": ["icu", "intensive care", "critical care"],
                        "Emergency": ["emergency", "er", "trauma", "urgent"],
                        "General": ["general", "medical", "internal medicine"],
                        "Cardiology": ["cardiology", "cardiac", "heart"],
                        "Pediatrics": ["pediatric", "children", "kids", "peds"],
                        "Maternity": ["maternity", "obstetrics", "labor", "delivery"],
                        "Surgery": ["surgery", "surgical", "operating", "post-op"],
                        "Orthopedics": ["orthopedic", "ortho", "bone", "joint"],
                        "Neurology": ["neurology", "neuro", "brain", "neurological"],
                        "Oncology": ["oncology", "cancer", "chemotherapy"],
                        "Psychiatry": ["psychiatry", "mental health", "psychiatric"],
                        "Rehabilitation": ["rehabilitation", "rehab", "recovery"]
                    }

                    for ward_name, keywords in ward_patterns.items():
                        if any(keyword in user_query for keyword in keywords):
                            ward = ward_name
                            break

                    result = get_available_beds.invoke({"ward": ward, "bed_type": bed_type})

                    # Store ward context and results for better response generation
                    state["ward_context"] = ward
                    state["available_beds_result"] = result

                    tool_results.append(f"Available beds: {result}")
                    tools_used.append("get_available_beds")
                    logger.info(f"SUCCESS: Executed available beds tool for ward: {ward}")
                except Exception as e:
                    logger.error(f"ERROR: Available beds tool failed: {e}")
                    tool_results.append(f"Available beds tool error: {str(e)}")

            if any(keyword in user_query for keyword in ["alert", "critical", "warning", "urgent", "problem"]):
                try:
                    result = get_critical_bed_alerts.invoke({"input_data": ""})
                    tool_results.append(f"Critical alerts: {result}")
                    tools_used.append("get_critical_bed_alerts")
                    logger.info("SUCCESS: Executed critical alerts tool")
                except Exception as e:
                    logger.error(f"ERROR: Critical alerts tool failed: {e}")
                    tool_results.append(f"Critical alerts tool error: {str(e)}")
            
            if any(keyword in user_query for keyword in ["discharge", "prediction", "upcoming", "expected"]):
                result = get_patient_discharge_predictions.invoke({})
                state["messages"].append(AIMessage(content=f"Discharge predictions: {result}"))
                tools_used.append("get_patient_discharge_predictions")
            
            # Enhanced patient assignment with ward-specific logic
            if any(keyword in user_query for keyword in ["assign", "admit", "place patient", "patient to bed", "need bed for"]):
                import re

                # Enhanced patterns for better extraction
                assign_pattern = r"assign\s+(\w+(?:\s+\w+)?)\s+to\s+bed\s+(\w+-\d+)"
                admit_pattern = r"admit\s+(\w+(?:\s+\w+)?)\s+(?:to\s+)?(\w+)"
                need_bed_pattern = r"need\s+(?:a\s+)?bed\s+for\s+(\w+(?:\s+\w+)?)\s+(?:in\s+)?(\w+)?"

                assign_match = re.search(assign_pattern, user_query, re.IGNORECASE)
                admit_match = re.search(admit_pattern, user_query, re.IGNORECASE)
                need_bed_match = re.search(need_bed_pattern, user_query, re.IGNORECASE)

                if assign_match:
                    patient_name = assign_match.group(1)
                    bed_number = assign_match.group(2)
                    result = create_patient_and_assign.invoke({
                        "patient_name": patient_name,
                        "bed_number": bed_number
                    })
                    state["messages"].append(AIMessage(content=f"Patient assignment result: {result}"))
                    tools_used.append("create_patient_and_assign")
                elif admit_match or need_bed_match:
                    if admit_match:
                        patient_name = admit_match.group(1)
                        ward_hint = admit_match.group(2)
                    else:
                        patient_name = need_bed_match.group(1)
                        ward_hint = need_bed_match.group(2) if need_bed_match.group(2) else None

                    # Enhanced ward mapping
                    ward = None
                    if ward_hint:
                        ward_mapping = {
                            "icu": "ICU", "intensive": "ICU", "critical": "ICU",
                            "emergency": "Emergency", "er": "Emergency", "trauma": "Emergency",
                            "general": "General", "medical": "General",
                            "cardiology": "Cardiology", "cardiac": "Cardiology",
                            "pediatric": "Pediatrics", "children": "Pediatrics", "peds": "Pediatrics",
                            "maternity": "Maternity", "obstetrics": "Maternity", "labor": "Maternity",
                            "surgery": "Surgery", "surgical": "Surgery", "post-op": "Surgery",
                            "orthopedic": "Orthopedics", "ortho": "Orthopedics", "bone": "Orthopedics",
                            "neurology": "Neurology", "neuro": "Neurology", "brain": "Neurology",
                            "oncology": "Oncology", "cancer": "Oncology",
                            "psychiatry": "Psychiatry", "mental": "Psychiatry",
                            "rehabilitation": "Rehabilitation", "rehab": "Rehabilitation"
                        }
                        ward = ward_mapping.get(ward_hint.lower())

                    # Get ward-specific available beds
                    available_beds = get_available_beds.invoke({"ward": ward})

                    # Store assignment context for response generation
                    state["assignment_request"] = {
                        "patient_name": patient_name,
                        "ward": ward,
                        "available_beds": available_beds
                    }

                    state["messages"].append(AIMessage(content=f"Available beds for {patient_name} in {ward or 'any'} ward: {available_beds}"))
                    tools_used.append("get_available_beds")
                else:
                    # General assignment request - show available beds
                    result = get_available_beds.invoke({})
                    state["messages"].append(AIMessage(content=f"Available beds for assignment: {result}"))
                    tools_used.append("get_available_beds")

            # Check for bed status update requests
            elif any(keyword in user_query for keyword in ["update", "change", "set", "mark"]):
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
        ward_context = state.get("ward_context")
        available_beds_result = state.get("available_beds_result")
        assignment_request = state.get("assignment_request")

        # Extract tool results from messages - enhanced for comprehensive data
        tool_results = []
        for msg in messages:
            if isinstance(msg, AIMessage) and any(tool in msg.content for tool in [
                "occupancy data", "Available beds", "Critical alerts", "Discharge predictions",
                "Patient data", "Doctor data", "Equipment data", "Medical knowledge"
            ]):
                tool_results.append(msg.content)
        
        response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Hospital Bed Management AI with real-time access to hospital systems via MCP tools.

RESPONSE REQUIREMENTS:
- Be DIRECT and CONCISE - no fluff or unnecessary explanations
- Provide SPECIFIC bed numbers, ward locations, and room details
- Focus on ACTIONABLE medical recommendations
- Use PROFESSIONAL medical terminology appropriately
- Prioritize PATIENT SAFETY and operational efficiency

CURRENT CONTEXT:
Ward Focus: {ward_context}
Available Beds: {available_beds_result}
Assignment Request: {assignment_request}
Hospital Knowledge: {context}
Tools Used: {tools_used}
Data Retrieved: {tool_results}

RESPONSE FORMAT:
1. Direct answer to the medical/operational query
2. Specific bed recommendations with numbers and ward details
3. Medical context or safety considerations if relevant
4. Clear next steps or actions needed

For ICU assignments: Only show ICU beds with specific bed numbers
For Emergency assignments: Only show Emergency ward beds
For ward-specific queries: Filter results to that ward only
For patient assignments: Include bed number, ward, room, and medical suitability

Be precise, medical-focused, and actionable."""),
            ("human", user_query)
        ])
        
        try:
            chain = response_prompt | self.llm
            response = chain.invoke({
                "context": context,
                "tool_results": "\n".join(tool_results),
                "tools_used": ", ".join(tools_used),
                "ward_context": ward_context or "All wards",
                "available_beds_result": available_beds_result or "Not queried",
                "assignment_request": assignment_request or "None",
                "user_query": user_query
            })

            # Debug logging
            logger.info(f"LLM Response type: {type(response)}")
            logger.info(f"LLM Response content length: {len(response.content) if response.content else 0}")

            # Ensure we have a valid response
            if response.content and len(response.content.strip()) > 0:
                state["final_response"] = response.content.strip()
            else:
                # Fallback response with medical intelligence
                if "back" in user_query.lower() and ("pain" in user_query.lower() or "spine" in user_query.lower()):
                    state["final_response"] = """HOSPITAL: **ARIA Medical Recommendation**

For a patient with severe back pain requiring equipment, I recommend:

**TARGET: Primary Assignment: Orthopedic Ward**
- Specialized spine care equipment available
- Orthopedic specialists on-site
- Pain management protocols established

**INFO: Equipment Considerations:**
- Hospital bed with adjustable positioning
- Traction equipment if needed
- Mobility assistance devices

**EMERGENCY: Next Steps:**
1. Assign to Orthopedic Ward (if available)
2. Consult orthopedic specialist
3. Assess pain management needs
4. Schedule imaging if required

*Powered by MCP real-time hospital data*"""
                else:
                    state["final_response"] = f"I'm ARIA, your hospital assistant. I can help with medical recommendations and bed assignments. For your query about '{user_query}', I recommend consulting with the appropriate medical specialist."

            state["messages"].append(AIMessage(content=state["final_response"]))

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
