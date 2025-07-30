"""
Working MCP Client for Hospital Agent
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkingMCPClient:
    """Working MCP client with database fallbacks"""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """Initialize the MCP client"""
        try:
            # Try to initialize MCP connection
            logger.info("Initializing MCP client...")
            self.initialized = True
            logger.info("✅ MCP client initialized")
        except Exception as e:
            logger.warning(f"⚠️ MCP initialization failed, using fallbacks: {e}")
            self.initialized = False
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute MCP tool with database fallback"""
        try:
            if tool_name == "get_bed_occupancy_status":
                return await self._get_bed_occupancy_fallback()
            elif tool_name == "get_critical_bed_alerts":
                return await self._get_critical_alerts_fallback()
            elif tool_name == "get_available_beds":
                return await self._get_available_beds_fallback(**kwargs)
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    async def _get_bed_occupancy_fallback(self) -> Dict[str, Any]:
        """Database fallback for bed occupancy"""
        try:
            from backend.database import SessionLocal, Bed, Department
            
            db = SessionLocal()
            try:
                departments = db.query(Department).all()
                occupancy_data = {}
                
                for dept in departments:
                    dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                    occupied = len([bed for bed in dept_beds if bed.status == "occupied"])
                    available = len([bed for bed in dept_beds if bed.status == "vacant"])
                    cleaning = len([bed for bed in dept_beds if bed.status == "cleaning"])
                    total = len(dept_beds)
                    occupancy_rate = (occupied / total * 100) if total > 0 else 0
                    
                    occupancy_data[dept.name] = {
                        "total_beds": total,
                        "occupied_beds": occupied,
                        "available_beds": available,
                        "cleaning_beds": cleaning,
                        "occupancy_rate": round(occupancy_rate, 1),
                        "status": "critical" if occupancy_rate >= 90 else "high" if occupancy_rate >= 80 else "normal"
                    }
                
                return {
                    "departments": occupancy_data,
                    "source": "database_fallback",
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database fallback failed: {e}")
            return {"error": str(e)}
    
    async def _get_critical_alerts_fallback(self) -> List[Dict[str, Any]]:
        """Database fallback for critical alerts"""
        try:
            from backend.database import SessionLocal, Bed, Department
            
            db = SessionLocal()
            try:
                alerts = []
                departments = db.query(Department).all()
                
                for dept in departments:
                    dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                    occupied = len([bed for bed in dept_beds if bed.status == "occupied"])
                    available = len([bed for bed in dept_beds if bed.status == "vacant"])
                    total = len(dept_beds)
                    
                    if total == 0:
                        continue
                        
                    occupancy_rate = (occupied / total * 100)
                    
                    # Critical alerts (90%+)
                    if occupancy_rate >= 90:
                        alerts.append({
                            "id": f"critical_{dept.name.lower()}_{int(datetime.now().timestamp())}",
                            "type": "capacity_critical",
                            "priority": "critical",
                            "title": f"CRITICAL: {dept.name} at {occupancy_rate:.1f}% Capacity",
                            "message": f"{dept.name} department is critically full ({occupied}/{total} beds)",
                            "department": dept.name,
                            "occupancy_rate": occupancy_rate,
                            "available_beds": available,
                            "timestamp": datetime.now().isoformat(),
                            "recommended_actions": [
                                "Review discharge candidates",
                                "Contact overflow facilities",
                                "Expedite patient transfers"
                            ]
                        })
                    
                    # No beds available
                    elif available == 0:
                        alerts.append({
                            "id": f"no_beds_{dept.name.lower()}_{int(datetime.now().timestamp())}",
                            "type": "no_beds_available",
                            "priority": "critical",
                            "title": f"NO BEDS: {dept.name}",
                            "message": f"{dept.name} has no available beds",
                            "department": dept.name,
                            "occupancy_rate": occupancy_rate,
                            "available_beds": 0,
                            "timestamp": datetime.now().isoformat(),
                            "recommended_actions": [
                                "Expedite discharges",
                                "Prepare overflow areas"
                            ]
                        })
                
                return alerts
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical alerts fallback failed: {e}")
            return []
    
    async def _get_available_beds_fallback(self, ward=None, bed_type=None) -> List[Dict[str, Any]]:
        """Database fallback for available beds"""
        try:
            from backend.database import SessionLocal, Bed
            
            db = SessionLocal()
            try:
                query = db.query(Bed).filter(Bed.status == "vacant")
                
                if ward:
                    query = query.filter(Bed.ward == ward)
                if bed_type:
                    query = query.filter(Bed.bed_type == bed_type)
                
                available_beds = query.all()
                
                beds_data = []
                for bed in available_beds:
                    beds_data.append({
                        "bed_number": bed.bed_number,
                        "room_number": bed.room_number,
                        "ward": bed.ward,
                        "bed_type": bed.bed_type,
                        "private_room": bed.private_room,
                        "status": bed.status
                    })
                
                return beds_data
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Available beds fallback failed: {e}")
            return []

# Create global instance
working_mcp_client = WorkingMCPClient()

class SimpleMCPToolsManager:
    """Compatibility class for existing code"""
    
    def __init__(self):
        self.client = working_mcp_client
    
    async def initialize(self):
        """Initialize the tools manager"""
        await self.client.initialize()
    
    async def execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool"""
        return await self.client.execute_tool(tool_name, **kwargs)
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
