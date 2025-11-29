"""
Main entry point for Docker Auto-Heal Service
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from pathlib import Path

import uvicorn
from prometheus_client import start_http_server, Counter, Gauge

from app.config.config_manager import config_manager
from app.docker_client.docker_client_wrapper import DockerClientWrapper
from app.monitor.monitoring_engine import MonitoringEngine
from app.monitor.uptime_kuma_monitor import UptimeKumaMonitor
from app.notifications.notification_manager import notification_manager
from app.api.api import app, init_api

# Ensure /data/logs directory exists
LOG_DIR = Path("/data/logs")
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # Fallback to ./data/logs if /data is not writable
    LOG_DIR = Path("./data/logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "autoheal.log"

# Configure logging (will be updated with config)
logging.basicConfig(
    level=logging.INFO,  # Default, will be updated
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE))
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging to: {LOG_FILE}")


class CancelledErrorFilter(logging.Filter):
    """Filter to suppress CancelledError from uvicorn.error logs during shutdown"""
    def filter(self, record):
        # Suppress CancelledError tracebacks from uvicorn (these are expected during shutdown)
        if record.name == "uvicorn.error" and "CancelledError" in record.getMessage():
            return False
        return True


def update_log_level(level_name: str):
    """Update logging level for all loggers"""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(level_name.upper(), logging.INFO)

    # Set root logger level
    logging.getLogger().setLevel(level)

    # Disable uvicorn access logs completely (set to WARNING to suppress INFO logs)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)

    # Add filter to suppress CancelledError tracebacks
    logging.getLogger("uvicorn.error").addFilter(CancelledErrorFilter())

    logger.info(f"Log level set to: {level_name}")

# Prometheus metrics
container_restarts = Counter('autoheal_container_restarts_total', 'Total container restarts', ['container_name'])
containers_monitored = Gauge('autoheal_containers_monitored', 'Number of containers being monitored')
containers_quarantined = Gauge('autoheal_containers_quarantined', 'Number of quarantined containers')
health_checks_total = Counter('autoheal_health_checks_total', 'Total health checks performed')
health_checks_failed = Counter('autoheal_health_checks_failed', 'Failed health checks', ['container_name'])


class AutoHealService:
    """Main service orchestrator"""

    def __init__(self):
        self.docker_client: Optional[DockerClientWrapper] = None
        self.monitoring_engine: Optional[MonitoringEngine] = None
        self.notification_manager = notification_manager
        self.uptime_kuma_monitor: Optional[UptimeKumaMonitor] = None
        self.running = False

    async def start(self):
        """Start the auto-heal service"""
        try:
            logger.info("Starting Docker Auto-Heal Service v1.1")

            # Load configuration
            config = config_manager.get_config()

            # Set log level from config
            update_log_level(config.observability.log_level)

            logger.info(f"Configuration loaded: monitoring interval={config.monitor.interval_seconds}s")

            # Initialize Docker client
            logger.info("Connecting to Docker daemon...")
            self.docker_client = DockerClientWrapper()
            logger.info("Docker client connected successfully")

            # Initialize monitoring engine
            logger.info("Initializing monitoring engine...")
            self.monitoring_engine = MonitoringEngine(self.docker_client)

            # Initialize Uptime-Kuma monitor (independent service that provides status)
            logger.info("Initializing Uptime-Kuma monitor...")
            self.uptime_kuma_monitor = UptimeKumaMonitor()

            # Attach to monitoring engine for API access
            self.monitoring_engine.uptime_kuma_monitor = self.uptime_kuma_monitor

            # Initialize API
            init_api(self.docker_client, self.monitoring_engine)

            # Start Prometheus metrics server if enabled
            if config.observability.prometheus_enabled:
                logger.info(f"Starting Prometheus metrics server on port {config.observability.metrics_port}")
            # Start notification manager
            logger.info("Starting notification manager...")
            await self.notification_manager.start()
            if config.notifications.enabled:
                logger.info(f"Notifications enabled with {len(config.notifications.services)} service(s)")

                start_http_server(config.observability.metrics_port)

            # Start monitoring engine
            logger.info("Starting monitoring engine...")
            await self.monitoring_engine.start()

            # Start Uptime-Kuma monitor
            logger.info(f"Uptime-Kuma enabled status: {config.uptime_kuma.enabled}")
            if config.uptime_kuma.enabled:
                logger.info("Starting Uptime-Kuma monitor...")
                try:
                    await self.uptime_kuma_monitor.start()
                except Exception as e:
                    logger.warning(f"Uptime-Kuma failed to start: {e}")

            self.running = True
            logger.info("Docker Auto-Heal Service started successfully")
            logger.info(f"Web UI available at http://{config.ui.listen_address}:{config.ui.listen_port}")
            logger.info(f"API documentation available at http://{config.ui.listen_address}:{config.ui.listen_port}/docs")

        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            if self.notification_manager:
                await self.notification_manager.stop()
            raise

    async def stop(self):
        """Stop the auto-heal service"""
        logger.info("Stopping Docker Auto-Heal Service...")

        self.running = False

        # Stop components gracefully with error handling
        if self.uptime_kuma_monitor:
            try:
                await self.uptime_kuma_monitor.stop()
            except Exception as e:
                logger.warning(f"Error stopping Uptime-Kuma monitor: {e}")

        if self.monitoring_engine:
            try:
                await self.monitoring_engine.stop()
            except Exception as e:
                logger.warning(f"Error stopping monitoring engine: {e}")

        if self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                logger.warning(f"Error closing Docker client: {e}")

        logger.info("Docker Auto-Heal Service stopped")

    async def run(self):
        """Run the service (blocking)"""
        await self.start()

        # Keep running until stopped
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()


# Global service instance
service: Optional[AutoHealService] = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    if service:
        asyncio.create_task(service.stop())


async def run_api_server():
    """Run FastAPI server"""
    config = config_manager.get_config()

    # Map our log level to uvicorn format (lowercase)
    uvicorn_log_level = config.observability.log_level.lower()

    # Disable all uvicorn access logs completely
    uvicorn_config = uvicorn.Config(
        app,
        host=config.ui.listen_address,
        port=config.ui.listen_port,
        log_level="warning",  # Set to warning to suppress info logs
        access_log=False,  # Completely disable access logs
        log_config=None  # Use default logging config
    )

    server = uvicorn.Server(uvicorn_config)
    await server.serve()


async def main():
    """Main entry point"""
    global service

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create service instance
    service = AutoHealService()

    # Start service and API server concurrently
    try:
        await asyncio.gather(
            service.run(),
            run_api_server(),
            return_exceptions=True  # Don't propagate CancelledError
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except asyncio.CancelledError:
        logger.info("Application cancelled, shutting down gracefully")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
    finally:
        if service and service.running:
            await service.stop()


if __name__ == "__main__":
    # Run the service
    asyncio.run(main())
