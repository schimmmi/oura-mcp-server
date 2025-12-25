#!/usr/bin/env python3
"""
Test Advanced Features - Oura MCP Server

Tests the new intelligence layer features:
- HRV resources with baseline comparison
- Recovery status detection
- Training readiness assessment
- Metric correlation analysis
- Anomaly detection
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from oura_mcp.core.server import OuraMCPServer
from oura_mcp.utils.config import get_config


async def test_hrv_resources(server: OuraMCPServer):
    """Test HRV resources."""
    print("\n" + "="*80)
    print("TEST 1: HRV Resources")
    print("="*80)

    # Test latest HRV
    print("\n📍 Testing: oura://hrv/latest")
    print("-" * 80)
    result = await server._get_hrv_resource("latest")
    print(result)

    # Test 7-day trend
    print("\n📍 Testing: oura://hrv/trend/7_days")
    print("-" * 80)
    result = await server._get_hrv_resource("trend_7_days")
    print(result)


async def test_recovery_status(server: OuraMCPServer):
    """Test recovery status detection."""
    print("\n" + "="*80)
    print("TEST 2: Recovery Status Detection")
    print("="*80)

    result = await server._tool_detect_recovery_status()
    print(result)


async def test_training_readiness(server: OuraMCPServer):
    """Test training readiness assessment."""
    print("\n" + "="*80)
    print("TEST 3: Training Readiness Assessment")
    print("="*80)

    training_types = ["general", "endurance", "strength", "high_intensity"]

    for training_type in training_types:
        print(f"\n📍 Testing: {training_type.upper()}")
        print("-" * 80)
        result = await server._tool_assess_training_readiness(training_type)
        print(result)
        print()


async def test_correlate_metrics(server: OuraMCPServer):
    """Test metric correlation analysis."""
    print("\n" + "="*80)
    print("TEST 4: Metric Correlation Analysis")
    print("="*80)

    correlations = [
        ("sleep_score", "readiness_score", 14),
        ("activity_score", "sleep_score", 30),
        ("hrv_balance", "readiness_score", 30),
    ]

    for metric1, metric2, days in correlations:
        print(f"\n📍 Testing: {metric1} vs {metric2} ({days} days)")
        print("-" * 80)
        result = await server._tool_correlate_metrics(metric1, metric2, days)
        print(result)
        print()


async def test_anomaly_detection(server: OuraMCPServer):
    """Test anomaly detection."""
    print("\n" + "="*80)
    print("TEST 5: Anomaly Detection")
    print("="*80)

    metric_types = ["sleep", "readiness"]

    for metric_type in metric_types:
        print(f"\n📍 Testing: {metric_type.upper()} anomalies")
        print("-" * 80)
        result = await server._tool_detect_anomalies(metric_type, 7)
        print(result)
        print()


async def test_all_features():
    """Run all advanced feature tests."""
    print("\n" + "="*80)
    print("🧪 OURA MCP SERVER - ADVANCED FEATURES TEST SUITE")
    print("="*80)

    # Load config
    config = get_config()
    print(f"\n✅ Configuration loaded")
    print(f"   Server: {config.mcp.server.name} v{config.mcp.server.version}")
    print(f"   Enabled Resources: {', '.join(config.mcp.resources.enabled)}")
    print(f"   Enabled Tools: {len(config.mcp.tools.enabled)} tools")

    # Create server
    server = OuraMCPServer(config)

    async with server:
        print(f"✅ Server initialized")
        print(f"   Baseline Manager: Ready")
        print(f"   Anomaly Detector: Ready")
        print(f"   Interpretation Engine: Ready")

        try:
            # Run tests
            await test_hrv_resources(server)
            await test_recovery_status(server)
            await test_training_readiness(server)
            await test_correlate_metrics(server)
            await test_anomaly_detection(server)

            print("\n" + "="*80)
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
            print("="*80)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_all_features())
