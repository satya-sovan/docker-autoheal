"""
Simple test for clear_events API endpoint
Run this after starting the Docker Auto-Heal service
"""
import requests
import json

API_BASE = "http://localhost:3131"


def test_clear_events_api():
    """Test the clear events API endpoint"""
    print("=" * 60)
    print("Testing Clear Events API")
    print("=" * 60)
    print()

    # Get current events
    print("1. Fetching current events...")
    try:
        response = requests.get(f"{API_BASE}/api/events")
        response.raise_for_status()
        events = response.json()
        print(f"   Current events: {len(events)}")
        if events:
            print(f"   Latest event: {events[-1]['container_name']} - {events[-1]['message']}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    print()

    # Clear events
    print("2. Clearing all events...")
    try:
        response = requests.delete(f"{API_BASE}/api/events")
        response.raise_for_status()
        result = response.json()
        print(f"   ✓ {result['message']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    print()

    # Verify cleared
    print("3. Verifying events cleared...")
    try:
        response = requests.get(f"{API_BASE}/api/events")
        response.raise_for_status()
        events = response.json()
        print(f"   Remaining events: {len(events)}")
        
        if len(events) == 0:
            print("   ✅ SUCCESS: All events cleared!")
        else:
            print(f"   ⚠️  WARNING: {len(events)} events still remain")
    except Exception as e:
        print(f"   Error: {e}")
    print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("Make sure Docker Auto-Heal service is running on port 3131\n")
    test_clear_events_api()

