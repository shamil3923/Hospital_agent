"""
Enhanced LLM Prompt Engineering for Hospital Bed Management
"""
from typing import Dict, List, Any
from datetime import datetime

class EnhancedPromptEngine:
    """Advanced prompt engineering for better LLM responses"""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
        self.response_templates = self._create_response_templates()
        self.context_enhancers = self._create_context_enhancers()
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt"""
        return """You are an advanced AI Hospital Bed Management Agent with expertise in:

🏥 CORE COMPETENCIES:
- Real-time bed occupancy monitoring and optimization
- Patient flow management and discharge planning
- Resource allocation and capacity planning
- Emergency response and critical care coordination
- Staff workflow optimization
- Predictive analytics for bed availability

🎯 COMMUNICATION STYLE:
- Professional yet approachable healthcare communication
- Clear, actionable information with specific data points
- Proactive suggestions and recommendations
- Empathetic understanding of healthcare urgency
- Structured responses with bullet points and clear sections

📊 DATA INTERPRETATION:
- Always provide context for numbers (trends, comparisons, implications)
- Highlight critical situations requiring immediate attention
- Suggest optimization opportunities
- Explain the "why" behind recommendations

🚨 PRIORITY HANDLING:
- Critical/Emergency situations: Immediate, urgent tone with clear action items
- Routine inquiries: Helpful, informative, with optimization suggestions
- Planning queries: Strategic, forward-thinking with data-driven insights

🔍 RESPONSE STRUCTURE:
1. Direct answer to the query
2. Current status summary with key metrics
3. Relevant insights or trends
4. Actionable recommendations
5. Next steps or follow-up suggestions

Remember: You're supporting healthcare professionals making critical decisions. Be accurate, timely, and helpful."""

    def _create_response_templates(self) -> Dict[str, str]:
        """Create response templates for different query types"""
        return {
            'bed_availability': """
🛏️ **Bed Availability Status**

**Current Availability:** {available_beds} beds available out of {total_beds} total
**Occupancy Rate:** {occupancy_rate}% ({occupancy_status})

**Ward Breakdown:**
{ward_details}

**💡 Insights:**
{insights}

**🎯 Recommendations:**
{recommendations}
""",
            
            'patient_info': """
👥 **Patient Information**

**Current Census:** {patient_count} patients
{patient_details}

**📈 Key Metrics:**
{metrics}

**⚠️ Attention Required:**
{alerts}

**📋 Next Actions:**
{next_actions}
""",
            
            'occupancy_status': """
📊 **Hospital Occupancy Overview**

**Overall Status:** {occupancy_rate}% occupied ({status_indicator})
- **Occupied:** {occupied_beds} beds
- **Available:** {available_beds} beds  
- **Cleaning/Maintenance:** {cleaning_beds} beds

**🔍 Analysis:**
{analysis}

**⚡ Optimization Opportunities:**
{optimizations}
""",
            
            'critical_alert': """
🚨 **CRITICAL ALERT**

**Issue:** {alert_type}
**Severity:** {severity_level}
**Affected Area:** {affected_area}

**Immediate Actions Required:**
{immediate_actions}

**Current Status:**
{current_status}

**Escalation:** {escalation_info}
""",
            
            'predictive_insight': """
🔮 **Predictive Analysis**

**Forecast Period:** {forecast_period}
**Predicted Status:** {prediction}

**📈 Trends:**
{trends}

**🎯 Proactive Recommendations:**
{proactive_actions}

**📅 Timeline:**
{timeline}
"""
        }
    
    def _create_context_enhancers(self) -> Dict[str, callable]:
        """Create context enhancement functions"""
        return {
            'occupancy_analysis': self._analyze_occupancy,
            'trend_detection': self._detect_trends,
            'recommendation_engine': self._generate_recommendations,
            'urgency_assessment': self._assess_urgency,
            'optimization_suggestions': self._suggest_optimizations
        }
    
    def create_enhanced_prompt(self, query: str, bed_data: Dict, intent: str = None, 
                             entities: Dict = None, context: Dict = None) -> str:
        """Create enhanced prompt with context and intelligence"""
        
        # Analyze the data for insights
        insights = self._generate_insights(bed_data, intent, entities)
        
        # Determine response urgency
        urgency = self._assess_urgency(bed_data)
        
        # Create contextual prompt
        prompt = f"""
{self.system_prompt}

📋 **CURRENT HOSPITAL DATA:**
{self._format_hospital_data(bed_data)}

🎯 **USER QUERY:** "{query}"

📊 **CONTEXT ANALYSIS:**
- Query Intent: {intent or 'General inquiry'}
- Entities Detected: {entities or 'None'}
- Urgency Level: {urgency}
- Session Context: {context or 'New session'}

💡 **DATA INSIGHTS:**
{insights}

🎯 **RESPONSE REQUIREMENTS:**
1. Address the user's specific question directly
2. Provide relevant data with context and implications
3. Include actionable insights and recommendations
4. Use appropriate urgency level in tone
5. Structure response clearly with sections and bullet points
6. End with helpful next steps or follow-up suggestions

**Respond as the Hospital Bed Management Agent:**
"""
        return prompt
    
    def _format_hospital_data(self, bed_data: Dict) -> str:
        """Format hospital data for prompt context"""
        if "error" in bed_data:
            return f"⚠️ Data Error: {bed_data['error']}"
        
        summary = bed_data.get("summary", {})
        wards = bed_data.get("wards", {})
        
        data_text = f"""
**Overall Status:**
- Total Beds: {summary.get('total_beds', 0)}
- Occupied: {summary.get('occupied_beds', 0)} ({summary.get('occupancy_rate', 0)}%)
- Available: {summary.get('vacant_beds', 0)}
- Cleaning: {summary.get('cleaning_beds', 0)}

**Ward Details:**"""
        
        for ward_name, ward_data in wards.items():
            data_text += f"""
- **{ward_name}:** {ward_data.get('occupied', 0)}/{ward_data.get('total', 0)} occupied ({ward_data.get('occupancy_rate', 0)}%)"""
        
        return data_text
    
    def _generate_insights(self, bed_data: Dict, intent: str, entities: Dict) -> str:
        """Generate intelligent insights from data"""
        if "error" in bed_data:
            return "Unable to generate insights due to data error."
        
        summary = bed_data.get("summary", {})
        occupancy_rate = summary.get('occupancy_rate', 0)
        
        insights = []
        
        # Occupancy insights
        if occupancy_rate > 90:
            insights.append("🚨 Critical: Hospital near capacity - immediate attention required")
        elif occupancy_rate > 80:
            insights.append("⚠️ High occupancy - monitor closely for capacity issues")
        elif occupancy_rate < 50:
            insights.append("📉 Low occupancy - opportunity for elective procedures")
        else:
            insights.append("✅ Normal occupancy levels - stable operations")
        
        # Ward-specific insights
        wards = bed_data.get("wards", {})
        for ward_name, ward_data in wards.items():
            ward_occupancy = ward_data.get('occupancy_rate', 0)
            if ward_occupancy > 95:
                insights.append(f"🔴 {ward_name} critically full - consider transfers")
            elif ward_occupancy == 0:
                insights.append(f"💡 {ward_name} available for admissions")
        
        # Cleaning insights
        cleaning_beds = summary.get('cleaning_beds', 0)
        if cleaning_beds > 3:
            insights.append(f"🧹 {cleaning_beds} beds in cleaning - may impact availability")
        
        return "\n".join([f"• {insight}" for insight in insights]) if insights else "• Hospital operations within normal parameters"
    
    def _analyze_occupancy(self, bed_data: Dict) -> str:
        """Analyze occupancy patterns"""
        summary = bed_data.get("summary", {})
        occupancy_rate = summary.get('occupancy_rate', 0)
        
        if occupancy_rate > 90:
            return "Critical capacity - immediate action required"
        elif occupancy_rate > 80:
            return "High utilization - monitor closely"
        elif occupancy_rate > 60:
            return "Optimal utilization - good balance"
        else:
            return "Low utilization - capacity available"
    
    def _detect_trends(self, bed_data: Dict) -> List[str]:
        """Detect trends in bed data"""
        # This would analyze historical data in a real implementation
        return ["Stable occupancy pattern", "No significant trends detected"]
    
    def _generate_recommendations(self, bed_data: Dict, intent: str) -> List[str]:
        """Generate actionable recommendations"""
        summary = bed_data.get("summary", {})
        occupancy_rate = summary.get('occupancy_rate', 0)
        
        recommendations = []
        
        if occupancy_rate > 90:
            recommendations.extend([
                "Expedite discharge planning for stable patients",
                "Consider transferring patients to less occupied wards",
                "Activate overflow protocols if available",
                "Alert administration of capacity constraints"
            ])
        elif occupancy_rate < 50:
            recommendations.extend([
                "Consider scheduling elective procedures",
                "Review staffing levels for optimization",
                "Opportunity for deep cleaning and maintenance"
            ])
        
        if intent == "bed_assignment":
            recommendations.append("Review patient acuity to optimize bed placement")
        
        return recommendations
    
    def _assess_urgency(self, bed_data: Dict) -> str:
        """Assess urgency level of the situation"""
        summary = bed_data.get("summary", {})
        occupancy_rate = summary.get('occupancy_rate', 0)
        
        if occupancy_rate > 95:
            return "CRITICAL"
        elif occupancy_rate > 85:
            return "HIGH"
        elif occupancy_rate > 70:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _suggest_optimizations(self, bed_data: Dict) -> List[str]:
        """Suggest optimization opportunities"""
        optimizations = []
        
        summary = bed_data.get("summary", {})
        cleaning_beds = summary.get('cleaning_beds', 0)
        
        if cleaning_beds > 2:
            optimizations.append("Optimize housekeeping workflow to reduce bed turnover time")
        
        # Ward-specific optimizations
        wards = bed_data.get("wards", {})
        if isinstance(wards, dict):
            ward_occupancies = [(name, data.get('occupancy_rate', 0)) for name, data in wards.items()]
        else:
            ward_occupancies = []
        
        if len(ward_occupancies) > 1:
            max_ward = max(ward_occupancies, key=lambda x: x[1])
            min_ward = min(ward_occupancies, key=lambda x: x[1])
            
            if max_ward[1] - min_ward[1] > 30:
                optimizations.append(f"Consider patient transfers from {max_ward[0]} to {min_ward[0]}")
        
        return optimizations

# Global instance
enhanced_prompt_engine = EnhancedPromptEngine()
