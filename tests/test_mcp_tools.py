#!/usr/bin/env python3
"""
Test MCP Tools Integration and Usage
"""

import asyncio
import json
from hospital_mcp.simple_client import SimpleMCPToolsManager

async def test_mcp_tools():
    """Test all MCP tools and show their usage"""
    print("🔧 MCP TOOLS INTEGRATION TEST")
    print("=" * 50)
    
    manager = SimpleMCPToolsManager()
    await manager.initialize()
    
    if not manager.initialized:
        print("❌ MCP Manager failed to initialize")
        return
    
    print("✅ MCP Manager initialized successfully\n")
    
    # Test 1: Bed Occupancy Status
    print("1. 🏥 BED OCCUPANCY STATUS")
    print("-" * 30)
    try:
        result = await manager.execute_tool('get_bed_occupancy_status')
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   📊 Total beds: {result.get('total_beds', 'N/A')}")
            print(f"   🔴 Occupied: {result.get('occupied_beds', 'N/A')}")
            print(f"   🟢 Vacant: {result.get('vacant_beds', 'N/A')}")
            print(f"   🧹 Cleaning: {result.get('cleaning_beds', 'N/A')}")
            print(f"   📈 Occupancy rate: {result.get('occupancy_rate', 'N/A')}%")
            
            ward_breakdown = result.get('ward_breakdown', {})
            if ward_breakdown:
                print("   🏥 Ward Breakdown:")
                for ward, stats in ward_breakdown.items():
                    rate = (stats['occupied'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    print(f"      • {ward}: {rate:.1f}% ({stats['occupied']}/{stats['total']})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test 2: Available Beds
    print("2. 🛏️ AVAILABLE BEDS")
    print("-" * 30)
    try:
        result = await manager.execute_tool('get_available_beds')
        if isinstance(result, list):
            print(f"   📋 Available beds found: {len(result)}")
            for i, bed in enumerate(result[:5], 1):
                print(f"      {i}. {bed.get('bed_number', 'N/A')} - {bed.get('ward', 'N/A')}")
                print(f"         Status: {bed.get('status', 'N/A')}")
        else:
            print(f"   ❌ Unexpected result type: {type(result)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test 3: Available ICU Beds (Filtered)
    print("3. 🏥 AVAILABLE ICU BEDS (Filtered)")
    print("-" * 30)
    try:
        result = await manager.execute_tool('get_available_beds', ward='ICU')
        if isinstance(result, list):
            print(f"   📋 Available ICU beds: {len(result)}")
            for i, bed in enumerate(result, 1):
                print(f"      {i}. {bed.get('bed_number', 'N/A')} - {bed.get('ward', 'N/A')}")
        else:
            print(f"   ❌ No ICU beds available or error occurred")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test 4: Critical Alerts
    print("4. 🚨 CRITICAL ALERTS")
    print("-" * 30)
    try:
        result = await manager.execute_tool('get_critical_bed_alerts')
        if isinstance(result, list):
            print(f"   🚨 Active alerts: {len(result)}")
            for i, alert in enumerate(result, 1):
                priority = alert.get('priority', 'N/A').upper()
                title = alert.get('title', 'N/A')
                dept = alert.get('department', 'N/A')
                print(f"      {i}. [{priority}] {title} - {dept}")
                print(f"         {alert.get('message', 'N/A')}")
        else:
            print(f"   ❌ No alerts or error occurred")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test 5: Discharge Predictions
    print("5. 📊 DISCHARGE PREDICTIONS")
    print("-" * 30)
    try:
        result = await manager.execute_tool('get_patient_discharge_predictions')
        if isinstance(result, list):
            print(f"   📈 Predictions available: {len(result)}")
            for i, pred in enumerate(result[:3], 1):
                name = pred.get('patient_name', 'N/A')
                prob = pred.get('discharge_probability', 0)
                days = pred.get('days_admitted', 'N/A')
                print(f"      {i}. {name} - {prob:.1%} probability ({days} days admitted)")
        else:
            print(f"   ❌ No predictions available")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test 6: Update Bed Status (Demo)
    print("6. 🔄 UPDATE BED STATUS (Demo)")
    print("-" * 30)
    try:
        # First, get an available bed to test with
        beds = await manager.execute_tool('get_available_beds')
        if isinstance(beds, list) and beds:
            test_bed = beds[0]['bed_number']
            print(f"   🛏️ Testing with bed: {test_bed}")
            
            # Try to update status (this is just a demo, won't actually change anything)
            result = await manager.execute_tool('update_bed_status', 
                                              bed_number=test_bed, 
                                              new_status='cleaning')
            if result.get('success'):
                print(f"   ✅ Successfully updated {test_bed} to cleaning status")
            else:
                print(f"   ❌ Update failed: {result.get('error', 'Unknown error')}")
        else:
            print("   ❌ No beds available for testing")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    print("🎉 MCP TOOLS TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
