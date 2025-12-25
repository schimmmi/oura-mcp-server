#!/usr/bin/env python3
"""Quick test script for Oura API connection."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from oura_mcp.api.client import OuraClient
from oura_mcp.utils.config import get_config


async def test_api():
    """Test Oura API connection."""
    print("🔍 Testing Oura API connection...\n")
    
    try:
        # Load config
        config = get_config()
        print(f"✅ Config loaded")
        print(f"   Base URL: {config.oura.api.base_url}")
        print(f"   Token: {config.oura.api.access_token[:10]}...{config.oura.api.access_token[-4:]}\n")
        
        # Test API
        async with OuraClient(config.oura.api) as client:
            print("🔗 Connecting to Oura API...")
            
            # Test 1: Personal Info
            print("\n1️⃣ Fetching personal info...")
            info = await client.get_personal_info()
            print(f"   ✅ Connected!")
            print(f"   Age: {info.get('age', 'N/A')}")
            print(f"   Email: {info.get('email', 'N/A')}")
            
            # Test 2: Recent Sleep
            print("\n2️⃣ Fetching recent sleep data...")
            sleep_data = await client.get_daily_sleep()
            if sleep_data:
                latest = sleep_data[-1]
                print(f"   ✅ Found {len(sleep_data)} sleep record(s)")
                print(f"   Latest: {latest.get('day')}")
                print(f"   Score: {latest.get('score', 'N/A')}")
                total_sec = latest.get('total_sleep_duration', 0)
                print(f"   Duration: {total_sec // 3600}h {(total_sec % 3600) // 60}m")
            else:
                print("   ⚠️  No sleep data found")
            
            # Test 3: Readiness
            print("\n3️⃣ Fetching readiness data...")
            readiness_data = await client.get_daily_readiness()
            if readiness_data:
                latest = readiness_data[-1]
                print(f"   ✅ Found {len(readiness_data)} readiness record(s)")
                print(f"   Latest: {latest.get('day')}")
                print(f"   Score: {latest.get('score', 'N/A')}")
            else:
                print("   ⚠️  No readiness data found")
            
            # Test 4: Activity
            print("\n4️⃣ Fetching activity data...")
            activity_data = await client.get_daily_activity()
            if activity_data:
                latest = activity_data[-1]
                print(f"   ✅ Found {len(activity_data)} activity record(s)")
                print(f"   Latest: {latest.get('day')}")
                print(f"   Score: {latest.get('score', 'N/A')}")
                print(f"   Steps: {latest.get('steps', 0):,}")
            else:
                print("   ⚠️  No activity data found")
        
        print("\n✨ All tests passed! API is working correctly.\n")
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
