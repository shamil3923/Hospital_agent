"""
Response Formatting and Visualization for Enhanced Chatbot Output
"""
import re
from typing import Dict, List, Any
from datetime import datetime

class ResponseFormatter:
    """Format LLM responses for better user experience"""
    
    def __init__(self):
        self.emoji_map = {
            'critical': '🚨',
            'warning': '⚠️',
            'success': '✅',
            'info': 'ℹ️',
            'bed': '🛏️',
            'patient': '👥',
            'chart': '📊',
            'trend': '📈',
            'alert': '🔔',
            'time': '⏰',
            'location': '📍',
            'doctor': '👨‍⚕️',
            'nurse': '👩‍⚕️',
            'cleaning': '🧹',
            'available': '🟢',
            'occupied': '🔴',
            'maintenance': '🔧'
        }
    
    def format_response(self, response: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format LLM response with enhanced structure and visualization"""
        
        # Clean and structure the response
        formatted_response = self._clean_response(response)
        
        # Extract structured data
        structured_data = self._extract_structured_data(formatted_response)
        
        # Add visual enhancements
        enhanced_response = self._add_visual_enhancements(formatted_response)
        
        # Create response cards for complex data
        cards = self._create_response_cards(structured_data)
        
        # Generate quick actions
        quick_actions = self._generate_quick_actions(metadata or {})
        
        return {
            "formatted_response": enhanced_response,
            "structured_data": structured_data,
            "response_cards": cards,
            "quick_actions": quick_actions,
            "response_type": self._determine_response_type(formatted_response),
            "urgency_level": self._determine_urgency(formatted_response),
            "visual_elements": self._extract_visual_elements(formatted_response)
        }
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize the response text"""
        # Remove excessive whitespace
        response = re.sub(r'\n\s*\n', '\n\n', response)
        response = re.sub(r' +', ' ', response)
        
        # Fix common formatting issues
        response = response.strip()
        
        return response
    
    def _extract_structured_data(self, response: str) -> Dict[str, Any]:
        """Extract structured data from response"""
        structured = {
            "metrics": [],
            "recommendations": [],
            "alerts": [],
            "bed_info": [],
            "patient_info": []
        }
        
        # Extract metrics (numbers with context)
        metrics_pattern = r'(\d+(?:\.\d+)?%?)\s+([a-zA-Z\s]+(?:beds?|patients?|rate|occupancy))'
        metrics = re.findall(metrics_pattern, response, re.IGNORECASE)
        structured["metrics"] = [{"value": m[0], "label": m[1].strip()} for m in metrics]
        
        # Extract recommendations (bullet points or numbered lists)
        rec_pattern = r'(?:•|\d+\.)\s*([^•\n]+(?:recommend|suggest|should|consider)[^•\n]*)'
        recommendations = re.findall(rec_pattern, response, re.IGNORECASE)
        structured["recommendations"] = [rec.strip() for rec in recommendations]
        
        # Extract alerts (critical, urgent, warning keywords)
        alert_pattern = r'((?:critical|urgent|warning|alert|attention)[^.!?]*[.!?])'
        alerts = re.findall(alert_pattern, response, re.IGNORECASE)
        structured["alerts"] = [alert.strip() for alert in alerts]
        
        # Extract bed information
        bed_pattern = r'([A-Z]{2,}-\d+|bed\s+\d+|room\s+\d+)'
        beds = re.findall(bed_pattern, response, re.IGNORECASE)
        structured["bed_info"] = list(set(beds))
        
        return structured
    
    def _add_visual_enhancements(self, response: str) -> str:
        """Add visual enhancements like emojis and formatting"""
        
        # Add emojis for common terms
        emoji_replacements = {
            r'\bcritical\b': f'{self.emoji_map["critical"]} CRITICAL',
            r'\bwarning\b': f'{self.emoji_map["warning"]} Warning',
            r'\bavailable\b': f'{self.emoji_map["available"]} Available',
            r'\boccupied\b': f'{self.emoji_map["occupied"]} Occupied',
            r'\bbeds?\b': f'{self.emoji_map["bed"]} bed',
            r'\bpatients?\b': f'{self.emoji_map["patient"]} patient',
            r'\bcleaning\b': f'{self.emoji_map["cleaning"]} cleaning',
            r'\brecommend': f'{self.emoji_map["info"]} Recommend'
        }
        
        enhanced = response
        for pattern, replacement in emoji_replacements.items():
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        # Format sections with headers
        enhanced = self._format_sections(enhanced)
        
        return enhanced
    
    def _format_sections(self, response: str) -> str:
        """Format response sections with clear headers"""
        
        # Common section patterns
        section_patterns = {
            r'(Current Status|Status|Overview):', '📊 **\\1:**',
            r'(Recommendations?|Suggestions?):', '💡 **\\1:**',
            r'(Alerts?|Warnings?):', '⚠️ **\\1:**',
            r'(Next Steps?|Actions?):', '🎯 **\\1:**',
            r'(Analysis|Insights?):', '🔍 **\\1:**'
        }
        
        formatted = response
        for pattern, replacement in section_patterns.items():
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)
        
        return formatted
    
    def _create_response_cards(self, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create response cards for complex data visualization"""
        cards = []
        
        # Metrics card
        if structured_data["metrics"]:
            cards.append({
                "type": "metrics",
                "title": "📊 Key Metrics",
                "data": structured_data["metrics"],
                "style": "grid"
            })
        
        # Alerts card
        if structured_data["alerts"]:
            cards.append({
                "type": "alerts",
                "title": "⚠️ Attention Required",
                "data": structured_data["alerts"],
                "style": "list",
                "urgency": "high"
            })
        
        # Recommendations card
        if structured_data["recommendations"]:
            cards.append({
                "type": "recommendations",
                "title": "💡 Recommendations",
                "data": structured_data["recommendations"],
                "style": "checklist"
            })
        
        return cards
    
    def _generate_quick_actions(self, metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate quick action buttons based on context"""
        actions = []
        
        intent = metadata.get("intent", "")
        entities = metadata.get("entities", {})
        
        # Common actions
        actions.append({"label": "🔄 Refresh Data", "action": "refresh_data"})
        
        # Context-specific actions
        if intent == "bed_availability":
            actions.extend([
                {"label": "🛏️ Show All Beds", "action": "show_all_beds"},
                {"label": "📊 Ward Summary", "action": "ward_summary"}
            ])
        elif intent == "patient_info":
            actions.extend([
                {"label": "👥 Patient List", "action": "patient_list"},
                {"label": "🏥 Admission Queue", "action": "admission_queue"}
            ])
        elif intent == "occupancy_status":
            actions.extend([
                {"label": "📈 Trends", "action": "occupancy_trends"},
                {"label": "🎯 Optimize", "action": "optimization_suggestions"}
            ])
        
        # Ward-specific actions
        if "ward" in entities:
            ward = entities["ward"]
            actions.append({"label": f"🏥 {ward} Details", "action": f"ward_details_{ward.lower()}"})
        
        return actions[:6]  # Limit to 6 actions
    
    def _determine_response_type(self, response: str) -> str:
        """Determine the type of response for UI rendering"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["critical", "urgent", "alert"]):
            return "alert"
        elif any(word in response_lower for word in ["available", "vacant", "beds"]):
            return "availability"
        elif any(word in response_lower for word in ["patient", "admission", "discharge"]):
            return "patient_info"
        elif any(word in response_lower for word in ["occupancy", "status", "rate"]):
            return "status"
        elif any(word in response_lower for word in ["recommend", "suggest", "should"]):
            return "recommendation"
        else:
            return "general"
    
    def _determine_urgency(self, response: str) -> str:
        """Determine urgency level for UI styling"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["critical", "emergency", "immediate"]):
            return "critical"
        elif any(word in response_lower for word in ["urgent", "warning", "attention"]):
            return "high"
        elif any(word in response_lower for word in ["recommend", "suggest", "consider"]):
            return "medium"
        else:
            return "low"
    
    def _extract_visual_elements(self, response: str) -> Dict[str, Any]:
        """Extract elements that can be visualized"""
        visual_elements = {
            "charts": [],
            "progress_bars": [],
            "status_indicators": [],
            "maps": []
        }
        
        # Look for percentage data that can be shown as progress bars
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        percentages = re.findall(percentage_pattern, response)
        
        for percentage in percentages:
            visual_elements["progress_bars"].append({
                "value": float(percentage.replace('%', '')),
                "label": f"Occupancy: {percentage}",
                "color": self._get_progress_color(float(percentage.replace('%', '')))
            })
        
        # Look for ward/department data for charts
        ward_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:\s*(\d+)'
        ward_data = re.findall(ward_pattern, response)
        
        if ward_data:
            visual_elements["charts"].append({
                "type": "bar",
                "title": "Ward Occupancy",
                "data": [{"name": ward, "value": int(value)} for ward, value in ward_data]
            })
        
        return visual_elements
    
    def _get_progress_color(self, percentage: float) -> str:
        """Get color for progress bar based on percentage"""
        if percentage >= 90:
            return "red"
        elif percentage >= 80:
            return "orange"
        elif percentage >= 60:
            return "yellow"
        else:
            return "green"

# Global formatter instance
response_formatter = ResponseFormatter()
