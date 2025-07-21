"""
Hospital-specific RAG (Retrieval-Augmented Generation) System
Provides relevant hospital information and procedures
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HospitalRAGSystem:
    def __init__(self):
        self.knowledge_base = {
            'bed_management': {
                'icu_procedures': [
                    "ICU beds require specialized monitoring equipment",
                    "ICU patients need 1:1 or 1:2 nurse-to-patient ratios",
                    "ICU admissions require attending physician approval",
                    "ICU beds have ventilator capabilities and cardiac monitoring",
                    "ICU discharge planning should begin within 24 hours of admission"
                ],
                'emergency_procedures': [
                    "Emergency beds are for acute care patients requiring immediate attention",
                    "Emergency department follows triage protocols for bed assignment",
                    "Emergency beds should be turned over within 4 hours when possible",
                    "Emergency patients may need rapid transfer to specialized units"
                ],
                'general_procedures': [
                    "General ward beds are for stable patients requiring ongoing care",
                    "General ward patients typically have 1:4 to 1:6 nurse ratios",
                    "Bed assignments should consider patient acuity and care needs",
                    "Discharge planning begins on admission day"
                ]
            },
            'patient_assignment': {
                'criteria': [
                    "Patient acuity level determines appropriate bed type",
                    "Isolation requirements affect bed placement",
                    "Patient age and gender preferences when possible",
                    "Proximity to nursing station for high-acuity patients",
                    "Equipment needs (telemetry, oxygen, etc.)"
                ],
                'workflow': [
                    "Verify bed availability and cleanliness status",
                    "Confirm appropriate medical equipment is functional",
                    "Notify nursing staff of incoming patient",
                    "Update electronic health record with bed assignment",
                    "Coordinate with housekeeping for room preparation"
                ]
            },
            'doctor_assignment': {
                'specialties': {
                    'ICU': ['Critical Care Medicine', 'Pulmonology', 'Cardiology'],
                    'Emergency': ['Emergency Medicine', 'Trauma Surgery', 'Internal Medicine'],
                    'General': ['Internal Medicine', 'Family Medicine', 'Hospitalist'],
                    'Pediatric': ['Pediatrics', 'Pediatric Surgery'],
                    'Cardiac': ['Cardiology', 'Cardiac Surgery'],
                    'Surgical': ['General Surgery', 'Orthopedics', 'Neurosurgery']
                },
                'assignment_rules': [
                    "Primary attending physician based on patient condition",
                    "Consulting specialists as needed for complex cases",
                    "On-call coverage for after-hours admissions",
                    "Continuity of care when possible"
                ]
            },
            'hospital_policies': {
                'admission_criteria': [
                    "Medical necessity for inpatient level of care",
                    "Appropriate bed type available for patient needs",
                    "Insurance authorization when required",
                    "Completed admission orders and documentation"
                ],
                'discharge_criteria': [
                    "Medical stability for discharge destination",
                    "Appropriate follow-up care arranged",
                    "Patient/family education completed",
                    "Discharge medications reconciled"
                ],
                'capacity_management': [
                    "Monitor bed occupancy rates by unit",
                    "Coordinate with case management for discharge planning",
                    "Implement overflow protocols when at capacity",
                    "Communicate capacity status to emergency department"
                ]
            },
            'emergency_protocols': {
                'code_blue': [
                    "Immediate response team activation",
                    "Clear bed space for resuscitation efforts",
                    "Notify attending physician and family",
                    "Document all interventions and outcomes"
                ],
                'rapid_response': [
                    "Early intervention for deteriorating patients",
                    "Assess need for higher level of care",
                    "Consider ICU transfer if indicated",
                    "Communicate with primary team"
                ],
                'disaster_protocols': [
                    "Activate incident command system",
                    "Implement surge capacity plans",
                    "Coordinate with external agencies",
                    "Prioritize resources based on patient acuity"
                ]
            }
        }
        
        self.common_queries = {
            'bed_availability': [
                'how many beds', 'bed status', 'available beds', 'occupancy rate'
            ],
            'patient_admission': [
                'admit patient', 'assign bed', 'patient placement', 'admission process'
            ],
            'doctor_assignment': [
                'assign doctor', 'attending physician', 'specialist', 'medical team'
            ],
            'discharge_planning': [
                'discharge', 'release patient', 'discharge planning', 'send home'
            ],
            'emergency_procedures': [
                'emergency', 'urgent', 'critical', 'code blue', 'rapid response'
            ]
        }
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        query_lower = query.lower()
        results = []
        
        # Determine query category
        category = self.categorize_query(query_lower)
        
        # Search relevant sections
        for section, content in self.knowledge_base.items():
            if category and category in section:
                # High relevance match
                relevance = 0.9
            else:
                # Check for keyword matches
                relevance = self.calculate_relevance(query_lower, content)
            
            if relevance > 0.3:  # Threshold for inclusion
                results.append({
                    'section': section,
                    'content': content,
                    'relevance': relevance,
                    'type': 'knowledge_base'
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:5]  # Return top 5 results
    
    def categorize_query(self, query: str) -> str:
        """Categorize the query to find most relevant information"""
        for category, keywords in self.common_queries.items():
            if any(keyword in query for keyword in keywords):
                return category
        return None
    
    def calculate_relevance(self, query: str, content: Any) -> float:
        """Calculate relevance score between query and content"""
        if isinstance(content, dict):
            # Search in dictionary values
            text = ' '.join(str(v) for v in content.values() if isinstance(v, (str, list)))
        elif isinstance(content, list):
            text = ' '.join(str(item) for item in content)
        else:
            text = str(content)
        
        text_lower = text.lower()
        query_words = query.split()
        
        # Count matching words
        matches = sum(1 for word in query_words if word in text_lower)
        return matches / len(query_words) if query_words else 0
    
    def generate_contextual_response(self, query: str, search_results: List[Dict]) -> str:
        """Generate a contextual response based on search results"""
        if not search_results:
            return self.get_default_response(query)
        
        # Get the most relevant result
        top_result = search_results[0]
        section = top_result['section']
        content = top_result['content']
        
        response = f"📋 **Hospital Information - {section.replace('_', ' ').title()}**\n\n"
        
        if isinstance(content, dict):
            for key, value in content.items():
                response += f"**{key.replace('_', ' ').title()}:**\n"
                if isinstance(value, list):
                    for item in value[:3]:  # Show top 3 items
                        response += f"• {item}\n"
                else:
                    response += f"• {value}\n"
                response += "\n"
        elif isinstance(content, list):
            response += "**Key Points:**\n"
            for item in content[:5]:  # Show top 5 items
                response += f"• {item}\n"
        
        response += f"\n💡 **Related Actions:**\n"
        response += self.get_suggested_actions(section, query)
        
        return response
    
    def get_suggested_actions(self, section: str, query: str) -> str:
        """Get suggested actions based on the section and query"""
        actions = {
            'bed_management': [
                "Check current bed availability",
                "View bed occupancy by ward",
                "Assign patient to available bed"
            ],
            'patient_assignment': [
                "Start patient admission workflow",
                "Check patient placement criteria",
                "Notify nursing staff of assignment"
            ],
            'doctor_assignment': [
                "Find available specialists",
                "Check doctor schedules",
                "Assign attending physician"
            ],
            'hospital_policies': [
                "Review admission criteria",
                "Check discharge requirements",
                "View capacity management protocols"
            ],
            'emergency_protocols': [
                "Activate emergency response",
                "Check rapid response criteria",
                "Review disaster protocols"
            ]
        }
        
        section_actions = actions.get(section, ["Ask for more specific information"])
        return '\n'.join(f"• {action}" for action in section_actions[:3])
    
    def get_default_response(self, query: str) -> str:
        """Generate default response when no specific knowledge found"""
        return f"""🏥 **Hospital Operations Assistant**

I understand you're asking about: "{query}"

While I don't have specific information about that topic in my knowledge base, I can help you with:

📋 **Bed Management:**
• Check bed availability by ward type
• Assign patients to appropriate beds
• Monitor occupancy rates

👨‍⚕️ **Staff Coordination:**
• Find available doctors by specialty
• Check nursing assignments
• Coordinate medical teams

📊 **Hospital Operations:**
• Review admission and discharge procedures
• Emergency response protocols
• Capacity management

Could you please be more specific? For example:
• "Show me ICU bed procedures"
• "What are the admission criteria?"
• "How do I assign a doctor to a patient?"
"""
    
    def enhance_chat_response(self, query: str, base_response: str) -> str:
        """Enhance chat response with RAG information"""
        search_results = self.search_knowledge(query)
        
        if search_results and search_results[0]['relevance'] > 0.5:
            rag_response = self.generate_contextual_response(query, search_results)
            
            # Combine base response with RAG enhancement
            enhanced_response = f"{base_response}\n\n---\n\n{rag_response}"
            return enhanced_response
        
        return base_response
