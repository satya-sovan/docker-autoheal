"""
FastAPI application - REST API endpoints for Docker Auto-Heal Service
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timezone
import json

from app.config.config_manager import (
    config_manager,
    AutoHealConfig,
    HealthCheckConfig,
    MonitorConfig,
    RestartConfig,
    NotificationService,
    NotificationsConfig, AutoHealEvent
)
from app.docker_client.docker_client_wrapper import DockerClientWrapper
from app.monitor.monitoring_engine import MonitoringEngine
from app.notifications.notification_manager import notification_manager

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Docker Auto-Heal Service",
    description="Automated container monitoring and healing service",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (will be initialized in main.py)
docker_client: Optional[DockerClientWrapper] = None
monitoring_engine: Optional[MonitoringEngine] = None


def init_api(docker_client_instance: DockerClientWrapper, monitoring_engine_instance: MonitoringEngine):
    """Initialize API with Docker client and monitoring engine"""
    global docker_client, monitoring_engine
    docker_client = docker_client_instance
    monitoring_engine = monitoring_engine_instance


# ==================== Pydantic Models for API ====================

class ContainerSelectionRequest(BaseModel):
    container_ids: List[str]
    enabled: bool


class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: Dict[str, Any]
    labels: Dict[str, str]
    health: Optional[Dict[str, Any]]
    restart_count: int
    monitored: bool
    quarantined: bool
    uptime_kuma_status: Optional[int] = None  # 0=down, 1=up, 2=pending, 3=maintenance, None=not mapped/disabled
    uptime_kuma_monitor_name: Optional[str] = None


class SystemStatus(BaseModel):
    monitoring_active: bool
    docker_connected: bool
    total_containers: int
    monitored_containers: int
    quarantined_containers: int
    maintenance_mode: bool
    maintenance_start_time: Optional[str]
    config: AutoHealConfig


# ==================== Health & Status Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint for the service itself"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "docker_connected": docker_client.is_connected() if docker_client else False,
        "monitoring_active": monitoring_engine._running if monitoring_engine else False
    }


@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status"""
    try:
        config = config_manager.get_config()
        # Get ALL containers (including stopped) for accurate count
        containers = docker_client.list_containers(all_containers=True) if docker_client else []
        monitored_count = 0

        # Count monitored containers
        for container in containers:
            info = docker_client.get_container_info(container)
            if monitoring_engine and info:
                if monitoring_engine.should_monitor_container(container, info):
                    monitored_count += 1

        maintenance_start = config_manager.get_maintenance_start_time()
        return SystemStatus(
            monitoring_active=monitoring_engine._running if monitoring_engine else False,
            docker_connected=docker_client.is_connected() if docker_client else False,
            total_containers=len(containers),
            monitored_containers=monitored_count,
            quarantined_containers=len(config_manager.get_quarantined_containers()),
            maintenance_mode=config_manager.is_maintenance_mode(),
            maintenance_start_time=maintenance_start.isoformat() if maintenance_start else None,
            config=config
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Container Management Endpoints ====================

@app.get("/api/containers", response_model=List[ContainerInfo])
async def list_containers(include_stopped: bool = False):
    """List all containers with their monitoring status"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        containers = docker_client.list_containers(all_containers=include_stopped)
        result = []
        
        # Get Uptime Kuma configuration
        config = config_manager.get_config()
        uptime_kuma_enabled = config.uptime_kuma.enabled

        # Use the uptime_kuma_monitor from monitoring_engine if available
        uptime_kuma_monitor = None
        if uptime_kuma_enabled and monitoring_engine and hasattr(monitoring_engine, 'uptime_kuma_monitor'):
            uptime_kuma_monitor = monitoring_engine.uptime_kuma_monitor

        for container in containers:
            info = docker_client.get_container_info(container)
            if not info:
                continue

            container_id = info.get("full_id")
            stable_id = info.get("stable_id")  # Get stable identifier

            # Check if monitored
            monitored = False
            if monitoring_engine:
                monitored = monitoring_engine.should_monitor_container(container, info)

            # Check if quarantined (use stable_id, matching how quarantine is stored)
            quarantined = config_manager.is_quarantined(stable_id)

            # Get locally tracked restart count (persists across container recreations)
            locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)
            
            # Check for Uptime Kuma mapping and status using uptime_kuma_monitor
            uptime_kuma_status = None
            uptime_kuma_monitor_name = None
            
            if uptime_kuma_enabled and uptime_kuma_monitor:
                # Check if container is mapped
                if uptime_kuma_monitor.is_container_mapped(stable_id):
                    # Get the monitor name from mappings
                    for mapping in config.uptime_kuma_mappings:
                        if mapping.container_id == stable_id:
                            uptime_kuma_monitor_name = mapping.monitor_friendly_name
                            break

                    # Get cached status from uptime_kuma_monitor
                    uptime_kuma_status = uptime_kuma_monitor.get_container_status(stable_id)
            elif uptime_kuma_enabled and not uptime_kuma_monitor:
                # Uptime-Kuma integration enabled but monitor not initialized
                uptime_kuma_status = 4  # Indicate unknown status
            elif not uptime_kuma_enabled:
                uptime_kuma_status = 5  # Integration disabled


            container_info = ContainerInfo(
                id=info.get("id"),
                name=info.get("name"),
                image=info.get("image"),
                status=info.get("status"),
                state=info.get("state", {}),
                labels=info.get("labels", {}),
                health=info.get("health"),
                restart_count=locally_tracked_restarts,  # Use locally tracked count instead of Docker's
                monitored=monitored,
                quarantined=quarantined,
                uptime_kuma_status=uptime_kuma_status,
                uptime_kuma_monitor_name=uptime_kuma_monitor_name
            )
            result.append(container_info)

        return result
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/containers/{container_id}")
async def get_container_details(container_id: str):
    """Get detailed information about a specific container"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        info = docker_client.get_container_info(container)

        # Use stable_id for tracking (persists across recreations)
        full_container_id = info.get("full_id")
        container_name = info.get("name")
        stable_id = info.get("stable_id")

        # Get locally tracked restart counts (using stable_id)
        recent_restart_count = config_manager.get_restart_count(
            stable_id,
            config_manager.get_config().restart.max_restarts_window_seconds
        )
        total_restart_count = config_manager.get_total_restart_count(stable_id)

        # Check monitoring status
        monitored = False
        if monitoring_engine:
            monitored = monitoring_engine.should_monitor_container(container, info)

        # Check if quarantined (use stable_id, matching how quarantine is stored)
        quarantined = config_manager.is_quarantined(stable_id)

        # Get custom health check (by name first, then ID)
        custom_hc = config_manager.get_custom_health_check(container_name)
        if not custom_hc:
            custom_hc = config_manager.get_custom_health_check(full_container_id)

        # Override restart_count in info with locally tracked count
        info["restart_count"] = total_restart_count

        return {
            **info,
            "monitored": monitored,
            "quarantined": quarantined,
            "recent_restart_count": recent_restart_count,
            "total_restart_count": total_restart_count,
            "custom_health_check": custom_hc
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containers/select")
async def update_container_selection(request: ContainerSelectionRequest):
    """Enable or disable auto-heal for specific containers"""
    try:
        logger.debug(f"Container selection request: containers={request.container_ids}, enabled={request.enabled}")
        config = config_manager.get_config()

        if request.enabled:
            # Add to selected list - resolve stable identifiers for persistence
            for cid in request.container_ids:
                # Try to get container to resolve its stable identifier
                container = docker_client.get_container(cid)
                if container:
                    info = docker_client.get_container_info(container)
                    container_name = info.get("name")

                    # Get stable identifier (handles all edge cases)
                    labels = info.get("labels", {})
                    monitoring_id = labels.get("monitoring.id")
                    compose_project = labels.get("com.docker.compose.project")
                    compose_service = labels.get("com.docker.compose.service")

                    if monitoring_id:
                        stable_id = monitoring_id
                    elif compose_project and compose_service:
                        stable_id = f"{compose_project}_{compose_service}"
                    else:
                        stable_id = container_name

                    # Store by stable_id for persistence across recreations
                    if stable_id not in config.containers.selected:
                        config.containers.selected.append(stable_id)
                        logger.debug(f"Added container '{container_name}' with stable_id '{stable_id}' to selected list (ID: {cid})")

                    # Remove from excluded if present (check stable_id, name, and ID)
                    for identifier in [stable_id, container_name, cid]:
                        if identifier in config.containers.excluded:
                            config.containers.excluded.remove(identifier)
                            logger.debug(f"Removed '{identifier}' from excluded list")
                else:
                    # Fallback: store the identifier as-is
                    if cid not in config.containers.selected:
                        config.containers.selected.append(cid)
                        logger.debug(f"Added container {cid} to selected list (container not resolved)")
                    if cid in config.containers.excluded:
                        config.containers.excluded.remove(cid)
        else:
            # Add to excluded list - resolve stable identifiers for persistence
            for cid in request.container_ids:
                # Try to get container to resolve its stable identifier
                container = docker_client.get_container(cid)
                if container:
                    info = docker_client.get_container_info(container)
                    container_name = info.get("name")

                    # Get stable identifier
                    labels = info.get("labels", {})
                    monitoring_id = labels.get("monitoring.id")
                    compose_project = labels.get("com.docker.compose.project")
                    compose_service = labels.get("com.docker.compose.service")

                    if monitoring_id:
                        stable_id = monitoring_id
                    elif compose_project and compose_service:
                        stable_id = f"{compose_project}_{compose_service}"
                    else:
                        stable_id = container_name

                    # Store by stable_id for persistence across recreations
                    if stable_id not in config.containers.excluded:
                        config.containers.excluded.append(stable_id)
                        logger.debug(f"Added container '{container_name}' with stable_id '{stable_id}' to excluded list (ID: {cid})")

                    # Remove from selected if present (check stable_id, name, and ID)
                    for identifier in [stable_id, container_name, cid]:
                        if identifier in config.containers.selected:
                            config.containers.selected.remove(identifier)
                            logger.debug(f"Removed '{identifier}' from selected list")
                else:
                    # Fallback: store the identifier as-is
                    if cid not in config.containers.excluded:
                        config.containers.excluded.append(cid)
                        logger.debug(f"Added container {cid} to excluded list (container not resolved)")
                    if cid in config.containers.selected:
                        config.containers.selected.remove(cid)

        config_manager.update_config(config)

        logger.info(f"Container selection updated: {len(request.container_ids)} container(s) {'enabled' if request.enabled else 'disabled'}")

        return {"status": "success", "message": f"Updated {len(request.container_ids)} containers"}
    except Exception as e:
        logger.error(f"Error updating container selection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containers/{container_id}/restart")
async def restart_container_manual(container_id: str):
    """Manually restart a container"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        success = docker_client.restart_container(container)

        if success:
            return {"status": "success", "message": f"Container {container_id} restarted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to restart container")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containers/{container_id}/unquarantine")
async def unquarantine_container(container_id: str):
    """Remove container from quarantine"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        # Get the container to resolve stable_id
        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        info = docker_client.get_container_info(container)
        container_name = info.get("name")
        stable_id = info.get("stable_id")

        # Remove from quarantine using stable_id (matches how quarantine is stored)
        config_manager.unquarantine_container(stable_id)

        # Clear restart history using stable_id
        config_manager.clear_restart_history(stable_id)

        return {"status": "success", "message": f"Container {container_name} removed from quarantine"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unquarantining container: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Maintenance Mode Endpoints ====================

@app.post("/api/maintenance/enable")
async def enable_maintenance_mode():
    """Enable maintenance mode - stops all auto-healing"""
    try:
        config_manager.enable_maintenance_mode()
        logger.info("Maintenance mode enabled")
        return {
            "status": "success",
            "message": "Maintenance mode enabled",
            "maintenance_mode": True,
            "maintenance_start_time": config_manager.get_maintenance_start_time().isoformat()
        }
    except Exception as e:
        logger.error(f"Error enabling maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/maintenance/disable")
async def disable_maintenance_mode():
    """Disable maintenance mode - resumes auto-healing"""
    try:
        config_manager.disable_maintenance_mode()
        logger.info("Maintenance mode disabled")
        return {
            "status": "success",
            "message": "Maintenance mode disabled",
            "maintenance_mode": False
        }
    except Exception as e:
        logger.error(f"Error disabling maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/maintenance/status")
async def get_maintenance_status():
    """Get current maintenance mode status"""
    try:
        maintenance_start = config_manager.get_maintenance_start_time()
        return {
            "maintenance_mode": config_manager.is_maintenance_mode(),
            "maintenance_start_time": maintenance_start.isoformat() if maintenance_start else None
        }
    except Exception as e:
        logger.error(f"Error getting maintenance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Configuration Endpoints ====================

@app.get("/api/config", response_model=AutoHealConfig)
async def get_config():
    """Get current configuration"""
    return config_manager.get_config()


@app.put("/api/config")
async def update_config(config: AutoHealConfig):
    """Update configuration"""
    try:
        config_manager.update_config(config)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config/monitor")
async def update_monitor_config(monitor_config: MonitorConfig):
    """Update monitor configuration"""
    try:
        config = config_manager.get_config()
        config.monitor = monitor_config
        config_manager.update_config(config)
        return {"status": "success", "message": "Monitor configuration updated"}
    except Exception as e:
        logger.error(f"Error updating monitor config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config/restart")
async def update_restart_config(restart_config: RestartConfig):
    """Update restart configuration"""
    try:
        config = config_manager.get_config()
        config.restart = restart_config
        config_manager.update_config(config)
        return {"status": "success", "message": "Restart configuration updated"}
    except Exception as e:
        logger.error(f"Error updating restart config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/export")
async def export_config():
    """Export configuration as JSON"""
    try:
        config_json = config_manager.export_config()

        # Return as downloadable file
        return JSONResponse(
            content=json.loads(config_json),
            headers={
                "Content-Disposition": f"attachment; filename=autoheal-config-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/import")
async def import_config(file: UploadFile = File(...)):
    """Import configuration from JSON file"""
    try:
        content = await file.read()
        config_json = content.decode('utf-8')

        config_manager.import_config(config_json)

        return {"status": "success", "message": "Configuration imported successfully"}
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check Management ====================

@app.post("/api/healthchecks")
async def add_health_check(health_check: HealthCheckConfig):
    """Add custom health check for a container"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        # Get the container to resolve full container ID
        container = docker_client.get_container(health_check.container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        # Update the health check config with full container ID
        health_check.container_id = container.id

        config_manager.add_custom_health_check(health_check)
        return {"status": "success", "message": f"Health check added for container {health_check.container_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/healthchecks/{container_id}")
async def get_health_check(container_id: str):
    """Get custom health check for a container"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        # Get the container to resolve full container ID
        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        full_container_id = container.id
        health_check = config_manager.get_custom_health_check(full_container_id)
        if not health_check:
            raise HTTPException(status_code=404, detail="No custom health check found for this container")
        return health_check
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/healthchecks/{container_id}")
async def delete_health_check(container_id: str):
    """Delete custom health check for a container"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        # Get the container to resolve full container ID
        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        full_container_id = container.id
        config_manager.remove_custom_health_check(full_container_id)
        return {"status": "success", "message": f"Health check removed for container {container_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/healthchecks")
async def list_health_checks():
    """List all custom health checks"""
    return config_manager.get_all_custom_health_checks()


# ==================== Event Log Endpoints ====================

@app.get("/api/events")
async def get_events(limit: int = 100):
    """Get recent auto-heal events"""
    try:
        events = config_manager.get_events(limit)
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "container_id": event.container_id,
                "container_name": event.container_name,
                "event_type": event.event_type,
                "restart_count": event.restart_count,
                "status": event.status,
                "message": event.message
            }
            for event in events
        ]
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/events")
async def clear_events():
    """Clear all events from the log"""
    try:
        config_manager.clear_events()
        return {"status": "success", "message": "All events cleared"}
    except Exception as e:
        logger.error(f"Error clearing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config/observability")
async def update_observability_config(observability_config: dict):
    """Update observability configuration including log level"""
    try:
        config = config_manager.get_config()

        # Update observability config
        if "log_level" in observability_config:
            level_name = observability_config["log_level"]
            config.observability.log_level = level_name

            # Update log level directly without importing main
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

            # Disable uvicorn access logs completely
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
            logging.getLogger("uvicorn").setLevel(logging.WARNING)

            logger.info(f"Log level changed to: {level_name}")

        if "prometheus_enabled" in observability_config:
            config.observability.prometheus_enabled = observability_config["prometheus_enabled"]

        if "log_format" in observability_config:
            config.observability.log_format = observability_config["log_format"]

        config_manager.update_config(config)

        return {"status": "success", "message": "Observability configuration updated"}
    except Exception as e:
        logger.error(f"Error updating observability config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Uptime-Kuma Integration Endpoints ====================

@app.post("/api/uptime-kuma/test-connection")
async def test_uptime_kuma_connection(config_data: dict):
    """Test connection to Uptime-Kuma server"""
    from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient

    try:
        client = UptimeKumaClient(
            config_data.get('server_url'),
            config_data.get('api_token'),      # password (API key or user password)
            config_data.get('username', '')    # username (optional, empty for API key)
        )
        success = await client.connect()

        if success:
            # Fetch monitors to validate full access
            monitors = await client.get_all_monitors()
            return {
                "success": True,
                "message": "Connection successful",
                "monitor_count": len(monitors)
            }
        else:
            return {
                "success": False,
                "message": "Connection failed - check URL and credentials"
            }
    except Exception as e:
        logger.error(f"Uptime-Kuma connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }


@app.post("/api/uptime-kuma/enable")
async def enable_uptime_kuma_integration(integration_config: dict):
    """Enable Uptime-Kuma integration and fetch monitors"""
    from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient
    from app.config.config_manager import UptimeKumaMapping

    try:
        # Update configuration
        config = config_manager.get_config()
        config.uptime_kuma.enabled = True
        config.uptime_kuma.server_url = integration_config.get('server_url')
        config.uptime_kuma.username = integration_config.get('username', '')
        config.uptime_kuma.api_token = integration_config.get('api_token')
        config.uptime_kuma.auto_restart_on_down = integration_config.get('auto_restart_on_down', True)

        # Fetch monitors
        client = UptimeKumaClient(
            config.uptime_kuma.server_url,
            config.uptime_kuma.api_token,      # password (API key or user password)
            config.uptime_kuma.username        # username (optional, empty for API key)
        )
        monitors = await client.get_all_monitors()

        # Perform auto-mapping
        containers = docker_client.list_containers(all_containers=False)
        auto_mappings = []

        for container in containers:
            container_name = container.name
            # Get container info to extract stable_id
            info = docker_client.get_container_info(container)
            if not info:
                continue

            stable_id = info.get("stable_id")
            if not stable_id:
                continue

            # Check if any monitor friendly name matches container name
            for monitor in monitors:
                if monitor['friendly_name'].lower() == container_name.lower():
                    mapping = UptimeKumaMapping(
                        container_id=stable_id,  # Use stable_id instead of short container ID
                        monitor_friendly_name=monitor['friendly_name'],
                        auto_mapped=True
                    )
                    auto_mappings.append(mapping)
                    break

        # Add auto-mappings to config
        config.uptime_kuma_mappings = auto_mappings
        config_manager.update_config(config)

        # Restart Uptime-Kuma monitor
        if hasattr(monitoring_engine, 'uptime_kuma_monitor'):
            await monitoring_engine.uptime_kuma_monitor.stop()
            await monitoring_engine.uptime_kuma_monitor.start()

        logger.info(f"Uptime-Kuma integration enabled with {len(auto_mappings)} auto-mappings using monitoring interval: {config.monitor.interval_seconds}s")


        return {
            "success": True,
            "monitors": monitors,
            "auto_mappings": [m.model_dump() for m in auto_mappings]
        }

    except Exception as e:
        logger.error(f"Failed to enable Uptime-Kuma: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/uptime-kuma/monitors")
async def get_uptime_kuma_monitors():
    """Get all Uptime-Kuma monitors"""
    from app.uptime_kuma.uptime_kuma_client import UptimeKumaClient

    config = config_manager.get_config()

    if not config.uptime_kuma.enabled:
        raise HTTPException(status_code=400, detail="Uptime-Kuma integration not enabled")

    try:
        client = UptimeKumaClient(
            config.uptime_kuma.server_url,
            config.uptime_kuma.api_token,      # password (API key or user password)
            config.uptime_kuma.username        # username (optional, empty for API key)
        )
        monitors = await client.get_all_monitors()
        return {"monitors": monitors}
    except Exception as e:
        logger.error(f"Failed to fetch Uptime-Kuma monitors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/uptime-kuma/mappings")
async def get_uptime_kuma_mappings():
    """Get all container-to-monitor mappings"""
    config = config_manager.get_config()
    return {
        "mappings": [m.model_dump() for m in config.uptime_kuma_mappings]
    }


@app.post("/api/uptime-kuma/mappings")
async def create_uptime_kuma_mapping(mapping: dict):
    """Create a new container-to-monitor mapping"""
    from app.config.config_manager import UptimeKumaMapping

    try:
        # Get the container to resolve stable_id
        container = docker_client.get_container(mapping['container_id'])
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        info = docker_client.get_container_info(container)
        container_name = info.get("name")
        stable_id = info.get("stable_id")

        config = config_manager.get_config()
        new_mapping = UptimeKumaMapping(
            container_id=stable_id,
            monitor_friendly_name=mapping['monitor_friendly_name'],
            auto_mapped=False
        )

        config.uptime_kuma_mappings.append(new_mapping)
        config_manager.update_config(config)

        logger.info(f"Created Uptime-Kuma mapping: {mapping['container_id']} -> {mapping['monitor_friendly_name']}")

        return {"success": True, "mapping": new_mapping.model_dump()}
    except Exception as e:
        logger.error(f"Failed to create Uptime-Kuma mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/uptime-kuma/mappings/{container_id}")
async def delete_uptime_kuma_mapping(container_id: str):
    """Delete a container-to-monitor mapping (container_id is actually stable_id)"""
    try:
        config = config_manager.get_config()
        config.uptime_kuma_mappings = [
            m for m in config.uptime_kuma_mappings if m.container_id != container_id
        ]
        config_manager.update_config(config)

        logger.info(f"Deleted Uptime-Kuma mapping for stable_id: {container_id}")

        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to delete Uptime-Kuma mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/uptime-kuma/disable")
async def disable_uptime_kuma_integration():
    """Disable Uptime-Kuma integration"""
    try:
        config = config_manager.get_config()
        config.uptime_kuma.enabled = False
        config_manager.update_config(config)

        # Stop monitoring
        if hasattr(monitoring_engine, 'uptime_kuma_monitor'):
            await monitoring_engine.uptime_kuma_monitor.stop()

        logger.info("Uptime-Kuma integration disabled")

        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to disable Uptime-Kuma: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Notification Endpoints ====================

@app.get("/api/notifications/config")
async def get_notifications_config():
    """Get current notification configuration"""
    try:
        config = config_manager.get_config()
        return {
            "enabled": config.notifications.enabled,
            "services": [service.model_dump() for service in config.notifications.services],
            "event_filters": config.notifications.event_filters
        }
    except Exception as e:
        logger.error(f"Error getting notifications config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/notifications/config")
async def update_notifications_config(notifications_config: dict):
    """Update notification configuration"""
    try:
        config = config_manager.get_config()

        if "enabled" in notifications_config:
            config.notifications.enabled = notifications_config["enabled"]

        if "event_filters" in notifications_config:
            config.notifications.event_filters = notifications_config["event_filters"]

        if "services" in notifications_config:
            # Parse and validate services
            services = []
            for service_data in notifications_config["services"]:
                service = NotificationService(**service_data)
                services.append(service)
            config.notifications.services = services

        config_manager.update_config(config)

        return {
            "status": "success",
            "message": "Notification configuration updated",
            "config": {
                "enabled": config.notifications.enabled,
                "services": [s.model_dump() for s in config.notifications.services],
                "event_filters": config.notifications.event_filters
            }
        }
    except Exception as e:
        logger.error(f"Error updating notifications config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/services")
async def add_notification_service(service: dict):
    """Add a new notification service"""
    try:
        config = config_manager.get_config()

        # Validate and create service
        new_service = NotificationService(**service)

        # Check if service with same name already exists
        for existing in config.notifications.services:
            if existing.name == new_service.name:
                raise HTTPException(status_code=400, detail=f"Service with name '{new_service.name}' already exists")

        config.notifications.services.append(new_service)
        config_manager.update_config(config)

        return {
            "status": "success",
            "message": f"Notification service '{new_service.name}' added",
            "service": new_service.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding notification service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/notifications/services/{service_name}")
async def update_notification_service(service_name: str, service: dict):
    """Update an existing notification service"""
    try:
        config = config_manager.get_config()

        # Find and update service
        updated_service = None
        found = False
        for i, existing in enumerate(config.notifications.services):
            if existing.name == service_name:
                # Preserve name if not provided
                if "name" not in service:
                    service["name"] = service_name
                updated_service = NotificationService(**service)
                config.notifications.services[i] = updated_service
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

        config_manager.update_config(config)

        return {
            "status": "success",
            "message": f"Notification service '{service_name}' updated",
            "service": updated_service.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/notifications/services/{service_name}")
async def delete_notification_service(service_name: str):
    """Delete a notification service"""
    try:
        config = config_manager.get_config()

        # Find and remove service
        original_count = len(config.notifications.services)
        config.notifications.services = [
            s for s in config.notifications.services if s.name != service_name
        ]

        if len(config.notifications.services) == original_count:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

        config_manager.update_config(config)

        return {
            "status": "success",
            "message": f"Notification service '{service_name}' deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/test/{service_name}")
async def test_notification_service(service_name: str):
    """Send a test notification to verify configuration"""
    try:
        result = await notification_manager.test_notification(service_name)

        if result["success"]:
            return {
                "status": "success",
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UI Endpoint ====================

def serve_react_app():
    """Helper function to serve React index.html"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Docker Auto-Heal Service</h1>"
                   "<p>React UI not found. Please build the frontend first:</p>"
                   "<pre>cd frontend && npm install && npm run build</pre>"
                   "<p>API documentation is available at <a href='/docs'>/docs</a></p>"
        )

@app.get("/", response_class=HTMLResponse)
async def serve_ui_root():
    """Serve the React UI at root"""
    return serve_react_app()


# Mount static files for React build
import os

try:
    # Mount the entire static directory at root to serve assets properly
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.debug("Static files mounted: React UI available")
except Exception as e:
    logger.error(f"Failed to mount static directory: {e}")
    logger.error("React build not found. Run 'cd frontend && npm run build' first.")


# Catch-all route for React Router - must be at the end
# This serves index.html for all non-API routes, allowing React Router to handle client-side routing
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_ui_catchall(full_path: str):
    """Serve the React UI for all non-API routes (React Router support)"""
    # Don't intercept API routes, docs, or static files
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "assets/", "static/")):
        raise HTTPException(status_code=404, detail="Not Found")
    return serve_react_app()
