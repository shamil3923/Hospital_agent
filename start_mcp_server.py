"""
MCP Server Startup Script for Hospital Agent
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for MCP server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def start_mcp_server():
    """Start the MCP server"""
    print("🔧 Starting Hospital MCP Server...")
    
    # Setup logging
    setup_logging()
    
    # Get the MCP server script path
    server_path = Path(__file__).parent / "hospital_mcp" / "server.py"
    
    if not server_path.exists():
        print(f"❌ MCP server script not found at {server_path}")
        return 1
    
    try:
        # Start the MCP server
        print(f"🚀 Starting MCP server from {server_path}")
        print("📡 MCP server will communicate via stdio")
        print("Press Ctrl+C to stop")
        
        # Run the server
        subprocess.run([
            sys.executable, str(server_path)
        ], cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n🛑 MCP server stopped")
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return 1
    
    return 0

def main():
    """Main function"""
    print("🏥 Hospital Agent - MCP Server Startup")
    print("=" * 50)
    
    return start_mcp_server()

if __name__ == "__main__":
    sys.exit(main())
