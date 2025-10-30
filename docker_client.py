"""
Docker client wrapper for container operations
Provides interface to Docker API for monitoring and management
"""

import docker
from docker.models.containers import Container
from typing import List, Dict, Optional, Any
import logging
import requests
import socket

logger = logging.getLogger(__name__)


class DockerClientWrapper:
    """Wrapper around Docker SDK client with retry logic"""

    def __init__(self, base_url: str = "unix://var/run/docker.sock"):
        """
        Initialize Docker client
        Args:
            base_url: Docker daemon socket URL
        """
        self.base_url = base_url
        self._client: Optional[docker.DockerClient] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Docker daemon with retry logic"""
        try:
            self._client = docker.DockerClient(base_url=self.base_url)
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Docker daemon at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise

    def reconnect(self) -> bool:
        """Reconnect to Docker daemon"""
        try:
            self._connect()
            return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to Docker daemon"""
        try:
            if self._client:
                self._client.ping()
                return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
        return False

    def list_containers(self, all_containers: bool = False) -> List[Container]:
        """
        List containers
        Args:
            all_containers: If True, list all containers including stopped ones
        Returns:
            List of Container objects
        """
        try:
            return self._client.containers.list(all=all_containers)
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            if not self.is_connected():
                self.reconnect()
            return []

    def get_container(self, container_id: str) -> Optional[Container]:
        """
        Get container by ID or name
        Args:
            container_id: Container ID or name
        Returns:
            Container object or None if not found
        """
        try:
            return self._client.containers.get(container_id)
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get container {container_id}: {e}")
            return None

    def get_container_info(self, container: Container) -> Dict[str, Any]:
        """
        Get detailed container information
        Args:
            container: Container object
        Returns:
            Dictionary with container details
        """
        try:
            container.reload()  # Refresh container state
            attrs = container.attrs

            # Extract relevant information
            info = {
                "id": container.id[:12],  # Short ID
                "full_id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "state": attrs.get("State", {}),
                "labels": attrs.get("Config", {}).get("Labels", {}),
                "created": attrs.get("Created"),
                "started_at": attrs.get("State", {}).get("StartedAt"),
                "finished_at": attrs.get("State", {}).get("FinishedAt"),
                "exit_code": attrs.get("State", {}).get("ExitCode"),
                "restart_count": attrs.get("RestartCount", 0),
                "health": self._get_health_status(attrs),
                "restart_policy": attrs.get("HostConfig", {}).get("RestartPolicy", {}),
            }

            return info
        except Exception as e:
            logger.error(f"Failed to get container info for {container.name}: {e}")
            return {}

    def _get_health_status(self, attrs: Dict) -> Optional[Dict[str, Any]]:
        """Extract health status from container attributes"""
        state = attrs.get("State", {})
        health = state.get("Health")

        if health:
            return {
                "status": health.get("Status"),  # healthy, unhealthy, starting
                "failing_streak": health.get("FailingStreak", 0),
                "log": health.get("Log", [])[-1] if health.get("Log") else None
            }
        return None

    def restart_container(self, container: Container, timeout: int = 10) -> bool:
        """
        Restart a container
        Args:
            container: Container object
            timeout: Timeout in seconds
        Returns:
            True if restart successful, False otherwise
        """
        try:
            logger.info(f"Restarting container {container.name} ({container.id[:12]})")
            container.restart(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Failed to restart container {container.name}: {e}")
            return False

    def stop_container(self, container: Container, timeout: int = 10) -> bool:
        """
        Stop a container
        Args:
            container: Container object
            timeout: Timeout in seconds
        Returns:
            True if stop successful, False otherwise
        """
        try:
            logger.info(f"Stopping container {container.name} ({container.id[:12]})")
            container.stop(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Failed to stop container {container.name}: {e}")
            return False

    def execute_command(self, container: Container, command: List[str]) -> tuple[int, str]:
        """
        Execute command in container
        Args:
            container: Container object
            command: Command to execute as list
        Returns:
            Tuple of (exit_code, output)
        """
        try:
            exec_result = container.exec_run(command)
            return exec_result.exit_code, exec_result.output.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to execute command in container {container.name}: {e}")
            return -1, str(e)

    def check_http_health(self, container: Container, endpoint: str,
                         expected_status: int = 200, timeout: int = 5) -> bool:
        """
        Perform HTTP health check on container
        Args:
            container: Container object
            endpoint: HTTP endpoint to check (e.g., "http://localhost:3131/health")
            expected_status: Expected HTTP status code
            timeout: Request timeout
        Returns:
            True if health check passes, False otherwise
        """
        try:
            # Get container's network settings
            container.reload()
            networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})

            # Try to get IP address from any network
            ip_address = None
            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    break

            if not ip_address:
                logger.warning(f"Cannot get IP address for container {container.name}")
                return False

            # Replace localhost/127.0.0.1 with container IP
            endpoint = endpoint.replace("localhost", ip_address).replace("127.0.0.1", ip_address)

            response = requests.get(endpoint, timeout=timeout)
            return response.status_code == expected_status
        except Exception as e:
            logger.warning(f"HTTP health check failed for {container.name}: {e}")
            return False

    def get_events(self, decode=True, filters=None):
        """
        Get Docker events stream
        Args:
            decode: Whether to decode JSON events
            filters: Event filters (dict)
        Returns:
            Generator of events
        """
        try:
            return self._client.events(decode=decode, filters=filters)
        except Exception as e:
            logger.error(f"Failed to get events stream: {e}")
            return None

    def check_tcp_health(self, container: Container, port: int, timeout: int = 5) -> bool:
        """
        Perform TCP health check on container
        Args:
            container: Container object
            port: TCP port to check
            timeout: Connection timeout
        Returns:
            True if TCP connection successful, False otherwise
        """
        try:
            container.reload()
            networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})

            ip_address = None
            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    break

            if not ip_address:
                logger.warning(f"Cannot get IP address for container {container.name}")
                return False

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            sock.close()

            return result == 0
        except Exception as e:
            logger.warning(f"TCP health check failed for {container.name}: {e}")
            return False

    def check_exec_health(self, container: Container, command: List[str]) -> bool:
        """
        Perform exec-based health check on container
        Args:
            container: Container object
            command: Command to execute
        Returns:
            True if command exits with 0, False otherwise
        """
        exit_code, _ = self.execute_command(container, command)
        return exit_code == 0

    def get_docker_native_health(self, container: Container) -> Optional[str]:
        """
        Get Docker's native health check status
        Args:
            container: Container object
        Returns:
            Health status string or None if no health check defined
        """
        try:
            container.reload()
            info = self.get_container_info(container)
            health = info.get("health")
            if health:
                return health.get("status")
            return None
        except Exception as e:
            logger.error(f"Failed to get native health for {container.name}: {e}")
            return None

    def close(self) -> None:
        """Close Docker client connection"""
        if self._client:
            self._client.close()
            logger.info("Docker client connection closed")

