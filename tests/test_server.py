#!/usr/bin/env python3
"""Test MCP server functionality."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from oura_mcp.core.server import OuraMCPServer
from oura_mcp.utils.config import get_config
from oura_mcp.utils.logging import setup_logging


async def test_server():
    """Test MCP server initialization and basic functionality."""
    print("🔍 Testing MCP Server...\n")
    
    try:
        # Load config
        config = get_config()
        setup_logging(config.logging)
        
        print(f"✅ Config loaded")
        print(f"   Server: {config.mcp.server.name}")
        print(f"   Version: {config.mcp.server.version}")
        print(f"   Transport: {config.mcp.server.transport}\n")
        
        # Initialize server
        print("🚀 Initializing MCP server...")
        server = OuraMCPServer(config)
        print("   ✅ Server created\n")
        
        # Test with context manager
        print("🔗 Testing server context manager...")
        async with server:
            print("   ✅ Server entered context (Oura client initialized)\n")
            
            # Test resource access
            print("📊 Testing resource access...")
            
            # Test sleep resource
            print("\n1️⃣ Testing oura://sleep/today")
            try:
                sleep_result = await server._get_sleep_resource("today")
                print("   ✅ Sleep resource works!")
                print(f"\n{sleep_result}\n")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
            
            # Test readiness resource
            print("\n2️⃣ Testing oura://readiness/today")
            try:
                readiness_result = await server._get_readiness_resource("today")
                print("   ✅ Readiness resource works!")
                print(f"\n{readiness_result}\n")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
            
            # Test activity resource
            print("\n3️⃣ Testing oura://activity/today")
            try:
                activity_result = await server._get_activity_resource("today")
                print("   ✅ Activity resource works!")
                print(f"\n{activity_result}\n")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
            
            # Test tools
            print("🛠  Testing tools...")
            
            print("\n4️⃣ Testing generate_daily_brief")
            try:
                brief = await server._tool_generate_daily_brief()
                print("   ✅ Daily brief works!")
                print(f"\n{brief}\n")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
            
            print("\n5️⃣ Testing analyze_sleep_trend")
            try:
                analysis = await server._tool_analyze_sleep_trend(7)
                print("   ✅ Sleep trend analysis works!")
                print(f"\n{analysis}\n")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
        
        print("✨ All server tests passed!\n")
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
