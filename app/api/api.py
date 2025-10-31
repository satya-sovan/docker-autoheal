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
    RestartConfig
)
from app.docker_client.docker_client_wrapper import DockerClientWrapper
from app.monitor.monitoring_engine import MonitoringEngine

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
                if monitoring_engine._should_monitor_container(container, info):
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

        for container in containers:
            info = docker_client.get_container_info(container)
            if not info:
                continue

            container_id = info.get("full_id")

            # Check if monitored
            monitored = False
            if monitoring_engine:
                monitored = monitoring_engine._should_monitor_container(container, info)

            # Check if quarantined
            quarantined = config_manager.is_quarantined(container_id)

            container_info = ContainerInfo(
                id=info.get("id"),
                name=info.get("name"),
                image=info.get("image"),
                status=info.get("status"),
                state=info.get("state", {}),
                labels=info.get("labels", {}),
                health=info.get("health"),
                restart_count=info.get("restart_count", 0),
                monitored=monitored,
                quarantined=quarantined
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

        # Use full container ID for all operations
        full_container_id = info.get("full_id")

        # Get restart history
        restart_count = config_manager.get_restart_count(
            full_container_id,
            config_manager.get_config().restart.max_restarts_window_seconds
        )

        # Check monitoring status
        monitored = False
        if monitoring_engine:
            monitored = monitoring_engine._should_monitor_container(container, info)

        return {
            **info,
            "monitored": monitored,
            "quarantined": config_manager.is_quarantined(full_container_id),
            "recent_restart_count": restart_count,
            "custom_health_check": config_manager.get_custom_health_check(full_container_id)
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
            # Add to selected list
            for cid in request.container_ids:
                if cid not in config.containers.selected:
                    config.containers.selected.append(cid)
                    logger.debug(f"Added container {cid} to selected list")
                # Remove from excluded if present
                if cid in config.containers.excluded:
                    config.containers.excluded.remove(cid)
                    logger.debug(f"Removed container {cid} from excluded list")
        else:
            # Add to excluded list
            for cid in request.container_ids:
                if cid not in config.containers.excluded:
                    config.containers.excluded.append(cid)
                    logger.debug(f"Added container {cid} to excluded list")
                # Remove from selected if present
                if cid in config.containers.selected:
                    config.containers.selected.remove(cid)
                    logger.debug(f"Removed container {cid} from selected list")

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

        # Get the container to resolve full container ID
        container = docker_client.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")

        # Use the full container ID for quarantine operations
        full_container_id = container.id

        config_manager.unquarantine_container(full_container_id)
        config_manager.clear_restart_history(full_container_id)

        return {"status": "success", "message": f"Container {container_id} removed from quarantine"}
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
