"""
MCP-compatible tools for Bed Management Agent
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Global MCP tools manager instance
_mcp_manager = None

async def get_mcp_manager():
    """Get or create MCP tools manager"""
    global _mcp_manager
    if _mcp_manager is None:
        import sys
        import os
        # Add the project root to the path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sys.path.insert(0, project_root)
        from hospital_mcp.simple_client import SimpleMCPToolsManager
        _mcp_manager = SimpleMCPToolsManager()
        await _mcp_manager.initialize()
    return _mcp_manager

def run_async_tool(coro):
    """Helper to run async tools in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)

@tool
def get_bed_occupancy_status() -> Dict[str, Any]:
    """Get current bed occupancy status across all wards using MCP"""
    async def _get_occupancy():
        manager = await get_mcp_manager()
        return await manager.execute_tool("get_bed_occupancy_status")
    
    try:
        result = run_async_tool(_get_occupancy())
        logger.info("Retrieved bed occupancy status via MCP")
        return result
    except Exception as e:
        logger.error(f"Error getting bed occupancy via MCP: {e}")
        return {"error": str(e)}

@tool
def get_available_beds(ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of available beds, optionally filtered by ward or bed type using MCP"""
    async def _get_available():
        manager = await get_mcp_manager()
        kwargs = {}
        if ward:
            kwargs["ward"] = ward
        if bed_type:
            kwargs["bed_type"] = bed_type
        return await manager.execute_tool("get_available_beds", **kwargs)
    
    try:
        result = run_async_tool(_get_available())
        logger.info(f"Retrieved available beds via MCP (ward={ward}, bed_type={bed_type})")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting available beds via MCP: {e}")
        return []

@tool
def get_critical_bed_alerts() -> List[Dict[str, Any]]:
    """Get critical bed management alerts and recommendations using MCP"""
    async def _get_alerts():
        manager = await get_mcp_manager()
        return await manager.execute_tool("get_critical_bed_alerts")
    
    try:
        result = run_async_tool(_get_alerts())
        logger.info("Retrieved critical bed alerts via MCP")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting critical alerts via MCP: {e}")
        return []

@tool
def get_patient_discharge_predictions() -> List[Dict[str, Any]]:
    """Get predicted patient discharges for bed planning using MCP"""
    async def _get_predictions():
        manager = await get_mcp_manager()
        return await manager.execute_tool("get_patient_discharge_predictions")
    
    try:
        result = run_async_tool(_get_predictions())
        logger.info("Retrieved discharge predictions via MCP")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting discharge predictions via MCP: {e}")
        return []

@tool
def update_bed_status(bed_number: str, new_status: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
    """Update bed status (occupied, vacant, cleaning, maintenance) using MCP"""
    async def _update_status():
        manager = await get_mcp_manager()
        kwargs = {
            "bed_number": bed_number,
            "new_status": new_status
        }
        if patient_id:
            kwargs["patient_id"] = patient_id
        return await manager.execute_tool("update_bed_status", **kwargs)

    try:
        result = run_async_tool(_update_status())
        logger.info(f"Updated bed {bed_number} status to {new_status} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error updating bed status via MCP: {e}")
        return {"error": str(e)}

@tool
def assign_patient_to_bed(patient_id: str, bed_number: str, doctor_id: Optional[str] = None) -> Dict[str, Any]:
    """Assign existing patient to a bed using MCP"""
    async def _assign_patient():
        manager = await get_mcp_manager()
        kwargs = {
            "patient_id": patient_id,
            "bed_number": bed_number
        }
        if doctor_id:
            kwargs["doctor_id"] = doctor_id
        return await manager.execute_tool("assign_patient_to_bed", **kwargs)

    try:
        result = run_async_tool(_assign_patient())
        logger.info(f"Assigned patient {patient_id} to bed {bed_number} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error assigning patient to bed via MCP: {e}")
        return {"error": str(e)}

@tool
def create_patient_and_assign(patient_name: str, bed_number: str, age: Optional[int] = None,
                            gender: Optional[str] = None, condition: Optional[str] = None,
                            doctor_id: Optional[str] = None) -> Dict[str, Any]:
    """Create new patient and assign to bed using MCP"""
    async def _create_and_assign():
        manager = await get_mcp_manager()
        kwargs = {
            "patient_name": patient_name,
            "bed_number": bed_number
        }
        if age:
            kwargs["age"] = age
        if gender:
            kwargs["gender"] = gender
        if condition:
            kwargs["condition"] = condition
        if doctor_id:
            kwargs["doctor_id"] = doctor_id
        return await manager.execute_tool("create_patient_and_assign", **kwargs)

    try:
        result = run_async_tool(_create_and_assign())
        logger.info(f"Created patient {patient_name} and assigned to bed {bed_number} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error creating patient and assigning to bed via MCP: {e}")
        return {"error": str(e)}

# Tool cleanup function
async def cleanup_mcp_tools():
    """Cleanup MCP tools manager"""
    global _mcp_manager
    if _mcp_manager:
        await _mcp_manager.cleanup()
        _mcp_manager = None

# List of all MCP tools for easy import
MCP_TOOLS = [
    get_bed_occupancy_status,
    get_available_beds,
    get_critical_bed_alerts,
    get_patient_discharge_predictions,
    update_bed_status,
    assign_patient_to_bed,
    create_patient_and_assign
]
