"""
WebSocket Manager for Real-time Hospital Dashboard
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by type
        self.dashboard_connections: Set[WebSocket] = set()
        self.alert_connections: Set[WebSocket] = set()
        self.bed_status_connections: Set[WebSocket] = set()
        self.all_connections: Set[WebSocket] = set()
    
    async def connect_dashboard(self, websocket: WebSocket):
        """Connect dashboard client"""
        await websocket.accept()
        self.dashboard_connections.add(websocket)
        self.all_connections.add(websocket)
        logger.info(f"Dashboard client connected. Total: {len(self.dashboard_connections)}")
        
        # Send initial data
        await self.send_initial_dashboard_data(websocket)
    
    async def connect_alerts(self, websocket: WebSocket):
        """Connect alerts client"""
        await websocket.accept()
        self.alert_connections.add(websocket)
        self.all_connections.add(websocket)
        logger.info(f"Alert client connected. Total: {len(self.alert_connections)}")
    
    async def connect_bed_status(self, websocket: WebSocket):
        """Connect bed status client"""
        await websocket.accept()
        self.bed_status_connections.add(websocket)
        self.all_connections.add(websocket)
        logger.info(f"Bed status client connected. Total: {len(self.bed_status_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect client"""
        self.dashboard_connections.discard(websocket)
        self.alert_connections.discard(websocket)
        self.bed_status_connections.discard(websocket)
        self.all_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.all_connections)}")
    
    async def send_to_dashboard(self, message: dict):
        """Send message to all dashboard clients"""
        if self.dashboard_connections:
            await self._broadcast_to_connections(self.dashboard_connections, message)
    
    async def send_to_alerts(self, message: dict):
        """Send message to all alert clients"""
        if self.alert_connections:
            await self._broadcast_to_connections(self.alert_connections, message)
    
    async def send_to_bed_status(self, message: dict):
        """Send message to all bed status clients"""
        if self.bed_status_connections:
            logger.info(f"📡 Broadcasting bed status update to {len(self.bed_status_connections)} clients")
            await self._broadcast_to_connections(self.bed_status_connections, message)

    async def broadcast_to_bed_status(self, message: dict):
        """Alias for send_to_bed_status for compatibility"""
        await self.send_to_bed_status(message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.all_connections:
            await self._broadcast_to_connections(self.all_connections, message)
    
    async def _broadcast_to_connections(self, connections: Set[WebSocket], message: dict):
        """Broadcast message to specific set of connections"""
        if not connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in connections.copy():
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_initial_dashboard_data(self, websocket: WebSocket):
        """Send initial data when dashboard connects"""
        try:
            # Import here to avoid circular imports
            from alert_system import alert_system
            from hospital_mcp.simple_server import get_server
            
            # Get current hospital status
            mcp_server = get_server()
            
            # Get bed occupancy
            occupancy_result = await mcp_server.call_tool("get_bed_occupancy_status")
            occupancy_data = occupancy_result.get("result", {})
            
            # Get available beds
            available_result = await mcp_server.call_tool("get_available_beds")
            available_beds = available_result.get("result", [])
            
            # Get critical alerts
            alerts_result = await mcp_server.call_tool("get_critical_bed_alerts")
            critical_alerts = alerts_result.get("result", [])
            
            # Get active real-time alerts
            active_alerts = alert_system.get_active_alerts()
            
            initial_data = {
                "type": "initial_data",
                "data": {
                    "occupancy": occupancy_data,
                    "available_beds": available_beds[:10],  # Limit to 10 for initial load
                    "critical_alerts": critical_alerts,
                    "active_alerts": active_alerts,
                    "timestamp": occupancy_data.get("timestamp")
                }
            }
            
            await websocket.send_text(json.dumps(initial_data))
            
        except Exception as e:
            logger.error(f"Error sending initial dashboard data: {e}")
    
    async def send_bed_update(self, bed_data: dict):
        """Send bed status update"""
        message = {
            "type": "bed_update",
            "data": bed_data,
            "timestamp": bed_data.get("last_updated")
        }
        await self.send_to_bed_status(message)
        await self.send_to_dashboard(message)
    
    async def send_alert_update(self, alert_data: dict):
        """Send alert update"""
        message = {
            "type": "alert_update",
            "data": alert_data
        }
        await self.send_to_alerts(message)
        await self.send_to_dashboard(message)
    
    async def send_occupancy_update(self, occupancy_data: dict):
        """Send occupancy update"""
        message = {
            "type": "occupancy_update",
            "data": occupancy_data
        }
        await self.send_to_dashboard(message)
    
    async def send_discharge_notification(self, discharge_data: dict):
        """Send discharge notification"""
        message = {
            "type": "discharge_notification",
            "data": discharge_data
        }
        await self.send_to_dashboard(message)
    
    async def send_admission_notification(self, admission_data: dict):
        """Send admission notification"""
        message = {
            "type": "admission_notification",
            "data": admission_data
        }
        await self.send_to_dashboard(message)
    
    async def send_capacity_warning(self, capacity_data: dict):
        """Send capacity warning"""
        message = {
            "type": "capacity_warning",
            "data": capacity_data,
            "priority": "high"
        }
        await self.broadcast_to_all(message)
    
    async def send_equipment_alert(self, equipment_data: dict):
        """Send equipment alert"""
        message = {
            "type": "equipment_alert",
            "data": equipment_data
        }
        await self.send_to_alerts(message)
        await self.send_to_dashboard(message)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.all_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "alert_connections": len(self.alert_connections),
            "bed_status_connections": len(self.bed_status_connections)
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()


class RealTimeUpdater:
    """Handles real-time updates and notifications"""
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.update_tasks = []
        self.running = False
    
    async def start_updates(self):
        """Start real-time update tasks"""
        if self.running:
            return
        
        self.running = True
        logger.info("🔄 Starting real-time updates...")
        
        # Start update tasks
        self.update_tasks = [
            asyncio.create_task(self._periodic_occupancy_updates()),
            asyncio.create_task(self._periodic_bed_status_updates()),
            asyncio.create_task(self._periodic_alert_checks())
        ]
        
        logger.info("✅ Real-time updates started")
    
    async def stop_updates(self):
        """Stop real-time update tasks"""
        self.running = False
        
        # Cancel all update tasks
        for task in self.update_tasks:
            task.cancel()
        
        await asyncio.gather(*self.update_tasks, return_exceptions=True)
        self.update_tasks.clear()
        
        logger.info("🛑 Real-time updates stopped")
    
    async def _periodic_occupancy_updates(self):
        """Send periodic occupancy updates"""
        while self.running:
            try:
                if self.ws_manager.dashboard_connections:
                    from hospital_mcp.simple_server import get_server
                    
                    mcp_server = get_server()
                    result = await mcp_server.call_tool("get_bed_occupancy_status")
                    occupancy_data = result.get("result", {})
                    
                    await self.ws_manager.send_occupancy_update(occupancy_data)
                
            except Exception as e:
                logger.error(f"Error in periodic occupancy updates: {e}")
            
            await asyncio.sleep(60)  # Update every minute
    
    async def _periodic_bed_status_updates(self):
        """Send periodic bed status updates"""
        while self.running:
            try:
                if self.ws_manager.bed_status_connections or self.ws_manager.dashboard_connections:
                    from hospital_mcp.simple_server import get_server
                    
                    mcp_server = get_server()
                    result = await mcp_server.call_tool("get_available_beds")
                    available_beds = result.get("result", [])
                    
                    # Send update if there are connections
                    if available_beds:
                        message = {
                            "type": "bed_status_update",
                            "data": {
                                "available_beds": available_beds,
                                "count": len(available_beds)
                            }
                        }
                        await self.ws_manager.send_to_bed_status(message)
                
            except Exception as e:
                logger.error(f"Error in periodic bed status updates: {e}")
            
            await asyncio.sleep(30)  # Update every 30 seconds
    
    async def _periodic_alert_checks(self):
        """Send periodic alert checks"""
        while self.running:
            try:
                if self.ws_manager.alert_connections or self.ws_manager.dashboard_connections:
                    from hospital_mcp.simple_server import get_server
                    
                    mcp_server = get_server()
                    result = await mcp_server.call_tool("get_critical_bed_alerts")
                    alerts = result.get("result", [])
                    
                    if alerts:
                        message = {
                            "type": "critical_alerts_update",
                            "data": {
                                "alerts": alerts,
                                "count": len(alerts)
                            }
                        }
                        await self.ws_manager.send_to_alerts(message)
                
            except Exception as e:
                logger.error(f"Error in periodic alert checks: {e}")
            
            await asyncio.sleep(120)  # Check every 2 minutes

# Global real-time updater
real_time_updater = RealTimeUpdater(websocket_manager)
