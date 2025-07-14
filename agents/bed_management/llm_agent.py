"""
LLM-Powered Bed Management Agent
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any

class LLMBedAgent:
    def __init__(self):
        self.db_path = "hospital.db"
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Gemini LLM"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyCrEfICW4RYyJW45Uy0ZSduXVKUKjNu25I")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=api_key,
                temperature=0.1
            )
            print("LLM initialized successfully")
            
        except Exception as e:
            print(f"LLM initialization failed: {e}")
            self.llm = None
    
    def get_bed_data(self):
        """Get comprehensive bed data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all beds with details
            cursor.execute("""
                SELECT bed_number, room_number, ward, bed_type, status, patient_id 
                FROM beds 
                ORDER BY ward, room_number
            """)
            beds = cursor.fetchall()
            
            # Get summary statistics
            cursor.execute("SELECT COUNT(*) FROM beds")
            total_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'occupied'")
            occupied_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'vacant'")
            vacant_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'cleaning'")
            cleaning_beds = cursor.fetchone()[0]
            
            # Get ward-wise breakdown
            cursor.execute("""
                SELECT ward, 
                       COUNT(*) as total,
                       SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                       SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) as vacant
                FROM beds 
                GROUP BY ward
            """)
            ward_stats = cursor.fetchall()
            
            conn.close()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            return {
                "beds": beds,
                "summary": {
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "vacant_beds": vacant_beds,
                    "cleaning_beds": cleaning_beds,
                    "occupancy_rate": round(occupancy_rate, 1)
                },
                "ward_stats": ward_stats
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def create_context_prompt(self, user_query: str, bed_data: Dict) -> str:
        """Create a context-rich prompt for the LLM"""
        
        if "error" in bed_data:
            return f"""
You are a Hospital Bed Management Agent. The user asked: "{user_query}"

Unfortunately, I'm experiencing a database error: {bed_data['error']}

Please respond helpfully and suggest they contact IT support.
"""
        
        summary = bed_data["summary"]
        ward_stats = bed_data["ward_stats"]
        
        # Format ward statistics
        ward_info = []
        for ward, total, occupied, vacant in ward_stats:
            ward_info.append(f"- {ward}: {occupied}/{total} occupied ({vacant} available)")
        
        ward_breakdown = "\n".join(ward_info)
        
        prompt = f"""
You are an intelligent Hospital Bed Management Agent. A user has asked: "{user_query}"

Current Hospital Status:
- Total Beds: {summary['total_beds']}
- Occupied: {summary['occupied_beds']} ({summary['occupancy_rate']}%)
- Available: {summary['vacant_beds']}
- Cleaning: {summary['cleaning_beds']}

Ward Breakdown:
{ward_breakdown}

Instructions:
1. Answer the user's question directly and helpfully
2. Use the provided data to give accurate, specific information
3. Be professional but friendly
4. If asked about predictions or future planning, provide thoughtful insights based on current data
5. If the question is outside bed management, politely redirect to bed-related topics
6. Always be concise but informative

Respond as the Hospital Bed Management Agent:
"""
        return prompt
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query with LLM intelligence"""
        
        # Get current bed data
        bed_data = self.get_bed_data()
        
        # If LLM is not available, fall back to simple responses
        if not self.llm:
            return self._fallback_response(query, bed_data)
        
        try:
            # Create context prompt
            prompt = self.create_context_prompt(query, bed_data)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            return {
                "response": response.content,
                "timestamp": datetime.now().isoformat(),
                "agent": "llm_bed_agent",
                "data_used": bed_data.get("summary", {}),
                "llm_used": True
            }
            
        except Exception as e:
            print(f"LLM processing error: {e}")
            return self._fallback_response(query, bed_data)
    
    def _fallback_response(self, query: str, bed_data: Dict) -> Dict[str, Any]:
        """Fallback response when LLM is not available"""
        
        if "error" in bed_data:
            response = f"I'm experiencing a database error: {bed_data['error']}. Please contact IT support."
        else:
            summary = bed_data["summary"]
            query_lower = query.lower()
            
            if any(word in query_lower for word in ["occupancy", "status", "current"]):
                response = f"Current bed occupancy is {summary['occupancy_rate']}% with {summary['occupied_beds']} occupied beds out of {summary['total_beds']} total beds. {summary['vacant_beds']} beds are available."
            
            elif any(word in query_lower for word in ["available", "vacant", "free"]):
                response = f"There are {summary['vacant_beds']} available beds out of {summary['total_beds']} total beds."
            
            elif any(word in query_lower for word in ["predict", "forecast", "future", "flow"]):
                response = f"Based on current data, we have {summary['vacant_beds']} available beds. For detailed predictions, I'd need historical data patterns. Currently {summary['cleaning_beds']} beds are being cleaned and will be available soon."
            
            else:
                response = f"I'm the Bed Management Agent. Current status: {summary['occupied_beds']}/{summary['total_beds']} beds occupied ({summary['occupancy_rate']}%). How can I help you with bed management?"
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "agent": "llm_bed_agent_fallback",
            "data_used": bed_data.get("summary", {}),
            "llm_used": False
        }

# Global instance
llm_bed_agent = LLMBedAgent()
