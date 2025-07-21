#!/usr/bin/env python3
"""
Test Enhanced Discharge Prediction System
"""

import asyncio
from hospital_mcp.simple_client import SimpleMCPToolsManager

async def test_enhanced_predictions():
    print('=== ENHANCED DISCHARGE PREDICTION SYSTEM ===')
    print()
    
    manager = SimpleMCPToolsManager()
    await manager.initialize()
    
    result = await manager.execute_tool('get_patient_discharge_predictions')
    
    if isinstance(result, list) and result:
        print(f'📊 Total Predictions: {len(result)}')
        print()
        
        for i, pred in enumerate(result, 1):
            print(f'{i}. 👤 Patient: {pred.get("patient_name", "N/A")}')
            print(f'   📅 Admitted: {pred.get("days_admitted", "N/A")} days ago')
            print(f'   📈 Discharge Probability: {pred.get("discharge_probability", 0):.1%}')
            print(f'   🎯 Confidence: {pred.get("confidence", "N/A").title()}')
            print(f'   📋 Readiness: {pred.get("readiness_category", "N/A")}')
            
            discharge_date = pred.get("predicted_discharge_date", "N/A")
            if discharge_date != "N/A":
                discharge_date = discharge_date[:10]  # Just the date part
            print(f'   📅 Predicted Discharge: {discharge_date}')
            
            factors = pred.get('factors', {})
            if factors:
                print(f'   🔍 Analysis:')
                print(f'      • Length of stay: {factors.get("length_of_stay", "N/A")}')
                print(f'      • Base probability: {factors.get("base_probability", "N/A")}')
                print(f'      • Final probability: {factors.get("final_probability", "N/A")}')
            
            recommendations = pred.get('recommendations', [])
            if recommendations:
                print(f'   💡 Recommendations:')
                for rec in recommendations[:3]:
                    print(f'      • {rec}')
            print()
    else:
        print('❌ No predictions available')

if __name__ == "__main__":
    asyncio.run(test_enhanced_predictions())
