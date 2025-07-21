#!/usr/bin/env python3
"""
Enhanced MCP Server for Hospital Agent with useful tools
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.models import InitializeResult
from mcp.server.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import hospital backend
try:
    from backend.database import SessionLocal, Bed, Patient, BedOccupancyHistory
    from backend.alert_system import alert_system, Alert, AlertType, AlertPriority
    from backend.autonomous_bed_agent import autonomous_bed_agent
    from backend.intelligent_bed_assignment import intelligent_bed_assignment
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")
    SessionLocal = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital-mcp-server")

# Create server instance
server = Server("hospital-enhanced-mcp")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available hospital management tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="get_hospital_status",
                description="Get comprehensive hospital status including bed occupancy, alerts, and system health",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_predictions": {
                            "type": "boolean",
                            "description": "Include 24-hour predictions",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_critical_alerts",
                description="Get all critical alerts requiring immediate attention",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "string",
                            "description": "Filter by department (ICU, Emergency, General, etc.)",
                            "default": None
                        }
                    }
                }
            ),
            Tool(
                name="find_available_beds",
                description="Find available beds matching specific criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bed_type": {
                            "type": "string",
                            "description": "Type of bed needed (ICU, General, Emergency, Pediatric, Maternity)"
                        },
                        "ward": {
                            "type": "string",
                            "description": "Preferred ward"
                        },
                        "isolation_required": {
                            "type": "boolean",
                            "description": "Requires isolation room",
                            "default": False
                        },
                        "private_room": {
                            "type": "boolean",
                            "description": "Requires private room",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_bed_recommendations",
                description="Get AI-powered bed recommendations for a patient",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient ID to get recommendations for"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Assignment priority (emergency, urgent, routine)",
                            "default": "routine"
                        }
                    },
                    "required": ["patient_id"]
                }
            ),
            Tool(
                name="trigger_capacity_alert",
                description="Manually trigger capacity alerts for testing or emergency situations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "string",
                            "description": "Department to check (ICU, Emergency, General, All)",
                            "default": "All"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force alert creation even if thresholds not met",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_autonomous_system_status",
                description="Get status of all autonomous systems and their performance metrics",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="predict_bed_demand",
                description="Get 24-hour bed demand predictions with risk assessment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ward": {
                            "type": "string",
                            "description": "Specific ward to predict (optional)"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Number of hours to predict (1-24)",
                            "default": 24
                        }
                    }
                }
            ),
            Tool(
                name="optimize_bed_assignments",
                description="Run AI optimization to suggest better bed assignments",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ward": {
                            "type": "string",
                            "description": "Focus on specific ward (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="generate_capacity_report",
                description="Generate comprehensive capacity management report",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Report format (summary, detailed, json)",
                            "default": "summary"
                        }
                    }
                }
            ),
            Tool(
                name="emergency_bed_protocol",
                description="Activate emergency bed allocation protocol",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Emergency patient ID"
                        },
                        "condition": {
                            "type": "string",
                            "description": "Patient condition/diagnosis"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Emergency priority level (critical, urgent)",
                            "default": "critical"
                        }
                    },
                    "required": ["patient_id", "condition"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "get_hospital_status":
            return await get_hospital_status(arguments)
        elif name == "get_critical_alerts":
            return await get_critical_alerts(arguments)
        elif name == "find_available_beds":
            return await find_available_beds(arguments)
        elif name == "get_bed_recommendations":
            return await get_bed_recommendations(arguments)
        elif name == "trigger_capacity_alert":
            return await trigger_capacity_alert(arguments)
        elif name == "get_autonomous_system_status":
            return await get_autonomous_system_status(arguments)
        elif name == "predict_bed_demand":
            return await predict_bed_demand(arguments)
        elif name == "optimize_bed_assignments":
            return await optimize_bed_assignments(arguments)
        elif name == "generate_capacity_report":
            return await generate_capacity_report(arguments)
        elif name == "emergency_bed_protocol":
            return await emergency_bed_protocol(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def get_hospital_status(args: Dict[str, Any]) -> CallToolResult:
    """Get comprehensive hospital status"""
    if not SessionLocal:
        return CallToolResult(
            content=[TextContent(type="text", text="Database not available")]
        )
    
    try:
        with SessionLocal() as db:
            # Basic metrics
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            available_beds = db.query(Bed).filter(Bed.status == "vacant").count()
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            # Ward breakdown
            wards = {}
            for ward_name in ["ICU", "Emergency", "General", "Pediatric", "Maternity"]:
                ward_total = db.query(Bed).filter(Bed.ward == ward_name).count()
                ward_occupied = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == "occupied").count()
                ward_rate = (ward_occupied / ward_total * 100) if ward_total > 0 else 0
                
                wards[ward_name] = {
                    "total": ward_total,
                    "occupied": ward_occupied,
                    "available": ward_total - ward_occupied,
                    "occupancy_rate": ward_rate,
                    "status": "critical" if ward_rate >= 90 else "high" if ward_rate >= 80 else "normal"
                }
            
            # Get active alerts
            alerts = []
            if alert_system:
                active_alerts = alert_system.get_active_alerts()
                alerts = [
                    {
                        "priority": alert["priority"],
                        "title": alert["title"],
                        "department": alert["department"],
                        "message": alert["message"]
                    }
                    for alert in active_alerts
                ]
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "overall": {
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "available_beds": available_beds,
                    "cleaning_beds": cleaning_beds,
                    "occupancy_rate": round(occupancy_rate, 1),
                    "status": "critical" if occupancy_rate >= 90 else "high" if occupancy_rate >= 80 else "normal"
                },
                "wards": wards,
                "alerts": {
                    "total": len(alerts),
                    "critical": len([a for a in alerts if a["priority"] == "critical"]),
                    "high": len([a for a in alerts if a["priority"] == "high"]),
                    "active_alerts": alerts[:5]  # Show top 5
                },
                "system_health": {
                    "autonomous_systems": "operational" if autonomous_bed_agent else "unavailable",
                    "alert_system": "operational" if alert_system else "unavailable",
                    "bed_assignment": "operational" if intelligent_bed_assignment else "unavailable"
                }
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(status, indent=2))]
            )
            
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error getting hospital status: {str(e)}")]
        )

# Additional tool implementations would go here...
# (Continuing with other tools in the next part due to length limit)

async def get_critical_alerts(args: Dict[str, Any]) -> CallToolResult:
    """Get critical alerts"""
    if not alert_system:
        return CallToolResult(
            content=[TextContent(type="text", text="Alert system not available")]
        )
    
    try:
        alerts = alert_system.get_active_alerts()
        department = args.get("department")
        
        if department:
            alerts = [a for a in alerts if a.get("department", "").lower() == department.lower()]
        
        critical_alerts = [a for a in alerts if a.get("priority") == "critical"]
        
        if not critical_alerts:
            return CallToolResult(
                content=[TextContent(type="text", text="No critical alerts found")]
            )
        
        result = {
            "critical_alerts_count": len(critical_alerts),
            "alerts": critical_alerts
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error getting critical alerts: {str(e)}")]
        )

async def trigger_capacity_alert(args: Dict[str, Any]) -> CallToolResult:
    """Trigger capacity alerts"""
    if not alert_system:
        return CallToolResult(
            content=[TextContent(type="text", text="Alert system not available")]
        )
    
    try:
        department = args.get("department", "All")
        force = args.get("force", False)
        
        # Force capacity check
        await alert_system._monitor_capacity_levels()
        
        # Get resulting alerts
        alerts = alert_system.get_active_alerts()
        capacity_alerts = [a for a in alerts if "capacity" in a.get("title", "").lower()]
        
        result = {
            "triggered": True,
            "department": department,
            "capacity_alerts_created": len(capacity_alerts),
            "alerts": capacity_alerts
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error triggering capacity alert: {str(e)}")]
        )

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializeResult(
                protocolVersion="2024-11-05",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
                serverInfo={
                    "name": "hospital-enhanced-mcp",
                    "version": "1.0.0",
                },
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
