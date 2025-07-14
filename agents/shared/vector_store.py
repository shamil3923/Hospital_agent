"""
Vector Store and RAG implementation for Hospital Agent Platform
"""
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class HospitalVectorStore:
    """Vector store for hospital knowledge base and RAG"""
    
    def __init__(self):
        self.persist_directory = settings.chroma_persist_directory
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize Chroma vector store
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="hospital_knowledge"
            )
            
            # Initialize with hospital knowledge if empty
            if self.vector_store._collection.count() == 0:
                self._load_initial_knowledge()
                
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _load_initial_knowledge(self):
        """Load initial hospital knowledge base"""
        # Comprehensive hospital knowledge base - Part 1
        hospital_knowledge = [
            # Bed Management Policies
            {
                "content": "Bed occupancy rates above 85% indicate high capacity utilization and may require immediate attention for patient flow optimization. At 90% occupancy, implement surge protocols.",
                "metadata": {"type": "policy", "category": "bed_management", "priority": "high", "department": "all"}
            },
            {
                "content": "Bed assignment priority: Critical patients first, then by admission time. Consider patient condition, required equipment, and isolation needs.",
                "metadata": {"type": "policy", "category": "bed_management", "priority": "high", "department": "all"}
            },
            {
                "content": "Reserved beds policy: Maintain 5% of total beds as emergency reserves. ICU reserves should be 2 beds minimum.",
                "metadata": {"type": "policy", "category": "bed_management", "priority": "medium", "department": "all"}
            },

            # ICU Management
            {
                "content": "ICU beds require specialized equipment: ventilators, cardiac monitors, infusion pumps, and defibrillators. Nurse-to-patient ratio should be 1:2 maximum.",
                "metadata": {"type": "guideline", "category": "icu_management", "priority": "critical", "department": "ICU"}
            },
            {
                "content": "ICU admission criteria: Respiratory failure, hemodynamic instability, neurological compromise, or post-operative monitoring requirements.",
                "metadata": {"type": "guideline", "category": "icu_management", "priority": "critical", "department": "ICU"}
            },
            {
                "content": "ICU discharge criteria: Stable vital signs for 24 hours, no vasopressor support, adequate oxygenation on room air or minimal support.",
                "metadata": {"type": "guideline", "category": "icu_management", "priority": "high", "department": "ICU"}
            },
            {
                "content": "Average ICU length of stay: 3-5 days for stable patients, 7-14 days for complex cases. Monitor daily for step-down opportunities.",
                "metadata": {"type": "guideline", "category": "icu_management", "priority": "medium", "department": "ICU"}
            },

            # Emergency Department
            {
                "content": "Emergency department should maintain at least 10% bed availability for incoming critical cases. Implement diversion protocols when below 5%.",
                "metadata": {"type": "protocol", "category": "emergency_management", "priority": "critical", "department": "Emergency"}
            },
            {
                "content": "ED triage levels: Level 1 (immediate), Level 2 (emergent - 15 min), Level 3 (urgent - 30 min), Level 4 (less urgent - 1 hour), Level 5 (non-urgent - 2 hours).",
                "metadata": {"type": "protocol", "category": "emergency_management", "priority": "critical", "department": "Emergency"}
            },
            {
                "content": "ED boarding time should not exceed 4 hours. Patients waiting longer require escalation to bed management team.",
                "metadata": {"type": "protocol", "category": "emergency_management", "priority": "high", "department": "Emergency"}
            },

            # Patient Flow and Discharge
            {
                "content": "Patient discharge planning should begin within 24 hours of admission. Multidisciplinary rounds should identify discharge barriers daily.",
                "metadata": {"type": "procedure", "category": "patient_flow", "priority": "high", "department": "all"}
            },
            {
                "content": "Discharge criteria checklist: Medical stability, home care arrangements, medication reconciliation, follow-up appointments scheduled, transportation arranged.",
                "metadata": {"type": "procedure", "category": "patient_flow", "priority": "high", "department": "all"}
            },
            {
                "content": "Target discharge times: 11 AM for planned discharges to allow same-day admissions. Weekend discharges require special coordination.",
                "metadata": {"type": "procedure", "category": "patient_flow", "priority": "medium", "department": "all"}
            },
            {
                "content": "Patient transfer protocols: Ensure receiving unit has appropriate bed type, required equipment, and staffing before transfer.",
                "metadata": {"type": "procedure", "category": "patient_flow", "priority": "high", "department": "all"}
            }
        ]

        # Add more comprehensive knowledge - Part 2
        additional_knowledge = [
            # Infection Control and Isolation
            {
                "content": "Isolation room requirements: Negative pressure for airborne precautions, positive pressure for protective isolation. HEPA filtration required.",
                "metadata": {"type": "guideline", "category": "infection_control", "priority": "critical", "department": "all"}
            },
            {
                "content": "Contact isolation: Private room preferred, dedicated equipment, PPE required for all staff contact. Duration based on pathogen type.",
                "metadata": {"type": "guideline", "category": "infection_control", "priority": "critical", "department": "all"}
            },
            {
                "content": "COVID-19 protocols: Negative pressure rooms for suspected/confirmed cases, N95 masks required, limit staff exposure, daily symptom screening.",
                "metadata": {"type": "guideline", "category": "infection_control", "priority": "critical", "department": "all"}
            },

            # Equipment and Maintenance
            {
                "content": "Critical equipment inventory: Each ICU bed requires ventilator, cardiac monitor, infusion pumps (2), suction device, and emergency cart access.",
                "metadata": {"type": "operational", "category": "equipment", "priority": "critical", "department": "ICU"}
            },
            {
                "content": "Equipment maintenance schedules: Daily safety checks, weekly calibration, monthly preventive maintenance, annual certification required.",
                "metadata": {"type": "operational", "category": "equipment", "priority": "high", "department": "all"}
            },
            {
                "content": "Backup equipment policy: 10% spare equipment maintained for critical devices. Emergency equipment carts on each floor.",
                "metadata": {"type": "operational", "category": "equipment", "priority": "high", "department": "all"}
            },

            # Housekeeping and Environmental Services
            {
                "content": "Bed cleaning and preparation typically takes 30-45 minutes between patients. Terminal cleaning for isolation rooms requires 60-90 minutes.",
                "metadata": {"type": "operational", "category": "housekeeping", "priority": "medium", "department": "Environmental"}
            },
            {
                "content": "Room turnover checklist: Disinfection, linen change, equipment check, supply restocking, safety inspection, documentation update.",
                "metadata": {"type": "operational", "category": "housekeeping", "priority": "medium", "department": "Environmental"}
            },
            {
                "content": "Deep cleaning schedule: Weekly for all patient rooms, daily for ICU and isolation rooms, monthly for common areas.",
                "metadata": {"type": "operational", "category": "housekeeping", "priority": "medium", "department": "Environmental"}
            },

            # Staffing and Scheduling
            {
                "content": "Nurse-to-patient ratios: ICU 1:2, Step-down 1:3, Medical/Surgical 1:4-6, Emergency 1:3-4. Adjust based on patient acuity.",
                "metadata": {"type": "guideline", "category": "staffing", "priority": "critical", "department": "Nursing"}
            },
            {
                "content": "Physician coverage requirements: ICU 24/7 intensivist, Emergency 24/7 emergency physician, floors minimum 12-hour coverage with on-call backup.",
                "metadata": {"type": "guideline", "category": "staffing", "priority": "critical", "department": "Medical"}
            },
            {
                "content": "Float pool utilization: Cross-trained nurses available for surge capacity. Minimum 2 hours orientation required for unfamiliar units.",
                "metadata": {"type": "guideline", "category": "staffing", "priority": "medium", "department": "Nursing"}
            },

            # Quality and Safety
            {
                "content": "Patient safety indicators: Fall rates <3 per 1000 patient days, medication errors <1%, hospital-acquired infections <2%, readmission rates <10%.",
                "metadata": {"type": "quality_metric", "category": "safety", "priority": "high", "department": "Quality"}
            },
            {
                "content": "Rapid response team activation criteria: Respiratory rate >30 or <8, Heart rate >130 or <40, Systolic BP <90, Altered mental status, Staff concern.",
                "metadata": {"type": "protocol", "category": "safety", "priority": "critical", "department": "all"}
            },
            {
                "content": "Code blue procedures: Immediate response within 3 minutes, designated team roles, post-event debriefing required, documentation within 24 hours.",
                "metadata": {"type": "protocol", "category": "safety", "priority": "critical", "department": "all"}
            },

            # Technology and Documentation
            {
                "content": "Real-time bed status updates are critical for efficient patient placement. System updates required within 15 minutes of status changes.",
                "metadata": {"type": "best_practice", "category": "technology", "priority": "high", "department": "IT"}
            },
            {
                "content": "Electronic health record documentation: Real-time entry preferred, maximum 24-hour delay acceptable, all entries require authentication.",
                "metadata": {"type": "best_practice", "category": "technology", "priority": "high", "department": "all"}
            },
            {
                "content": "Bed management system integration: Automatic updates from ADT system, real-time census reporting, predictive analytics for capacity planning.",
                "metadata": {"type": "best_practice", "category": "technology", "priority": "medium", "department": "IT"}
            },

            # Financial and Administrative
            {
                "content": "Length of stay optimization: Target LOS by diagnosis, daily utilization review, case management intervention for extended stays.",
                "metadata": {"type": "administrative", "category": "financial", "priority": "medium", "department": "Administration"}
            },
            {
                "content": "Bed utilization targets: 85-90% occupancy optimal, >95% indicates capacity strain, <80% suggests inefficiency.",
                "metadata": {"type": "administrative", "category": "financial", "priority": "medium", "department": "Administration"}
            },
            {
                "content": "Revenue cycle management: Accurate bed charges, timely discharge processing, insurance verification within 24 hours of admission.",
                "metadata": {"type": "administrative", "category": "financial", "priority": "medium", "department": "Finance"}
            }
        ]

        # Combine all knowledge
        all_knowledge = hospital_knowledge + additional_knowledge

        documents = [
            Document(
                page_content=item["content"],
                metadata=item["metadata"]
            )
            for item in all_knowledge
        ]
        
        self.vector_store.add_documents(documents)
        logger.info(f"Loaded {len(documents)} knowledge documents")
    
    def search_knowledge(self, query: str, k: int = 3) -> List[Document]:
        """Search knowledge base for relevant information"""
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def add_knowledge(self, content: str, metadata: Dict[str, Any]):
        """Add new knowledge to the vector store"""
        try:
            document = Document(page_content=content, metadata=metadata)
            self.vector_store.add_documents([document])
            logger.info("Added new knowledge document")
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
    
    def get_context_for_query(self, query: str, max_context_length: int = 1000) -> str:
        """Get relevant context for a query"""
        relevant_docs = self.search_knowledge(query)
        
        context_parts = []
        current_length = 0
        
        for doc in relevant_docs:
            content = doc.page_content
            if current_length + len(content) <= max_context_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                # Add partial content if it fits
                remaining_space = max_context_length - current_length
                if remaining_space > 50:  # Only add if meaningful space remains
                    context_parts.append(content[:remaining_space] + "...")
                break
        
        return "\n\n".join(context_parts)


# Global vector store instance
vector_store = HospitalVectorStore()
