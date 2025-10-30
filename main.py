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

from config import config_manager
from docker_client import DockerClientWrapper
from monitor import MonitoringEngine
from api import app, init_api

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

            # Initialize API
            init_api(self.docker_client, self.monitoring_engine)

            # Start Prometheus metrics server if enabled
            if config.observability.prometheus_enabled:
                logger.info(f"Starting Prometheus metrics server on port {config.observability.metrics_port}")
                start_http_server(config.observability.metrics_port)

            # Start monitoring engine
            logger.info("Starting monitoring engine...")
            await self.monitoring_engine.start()

            self.running = True
            logger.info("Docker Auto-Heal Service started successfully")
            logger.info(f"Web UI available at http://{config.ui.listen_address}:{config.ui.listen_port}")
            logger.info(f"API documentation available at http://{config.ui.listen_address}:{config.ui.listen_port}/docs")

        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the auto-heal service"""
        logger.info("Stopping Docker Auto-Heal Service...")

        self.running = False

        if self.monitoring_engine:
            await self.monitoring_engine.stop()

        if self.docker_client:
            self.docker_client.close()

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
            run_api_server()
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
    finally:
        if service and service.running:
            await service.stop()


if __name__ == "__main__":
    # Run the service
    asyncio.run(main())

