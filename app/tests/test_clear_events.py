"""
Test script to demonstrate the clear_events feature
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.config.config_manager import config_manager, AutoHealEvent
from datetime import datetime, timezone


def test_clear_events():
    """Test the clear_events functionality"""
    print("=" * 60)
    print("Testing Clear Events Feature")
    print("=" * 60)
    print()

    # Add some test events
    print("1. Adding test events...")
    for i in range(5):
        event = AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id=f"test_container_{i}",
            container_name=f"test-container-{i}",
            event_type="restart",
            restart_count=i + 1,
            status="success",
            message=f"Test event {i + 1}"
        )
        config_manager.add_event(event)

    # Get current events
    events = config_manager.get_events()
    print(f"   Added {len(events)} test events")
    print()

    # Display events
    print("2. Current events:")
    for event in events[-5:]:
        print(f"   - {event.container_name}: {event.message}")
    print()

    # Clear events
    print("3. Clearing all events...")
    config_manager.clear_events()
    print("   ✓ Events cleared")
    print()

    # Verify events are cleared
    print("4. Verifying events cleared...")
    remaining_events = config_manager.get_events()
    print(f"   Remaining events: {len(remaining_events)}")

    if len(remaining_events) == 0:
        print("   ✅ SUCCESS: All events cleared!")
    else:
        print(f"   ❌ FAILED: {len(remaining_events)} events still remain")
    print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_clear_events()

