"""
Simplified Bed Management Agent
"""
from datetime import datetime
import sqlite3
import json

class SimpleBedAgent:
    def __init__(self):
        self.db_path = "hospital.db"
    
    def get_bed_occupancy(self):
        """Get bed occupancy statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM beds")
            total_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'occupied'")
            occupied_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'vacant'")
            vacant_beds = cursor.fetchone()[0]
            
            conn.close()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            return {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "occupancy_rate": round(occupancy_rate, 1)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def process_query(self, query):
        """Process user query"""
        query_lower = query.lower()
        
        if "occupancy" in query_lower or "status" in query_lower:
            data = self.get_bed_occupancy()
            if "error" in data:
                response = f"Sorry, I encountered an error: {data['error']}"
            else:
                response = f"Current bed occupancy is {data['occupancy_rate']}% with {data['occupied_beds']} occupied beds out of {data['total_beds']} total beds. {data['vacant_beds']} beds are available."
        
        elif "available" in query_lower or "vacant" in query_lower:
            data = self.get_bed_occupancy()
            if "error" in data:
                response = f"Sorry, I encountered an error: {data['error']}"
            else:
                response = f"There are {data['vacant_beds']} available beds out of {data['total_beds']} total beds."
        
        else:
            response = "I'm the Bed Management Agent. I can help you with bed occupancy and availability. Try asking: 'What is the current bed occupancy?' or 'How many beds are available?'"
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "agent": "simple_bed_agent"
        }

# Global instance
simple_bed_agent = SimpleBedAgent()
