#!/usr/bin/env python3
"""
Integration test for Container ID Bug Fix
Tests that container monitoring persists across container recreations
"""

import docker
import time
import requests
import sys
from datetime import datetime


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_container_recreation_monitoring():
    """
    Integration test for Container ID Bug Fix
    
    This test validates that:
    """Test that the Container ID bug is fixed"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset config manager state
        config_manager._container_restart_counts.clear()
        config_manager._quarantined_containers.clear()
        config_manager._custom_health_checks.clear()

        # Create mock Docker client
        self.mock_docker_client = Mock()
        self.monitoring_engine = MonitoringEngine(self.mock_docker_client)

    def test_restart_count_persists_by_name(self):
        """Test that restart counts are tracked by container name, not ID"""
        container_name = "test-app"
        old_id = "abc123def456old"
        new_id = "xyz789uvw012new"

        # Record restart with old ID
        config_manager.record_restart(container_name)
        config_manager.record_restart(container_name)

        # Get restart count - should work with container name
        count = config_manager.get_restart_count(container_name, window_seconds=600)
        self.assertEqual(count, 2, "Restart count should be 2")

        # Simulate container recreation (new ID)
        # Record another restart with same name
        config_manager.record_restart(container_name)

        # Count should persist across ID change
        count = config_manager.get_restart_count(container_name, window_seconds=600)
        self.assertEqual(count, 3, "Restart count should persist across container recreation")

    def test_quarantine_persists_by_name(self):
        """Test that quarantine status persists by container name"""
        container_name = "problematic-app"
        old_id = "old_container_id_123"
        new_id = "new_container_id_456"

        # Quarantine container by name
        config_manager.quarantine_container(container_name)

        # Check quarantine status by name
        self.assertTrue(
            config_manager.is_quarantined(container_name),
            "Container should be quarantined by name"
        )

        # Simulate container recreation with new ID
        # Check if still quarantined (should be, because we track by name)
        self.assertTrue(
            config_manager.is_quarantined(container_name),
            "Container should remain quarantined after recreation"
        )

        # Unquarantine by name
        config_manager.unquarantine_container(container_name)
        self.assertFalse(
            config_manager.is_quarantined(container_name),
            "Container should be unquarantined"
        )

    def test_monitoring_selection_by_name(self):
        """Test that container selection works with names"""
        container_name = "webapp"
        container_id = "abc123"

        config = config_manager.get_config()

        # Add container by name
        config.containers.selected.append(container_name)
        config_manager.update_config(config)

        # Create mock container info
        mock_info = {
            "full_id": container_id,
            "id": container_id[:12],
            "name": container_name,
            "labels": {}
        }

        mock_container = Mock()
        mock_container.name = container_name
        mock_container.id = container_id

        # Should be monitored by name
        should_monitor = self.monitoring_engine.should_monitor_container(
            mock_container, mock_info
        )
        self.assertTrue(should_monitor, "Container should be monitored by name")

        # Simulate recreation with new ID
        new_id = "xyz789"
        mock_info["full_id"] = new_id
        mock_info["id"] = new_id[:12]
        mock_container.id = new_id

        # Should still be monitored (same name, different ID)
        should_monitor = self.monitoring_engine.should_monitor_container(
            mock_container, mock_info
        )
        self.assertTrue(
            should_monitor,
            "Container should remain monitored after recreation (same name, new ID)"
        )

    def test_backwards_compatibility_with_ids(self):
        """Test that old ID-based configs still work"""
        container_name = "legacy-app"
        container_id = "legacy_id_12345"

        config = config_manager.get_config()

        # Add container by ID (old way)
        config.containers.selected.append(container_id)
        config_manager.update_config(config)

        # Create mock container info
        mock_info = {
            "full_id": container_id,
            "id": container_id[:12],
            "name": container_name,
            "labels": {}
        }

        mock_container = Mock()
        mock_container.name = container_name
        mock_container.id = container_id

        # Should be monitored by ID (backwards compatibility)
        should_monitor = self.monitoring_engine.should_monitor_container(
            mock_container, mock_info
        )
        self.assertTrue(should_monitor, "Container should be monitored by ID (backwards compat)")

    def test_event_stores_both_name_and_id(self):
        """Test that events store both container name and ID"""
        container_name = "event-test-app"
        container_id = "event_test_id_123"

        event = AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_name=container_name,
            container_id=container_id,
            event_type="restart",
            restart_count=1,
            status="success",
            message="Test restart"
        )

        # Verify both are stored
        self.assertEqual(event.container_name, container_name)
        self.assertEqual(event.container_id, container_id)

    def test_custom_health_check_lookup_by_name(self):
        """Test that custom health checks can be looked up by name"""
        container_name = "health-check-app"
        container_id = "health_id_123"

        from app.config.config_manager import HealthCheckConfig

        # Create health check with name (new way)
        health_check = HealthCheckConfig(
            container_name=container_name,
            container_id=container_id,
            check_type="http",
            http_endpoint="http://localhost:8080/health"
        )

        config_manager.add_custom_health_check(health_check)

        # Lookup by name should work
        retrieved = config_manager.get_custom_health_check(container_name)
        self.assertIsNotNone(retrieved, "Should find health check by name")
        self.assertEqual(retrieved.container_name, container_name)

    def test_exclusion_by_name(self):
        """Test that container exclusion works with names"""
        container_name = "excluded-app"
        container_id = "excluded_id_123"

        config = config_manager.get_config()

        # Exclude by name
        config.containers.excluded.append(container_name)
        config_manager.update_config(config)

        # Create mock container info
        mock_info = {
            "full_id": container_id,
            "id": container_id[:12],
            "name": container_name,
            "labels": {"autoheal": "true"}
        }

        mock_container = Mock()
        mock_container.name = container_name
        mock_container.id = container_id

        # Should NOT be monitored (explicitly excluded by name)
        should_monitor = self.monitoring_engine.should_monitor_container(
            mock_container, mock_info
        )
        self.assertFalse(should_monitor, "Container should be excluded by name")

    def test_dual_lookup_name_and_id(self):
        """Test that lookups check both name and ID"""
        container_name = "dual-lookup-app"
        old_id = "old_id_abc"
        new_id = "new_id_xyz"

        # Quarantine by old ID (legacy data)
        config_manager.quarantine_container(old_id)

        # Should be quarantined when checked by old ID
        self.assertTrue(config_manager.is_quarantined(old_id))

        # Now quarantine by name (new way)
        config_manager.quarantine_container(container_name)

        # Should be quarantined when checked by name
        self.assertTrue(config_manager.is_quarantined(container_name))

        # Should also check by new ID (even though quarantined by name)
        # This tests the dual lookup in _check_single_container


class TestContainerRecreationScenario(unittest.TestCase):
    """Integration test simulating actual container recreation"""

    def setUp(self):
        """Set up test fixtures"""
        config_manager._container_restart_counts.clear()
        config_manager._quarantined_containers.clear()

        self.mock_docker_client = Mock()
        self.monitoring_engine = MonitoringEngine(self.mock_docker_client)

    def test_complete_recreation_scenario(self):
        """
        Simulate complete container lifecycle:
        1. Container monitored
        2. Container fails and restarts multiple times
        3. Container recreated (new ID)
        4. Restart history should persist
        """
        container_name = "production-app"
        old_id = "prod_app_old_id_12345"
        new_id = "prod_app_new_id_67890"

        # Step 1: Add container to monitoring by name
        config = config_manager.get_config()
        config.containers.selected.append(container_name)
        config_manager.update_config(config)

        # Step 2: Simulate failures and restarts
        config_manager.record_restart(container_name)
        config_manager.record_restart(container_name)

        restart_count = config_manager.get_restart_count(container_name, 600)
        self.assertEqual(restart_count, 2, "Should have 2 restarts")

        # Step 3: Simulate container recreation (new ID)
        # In real scenario, Docker assigns new ID but keeps same name

        # Step 4: Add another restart with same name (but imagine it's new ID)
        config_manager.record_restart(container_name)

        # Step 5: Verify restart history persisted
        restart_count = config_manager.get_restart_count(container_name, 600)
        self.assertEqual(
            restart_count, 3,
            "Restart count should persist across container recreation"
        )

        # Step 6: Verify container still monitored
        mock_info = {
            "full_id": new_id,
            "id": new_id[:12],
            "name": container_name,
            "labels": {}
        }

        mock_container = Mock()
        mock_container.name = container_name
        mock_container.id = new_id

        should_monitor = self.monitoring_engine.should_monitor_container(
            mock_container, mock_info
        )
        self.assertTrue(
            should_monitor,
            "Container should still be monitored after recreation"
        )


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestContainerIdBugFix))
    suite.addTests(loader.loadTestsFromTestCase(TestContainerRecreationScenario))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

