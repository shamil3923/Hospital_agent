"""
Clinical Decision Support System (CDSS)
Integrates RAG policies with MCP real-time data for intelligent recommendations
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, Staff, Department
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, Staff, Department
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from agents.shared.vector_store import vector_store
from hospital_mcp.simple_server import get_server
from alert_system import alert_system, Alert, AlertType, AlertPriority

logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Types of clinical recommendations"""
    BED_ASSIGNMENT = "bed_assignment"
    DISCHARGE_PLANNING = "discharge_planning"
    TRANSFER_RECOMMENDATION = "transfer_recommendation"
    CAPACITY_MANAGEMENT = "capacity_management"
    RESOURCE_ALLOCATION = "resource_allocation"
    QUALITY_IMPROVEMENT = "quality_improvement"
    SAFETY_ALERT = "safety_alert"

class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    IMMEDIATE = "immediate"    # Act within minutes
    URGENT = "urgent"         # Act within hours
    ROUTINE = "routine"       # Act within days
    ADVISORY = "advisory"     # For consideration

@dataclass
class ClinicalRecommendation:
    """Clinical decision support recommendation"""
    id: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    rationale: str
    evidence_sources: List[str]
    recommended_actions: List[str]
    contraindications: List[str]
    related_patient_id: Optional[str] = None
    related_bed_id: Optional[int] = None
    department: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class ClinicalDecisionSupport:
    """Clinical Decision Support System"""
    
    def __init__(self):
        self.active_recommendations: Dict[str, ClinicalRecommendation] = {}
        self.mcp_server = None
        self.running = False
        self.analysis_tasks: List = []
        
        # Initialize MCP server
        try:
            self.mcp_server = get_server()
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
    
    async def start_system(self):
        """Start the clinical decision support system"""
        if self.running:
            return
        
        self.running = True
        logger.info("🧠 Starting Clinical Decision Support System...")
        
        # Start analysis tasks
        self.analysis_tasks = [
            asyncio.create_task(self._continuous_analysis()),
            asyncio.create_task(self._bed_assignment_recommendations()),
            asyncio.create_task(self._discharge_planning_analysis()),
            asyncio.create_task(self._capacity_optimization()),
            asyncio.create_task(self._quality_monitoring()),
            asyncio.create_task(self._safety_surveillance())
        ]
        
        logger.info("✅ Clinical Decision Support System started")
    
    async def stop_system(self):
        """Stop the clinical decision support system"""
        self.running = False
        
        # Cancel all analysis tasks
        for task in self.analysis_tasks:
            task.cancel()
        
        await asyncio.gather(*self.analysis_tasks, return_exceptions=True)
        self.analysis_tasks.clear()
        
        logger.info("🛑 Clinical Decision Support System stopped")
    
    async def get_recommendation(self, query: str, context: Dict[str, Any] = None) -> List[ClinicalRecommendation]:
        """Get clinical recommendations for a specific query"""
        try:
            # Get relevant knowledge from RAG system
            rag_context = await self._get_rag_context(query)
            
            # Get real-time data from MCP
            mcp_data = await self._get_mcp_data(context)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(query, rag_context, mcp_data, context)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def _get_rag_context(self, query: str) -> List[Dict[str, Any]]:
        """Get relevant context from RAG system"""
        try:
            # Use vector store to find relevant knowledge
            relevant_docs = vector_store.similarity_search(query, k=5)
            
            context = []
            for doc in relevant_docs:
                context.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": "hospital_knowledge_base"
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return []
    
    async def _get_mcp_data(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get real-time data from MCP system"""
        try:
            if not self.mcp_server:
                return {}
            
            mcp_data = {}
            
            # Get bed occupancy status
            occupancy_result = await self.mcp_server.call_tool("get_bed_occupancy_status")
            mcp_data["occupancy"] = occupancy_result.get("result", {})
            
            # Get available beds
            available_result = await self.mcp_server.call_tool("get_available_beds")
            mcp_data["available_beds"] = available_result.get("result", [])
            
            # Get critical alerts
            alerts_result = await self.mcp_server.call_tool("get_critical_bed_alerts")
            mcp_data["critical_alerts"] = alerts_result.get("result", [])
            
            # Get discharge predictions if context includes patient info
            if context and context.get("patient_id"):
                discharge_result = await self.mcp_server.call_tool("get_patient_discharge_predictions")
                mcp_data["discharge_predictions"] = discharge_result.get("result", [])
            
            return mcp_data
            
        except Exception as e:
            logger.error(f"Error getting MCP data: {e}")
            return {}
    
    async def _generate_recommendations(self, query: str, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate clinical recommendations based on RAG and MCP data"""
        recommendations = []
        
        try:
            # Analyze query type
            query_lower = query.lower()
            
            # Bed assignment recommendations
            if any(keyword in query_lower for keyword in ["bed", "assign", "placement", "admit"]):
                bed_recs = await self._generate_bed_assignment_recommendations(rag_context, mcp_data, context)
                recommendations.extend(bed_recs)
            
            # Discharge planning recommendations
            if any(keyword in query_lower for keyword in ["discharge", "release", "home"]):
                discharge_recs = await self._generate_discharge_recommendations(rag_context, mcp_data, context)
                recommendations.extend(discharge_recs)
            
            # Capacity management recommendations
            if any(keyword in query_lower for keyword in ["capacity", "occupancy", "full", "overflow"]):
                capacity_recs = await self._generate_capacity_recommendations(rag_context, mcp_data, context)
                recommendations.extend(capacity_recs)
            
            # Transfer recommendations
            if any(keyword in query_lower for keyword in ["transfer", "move", "relocate"]):
                transfer_recs = await self._generate_transfer_recommendations(rag_context, mcp_data, context)
                recommendations.extend(transfer_recs)
            
            # Safety recommendations
            if any(keyword in query_lower for keyword in ["safety", "risk", "alert", "warning"]):
                safety_recs = await self._generate_safety_recommendations(rag_context, mcp_data, context)
                recommendations.extend(safety_recs)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def _generate_bed_assignment_recommendations(self, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate bed assignment recommendations"""
        recommendations = []
        
        try:
            occupancy = mcp_data.get("occupancy", {}).get("overall", {})
            available_beds = mcp_data.get("available_beds", [])
            
            # High occupancy warning
            occupancy_rate = occupancy.get("occupancy_rate", 0)
            if occupancy_rate > 90:
                # Find relevant policy from RAG
                policy_context = [doc for doc in rag_context if "bed" in doc["content"].lower() and "policy" in doc.get("metadata", {}).get("type", "")]
                
                rationale = "Hospital occupancy is critically high. "
                if policy_context:
                    rationale += f"According to hospital policy: {policy_context[0]['content'][:200]}..."
                
                rec = ClinicalRecommendation(
                    id=f"bed_capacity_{int(datetime.now().timestamp())}",
                    type=RecommendationType.CAPACITY_MANAGEMENT,
                    priority=RecommendationPriority.URGENT,
                    title="Critical Bed Capacity Alert",
                    description=f"Hospital occupancy at {occupancy_rate}% - immediate action required",
                    rationale=rationale,
                    evidence_sources=["Real-time occupancy data", "Hospital bed management policy"],
                    recommended_actions=[
                        "Review discharge candidates immediately",
                        "Consider patient transfers to step-down units",
                        "Activate surge capacity protocols",
                        "Contact overflow facilities"
                    ],
                    contraindications=["Do not discharge unstable patients"],
                    department="Bed Management",
                    confidence_score=0.95,
                    metadata={"occupancy_rate": occupancy_rate, "available_beds": len(available_beds)}
                )
                recommendations.append(rec)
            
            # ICU bed optimization
            ward_breakdown = mcp_data.get("occupancy", {}).get("ward_breakdown", [])
            icu_data = next((ward for ward in ward_breakdown if ward["ward"] == "ICU"), None)
            
            if icu_data and icu_data.get("occupancy_rate", 0) > 85:
                # Find ICU-specific policies
                icu_context = [doc for doc in rag_context if "icu" in doc["content"].lower()]
                
                rationale = f"ICU occupancy at {icu_data['occupancy_rate']}%. "
                if icu_context:
                    rationale += f"ICU guidelines state: {icu_context[0]['content'][:200]}..."
                
                rec = ClinicalRecommendation(
                    id=f"icu_optimization_{int(datetime.now().timestamp())}",
                    type=RecommendationType.TRANSFER_RECOMMENDATION,
                    priority=RecommendationPriority.URGENT,
                    title="ICU Capacity Optimization",
                    description="Review ICU patients for step-down opportunities",
                    rationale=rationale,
                    evidence_sources=["ICU occupancy data", "ICU management guidelines"],
                    recommended_actions=[
                        "Review all ICU patients for step-down criteria",
                        "Prioritize stable patients for transfer",
                        "Ensure step-down beds are available",
                        "Coordinate with attending physicians"
                    ],
                    contraindications=["Patients requiring intensive monitoring", "Unstable vital signs"],
                    department="ICU",
                    confidence_score=0.88,
                    metadata={"icu_occupancy": icu_data["occupancy_rate"], "icu_available": icu_data.get("vacant", 0)}
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating bed assignment recommendations: {e}")
            return []
    
    async def _generate_discharge_recommendations(self, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate discharge planning recommendations"""
        recommendations = []
        
        try:
            # Find discharge-related policies
            discharge_context = [doc for doc in rag_context if "discharge" in doc["content"].lower()]
            
            if discharge_context:
                policy = discharge_context[0]
                
                rec = ClinicalRecommendation(
                    id=f"discharge_planning_{int(datetime.now().timestamp())}",
                    type=RecommendationType.DISCHARGE_PLANNING,
                    priority=RecommendationPriority.ROUTINE,
                    title="Discharge Planning Best Practices",
                    description="Follow evidence-based discharge planning protocols",
                    rationale=f"Hospital policy states: {policy['content'][:300]}...",
                    evidence_sources=["Hospital discharge planning policy"],
                    recommended_actions=[
                        "Begin discharge planning within 24 hours of admission",
                        "Conduct multidisciplinary rounds daily",
                        "Identify and address discharge barriers early",
                        "Schedule follow-up appointments before discharge",
                        "Ensure medication reconciliation is complete"
                    ],
                    contraindications=["Medical instability", "Unresolved social issues"],
                    department="Case Management",
                    confidence_score=0.92,
                    metadata={"policy_source": policy.get("metadata", {})}
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating discharge recommendations: {e}")
            return []
    
    async def _generate_capacity_recommendations(self, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate capacity management recommendations"""
        recommendations = []
        
        try:
            occupancy = mcp_data.get("occupancy", {}).get("overall", {})
            occupancy_rate = occupancy.get("occupancy_rate", 0)
            
            # Find capacity management policies
            capacity_context = [doc for doc in rag_context if any(keyword in doc["content"].lower() for keyword in ["capacity", "occupancy", "surge"])]
            
            if occupancy_rate > 95:
                rationale = f"Hospital at {occupancy_rate}% capacity - critical level reached. "
                if capacity_context:
                    rationale += f"Policy guidance: {capacity_context[0]['content'][:200]}..."
                
                rec = ClinicalRecommendation(
                    id=f"capacity_critical_{int(datetime.now().timestamp())}",
                    type=RecommendationType.CAPACITY_MANAGEMENT,
                    priority=RecommendationPriority.IMMEDIATE,
                    title="Critical Capacity Management Required",
                    description="Immediate capacity management interventions needed",
                    rationale=rationale,
                    evidence_sources=["Real-time capacity data", "Capacity management protocols"],
                    recommended_actions=[
                        "Activate hospital incident command",
                        "Implement surge capacity protocols",
                        "Review all patients for early discharge",
                        "Contact regional hospitals for transfers",
                        "Consider elective procedure postponement"
                    ],
                    contraindications=["Do not compromise patient safety"],
                    department="Administration",
                    confidence_score=0.98,
                    metadata={"occupancy_rate": occupancy_rate, "trigger_threshold": 95}
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating capacity recommendations: {e}")
            return []
    
    async def _generate_transfer_recommendations(self, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate patient transfer recommendations"""
        # Implementation for transfer recommendations
        return []
    
    async def _generate_safety_recommendations(self, rag_context: List[Dict], mcp_data: Dict, context: Dict = None) -> List[ClinicalRecommendation]:
        """Generate safety recommendations"""
        recommendations = []
        
        try:
            # Find safety-related policies
            safety_context = [doc for doc in rag_context if any(keyword in doc["content"].lower() for keyword in ["safety", "risk", "infection", "fall"])]
            
            if safety_context:
                for safety_doc in safety_context[:2]:  # Limit to top 2 safety recommendations
                    rec = ClinicalRecommendation(
                        id=f"safety_{safety_doc.get('metadata', {}).get('category', 'general')}_{int(datetime.now().timestamp())}",
                        type=RecommendationType.SAFETY_ALERT,
                        priority=RecommendationPriority.ROUTINE,
                        title=f"Safety Protocol: {safety_doc.get('metadata', {}).get('category', 'General').title()}",
                        description="Follow established safety protocols",
                        rationale=safety_doc["content"],
                        evidence_sources=["Hospital safety policies"],
                        recommended_actions=[
                            "Review and implement safety protocols",
                            "Ensure staff compliance",
                            "Monitor safety metrics",
                            "Report incidents promptly"
                        ],
                        contraindications=[],
                        department="Quality & Safety",
                        confidence_score=0.85,
                        metadata=safety_doc.get("metadata", {})
                    )
                    recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating safety recommendations: {e}")
            return []
    
    # Continuous analysis tasks
    async def _continuous_analysis(self):
        """Continuously analyze hospital data for recommendations"""
        while self.running:
            try:
                # Perform periodic analysis
                await self._analyze_current_state()
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
            
            await asyncio.sleep(300)  # Analyze every 5 minutes
    
    async def _bed_assignment_recommendations(self):
        """Monitor bed assignments and provide recommendations"""
        while self.running:
            try:
                # Check for suboptimal bed assignments
                await self._analyze_bed_assignments()
                
            except Exception as e:
                logger.error(f"Error in bed assignment analysis: {e}")
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    async def _discharge_planning_analysis(self):
        """Analyze discharge planning opportunities"""
        while self.running:
            try:
                # Identify discharge planning opportunities
                await self._analyze_discharge_opportunities()
                
            except Exception as e:
                logger.error(f"Error in discharge planning analysis: {e}")
            
            await asyncio.sleep(900)  # Check every 15 minutes
    
    async def _capacity_optimization(self):
        """Monitor and optimize hospital capacity"""
        while self.running:
            try:
                # Analyze capacity utilization
                await self._analyze_capacity_utilization()
                
            except Exception as e:
                logger.error(f"Error in capacity optimization: {e}")
            
            await asyncio.sleep(180)  # Check every 3 minutes
    
    async def _quality_monitoring(self):
        """Monitor quality metrics and provide recommendations"""
        while self.running:
            try:
                # Analyze quality indicators
                await self._analyze_quality_metrics()
                
            except Exception as e:
                logger.error(f"Error in quality monitoring: {e}")
            
            await asyncio.sleep(1800)  # Check every 30 minutes
    
    async def _safety_surveillance(self):
        """Continuous safety surveillance"""
        while self.running:
            try:
                # Monitor safety indicators
                await self._analyze_safety_indicators()
                
            except Exception as e:
                logger.error(f"Error in safety surveillance: {e}")
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    # Analysis implementation stubs
    async def _analyze_current_state(self):
        """Analyze current hospital state"""
        pass
    
    async def _analyze_bed_assignments(self):
        """Analyze bed assignment efficiency"""
        pass
    
    async def _analyze_discharge_opportunities(self):
        """Analyze discharge opportunities"""
        pass
    
    async def _analyze_capacity_utilization(self):
        """Analyze capacity utilization patterns"""
        pass
    
    async def _analyze_quality_metrics(self):
        """Analyze quality metrics"""
        pass
    
    async def _analyze_safety_indicators(self):
        """Analyze safety indicators"""
        pass
    
    def get_active_recommendations(self) -> List[Dict[str, Any]]:
        """Get all active recommendations"""
        return [
            {
                "id": rec.id,
                "type": rec.type.value,
                "priority": rec.priority.value,
                "title": rec.title,
                "description": rec.description,
                "rationale": rec.rationale,
                "recommended_actions": rec.recommended_actions,
                "confidence_score": rec.confidence_score,
                "created_at": rec.created_at.isoformat(),
                "department": rec.department,
                "metadata": rec.metadata
            }
            for rec in self.active_recommendations.values()
        ]

# Global clinical decision support instance
clinical_decision_support = ClinicalDecisionSupport()
