"""
Simple MCP Client for Hospital Bed Management Tools
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

try:
    from .simple_server import get_server
except ImportError:
    from simple_server import get_server

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """Simple MCP Client for Hospital Bed Management"""
    
    def __init__(self):
        self.server = None
        self.connected = False
    
    async def connect(self):
        """Connect to the MCP server"""
        try:
            self.server = get_server()
            self.connected = True
            logger.info("Simple MCP client connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to simple MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        self.connected = False
        self.server = None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.connected or not self.server:
            raise RuntimeError("Not connected to MCP server")
        
        if arguments is None:
            arguments = {}
        
        try:
            result = await self.server.call_tool(tool_name, arguments)
            return result.get("result", result)
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        if not self.connected or not self.server:
            return []
        return self.server.get_available_tools()
    
    async def get_bed_occupancy_status(self) -> Dict[str, Any]:
        """Get current bed occupancy status"""
        return await self.call_tool("get_bed_occupancy_status")
    
    async def get_available_beds(self, ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available beds"""
        arguments = {}
        if ward:
            arguments["ward"] = ward
        if bed_type:
            arguments["bed_type"] = bed_type
        
        result = await self.call_tool("get_available_beds", arguments)
        return result if isinstance(result, list) else result.get("result", [])
    
    async def get_critical_bed_alerts(self) -> List[Dict[str, Any]]:
        """Get critical bed alerts"""
        result = await self.call_tool("get_critical_bed_alerts")
        return result if isinstance(result, list) else result.get("result", [])
    
    async def get_patient_discharge_predictions(self) -> List[Dict[str, Any]]:
        """Get patient discharge predictions"""
        result = await self.call_tool("get_patient_discharge_predictions")
        return result if isinstance(result, list) else result.get("result", [])
    
    async def update_bed_status(self, bed_number: str, new_status: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Update bed status"""
        arguments = {
            "bed_number": bed_number,
            "new_status": new_status
        }
        if patient_id:
            arguments["patient_id"] = patient_id
        
        return await self.call_tool("update_bed_status", arguments)


class SimpleMCPToolsManager:
    """Simple manager for MCP tools that can be used by the agent"""
    
    def __init__(self):
        self.client = SimpleMCPClient()
        self.connected = False
    
    async def initialize(self):
        """Initialize the MCP client connection"""
        self.connected = await self.client.connect()
        return self.connected
    
    async def cleanup(self):
        """Cleanup MCP client connection"""
        await self.client.disconnect()
        self.connected = False
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with the given arguments"""
        if not self.connected:
            raise RuntimeError("MCP client not connected")
        
        return await self.client.call_tool(tool_name, kwargs)
    
    def get_tool_descriptions(self) -> List[str]:
        """Get descriptions of available tools"""
        return self.client.get_available_tools()


# Convenience functions for direct tool access
async def create_simple_mcp_client() -> SimpleMCPClient:
    """Create and connect a simple MCP client"""
    client = SimpleMCPClient()
    await client.connect()
    return client


async def test_simple_mcp_connection():
    """Test simple MCP connection and tools"""
    client = await create_simple_mcp_client()
    try:
        # Test bed occupancy
        occupancy = await client.get_bed_occupancy_status()
        print("Bed Occupancy Status:", json.dumps(occupancy, indent=2))
        
        # Test available beds
        available = await client.get_available_beds()
        print("Available Beds:", json.dumps(available, indent=2))
        
        # Test alerts
        alerts = await client.get_critical_bed_alerts()
        print("Critical Alerts:", json.dumps(alerts, indent=2))
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_simple_mcp_connection())
