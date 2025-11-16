"""
Uptime-Kuma monitoring service that triggers container restarts
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config.config_manager import config_manager, AutoHealEvent
from app.docker_client.docker_client_wrapper import DockerClientWrapper
from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient

logger = logging.getLogger(__name__)


class UptimeKumaMonitor:
    """Monitor Uptime-Kuma statuses and trigger container restarts"""

    def __init__(self, docker_client: DockerClientWrapper):
        self.docker_client = docker_client
        self.client: Optional[UptimeKumaClient] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._monitor_cache = {}  # Cache monitor IDs by friendly name

    async def start(self):
        """Start Uptime-Kuma monitoring"""
        try:
            config = config_manager.get_config()

            if not config.uptime_kuma.enabled:
                logger.info("Uptime-Kuma integration is disabled - configure it via UI to enable")
                return

            if not config.uptime_kuma.server_url or not config.uptime_kuma.api_token:
                logger.info("Uptime-Kuma integration not configured yet - visit http://localhost:3131/config to set up")
                return

            self.client = UptimeKumaClient(
                config.uptime_kuma.server_url,
                config.uptime_kuma.api_token,  # password (API key or user password)
                config.uptime_kuma.username    # username (optional, empty for API key)
            )

            # Test connection
            logger.info(f"Testing connection to Uptime-Kuma at {config.uptime_kuma.server_url}...")
            if not await self.client.connect():
                logger.warning(f"Cannot connect to Uptime-Kuma at {config.uptime_kuma.server_url}")
                logger.info("Uptime-Kuma monitoring will remain disabled until connection is successful")
                return

            logger.info("Uptime-Kuma connection successful")

            # Build monitor cache
            await self._refresh_monitor_cache()

            # Start monitoring loop
            self._running = True
            self._task = asyncio.create_task(self._monitoring_loop())
        except Exception as e:
            logger.warning(f"Failed to start Uptime-Kuma monitor: {e}")
            logger.info("Uptime-Kuma integration is optional - the service will continue without it")

    async def stop(self):
        """Stop Uptime-Kuma monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Uptime-Kuma monitoring stopped")

    async def _refresh_monitor_cache(self):
        """Refresh cache of monitor IDs by friendly name"""
        if not self.client:
            return

        monitors = await self.client.get_all_monitors()
        self._monitor_cache = {m['friendly_name']: m for m in monitors}
        logger.info(f"Cached {len(self._monitor_cache)} Uptime-Kuma monitors")

    async def _monitoring_loop(self):
        """Main monitoring loop - check Uptime-Kuma statuses"""
        config = config_manager.get_config()

        while self._running:
            try:
                await self._check_all_mappings()
                # Use monitor.interval_seconds for consistency with container monitoring
                interval = config.monitor.interval_seconds
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Uptime-Kuma monitoring loop: {e}")
                config = config_manager.get_config()
                interval = config.monitor.interval_seconds
                await asyncio.sleep(interval)

    async def _check_all_mappings(self):
        """Check all configured mappings and restart containers if needed"""
        config = config_manager.get_config()

        if not config.uptime_kuma_mappings:
            return

        for mapping in config.uptime_kuma_mappings:
            try:
                # Use get_monitor_status_by_name directly since metrics endpoint doesn't provide stable IDs
                status = await self.client.get_monitor_status_by_name(mapping.monitor_friendly_name)

                if status is None:
                    logger.warning(f"Monitor '{mapping.monitor_friendly_name}' not found or could not fetch status")
                    continue

                # Status: 0=down, 1=up, 2=pending, 3=maintenance
                if status == 0 and config.uptime_kuma.auto_restart_on_down:
                    # mapping.container_id now stores stable_id
                    await self._handle_monitor_down(mapping.container_id, mapping.monitor_friendly_name)

            except Exception as e:
                logger.error(f"Error checking mapping {mapping.container_id}: {e}")

    async def _handle_monitor_down(self, stable_id: str, monitor_name: str):
        """Handle a DOWN status from Uptime-Kuma by restarting the container"""
        try:
            # Check if container is quarantined
            if config_manager.is_quarantined(stable_id):
                logger.info(f"Container {stable_id} is quarantined, skipping restart")
                return
            
            # Check maintenance mode
            if config_manager.is_maintenance_mode():
                logger.info("Maintenance mode active, skipping restart")
                return
            
            # Find container by stable_id
            containers = self.docker_client.list_containers(all_containers=False)
            container = None
            
            for c in containers:
                info = self.docker_client.get_container_info(c)
                if info and info.get("stable_id") == stable_id:
                    container = c
                    break
            
            if not container:
                logger.warning(f"Container with stable_id {stable_id} not found")
                return

            # Get container info to check if it should be monitored
            info = self.docker_client.get_container_info(container)
            if not info:
                logger.warning(f"Could not get info for container {stable_id}")
                return

            # Check if container is selected for monitoring
            config = config_manager.get_config()
            container_name = info.get("name")
            container_id = info.get("full_id")
            short_id = info.get("id")
            labels = info.get("labels", {})
            compose_service = labels.get("com.docker.compose.service")

            # Check if container should be monitored (same logic as monitoring_engine)
            is_selected = (
                stable_id in config.containers.selected or
                container_id in config.containers.selected or
                short_id in config.containers.selected or
                container_name in config.containers.selected or
                (compose_service and compose_service in config.containers.selected)
            )

            # If not explicitly selected, check if it would be monitored by label
            if not is_selected:
                if config.monitor.include_all:
                    is_selected = True
                else:
                    label_key = config.monitor.label_key
                    label_value = config.monitor.label_value
                    is_selected = (label_key in labels and labels[label_key] == label_value)

            if not is_selected:
                logger.info(f"Container {container_name} (stable_id: {stable_id}) is not selected for monitoring, skipping Uptime-Kuma restart")
                return

            logger.warning(f"Uptime-Kuma monitor '{monitor_name}' is DOWN - restarting container {container.name}")

            # Restart the container
            container.restart(timeout=10)

            # Record the restart using stable_id
            config_manager.record_restart(stable_id)

            # Log event
            event = AutoHealEvent(
                timestamp=datetime.now(timezone.utc),
                container_id=container.id[:12],
                container_name=container.name,
                event_type="uptime_kuma_restart",
                restart_count=config_manager.get_total_restart_count(stable_id),
                status="success",
                message=f"Restarted due to Uptime-Kuma monitor '{monitor_name}' DOWN status"
            )
            config_manager.add_event(event)

            logger.info(f"Successfully restarted {container.name} via Uptime-Kuma trigger")

        except Exception as e:
            logger.error(f"Failed to restart container {stable_id}: {e}")

            # Log failure event
            event = AutoHealEvent(
                timestamp=datetime.now(timezone.utc),
                container_id=stable_id,
                container_name=stable_id,
                event_type="uptime_kuma_restart",
                restart_count=config_manager.get_total_restart_count(stable_id),
                status="failure",
                message=f"Failed to restart: {str(e)}"
            )
            config_manager.add_event(event)

