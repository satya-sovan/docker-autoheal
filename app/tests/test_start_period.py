"""
Tests for the start-period grace window feature.

Containers that have recently started (within ``start_period_seconds``) should
not be restarted even when they report as unhealthy, because they may simply be
slow to initialise.  This mirrors Docker's native ``--health-start-period``
behaviour.

The effective start period is resolved in this priority order:
1. Per-container label ``autoheal.start-period``
2. Global ``restart.start_period_seconds`` configuration value
3. 0 (disabled)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def _make_engine():
    """Return a MonitoringEngine with a mocked Docker client."""
    from app.monitor.monitoring_engine import MonitoringEngine
    from app.docker_client.docker_client_wrapper import DockerClientWrapper

    mock_docker = Mock(spec=DockerClientWrapper)
    return MonitoringEngine(mock_docker)


def _make_info(started_seconds_ago: float, labels: dict = None,
               health_status: str = "unhealthy",
               state_status: str = "running") -> dict:
    """Build a minimal container-info dict."""
    started_at = datetime.now(timezone.utc) - timedelta(seconds=started_seconds_ago)
    info = {
        "name": "test-container",
        "full_id": "abc123",
        "started_at": started_at.isoformat(),
        "state": {"Status": state_status, "ExitCode": 0},
        "labels": labels or {},
        "health": {"status": health_status} if health_status else None,
    }
    return info


class TestStartPeriodConfig:
    """Tests for start_period_seconds config field."""

    def test_default_start_period_is_zero(self):
        from app.config.config_manager import RestartConfig

        cfg = RestartConfig()
        assert cfg.start_period_seconds == 0

    def test_start_period_can_be_set(self):
        from app.config.config_manager import RestartConfig

        cfg = RestartConfig(start_period_seconds=120)
        assert cfg.start_period_seconds == 120

    def test_start_period_cannot_be_negative(self):
        from app.config.config_manager import RestartConfig
        import pydantic

        with pytest.raises((ValueError, pydantic.ValidationError)):
            RestartConfig(start_period_seconds=-1)


class TestGetStartPeriodSeconds:
    """Tests for MonitoringEngine._get_start_period_seconds."""

    def test_returns_zero_when_disabled(self):
        engine = _make_engine()
        info = _make_info(5)

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=0))
            assert engine._get_start_period_seconds(info) == 0

    def test_returns_global_setting(self):
        engine = _make_engine()
        info = _make_info(5)

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            assert engine._get_start_period_seconds(info) == 60

    def test_per_container_label_overrides_global(self):
        engine = _make_engine()
        info = _make_info(5, labels={"autoheal.start-period": "90"})

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            assert engine._get_start_period_seconds(info) == 90

    def test_invalid_label_falls_back_to_global(self):
        engine = _make_engine()
        info = _make_info(5, labels={"autoheal.start-period": "not-a-number"})

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=45))
            assert engine._get_start_period_seconds(info) == 45

    def test_label_zero_disables_start_period(self):
        engine = _make_engine()
        info = _make_info(5, labels={"autoheal.start-period": "0"})

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            assert engine._get_start_period_seconds(info) == 0


class TestIsContainerInStartPeriod:
    """Tests for MonitoringEngine._is_container_in_start_period."""

    def test_disabled_when_start_period_zero(self):
        engine = _make_engine()
        info = _make_info(5)  # started 5 seconds ago

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=0))
            in_period, elapsed, period = engine._is_container_in_start_period(info)

        assert not in_period

    def test_in_start_period_when_recently_started(self):
        engine = _make_engine()
        info = _make_info(10)  # started 10 seconds ago

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            in_period, elapsed, period = engine._is_container_in_start_period(info)

        assert in_period
        assert elapsed < 60
        assert period == 60

    def test_not_in_start_period_after_grace_window(self):
        engine = _make_engine()
        info = _make_info(120)  # started 120 seconds ago

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            in_period, elapsed, period = engine._is_container_in_start_period(info)

        assert not in_period
        assert elapsed >= 60
        assert period == 60

    def test_missing_started_at_returns_false(self):
        engine = _make_engine()
        info = _make_info(10)
        info["started_at"] = None

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=60))
            in_period, elapsed, period = engine._is_container_in_start_period(info)

        assert not in_period

    def test_per_container_label_respected(self):
        engine = _make_engine()
        info = _make_info(10, labels={"autoheal.start-period": "30"})

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(restart=Mock(start_period_seconds=0))
            in_period, elapsed, period = engine._is_container_in_start_period(info)

        assert in_period
        assert period == 30


class TestEvaluateContainerHealthStartPeriod:
    """Integration tests for start-period behaviour inside _evaluate_container_health."""

    @pytest.mark.asyncio
    async def test_unhealthy_container_skipped_during_start_period(self):
        """A container that is unhealthy but within its start period must NOT trigger a restart."""
        engine = _make_engine()
        container = Mock()
        info = _make_info(10, health_status="unhealthy")  # 10 s old, unhealthy

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(
                restart=Mock(mode="health", start_period_seconds=60, respect_manual_stop=True),
            )
            mock_cfg.get_custom_health_check.return_value = None

            needs_restart, reason = await engine._evaluate_container_health(container, info)

        assert not needs_restart
        assert "start period" in reason.lower()

    @pytest.mark.asyncio
    async def test_unhealthy_container_restarted_after_start_period(self):
        """A container that is unhealthy and past its start period MUST trigger a restart."""
        engine = _make_engine()
        container = Mock()
        info = _make_info(120, health_status="unhealthy")  # 120 s old, unhealthy

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(
                restart=Mock(mode="health", start_period_seconds=60, respect_manual_stop=True),
            )
            mock_cfg.get_custom_health_check.return_value = None

            needs_restart, reason = await engine._evaluate_container_health(container, info)

        assert needs_restart
        assert "unhealthy" in reason.lower()

    @pytest.mark.asyncio
    async def test_docker_health_starting_not_restarted(self):
        """Docker health status 'starting' (native grace period) must not trigger a restart."""
        engine = _make_engine()
        container = Mock()
        info = _make_info(10, health_status="starting")

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(
                restart=Mock(mode="health", start_period_seconds=0, respect_manual_stop=True),
            )
            mock_cfg.get_custom_health_check.return_value = None

            needs_restart, reason = await engine._evaluate_container_health(container, info)

        assert not needs_restart
        assert "starting" in reason.lower()

    @pytest.mark.asyncio
    async def test_start_period_disabled_unhealthy_triggers_restart(self):
        """When start period is 0 (disabled) an unhealthy container must still be restarted."""
        engine = _make_engine()
        container = Mock()
        info = _make_info(5, health_status="unhealthy")  # 5 s old, unhealthy

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(
                restart=Mock(mode="health", start_period_seconds=0, respect_manual_stop=True),
            )
            mock_cfg.get_custom_health_check.return_value = None

            needs_restart, reason = await engine._evaluate_container_health(container, info)

        assert needs_restart
        assert "unhealthy" in reason.lower()

    @pytest.mark.asyncio
    async def test_per_container_label_overrides_global_in_health_eval(self):
        """Per-container 'autoheal.start-period' label takes precedence over global config."""
        engine = _make_engine()
        container = Mock()
        # Started 10 s ago; label says 120 s start period; global says 0
        info = _make_info(10, labels={"autoheal.start-period": "120"}, health_status="unhealthy")

        with patch('app.monitor.monitoring_engine.config_manager') as mock_cfg:
            mock_cfg.get_config.return_value = Mock(
                restart=Mock(mode="health", start_period_seconds=0, respect_manual_stop=True),
            )
            mock_cfg.get_custom_health_check.return_value = None

            needs_restart, reason = await engine._evaluate_container_health(container, info)

        assert not needs_restart
        assert "start period" in reason.lower()
