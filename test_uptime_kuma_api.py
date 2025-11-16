"""Test Uptime Kuma API connectivity"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient


async def main():
    server_url = "http://localhost:3001"
    api_key = "Admin@231" #"uk3_-Vo0N_-BFSE4rRfhPGY9qF7Nd9bUSIhDbmRkZ15Z"
    username = "admin"

    print("=" * 70)
    print("UPTIME KUMA API TEST")
    print("=" * 70)
    print(f"Server: {server_url}")
    print(f"API Key: {api_key[:20]}...")
    print(f"Username: '{username}' (empty for API key auth)")
    print()

    client = UptimeKumaClient(server_url, api_key, username)

    # Test 1: Connection
    print("TEST 1: Connection")
    print("-" * 70)
    connected = await client.connect()
    if connected:
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    print()

    # Test 2: Get monitors
    print("TEST 2: Get All Monitors")
    print("-" * 70)
    monitors = await client.get_all_monitors()
    print(f"Found {len(monitors)} monitors:")
    for m in monitors:
        status = {0: "DOWN", 1: "UP", 2: "PENDING", 3: "MAINTENANCE"}.get(m['status'], "UNKNOWN")
        print(f"  - {m['friendly_name']}: {status}")
    print()

    # Test 3: Get status by name
    if monitors:
        print("TEST 3: Get Status by Name")
        print("-" * 70)
        test_monitor = monitors[0]['friendly_name']
        status = await client.get_monitor_status_by_name(test_monitor)
        status_text = {0: "DOWN", 1: "UP", 2: "PENDING", 3: "MAINTENANCE"}.get(status, "UNKNOWN")
        print(f"Monitor '{test_monitor}': {status_text}")
        print()

    print("=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

