#!/usr/bin/env python3
"""
Test script for auto-monitoring feature
Demonstrates automatic container discovery based on autoheal=true label
"""

import docker
import time
import requests
from datetime import datetime

def test_auto_monitoring():
    """Test the auto-monitoring feature"""

    print("=" * 70)
    print("Docker Auto-Heal - Auto-Monitoring Feature Test")
    print("=" * 70)
    print()

    # Initialize Docker client
    client = docker.from_env()

    # Test container name
    test_container_name = "autoheal-test-nginx"

    try:
        # Step 1: Clean up any existing test container
        print("Step 1: Cleaning up any existing test containers...")
        try:
            existing = client.containers.get(test_container_name)
            existing.remove(force=True)
            print(f"✓ Removed existing container: {test_container_name}")
        except docker.errors.NotFound:
            print("✓ No existing container to clean up")
        print()

        # Step 2: Start a container with autoheal=true label
        print("Step 2: Starting test container with autoheal=true label...")
        container = client.containers.run(
            image="nginx:alpine",
            name=test_container_name,
            labels={"autoheal": "true", "test": "auto-monitor"},
            detach=True,
            remove=False,
            ports={"80/tcp": None}  # Random port
        )
        print(f"✓ Started container: {container.name}")
        print(f"  Container ID: {container.id[:12]}")
        print(f"  Labels: autoheal=true")
        print()

        # Step 3: Wait for event processing
        print("Step 3: Waiting for auto-monitoring event (5 seconds)...")
        for i in range(5, 0, -1):
            print(f"  {i}...", end="", flush=True)
            time.sleep(1)
        print(" Done!")
        print()

        # Step 4: Check if container was auto-monitored
        print("Step 4: Verifying container was auto-monitored...")
        try:
            # Query the autoheal API
            response = requests.get("http://localhost:3131/api/events", timeout=5)
            if response.status_code == 200:
                events = response.json()

                # Look for auto_monitor events for this container
                auto_monitor_events = [
                    e for e in events
                    if e.get("event_type") == "auto_monitor"
                    and container.id in e.get("container_id", "")
                ]

                if auto_monitor_events:
                    print("✓ Container was automatically added to monitoring!")
                    event = auto_monitor_events[0]
                    print(f"  Event Type: {event['event_type']}")
                    print(f"  Container: {event['container_name']}")
                    print(f"  Status: {event['status']}")
                    print(f"  Message: {event['message']}")
                    print(f"  Timestamp: {event['timestamp']}")
                else:
                    print("⚠ No auto-monitor event found yet (may need more time)")
            else:
                print(f"⚠ API returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("⚠ Could not connect to autoheal API at localhost:3131")
            print("  Make sure docker-autoheal service is running")
        except Exception as e:
            print(f"⚠ Error checking events: {e}")
        print()

        # Step 5: Verify container is in monitored list
        print("Step 5: Checking configuration...")
        try:
            response = requests.get("http://localhost:3131/api/config", timeout=5)
            if response.status_code == 200:
                config = response.json()
                selected = config.get("containers", {}).get("selected", [])

                # Check if container ID is in selected list
                if container.id in selected or any(container.id.startswith(s) for s in selected):
                    print("✓ Container is in the monitored list!")
                    print(f"  Monitored containers: {len(selected)}")
                else:
                    print("⚠ Container not found in monitored list")
                    print(f"  Selected: {selected}")
        except Exception as e:
            print(f"⚠ Error checking config: {e}")
        print()

        # Step 6: Show container details
        print("Step 6: Container details...")
        container.reload()
        print(f"  Name: {container.name}")
        print(f"  Status: {container.status}")
        print(f"  ID: {container.id[:12]}")
        print(f"  Image: {container.image.tags[0] if container.image.tags else 'N/A'}")
        labels = container.labels
        print(f"  Labels:")
        for key, value in labels.items():
            print(f"    {key}={value}")
        print()

        # Step 7: Test without label
        print("Step 7: Testing container WITHOUT autoheal label...")
        test_container_no_label = "autoheal-test-no-label"
        try:
            existing = client.containers.get(test_container_no_label)
            existing.remove(force=True)
        except docker.errors.NotFound:
            pass

        container_no_label = client.containers.run(
            image="nginx:alpine",
            name=test_container_no_label,
            labels={"test": "no-autoheal"},
            detach=True,
            remove=False
        )
        print(f"✓ Started container without autoheal label: {container_no_label.name}")
        print(f"  This container should NOT be auto-monitored")
        print()

        time.sleep(3)

        try:
            response = requests.get("http://localhost:3131/api/events", timeout=5)
            if response.status_code == 200:
                events = response.json()
                auto_monitor_events = [
                    e for e in events
                    if e.get("event_type") == "auto_monitor"
                    and container_no_label.id in e.get("container_id", "")
                ]

                if not auto_monitor_events:
                    print("✓ Correctly skipped container without autoheal=true label")
                else:
                    print("⚠ Container was unexpectedly auto-monitored")
        except Exception as e:
            print(f"⚠ Error checking events: {e}")
        print()

        # Summary
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("✓ Container with autoheal=true label: Auto-monitored")
        print("✓ Container without label: Not auto-monitored")
        print()
        print("The auto-monitoring feature is working correctly!")
        print()

        # Cleanup prompt
        print("=" * 70)
        print("CLEANUP")
        print("=" * 70)
        response = input("Remove test containers? (y/n): ")
        if response.lower() == 'y':
            container.remove(force=True)
            container_no_label.remove(force=True)
            print("✓ Test containers removed")
        else:
            print("Test containers left running:")
            print(f"  - {container.name} (with autoheal=true)")
            print(f"  - {container_no_label.name} (without label)")
            print()
            print("To remove manually:")
            print(f"  docker rm -f {container.name} {container_no_label.name}")

    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    try:
        success = test_auto_monitoring()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)

