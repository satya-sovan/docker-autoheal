"""
Unit tests for Prometheus metrics server startup logic.
Verifies that start_http_server is called when prometheus_enabled is True,
regardless of notification settings.
"""

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from app.main import AutoHealService


class TestPrometheusStart:
    """Test Prometheus metrics server startup"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up common mocks for all tests"""
        # Mock DockerClientWrapper
        self.docker_patcher = patch('app.main.DockerClientWrapper')
        self.mock_docker = self.docker_patcher.start()

        # Mock MonitoringEngine
        self.engine_patcher = patch('app.main.MonitoringEngine')
        self.mock_engine = self.engine_patcher.start()
        self.mock_engine.return_value.start = AsyncMock()

        # Mock UptimeKumaMonitor
        self.kuma_patcher = patch('app.main.UptimeKumaMonitor')
        self.mock_kuma = self.kuma_patcher.start()
        self.mock_kuma.return_value.start = AsyncMock()

        # Mock init_api
        self.api_patcher = patch('app.main.init_api')
        self.mock_api = self.api_patcher.start()

        # Mock notification_manager
        self.notif_patcher = patch('app.main.notification_manager')
        self.mock_notif = self.notif_patcher.start()
        self.mock_notif.start = AsyncMock()

        # Mock start_http_server
        self.http_patcher = patch('app.main.start_http_server')
        self.mock_http_server = self.http_patcher.start()

        yield

        self.docker_patcher.stop()
        self.engine_patcher.stop()
        self.kuma_patcher.stop()
        self.api_patcher.stop()
        self.notif_patcher.stop()
        self.http_patcher.stop()

    def _make_config(self, prometheus_enabled=True, notifications_enabled=False, metrics_port=9090):
        """Create a mock config object"""
        config = MagicMock()
        config.observability.prometheus_enabled = prometheus_enabled
        config.observability.metrics_port = metrics_port
        config.observability.log_level = "INFO"
        config.monitor.interval_seconds = 30
        config.notifications.enabled = notifications_enabled
        config.notifications.services = []
        config.uptime_kuma.enabled = False
        config.ui.listen_address = "0.0.0.0"
        config.ui.listen_port = 3131
        return config

    @pytest.mark.asyncio
    async def test_prometheus_starts_when_enabled_notifications_disabled(self):
        """Prometheus server should start when prometheus_enabled=True even if notifications are disabled"""
        config = self._make_config(prometheus_enabled=True, notifications_enabled=False)
        with patch('app.main.config_manager') as mock_cm:
            mock_cm.get_config.return_value = config

            service = AutoHealService()
            await service.start()

            self.mock_http_server.assert_called_once_with(9090)

    @pytest.mark.asyncio
    async def test_prometheus_starts_when_enabled_notifications_enabled(self):
        """Prometheus server should start when both prometheus and notifications are enabled"""
        config = self._make_config(prometheus_enabled=True, notifications_enabled=True)
        with patch('app.main.config_manager') as mock_cm:
            mock_cm.get_config.return_value = config

            service = AutoHealService()
            await service.start()

            self.mock_http_server.assert_called_once_with(9090)

    @pytest.mark.asyncio
    async def test_prometheus_does_not_start_when_disabled(self):
        """Prometheus server should NOT start when prometheus_enabled=False"""
        config = self._make_config(prometheus_enabled=False, notifications_enabled=True)
        with patch('app.main.config_manager') as mock_cm:
            mock_cm.get_config.return_value = config

            service = AutoHealService()
            await service.start()

            self.mock_http_server.assert_not_called()

    @pytest.mark.asyncio
    async def test_prometheus_uses_configured_port(self):
        """Prometheus server should use the configured metrics_port"""
        config = self._make_config(prometheus_enabled=True, metrics_port=8080)
        with patch('app.main.config_manager') as mock_cm:
            mock_cm.get_config.return_value = config

            service = AutoHealService()
            await service.start()

            self.mock_http_server.assert_called_once_with(8080)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
