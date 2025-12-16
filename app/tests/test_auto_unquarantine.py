"""
Tests for auto-unquarantine feature
When a quarantined container becomes healthy again, it should be automatically
removed from quarantine with an event logged.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestAutoUnquarantine:
    """Tests for auto-unquarantine feature"""

    def test_quarantine_check_logic(self):
        """Test that quarantine check logic correctly identifies quarantined containers"""
        from app.config.config_manager import ConfigManager
        import tempfile
        import shutil

        # Create temp directory for test data
        temp_dir = tempfile.mkdtemp()

        try:
            # Patch the data directory
            with patch.object(ConfigManager, 'DATA_DIR', temp_dir):
                with patch.object(ConfigManager, '_ensure_data_directory'):
                    manager = ConfigManager.__new__(ConfigManager)
                    manager.DATA_DIR = temp_dir
                    manager._lock = __import__('threading').RLock()
                    manager._quarantined_containers = set()

                    # Test quarantine operations
                    manager._quarantined_containers.add("test-container-1")
                    assert manager.is_quarantined("test-container-1")
                    assert not manager.is_quarantined("test-container-2")

                    # Test unquarantine
                    manager._quarantined_containers.discard("test-container-1")
                    assert not manager.is_quarantined("test-container-1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_auto_unquarantine_event_type_in_defaults(self):
        """Test that auto_unquarantine is in the default notification event filters"""
        from app.config.config_manager import NotificationsConfig

        # Create default config
        config = NotificationsConfig()

        # Check that auto_unquarantine is in the default filters
        assert "auto_unquarantine" in config.event_filters, \
            "auto_unquarantine should be in default notification event filters"

    def test_auto_heal_event_model(self):
        """Test that AutoHealEvent can accept auto_unquarantine event type"""
        from app.config.config_manager import AutoHealEvent

        # Create auto_unquarantine event
        event = AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id="test123",
            container_name="test-container (test_stable_id)",
            event_type="auto_unquarantine",
            restart_count=0,
            status="success",
            message="Container automatically removed from quarantine - auto-healed and now healthy"
        )

        assert event.event_type == "auto_unquarantine"
        assert event.status == "success"
        assert "auto-healed" in event.message

    @pytest.mark.asyncio
    async def test_auto_unquarantine_flow(self):
        """Test the full auto-unquarantine flow"""
        from app.monitor.monitoring_engine import MonitoringEngine
        from app.docker_client.docker_client_wrapper import DockerClientWrapper

        # Create mock docker client
        mock_docker = Mock(spec=DockerClientWrapper)
        engine = MonitoringEngine(mock_docker)

        with patch('app.monitor.monitoring_engine.config_manager') as mock_config, \
             patch('app.monitor.monitoring_engine.notification_manager') as mock_notif:

            # Setup mocks
            mock_config.unquarantine_container = Mock()
            mock_config.clear_restart_history = Mock()
            mock_config.add_event = Mock()
            mock_config.get_config.return_value = Mock(
                restart=Mock(backoff=Mock(initial_seconds=10))
            )
            mock_notif.send_event_notification = AsyncMock()

            # Call auto_unquarantine
            await engine._auto_unquarantine_container(
                quarantine_id="test_stable_id",
                stable_id="test_stable_id",
                container_name="test-container",
                container_id="test123abc"
            )

            # Verify unquarantine was called
            mock_config.unquarantine_container.assert_called_once_with("test_stable_id")

            # Verify restart history was cleared
            mock_config.clear_restart_history.assert_called_once_with("test_stable_id")

            # Verify event was added
            mock_config.add_event.assert_called_once()
            event = mock_config.add_event.call_args[0][0]
            assert event.event_type == "auto_unquarantine"
            assert event.status == "success"
            assert "auto-healed" in event.message

            # Verify notification was sent
            mock_notif.send_event_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_quarantine_check_reuses_evaluate_health(self):
        """Test that quarantine check reuses _evaluate_container_health for health verification"""
        from app.monitor.monitoring_engine import MonitoringEngine
        from app.docker_client.docker_client_wrapper import DockerClientWrapper

        # Create mock docker client
        mock_docker = Mock(spec=DockerClientWrapper)
        engine = MonitoringEngine(mock_docker)

        # Mock container
        mock_container = Mock()
        mock_container.name = "test-container"

        # Container info - running container
        container_info = {
            "full_id": "test123abc",
            "id": "test123abc",
            "name": "test-container",
            "state": {"Status": "running"},
            "health": {"status": "healthy"},
            "labels": {}
        }

        # Create a side_effect that returns container_info when get_container_info is called
        async def mock_to_thread(func, *args):
            if func == mock_docker.get_container_info:
                return container_info
            return func(*args)

        # Mock methods on engine BEFORE entering the with block
        engine.get_stable_identifier = Mock(return_value="test_stable_id")
        engine.should_monitor_container = Mock(return_value=True)
        engine._evaluate_container_health = AsyncMock(return_value=(False, ""))

        with patch('app.monitor.monitoring_engine.config_manager') as mock_config, \
             patch('app.monitor.monitoring_engine.notification_manager') as mock_notif, \
             patch('app.monitor.monitoring_engine.asyncio.to_thread', side_effect=mock_to_thread):

            # Setup: container is quarantined by stable_id
            mock_config.is_maintenance_mode.return_value = False
            mock_config.is_quarantined.side_effect = lambda x: x == "test_stable_id"
            mock_config.get_config.return_value = Mock(
                restart=Mock(mode="health", backoff=Mock(initial_seconds=10))
            )
            mock_config.get_custom_health_check.return_value = None
            mock_config.unquarantine_container = Mock()
            mock_config.clear_restart_history = Mock()
            mock_config.add_event = Mock()
            mock_notif.send_event_notification = AsyncMock()

            # Call check single container
            await engine._check_single_container(mock_container)

            # Verify _evaluate_container_health was called (reused existing method)
            engine._evaluate_container_health.assert_called_once()

            # Verify unquarantine was called (container was healthy)
            mock_config.unquarantine_container.assert_called_once_with("test_stable_id")

    @pytest.mark.asyncio
    async def test_quarantine_check_stays_quarantined_if_unhealthy(self):
        """Test that container stays quarantined if still unhealthy"""
        from app.monitor.monitoring_engine import MonitoringEngine
        from app.docker_client.docker_client_wrapper import DockerClientWrapper

        # Create mock docker client
        mock_docker = Mock(spec=DockerClientWrapper)
        engine = MonitoringEngine(mock_docker)

        # Mock container
        mock_container = Mock()
        mock_container.name = "test-container"

        # Container info - running but will be unhealthy
        container_info = {
            "full_id": "test123abc",
            "id": "test123abc",
            "name": "test-container",
            "state": {"Status": "running"},
            "health": {"status": "unhealthy"},
            "labels": {}
        }

        # Create a side_effect that returns container_info when get_container_info is called
        async def mock_to_thread(func, *args):
            if func == mock_docker.get_container_info:
                return container_info
            return func(*args)

        # Mock methods on engine BEFORE entering the with block
        engine.get_stable_identifier = Mock(return_value="test_stable_id")
        engine.should_monitor_container = Mock(return_value=True)
        engine._evaluate_container_health = AsyncMock(return_value=(True, "Docker health check reports unhealthy"))

        with patch('app.monitor.monitoring_engine.config_manager') as mock_config, \
             patch('app.monitor.monitoring_engine.notification_manager') as mock_notif, \
             patch('app.monitor.monitoring_engine.asyncio.to_thread', side_effect=mock_to_thread):

            # Setup: container is quarantined
            mock_config.is_maintenance_mode.return_value = False
            mock_config.is_quarantined.side_effect = lambda x: x == "test_stable_id"
            mock_config.get_config.return_value = Mock()
            mock_config.unquarantine_container = Mock()
            mock_notif.send_event_notification = AsyncMock()


            # Call check single container
            await engine._check_single_container(mock_container)

            # Verify _evaluate_container_health was called
            engine._evaluate_container_health.assert_called_once()

            # Verify unquarantine was NOT called (container is still unhealthy)
            mock_config.unquarantine_container.assert_not_called()


def run_tests():
    """Run all tests in this module"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()

