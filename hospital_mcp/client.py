"""
MCP Client for Hospital Bed Management Tools
"""
import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp import stdio_client
from mcp.types import CallToolRequest

logger = logging.getLogger(__name__)

class HospitalMCPClient:
    """MCP Client for Hospital Bed Management"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.server_process: Optional[subprocess.Popen] = None
        self.available_tools: List[Dict[str, Any]] = []
    
    async def connect(self):
        """Connect to the MCP server"""
        try:
            # Create stdio client connection
            server_path = Path(__file__).parent / "server.py"
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(server_path)]
            )

            # Initialize session using stdio_client
            self.session = await stdio_client(server_params).__aenter__()

            # Initialize the session
            init_result = await self.session.initialize()
            logger.info(f"MCP session initialized: {init_result}")

            # List available tools
            await self._list_tools()

            logger.info("MCP client connected successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.server_process = None
                
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
    
    async def _list_tools(self):
        """List available tools from the server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.list_tools()
            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in result.tools
            ]
            logger.info(f"Available tools: {[tool['name'] for tool in self.available_tools]}")
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            self.available_tools = []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        if arguments is None:
            arguments = {}
        
        try:
            # Validate tool exists
            tool_names = [tool["name"] for tool in self.available_tools]
            if tool_name not in tool_names:
                raise ValueError(f"Tool '{tool_name}' not available. Available tools: {tool_names}")
            
            # Call the tool
            result = await self.session.call_tool(tool_name, arguments)
            
            # Parse the result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {"result": content.text}
                else:
                    return {"result": str(content)}
            else:
                return {"result": "No content returned"}
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.available_tools
    
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


class MCPToolsManager:
    """Manager for MCP tools that can be used by the agent"""
    
    def __init__(self):
        self.client = HospitalMCPClient()
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
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of available tools"""
        return self.client.get_available_tools()


# Convenience functions for direct tool access
async def create_mcp_client() -> HospitalMCPClient:
    """Create and connect an MCP client"""
    client = HospitalMCPClient()
    await client.connect()
    return client


async def test_mcp_connection():
    """Test MCP connection and tools"""
    client = await create_mcp_client()
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
    asyncio.run(test_mcp_connection())
