"""
Conversation Memory and Context Management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    timestamp: str
    user_query: str
    intent: str
    entities: Dict
    bot_response: str
    confidence: float
    context_used: Dict

@dataclass
class ContextItem:
    """Represents a piece of context information"""
    key: str
    value: Any
    timestamp: str
    expires_at: Optional[str] = None
    priority: int = 1  # Higher priority items are kept longer

class ConversationMemory:
    """Manages conversation context and memory"""
    
    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history
        self.conversation_history: deque = deque(maxlen=max_history)
        self.context: Dict[str, ContextItem] = {}
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        
        # Context expiration times (in minutes)
        self.context_ttl = {
            'ward': 30,           # Ward context lasts 30 minutes
            'patient_id': 60,     # Patient context lasts 1 hour
            'current_topic': 15,  # Current topic lasts 15 minutes
            'last_query_type': 5, # Last query type lasts 5 minutes
            'user_preferences': 1440  # User preferences last 24 hours
        }
    
    def add_turn(self, user_query: str, intent: str, entities: Dict, 
                 bot_response: str, confidence: float):
        """Add a new conversation turn"""
        self.last_activity = datetime.now()
        
        # Create conversation turn
        turn = ConversationTurn(
            timestamp=self.last_activity.isoformat(),
            user_query=user_query,
            intent=intent,
            entities=entities,
            bot_response=bot_response,
            confidence=confidence,
            context_used=self.get_current_context()
        )
        
        self.conversation_history.append(turn)
        
        # Update context based on this turn
        self._update_context_from_turn(turn)
    
    def _update_context_from_turn(self, turn: ConversationTurn):
        """Update context based on the conversation turn"""
        now = datetime.now()
        
        # Update ward context
        if 'ward' in turn.entities:
            self.set_context('ward', turn.entities['ward'], 
                           expires_in_minutes=self.context_ttl['ward'])
        
        # Update patient context
        if 'patient_id' in turn.entities:
            self.set_context('patient_id', turn.entities['patient_id'],
                           expires_in_minutes=self.context_ttl['patient_id'])
        
        # Update current topic
        self.set_context('current_topic', turn.intent,
                        expires_in_minutes=self.context_ttl['current_topic'])
        
        # Update last query type
        self.set_context('last_query_type', turn.intent,
                        expires_in_minutes=self.context_ttl['last_query_type'])
        
        # Track query patterns for personalization
        query_patterns = self.get_context('query_patterns', [])
        query_patterns.append({
            'intent': turn.intent,
            'timestamp': turn.timestamp,
            'entities': turn.entities
        })
        # Keep only last 10 patterns
        if len(query_patterns) > 10:
            query_patterns = query_patterns[-10:]
        self.set_context('query_patterns', query_patterns,
                        expires_in_minutes=self.context_ttl['user_preferences'])
    
    def set_context(self, key: str, value: Any, expires_in_minutes: Optional[int] = None,
                   priority: int = 1):
        """Set a context item"""
        now = datetime.now()
        expires_at = None
        
        if expires_in_minutes:
            expires_at = (now + timedelta(minutes=expires_in_minutes)).isoformat()
        
        self.context[key] = ContextItem(
            key=key,
            value=value,
            timestamp=now.isoformat(),
            expires_at=expires_at,
            priority=priority
        )
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context item, checking for expiration"""
        self._cleanup_expired_context()
        
        if key in self.context:
            return self.context[key].value
        return default
    
    def get_current_context(self) -> Dict:
        """Get all current valid context"""
        self._cleanup_expired_context()
        return {key: item.value for key, item in self.context.items()}
    
    def _cleanup_expired_context(self):
        """Remove expired context items"""
        now = datetime.now()
        expired_keys = []
        
        for key, item in self.context.items():
            if item.expires_at:
                expires_at = datetime.fromisoformat(item.expires_at)
                if now > expires_at:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.context[key]
    
    def get_conversation_summary(self) -> Dict:
        """Get a summary of the conversation"""
        if not self.conversation_history:
            return {"message": "No conversation history"}
        
        # Analyze conversation patterns
        intents = [turn.intent for turn in self.conversation_history]
        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Get most recent topics
        recent_topics = list(set(intents[-5:]))  # Last 5 unique intents
        
        return {
            "session_duration": str(datetime.now() - self.session_start),
            "total_turns": len(self.conversation_history),
            "most_common_intents": sorted(intent_counts.items(), 
                                        key=lambda x: x[1], reverse=True)[:3],
            "recent_topics": recent_topics,
            "current_context": self.get_current_context(),
            "last_activity": self.last_activity.isoformat()
        }
    
    def get_contextual_suggestions(self) -> List[str]:
        """Generate contextual suggestions based on conversation history"""
        suggestions = []
        current_context = self.get_current_context()
        
        # Suggestions based on current ward context
        if 'ward' in current_context:
            ward = current_context['ward']
            suggestions.extend([
                f"Show me available beds in {ward}",
                f"List {ward} patients",
                f"What's the {ward} occupancy rate?"
            ])
        
        # Suggestions based on current patient context
        if 'patient_id' in current_context:
            patient_id = current_context['patient_id']
            suggestions.extend([
                f"Update {patient_id} status",
                f"Discharge {patient_id}",
                f"Transfer {patient_id} to another ward"
            ])
        
        # Suggestions based on recent query patterns
        recent_intents = [turn.intent for turn in list(self.conversation_history)[-3:]]
        
        if 'bed_availability' in recent_intents:
            suggestions.append("Assign a patient to an available bed")
        
        if 'patient_info' in recent_intents:
            suggestions.append("Check bed occupancy status")
        
        # Remove duplicates and limit to 5 suggestions
        suggestions = list(dict.fromkeys(suggestions))[:5]
        
        return suggestions
    
    def is_follow_up_query(self, current_intent: str, current_entities: Dict) -> bool:
        """Determine if current query is a follow-up to previous queries"""
        if not self.conversation_history:
            return False
        
        last_turn = self.conversation_history[-1]
        
        # Check if it's a related intent
        related_intents = {
            'bed_availability': ['bed_assignment', 'occupancy_status'],
            'patient_info': ['patient_lookup', 'discharge_info'],
            'patient_lookup': ['patient_info', 'bed_assignment']
        }
        
        if (last_turn.intent in related_intents and 
            current_intent in related_intents[last_turn.intent]):
            return True
        
        # Check if entities suggest continuation
        if ('ward' in current_entities and 
            'ward' in self.get_current_context() and
            current_entities['ward'] == self.get_current_context()['ward']):
            return True
        
        return False
    
    def get_session_stats(self) -> Dict:
        """Get detailed session statistics"""
        if not self.conversation_history:
            return {}
        
        turns = list(self.conversation_history)
        
        # Calculate average confidence
        avg_confidence = sum(turn.confidence for turn in turns) / len(turns)
        
        # Find most used entities
        all_entities = {}
        for turn in turns:
            for entity_type, entity_value in turn.entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = {}
                if entity_value not in all_entities[entity_type]:
                    all_entities[entity_type][entity_value] = 0
                all_entities[entity_type][entity_value] += 1
        
        return {
            "session_id": self.session_id,
            "duration": str(datetime.now() - self.session_start),
            "total_turns": len(turns),
            "average_confidence": round(avg_confidence, 2),
            "most_used_entities": all_entities,
            "context_items": len(self.context),
            "session_start": self.session_start.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
