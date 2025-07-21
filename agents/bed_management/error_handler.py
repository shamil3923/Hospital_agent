"""
Enhanced Error Handling and Recovery System
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import traceback
from enum import Enum

class ErrorType(Enum):
    """Types of errors that can occur"""
    DATABASE_ERROR = "database_error"
    QUERY_UNCLEAR = "query_unclear"
    NO_RESULTS = "no_results"
    INVALID_INPUT = "invalid_input"
    SYSTEM_ERROR = "system_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorHandler:
    """Advanced error handling with recovery suggestions"""
    
    def __init__(self):
        self.error_log = []
        self.recovery_strategies = {
            ErrorType.DATABASE_ERROR: self._handle_database_error,
            ErrorType.QUERY_UNCLEAR: self._handle_unclear_query,
            ErrorType.NO_RESULTS: self._handle_no_results,
            ErrorType.INVALID_INPUT: self._handle_invalid_input,
            ErrorType.SYSTEM_ERROR: self._handle_system_error,
            ErrorType.PERMISSION_ERROR: self._handle_permission_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorType.VALIDATION_ERROR: self._handle_validation_error
        }
        
        # Common error patterns and their types
        self.error_patterns = {
            'connection': ErrorType.DATABASE_ERROR,
            'timeout': ErrorType.TIMEOUT_ERROR,
            'permission': ErrorType.PERMISSION_ERROR,
            'not found': ErrorType.NO_RESULTS,
            'invalid': ErrorType.INVALID_INPUT,
            'unclear': ErrorType.QUERY_UNCLEAR
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Dict, user_query: str = "") -> Dict:
        """Main error handling function"""
        error_type = self._classify_error(error, context)
        severity = self._determine_severity(error_type, error)
        
        # Log the error
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'severity': severity.value,
            'error_message': str(error),
            'context': context,
            'user_query': user_query,
            'traceback': traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }
        
        self.error_log.append(error_info)
        self.logger.error(f"Error handled: {error_type.value} - {str(error)}")
        
        # Get recovery strategy
        recovery_handler = self.recovery_strategies.get(error_type, self._handle_generic_error)
        response = recovery_handler(error, context, user_query)
        
        # Add error tracking info to response
        response.update({
            'error_id': len(self.error_log),
            'error_type': error_type.value,
            'severity': severity.value,
            'timestamp': error_info['timestamp']
        })
        
        return response
    
    def _classify_error(self, error: Exception, context: Dict) -> ErrorType:
        """Classify the type of error"""
        error_message = str(error).lower()
        
        # Check for specific error patterns
        for pattern, error_type in self.error_patterns.items():
            if pattern in error_message:
                return error_type
        
        # Check by exception type
        if isinstance(error, ConnectionError):
            return ErrorType.DATABASE_ERROR
        elif isinstance(error, TimeoutError):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(error, PermissionError):
            return ErrorType.PERMISSION_ERROR
        elif isinstance(error, ValueError):
            return ErrorType.VALIDATION_ERROR
        elif isinstance(error, KeyError):
            return ErrorType.INVALID_INPUT
        
        return ErrorType.SYSTEM_ERROR
    
    def _determine_severity(self, error_type: ErrorType, error: Exception) -> ErrorSeverity:
        """Determine error severity"""
        severity_mapping = {
            ErrorType.DATABASE_ERROR: ErrorSeverity.HIGH,
            ErrorType.SYSTEM_ERROR: ErrorSeverity.HIGH,
            ErrorType.PERMISSION_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.QUERY_UNCLEAR: ErrorSeverity.LOW,
            ErrorType.NO_RESULTS: ErrorSeverity.LOW,
            ErrorType.INVALID_INPUT: ErrorSeverity.LOW,
            ErrorType.VALIDATION_ERROR: ErrorSeverity.LOW
        }
        
        return severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
    
    def _handle_database_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle database connection/query errors"""
        return {
            'response': "I'm experiencing database connectivity issues. Let me try to help you with cached information or suggest alternative actions.",
            'suggestions': [
                "Try your query again in a few moments",
                "Check system status",
                "Contact system administrator if problem persists"
            ],
            'fallback_actions': [
                "Use cached bed count data",
                "Provide general hospital information",
                "Suggest manual verification"
            ],
            'recovery_possible': True
        }
    
    def _handle_unclear_query(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle unclear or ambiguous queries"""
        suggestions = self._generate_query_suggestions(user_query, context)
        
        return {
            'response': f"I'm not sure I understood your request: '{user_query}'. Could you please clarify or try one of these suggestions?",
            'suggestions': suggestions,
            'clarification_needed': True,
            'recovery_possible': True,
            'help_text': "Try being more specific about what you're looking for (beds, patients, occupancy, etc.)"
        }
    
    def _handle_no_results(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle cases where query returns no results"""
        intent = context.get('intent', 'unknown')
        entities = context.get('entities', {})
        
        alternative_suggestions = []
        
        if intent == 'bed_availability':
            ward = entities.get('ward', 'specified ward')
            alternative_suggestions = [
                f"Check other wards for available beds",
                f"View overall hospital occupancy",
                f"See upcoming discharges for {ward}"
            ]
        elif intent == 'patient_info':
            ward = entities.get('ward', 'specified ward')
            alternative_suggestions = [
                f"Check patients in other wards",
                f"View recently discharged patients",
                f"See admission queue for {ward}"
            ]
        elif intent == 'patient_lookup':
            patient_id = entities.get('patient_id', 'specified patient')
            alternative_suggestions = [
                f"Search for similar patient IDs",
                f"Check recently discharged patients",
                f"Verify patient ID format (PAT followed by numbers)"
            ]
        
        return {
            'response': f"No results found for your query. This might be because there are no matching records or the search criteria is too specific.",
            'suggestions': alternative_suggestions,
            'recovery_possible': True,
            'alternative_actions': [
                "Broaden your search criteria",
                "Check different time periods",
                "Verify the information you're looking for"
            ]
        }
    
    def _handle_invalid_input(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle invalid input errors"""
        return {
            'response': "The information provided seems to be in an invalid format. Let me help you correct it.",
            'suggestions': [
                "Patient IDs should be in format: PAT123",
                "Ward names: ICU, Emergency, General, Pediatric, Maternity",
                "Severity levels: critical, serious, stable, improving"
            ],
            'recovery_possible': True,
            'input_examples': {
                'patient_id': 'PAT123',
                'ward': 'ICU',
                'severity': 'critical'
            }
        }
    
    def _handle_system_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle general system errors"""
        return {
            'response': "I encountered a system error while processing your request. The technical team has been notified.",
            'suggestions': [
                "Try your request again",
                "Use simpler queries",
                "Contact support if the problem continues"
            ],
            'recovery_possible': False,
            'support_info': {
                'error_id': len(self.error_log),
                'timestamp': datetime.now().isoformat(),
                'contact': "system-admin@hospital.com"
            }
        }
    
    def _handle_permission_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle permission/access errors"""
        return {
            'response': "You don't have permission to access this information. Please contact your administrator for access.",
            'suggestions': [
                "Request appropriate permissions",
                "Try queries within your access level",
                "Contact system administrator"
            ],
            'recovery_possible': False,
            'required_permissions': context.get('required_permissions', ['unknown'])
        }
    
    def _handle_timeout_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle timeout errors"""
        return {
            'response': "Your request is taking longer than expected. This might be due to high system load.",
            'suggestions': [
                "Try again in a few moments",
                "Use more specific search criteria",
                "Break complex queries into smaller parts"
            ],
            'recovery_possible': True,
            'retry_recommended': True,
            'retry_delay': 30  # seconds
        }
    
    def _handle_validation_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Handle data validation errors"""
        return {
            'response': "The data provided doesn't meet the required format or constraints.",
            'suggestions': [
                "Check data format requirements",
                "Verify all required fields are provided",
                "Ensure values are within acceptable ranges"
            ],
            'recovery_possible': True,
            'validation_rules': {
                'age': 'Must be between 0 and 150',
                'patient_id': 'Must start with PAT followed by numbers',
                'phone': 'Must be a valid phone number format'
            }
        }
    
    def _handle_generic_error(self, error: Exception, context: Dict, user_query: str) -> Dict:
        """Generic error handler for unclassified errors"""
        return {
            'response': "I encountered an unexpected error. Let me try to help you in a different way.",
            'suggestions': [
                "Rephrase your question",
                "Try a simpler query",
                "Contact support if needed"
            ],
            'recovery_possible': True
        }
    
    def _generate_query_suggestions(self, user_query: str, context: Dict) -> List[str]:
        """Generate helpful query suggestions based on unclear input"""
        suggestions = []
        query_lower = user_query.lower()
        
        # Suggestions based on partial matches
        if 'bed' in query_lower:
            suggestions.extend([
                "Show me available beds in ICU",
                "What is the current bed occupancy?",
                "How many beds are free in Emergency?"
            ])
        
        if 'patient' in query_lower:
            suggestions.extend([
                "List all patients",
                "Show me ICU patients",
                "Find patient PAT123"
            ])
        
        if not suggestions:
            suggestions = [
                "Show me bed availability",
                "List current patients",
                "What's the occupancy status?",
                "Help - show me what I can ask"
            ]
        
        return suggestions[:5]
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics for monitoring"""
        if not self.error_log:
            return {"message": "No errors recorded"}
        
        # Count errors by type
        error_counts = {}
        severity_counts = {}
        
        for error in self.error_log:
            error_type = error['error_type']
            severity = error['severity']
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'error_types': error_counts,
            'severity_distribution': severity_counts,
            'recent_errors': self.error_log[-5:],  # Last 5 errors
            'error_rate': len(self.error_log) / max(1, len(self.error_log))  # Placeholder calculation
        }
