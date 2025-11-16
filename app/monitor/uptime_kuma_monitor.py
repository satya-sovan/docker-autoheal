"""
Uptime-Kuma monitoring service that provides container health status from Uptime Kuma
This module only handles Uptime Kuma-specific operations (SOLID principles):
- Uptime Kuma API communication
- Monitor status retrieval
- Mapping configuration
- Providing health status to monitoring engine

Core functionality (restarts, quarantine, events, etc.) is delegated to MonitoringEngine
"""
import asyncio
import logging
from typing import Optional, Dict

from app.config.config_manager import config_manager
from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient

logger = logging.getLogger(__name__)


class UptimeKumaMonitor:
    """
    Uptime-Kuma integration service
    Provides container health status from Uptime Kuma monitors
    Does NOT perform core actions - only reports status to MonitoringEngine
    """

    def __init__(self):
        """Initialize Uptime-Kuma monitor"""
        self.client: Optional[UptimeKumaClient] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._monitor_cache: Dict[str, dict] = {}  # Cache monitor IDs by friendly name
        self._container_status_cache: Dict[str, int] = {}  # Cache of stable_id -> status

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
        """Main monitoring loop - check Uptime-Kuma statuses and cache them"""
        config = config_manager.get_config()

        while self._running:
            try:
                await self._update_status_cache()
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

    async def _update_status_cache(self):
        """Update cache of container health statuses from Uptime-Kuma monitors"""
        config = config_manager.get_config()

        if not config.uptime_kuma_mappings:
            return

        for mapping in config.uptime_kuma_mappings:
            try:
                # Use get_monitor_status_by_name directly since metrics endpoint doesn't provide stable IDs
                status = await self.client.get_monitor_status_by_name(mapping.monitor_friendly_name)

                if status is None:
                    logger.debug(f"Monitor '{mapping.monitor_friendly_name}' not found or could not fetch status")
                    continue

                # Cache the status (0=down, 1=up, 2=pending, 3=maintenance)
                # mapping.container_id now stores stable_id
                self._container_status_cache[mapping.container_id] = status

                logger.debug(f"Cached status for {mapping.container_id}: {status} (monitor: {mapping.monitor_friendly_name})")

            except Exception as e:
                logger.error(f"Error fetching status for mapping {mapping.container_id}: {e}")

    def get_container_status(self, stable_id: str) -> Optional[int]:
        return self._container_status_cache.get(stable_id)

    def is_container_mapped(self, stable_id: str) -> bool:
        config = config_manager.get_config()
        if not config.uptime_kuma_mappings:
            return False

        return any(mapping.container_id == stable_id for mapping in config.uptime_kuma_mappings)

    def should_restart_from_uptime_kuma(self, stable_id: str) -> bool:
        config = config_manager.get_config()

        # Check if auto-restart on down is enabled
        if not config.uptime_kuma.auto_restart_on_down:
            return False

        # Check if container is mapped
        if not self.is_container_mapped(stable_id):
            return False

        # Check monitor status
        status = self.get_container_status(stable_id)

        # Status 0 = down
        return status == 0

