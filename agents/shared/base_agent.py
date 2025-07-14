"""
Base agent class for all hospital agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

class BaseAgent(ABC):
    """Base class for all hospital agents"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = "initialized"
        self.last_update = datetime.utcnow()
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
    @abstractmethod
    async def execute_task(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        pass
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            status = await self.get_status()
            return status.get("healthy", False)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def log_activity(self, activity: str, details: Optional[Dict[str, Any]] = None):
        """Log agent activity"""
        self.logger.info(f"{self.name}: {activity}", extra=details or {})
        self.last_update = datetime.utcnow()
    
    async def communicate_with_agent(self, target_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Communicate with another agent"""
        # This will be implemented with the message queue system
        self.log_activity(f"Communicating with {target_agent}", {"message": message})
        return {"status": "message_sent", "target": target_agent}
