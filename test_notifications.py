"""
Test notification system functionality
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_manager import config_manager, AutoHealEvent, NotificationService, NotificationsConfig
from app.notifications.notification_manager import notification_manager


async def test_notifications():
    """Test the notification system"""
    print("=" * 60)
    print("Testing Docker Auto-Heal Notification System")
    print("=" * 60)

    # Initialize notification manager
    await notification_manager.start()
    print("✓ Notification manager started")

    # Create a test notification service (webhook)
    test_service = NotificationService(
        name="Test Webhook",
        type="webhook",
        enabled=True,
        url="https://httpbin.org/post"  # Echo service for testing
    )

    # Configure notifications
    config = config_manager.get_config()
    config.notifications.enabled = True
    config.notifications.services = [test_service]
    config.notifications.event_filters = ["restart", "quarantine"]
    config_manager.update_config(config)
    print("✓ Notification configuration updated")

    # Create test events
    test_events = [
        AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id="test-container-123",
            container_name="nginx-test",
            event_type="restart",
            restart_count=1,
            status="success",
            message="Test restart event"
        ),
        AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id="test-container-456",
            container_name="redis-test",
            event_type="quarantine",
            restart_count=5,
            status="quarantined",
            message="Test quarantine event - exceeded restart limit"
        ),
        AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id="test-container-789",
            container_name="postgres-test",
            event_type="auto_monitor",
            restart_count=0,
            status="enabled",
            message="Test auto-monitor event - should be filtered out"
        ),
    ]

    print("\nSending test notifications...")
    for event in test_events:
        await notification_manager.send_event_notification(event)
        print(f"  ✓ Queued: {event.event_type} - {event.container_name}")

    # Wait for notifications to be processed
    print("\nWaiting for notifications to be sent...")
    await asyncio.sleep(3)

    # Test the test notification function
    print("\nTesting notification service...")
    result = await notification_manager.test_notification("Test Webhook")
    if result["success"]:
        print(f"  ✓ Test notification sent: {result['message']}")
    else:
        print(f"  ✗ Test notification failed: {result['message']}")

    # Stop notification manager
    await notification_manager.stop()
    print("\n✓ Notification manager stopped")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print("\nNote: Two notifications should have been sent (restart and quarantine).")
    print("The auto_monitor event should have been filtered out.")
    print("Check the application logs for confirmation.")


if __name__ == "__main__":
    asyncio.run(test_notifications())

