"""
Uptime-Kuma API client for fetching monitor statuses
Uses the /metrics endpoint with Basic Authentication
"""
import aiohttp
import logging
import re
from typing import List, Dict, Optional
from aiohttp import BasicAuth

logger = logging.getLogger(__name__)


class UptimeKumaClient:
    """Client for interacting with Uptime-Kuma API using /metrics endpoint"""

    def __init__(self, server_url: str, password: str, username: str = ""):
        self.server_url = server_url.rstrip('/')
        self.password = password
        self.username = username
        # Use Basic Auth with username (empty for API key) and password/API key
        # For API key: username="", password=api_key
        # For user auth: username=username, password=password
        self.auth = BasicAuth(username if username else '', password)
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """Test connection to Uptime-Kuma server"""
        try:
            logger.debug(f"Attempting to connect to {self.server_url}/metrics")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/metrics",
                    auth=self.auth,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.debug(f"Response status: {response.status}")
                    if response.status == 200:
                        text = await response.text()
                        # Check if we got valid metrics data
                        has_metrics = 'monitor_status' in text or 'app_version' in text
                        logger.debug(f"Has metrics data: {has_metrics}")
                        return has_metrics
                    logger.warning(f"Unexpected response status: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Failed to connect to Uptime-Kuma: {e}")
            return False

    async def get_all_monitors(self) -> List[Dict]:
        """Fetch all monitors from /metrics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/metrics",
                    auth=self.auth,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch metrics: HTTP {response.status}")
                        return []

                    text = await response.text()
                    monitors = self._parse_monitors_from_metrics(text)
                    logger.debug(f"Parsed {len(monitors)} monitors from metrics")
                    return monitors
        except Exception as e:
            logger.error(f"Failed to fetch monitors: {e}")
            return []

    def _parse_monitors_from_metrics(self, metrics_text: str) -> List[Dict]:
        """Parse monitor data from Prometheus metrics format"""
        monitors = {}

        # Parse monitor_status lines
        # Format: monitor_status{monitor_name="My Monitor",monitor_url="https://example.com",monitor_hostname="",monitor_port=""} 1
        status_pattern = r'monitor_status\{monitor_name="([^"]+)"[^}]*\}\s+(\d+)'

        for match in re.finditer(status_pattern, metrics_text):
            monitor_name = match.group(1)
            status = int(match.group(2))

            # Generate a simple ID based on the name (since metrics don't provide IDs)
            monitor_id = abs(hash(monitor_name)) % (10 ** 8)

            monitors[monitor_name] = {
                'id': monitor_id,
                'friendly_name': monitor_name,
                'status': status  # 0=down, 1=up, 2=pending, 3=maintenance
            }

        return list(monitors.values())

    async def get_monitor_status(self, monitor_id: int) -> Optional[int]:
        """Get status of a specific monitor by ID"""
        # Since we use hashed IDs, we need to fetch all monitors and find the matching one
        monitors = await self.get_all_monitors()
        for monitor in monitors:
            if monitor['id'] == monitor_id:
                return monitor['status']
        return None

    async def get_monitor_status_by_name(self, monitor_name: str) -> Optional[int]:
        """Get status of a specific monitor by friendly name"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/metrics",
                    auth=self.auth,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None

                    text = await response.text()
                    # Look for this specific monitor's status
                    pattern = rf'monitor_status\{{monitor_name="{re.escape(monitor_name)}"[^}}]*\}}\s+(\d+)'
                    match = re.search(pattern, text)

                    if match:
                        return int(match.group(1))
                    return None
        except Exception as e:
            logger.error(f"Failed to get monitor status for '{monitor_name}': {e}")
            return None

