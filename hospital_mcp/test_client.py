#!/usr/bin/env python3
"""
Test client for Hospital MCP Server
"""

import asyncio
import json
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_hospital_mcp():
    """Test the hospital MCP server"""
    
    # Start the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["hospital_mcp/enhanced_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            print("🏥 Hospital MCP Server Connected!")
            print("=" * 50)
            
            # List available tools
            tools = await session.list_tools()
            print(f"📋 Available Tools ({len(tools.tools)}):")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
            
            print("\n" + "=" * 50)
            
            # Test 1: Get hospital status
            print("🏥 Testing: Get Hospital Status")
            try:
                result = await session.call_tool("get_hospital_status", {})
                status_data = json.loads(result.content[0].text)
                
                print(f"📊 Overall Occupancy: {status_data['overall']['occupancy_rate']}%")
                print(f"🛏️ Total Beds: {status_data['overall']['total_beds']}")
                print(f"👥 Occupied: {status_data['overall']['occupied_beds']}")
                print(f"✅ Available: {status_data['overall']['available_beds']}")
                
                print("\n🏥 Ward Status:")
                for ward, data in status_data['wards'].items():
                    status_icon = "🔴" if data['status'] == 'critical' else "🟡" if data['status'] == 'high' else "🟢"
                    print(f"  {status_icon} {ward}: {data['occupancy_rate']}% ({data['occupied']}/{data['total']})")
                
                print(f"\n🚨 Active Alerts: {status_data['alerts']['total']}")
                if status_data['alerts']['active_alerts']:
                    for alert in status_data['alerts']['active_alerts']:
                        priority_icon = "🔴" if alert['priority'] == 'critical' else "🟠" if alert['priority'] == 'high' else "🟡"
                        print(f"  {priority_icon} [{alert['priority'].upper()}] {alert['title']} - {alert['department']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "=" * 50)
            
            # Test 2: Get critical alerts
            print("🚨 Testing: Get Critical Alerts")
            try:
                result = await session.call_tool("get_critical_alerts", {})
                print(result.content[0].text)
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "=" * 50)
            
            # Test 3: Trigger capacity alert
            print("⚡ Testing: Trigger Capacity Alert")
            try:
                result = await session.call_tool("trigger_capacity_alert", {"department": "ICU"})
                alert_data = json.loads(result.content[0].text)
                print(f"✅ Triggered: {alert_data['triggered']}")
                print(f"📊 Alerts Created: {alert_data['capacity_alerts_created']}")
                
                if alert_data['alerts']:
                    print("🚨 New Alerts:")
                    for alert in alert_data['alerts']:
                        print(f"  • [{alert['priority'].upper()}] {alert['title']}")
                        print(f"    {alert['message']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "=" * 50)
            
            # Test 4: Find available beds
            print("🛏️ Testing: Find Available Beds")
            try:
                result = await session.call_tool("find_available_beds", {
                    "bed_type": "ICU",
                    "isolation_required": False
                })
                print(result.content[0].text)
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n🎉 MCP Server Testing Complete!")

async def quick_test():
    """Quick test of specific functionality"""
    server_params = StdioServerParameters(
        command="python",
        args=["hospital_mcp/enhanced_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Quick hospital status check
            result = await session.call_tool("get_hospital_status", {})
            status = json.loads(result.content[0].text)
            
            print(f"🏥 Hospital Status: {status['overall']['occupancy_rate']}% occupancy")
            print(f"🚨 Active Alerts: {status['alerts']['total']}")
            
            # Trigger alerts if needed
            if status['alerts']['total'] == 0:
                print("⚡ Triggering capacity alerts...")
                await session.call_tool("trigger_capacity_alert", {"force": True})
                
                # Check again
                result = await session.call_tool("get_hospital_status", {})
                status = json.loads(result.content[0].text)
                print(f"🚨 Alerts after trigger: {status['alerts']['total']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    else:
        asyncio.run(test_hospital_mcp())
