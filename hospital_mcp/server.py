"""
MCP Server for Hospital Bed Management Tools
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime, timedelta

from mcp import stdio_server
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import database and existing tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Bed, Patient, BedOccupancyHistory
from sqlalchemy import func

logger = logging.getLogger(__name__)

class HospitalMCPServer:
    """MCP Server for Hospital Bed Management"""
    
    def __init__(self):
        self.server = Server("hospital-bed-management")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_bed_occupancy_status",
                    description="Get current bed occupancy status across all wards",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_available_beds",
                    description="Get list of available beds, optionally filtered by ward or bed type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ward": {
                                "type": "string",
                                "description": "Filter by ward (ICU, Emergency, General, etc.)",
                                "enum": ["ICU", "Emergency", "General", "Pediatric", "Maternity"]
                            },
                            "bed_type": {
                                "type": "string",
                                "description": "Filter by bed type"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_critical_bed_alerts",
                    description="Get critical bed management alerts and recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_patient_discharge_predictions",
                    description="Get predicted patient discharges for bed planning",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="update_bed_status",
                    description="Update bed status (occupied, vacant, cleaning, maintenance)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bed_number": {
                                "type": "string",
                                "description": "Bed number to update"
                            },
                            "new_status": {
                                "type": "string",
                                "description": "New status for the bed",
                                "enum": ["occupied", "vacant", "cleaning", "maintenance"]
                            },
                            "patient_id": {
                                "type": "string",
                                "description": "Patient ID (required if status is occupied)",
                                "optional": True
                            }
                        },
                        "required": ["bed_number", "new_status"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls"""
            try:
                if name == "get_bed_occupancy_status":
                    result = await self._get_bed_occupancy_status()
                elif name == "get_available_beds":
                    result = await self._get_available_beds(
                        arguments.get("ward"),
                        arguments.get("bed_type")
                    )
                elif name == "get_critical_bed_alerts":
                    result = await self._get_critical_bed_alerts()
                elif name == "get_patient_discharge_predictions":
                    result = await self._get_patient_discharge_predictions()
                elif name == "update_bed_status":
                    result = await self._update_bed_status(
                        arguments["bed_number"],
                        arguments["new_status"],
                        arguments.get("patient_id")
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    async def _get_bed_occupancy_status(self) -> Dict[str, Any]:
        """Get current bed occupancy status across all wards"""
        db = SessionLocal()
        try:
            # Get overall statistics
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            vacant_beds = db.query(Bed).filter(Bed.status == "vacant").count()
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
            maintenance_beds = db.query(Bed).filter(Bed.status == "maintenance").count()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            # Get ward-wise breakdown
            ward_stats = db.query(
                Bed.ward,
                func.count(Bed.id).label('total'),
                func.sum(func.case([(Bed.status == 'occupied', 1)], else_=0)).label('occupied'),
                func.sum(func.case([(Bed.status == 'vacant', 1)], else_=0)).label('vacant'),
                func.sum(func.case([(Bed.status == 'cleaning', 1)], else_=0)).label('cleaning')
            ).group_by(Bed.ward).all()
            
            ward_breakdown = []
            for ward in ward_stats:
                ward_occupancy = (ward.occupied / ward.total * 100) if ward.total > 0 else 0
                ward_breakdown.append({
                    "ward": ward.ward,
                    "total_beds": ward.total,
                    "occupied": ward.occupied,
                    "vacant": ward.vacant,
                    "cleaning": ward.cleaning,
                    "occupancy_rate": round(ward_occupancy, 1)
                })
            
            return {
                "overall": {
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "vacant_beds": vacant_beds,
                    "cleaning_beds": cleaning_beds,
                    "maintenance_beds": maintenance_beds,
                    "occupancy_rate": round(occupancy_rate, 1)
                },
                "ward_breakdown": ward_breakdown,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting bed occupancy status: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def _get_available_beds(self, ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available beds, optionally filtered by ward or bed type"""
        db = SessionLocal()
        try:
            query = db.query(Bed).filter(Bed.status == "vacant")
            
            if ward:
                query = query.filter(Bed.ward == ward)
            if bed_type:
                query = query.filter(Bed.bed_type == bed_type)
                
            available_beds = query.all()
            
            result = []
            for bed in available_beds:
                result.append({
                    "bed_id": bed.id,
                    "bed_number": bed.bed_number,
                    "room_number": bed.room_number,
                    "ward": bed.ward,
                    "bed_type": bed.bed_type,
                    "last_updated": bed.last_updated
                })
            
            return result

        except Exception as e:
            logger.error(f"Error getting available beds: {e}")
            return []
        finally:
            db.close()

    async def _get_critical_bed_alerts(self) -> List[Dict[str, Any]]:
        """Get critical bed management alerts and recommendations"""
        db = SessionLocal()
        try:
            alerts = []

            # Check overall occupancy rate
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

            if occupancy_rate > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"Hospital occupancy at {occupancy_rate:.1f}% - Critical capacity reached",
                    "recommendation": "Initiate discharge planning and consider patient transfers",
                    "priority": "high"
                })
            elif occupancy_rate > 85:
                alerts.append({
                    "type": "warning",
                    "message": f"Hospital occupancy at {occupancy_rate:.1f}% - High capacity",
                    "recommendation": "Monitor closely and prepare for potential capacity issues",
                    "priority": "medium"
                })

            # Check ICU capacity specifically
            icu_total = db.query(Bed).filter(Bed.ward == "ICU").count()
            icu_occupied = db.query(Bed).filter(Bed.ward == "ICU", Bed.status == "occupied").count()
            icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0

            if icu_rate > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"ICU occupancy at {icu_rate:.1f}% - Critical care capacity reached",
                    "recommendation": "Review ICU patients for potential step-down candidates",
                    "priority": "high"
                })

            # Check for beds in cleaning status for too long
            cleaning_threshold = datetime.now() - timedelta(hours=2)
            long_cleaning_beds = db.query(Bed).filter(
                Bed.status == "cleaning",
                Bed.last_updated < cleaning_threshold.isoformat()
            ).count()

            if long_cleaning_beds > 0:
                alerts.append({
                    "type": "operational",
                    "message": f"{long_cleaning_beds} beds in cleaning status for over 2 hours",
                    "recommendation": "Check with housekeeping team for cleaning delays",
                    "priority": "medium"
                })

            return alerts

        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}")
            return []
        finally:
            db.close()

    async def _get_patient_discharge_predictions(self) -> List[Dict[str, Any]]:
        """Get predicted patient discharges for bed planning"""
        db = SessionLocal()
        try:
            # Get patients with expected discharge dates
            upcoming_discharges = db.query(Patient).filter(
                Patient.status == "admitted",
                Patient.expected_discharge_date.isnot(None),
                Patient.expected_discharge_date >= datetime.now(),
                Patient.expected_discharge_date <= datetime.now() + timedelta(days=3)
            ).all()

            predictions = []
            for patient in upcoming_discharges:
                bed = db.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                predictions.append({
                    "patient_id": patient.patient_id,
                    "patient_name": patient.name,
                    "current_bed": bed.bed_number if bed else "Unknown",
                    "ward": bed.ward if bed else "Unknown",
                    "expected_discharge": patient.expected_discharge_date.isoformat(),
                    "condition": patient.condition,
                    "severity": patient.severity
                })

            return sorted(predictions, key=lambda x: x["expected_discharge"])

        except Exception as e:
            logger.error(f"Error getting discharge predictions: {e}")
            return []
        finally:
            db.close()

    async def _update_bed_status(self, bed_number: str, new_status: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Update bed status (occupied, vacant, cleaning, maintenance)"""
        db = SessionLocal()
        try:
            bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
            if not bed:
                return {"error": f"Bed {bed_number} not found"}

            old_status = bed.status
            bed.status = new_status
            bed.patient_id = patient_id
            bed.last_updated = datetime.now().isoformat()

            if new_status == "occupied" and patient_id:
                bed.admission_time = datetime.now().isoformat()
            elif new_status == "vacant":
                bed.admission_time = None
                bed.expected_discharge = None
                bed.patient_id = None

            db.commit()

            return {
                "success": True,
                "bed_number": bed_number,
                "old_status": old_status,
                "new_status": new_status,
                "patient_id": patient_id,
                "updated_at": bed.last_updated
            }

        except Exception as e:
            logger.error(f"Error updating bed status: {e}")
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as streams:
            await self.server.run(*streams)


async def main():
    """Main function to run the MCP server"""
    logging.basicConfig(level=logging.INFO)
    server = HospitalMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
