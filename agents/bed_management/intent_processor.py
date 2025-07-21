"""
Enhanced Intent Recognition and Query Processing
"""
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

class IntentProcessor:
    """Advanced intent recognition and entity extraction"""
    
    def __init__(self):
        # Define intent patterns with keywords and regex
        self.intent_patterns = {
            'bed_availability': {
                'keywords': ['available', 'vacant', 'free', 'empty', 'beds', 'bed'],
                'patterns': [
                    r'(what|how many|show me).*(beds?|available)',
                    r'(available|vacant|free).*(beds?)',
                    r'beds?.*(available|vacant|free)'
                ]
            },
            'patient_info': {
                'keywords': ['patient', 'patients', 'admitted', 'list', 'show'],
                'patterns': [
                    r'(show me|list|give me).*(patients?)',
                    r'patients?.*(admitted|in|list)',
                    r'who.*(admitted|patients?)'
                ]
            },
            'patient_lookup': {
                'keywords': ['pat', 'id:', 'patient id'],
                'patterns': [
                    r'PAT\d+',
                    r'id:\s*PAT\d+',
                    r'patient\s+PAT\d+'
                ]
            },
            'bed_assignment': {
                'keywords': ['assign', 'book', 'reserve', 'allocate', 'admit'],
                'patterns': [
                    r'(assign|book|reserve).*(patient|bed)',
                    r'(admit|allocate).*(patient)',
                    r'need.*(bed|room)'
                ]
            },
            'occupancy_status': {
                'keywords': ['occupancy', 'status', 'capacity', 'utilization'],
                'patterns': [
                    r'(bed|occupancy|capacity).*(status|rate)',
                    r'how.*(full|occupied)',
                    r'utilization.*(rate|status)'
                ]
            },
            'discharge_info': {
                'keywords': ['discharge', 'discharged', 'leaving', 'release'],
                'patterns': [
                    r'(discharge|discharged).*(today|tomorrow)',
                    r'(leaving|release).*(patient)',
                    r'when.*(discharge|leave)'
                ]
            }
        }
        
        # Ward/department entities
        self.ward_entities = {
            'icu': ['icu', 'intensive care', 'critical care', 'intensive'],
            'emergency': ['emergency', 'er', 'emergency room', 'trauma'],
            'general': ['general', 'general ward', 'medical'],
            'pediatric': ['pediatric', 'peds', 'children', 'pediatrics'],
            'maternity': ['maternity', 'obstetrics', 'labor', 'delivery'],
            'surgery': ['surgery', 'surgical', 'operating', 'post-op']
        }
        
        # Severity entities
        self.severity_entities = {
            'critical': ['critical', 'severe', 'life-threatening'],
            'serious': ['serious', 'moderate', 'concerning'],
            'stable': ['stable', 'good', 'improving'],
            'recovering': ['recovering', 'better', 'healing']
        }
    
    def extract_intent(self, query: str) -> str:
        """Extract the primary intent from user query"""
        query_lower = query.lower().strip()
        
        # Check for exact pattern matches first
        for intent, config in self.intent_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, query_lower):
                    return intent
        
        # Fallback to keyword matching
        intent_scores = {}
        for intent, config in self.intent_patterns.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general_inquiry'
    
    def extract_entities(self, query: str) -> Dict:
        """Extract entities like ward, patient ID, severity, etc."""
        query_lower = query.lower().strip()
        entities = {}
        
        # Extract ward/department
        for ward, variations in self.ward_entities.items():
            for variation in variations:
                if variation in query_lower:
                    entities['ward'] = ward.upper()
                    break
            if 'ward' in entities:
                break
        
        # Extract patient ID
        patient_id_match = re.search(r'PAT\d+', query.upper())
        if patient_id_match:
            entities['patient_id'] = patient_id_match.group()
        
        # Extract severity
        for severity, variations in self.severity_entities.items():
            for variation in variations:
                if variation in query_lower:
                    entities['severity'] = severity
                    break
            if 'severity' in entities:
                break
        
        # Extract numbers (bed counts, room numbers, etc.)
        numbers = re.findall(r'\b\d+\b', query)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]
        
        # Extract time references
        time_patterns = {
            'today': r'\b(today|now)\b',
            'tomorrow': r'\b(tomorrow|next day)\b',
            'yesterday': r'\b(yesterday|last day)\b',
            'this_week': r'\b(this week|week)\b'
        }
        
        for time_ref, pattern in time_patterns.items():
            if re.search(pattern, query_lower):
                entities['time_reference'] = time_ref
                break
        
        return entities
    
    def process_query(self, query: str) -> Dict:
        """Main processing function that combines intent and entity extraction"""
        intent = self.extract_intent(query)
        entities = self.extract_entities(query)
        
        # Calculate confidence based on pattern matches and entity extraction
        confidence = self.calculate_confidence(query, intent, entities)
        
        return {
            'original_query': query,
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'processed_at': datetime.now().isoformat()
        }
    
    def calculate_confidence(self, query: str, intent: str, entities: Dict) -> float:
        """Calculate confidence score for the intent recognition"""
        base_confidence = 0.5
        
        # Boost confidence for exact pattern matches
        if intent != 'general_inquiry':
            base_confidence += 0.3
        
        # Boost confidence for entity extraction
        if entities:
            base_confidence += 0.1 * len(entities)
        
        # Boost confidence for specific patterns
        query_lower = query.lower()
        if any(pattern in query_lower for pattern in ['show me', 'give me', 'what is', 'how many']):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def suggest_corrections(self, query: str) -> List[str]:
        """Suggest corrections for unclear queries"""
        suggestions = []
        
        # Common typos and corrections
        corrections = {
            'pateint': 'patient',
            'patinet': 'patient',
            'availabe': 'available',
            'availible': 'available',
            'ocupancy': 'occupancy',
            'ocupied': 'occupied'
        }
        
        corrected_query = query.lower()
        for typo, correction in corrections.items():
            if typo in corrected_query:
                corrected_query = corrected_query.replace(typo, correction)
                suggestions.append(f"Did you mean: {corrected_query}?")
        
        # Suggest similar queries based on partial matches
        if 'bed' in query.lower():
            suggestions.extend([
                "Show me available beds in ICU",
                "What is the bed occupancy status?",
                "Assign a patient to a bed"
            ])
        
        if 'patient' in query.lower():
            suggestions.extend([
                "Show me all patients",
                "List ICU patients",
                "Patient PAT123"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
