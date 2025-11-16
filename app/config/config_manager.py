"""
Configuration management for Docker Auto-Heal Service
Handles in-memory configuration state with JSON export/import support
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import threading
from pathlib import Path
import logging
from app.config.init_defaults import initialize_defaults

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    """Monitor configuration settings"""
    interval_seconds: int = Field(default=30, ge=1, description="Monitoring interval in seconds")
    label_key: str = Field(default="autoheal", description="Label key to filter containers")
    label_value: str = Field(default="true", description="Label value to filter containers")
    include_all: bool = Field(default=False, description="Monitor all containers regardless of labels")


class BackoffConfig(BaseModel):
    """Restart backoff configuration"""
    enabled: bool = Field(default=True, description="Enable exponential backoff")
    initial_seconds: int = Field(default=10, ge=1, description="Initial backoff delay in seconds")
    multiplier: float = Field(default=2.0, ge=1.0, description="Backoff multiplier")


class RestartConfig(BaseModel):
    """Restart policy configuration"""
    mode: str = Field(default="on-failure", description="Restart mode: on-failure, health, or both")
    cooldown_seconds: int = Field(default=60, ge=0, description="Cooldown between restarts")
    max_restarts: int = Field(default=3, ge=1, description="Maximum restarts within window")
    max_restarts_window_seconds: int = Field(default=600, ge=1, description="Time window for max restarts")
    backoff: BackoffConfig = Field(default_factory=BackoffConfig)
    respect_manual_stop: bool = Field(default=True, description="Respect manual container stops (exit code 0)")


class ContainersConfig(BaseModel):
    """Container selection configuration"""
    selected: List[str] = Field(default_factory=list, description="Explicitly selected container IDs/names")
    excluded: List[str] = Field(default_factory=list, description="Explicitly excluded container IDs/names")
    restart_counts: Dict[str, int] = Field(default_factory=dict, description="Restart counts by stable_id")


class FiltersConfig(BaseModel):
    """Filtering rules for containers"""
    whitelist_names: List[str] = Field(default_factory=list, description="Container name patterns to whitelist")
    blacklist_names: List[str] = Field(default_factory=list, description="Container name patterns to blacklist")
    whitelist_labels: List[Dict[str, str]] = Field(default_factory=list, description="Label filters to whitelist")
    blacklist_labels: List[Dict[str, str]] = Field(default_factory=list, description="Label filters to blacklist")


class UIConfig(BaseModel):
    """UI configuration settings"""
    enable: bool = Field(default=True, description="Enable web UI")
    listen_address: str = Field(default="0.0.0.0", description="UI listen address")
    listen_port: int = Field(default=3131, ge=1, le=65535, description="UI listen port")
    allow_export_json: bool = Field(default=True, description="Allow configuration export")
    allow_import_json: bool = Field(default=True, description="Allow configuration import")
    max_log_entries: int = Field(default=50, ge=1, description="Maximum log entries to keep in memory")


class AlertsConfig(BaseModel):
    """Alerting configuration"""
    enabled: bool = Field(default=True, description="Enable alerts")
    webhook: Optional[str] = Field(default=None, description="Webhook URL for alerts")
    notify_on_quarantine: bool = Field(default=True, description="Send alert when container is quarantined")


class ObservabilityConfig(BaseModel):
    """Observability and metrics configuration"""
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, ge=1, le=65535, description="Metrics endpoint port")
    log_format: str = Field(default="json", description="Log format: json or text")
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")


class UptimeKumaConfig(BaseModel):
    """Uptime-Kuma integration configuration"""
    enabled: bool = Field(default=False, description="Enable Uptime-Kuma integration")
    server_url: str = Field(default="", description="Uptime-Kuma server URL (e.g., http://localhost:3001)")
    username: str = Field(default="", description="Uptime-Kuma username (optional for API key auth)")
    api_token: str = Field(default="", description="Uptime-Kuma API token or password")
    auto_restart_on_down: bool = Field(default=True, description="Auto-restart container when monitor is DOWN")


class UptimeKumaMapping(BaseModel):
    """Container to Uptime-Kuma monitor mapping"""
    container_id: str = Field(description="Container stable ID or name")
    monitor_friendly_name: str = Field(description="Uptime-Kuma monitor friendly name")
    auto_mapped: bool = Field(default=False, description="Whether this was auto-mapped")


class AutoHealConfig(BaseModel):
    """Main auto-heal configuration"""
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    containers: ContainersConfig = Field(default_factory=ContainersConfig)
    restart: RestartConfig = Field(default_factory=RestartConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    uptime_kuma: UptimeKumaConfig = Field(default_factory=UptimeKumaConfig)
    uptime_kuma_mappings: List[UptimeKumaMapping] = Field(default_factory=list)


class HealthCheckConfig(BaseModel):
    """Custom health check configuration for a container"""
    container_id: str
    check_type: str = Field(description="Type: http, tcp, exec, or docker")
    interval_seconds: int = Field(default=30, ge=1)
    timeout_seconds: int = Field(default=10, ge=1)
    retries: int = Field(default=3, ge=1)
    # For HTTP checks
    http_endpoint: Optional[str] = None
    http_expected_status: Optional[int] = 200
    # For TCP checks
    tcp_port: Optional[int] = None
    # For exec checks
    exec_command: Optional[List[str]] = None


class AutoHealEvent(BaseModel):
    """Auto-heal event log entry"""
    timestamp: datetime
    container_id: str
    container_name: str
    event_type: str  # restart, quarantine, health_check_failed, etc.
    restart_count: int
    status: str  # success, failure, quarantined
    message: str


class ConfigManager:
    """
    Thread-safe configuration manager with file-based persistence
    All data is automatically saved to /data directory
    """

    # Data directory paths
    DATA_DIR = Path("/data")
    CONFIG_FILE = DATA_DIR / "config.json"
    EVENTS_FILE = DATA_DIR / "events.json"
    RESTART_COUNTS_FILE = DATA_DIR / "restart_counts.json"
    QUARANTINE_FILE = DATA_DIR / "quarantine.json"
    MAINTENANCE_FILE = DATA_DIR / "maintenance.json"

    def __init__(self):
        self._lock = threading.RLock()

        # Create data directory if it doesn't exist
        self._ensure_data_directory()

        # Initialize default files if they don't exist
        initialize_defaults(self.DATA_DIR)

        # Load persisted data or initialize with defaults
        self._config = self._load_config()
        self._event_log: List[AutoHealEvent] = self._load_events()
        self._custom_health_checks: Dict[str, HealthCheckConfig] = self._load_custom_health_checks()
        # _container_restart_counts removed - now stored in self._config.containers.restart_counts
        self._quarantined_containers: set = self._load_quarantine()
        self._maintenance_mode: bool = False
        self._maintenance_start_time: Optional[datetime] = None
        self._load_maintenance_mode()

        logger.info("ConfigManager initialized with persistent storage at /data")

    def _ensure_data_directory(self) -> None:
        """Create data directory and subdirectories if they don't exist"""
        try:
            self.DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Data directory ensured at: {self.DATA_DIR}")
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            # Fallback to current directory if /data is not writable
            self.DATA_DIR = Path("./data")
            self.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._update_file_paths()
            logger.warning(f"Using fallback data directory: {self.DATA_DIR}")

    def _update_file_paths(self) -> None:
        """Update all file paths when data directory changes"""
        self.CONFIG_FILE = self.DATA_DIR / "config.json"
        self.EVENTS_FILE = self.DATA_DIR / "events.json"
        self.RESTART_COUNTS_FILE = self.DATA_DIR / "restart_counts.json"
        self.QUARANTINE_FILE = self.DATA_DIR / "quarantine.json"
        self.MAINTENANCE_FILE = self.DATA_DIR / "maintenance.json"

    def _load_config(self) -> AutoHealConfig:
        """Load configuration from file or return default"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # Extract custom health checks separately
                    self._custom_health_checks = {
                        cid: HealthCheckConfig(**hc)
                        for cid, hc in data.pop('custom_health_checks', {}).items()
                    }
                    config = AutoHealConfig(**data)
                    logger.info("Configuration loaded from disk")
                    return config
        except Exception as e:
            logger.warning(f"Failed to load config from disk: {e}, using defaults")
        return AutoHealConfig()

    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            config_dict = self._config.model_dump()
            config_dict['custom_health_checks'] = {
                cid: hc.model_dump() for cid, hc in self._custom_health_checks.items()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            logger.debug("Configuration saved to disk")
        except Exception as e:
            logger.error(f"Failed to save config to disk: {e}")

    def _load_events(self) -> List[AutoHealEvent]:
        """Load events from file or return empty list"""
        try:
            if self.EVENTS_FILE.exists():
                with open(self.EVENTS_FILE, 'r') as f:
                    data = json.load(f)
                    events = [AutoHealEvent(**event) for event in data]
                    logger.info(f"Loaded {len(events)} events from disk")
                    return events
        except Exception as e:
            logger.warning(f"Failed to load events from disk: {e}")
        return []

    def _save_events(self) -> None:
        """Save events to file"""
        try:
            events_data = [event.model_dump(mode='json') for event in self._event_log]
            with open(self.EVENTS_FILE, 'w') as f:
                json.dump(events_data, f, indent=2, default=str)
            logger.debug(f"Saved {len(self._event_log)} events to disk")
        except Exception as e:
            logger.error(f"Failed to save events to disk: {e}")

    def _load_custom_health_checks(self) -> Dict[str, HealthCheckConfig]:
        """Load custom health checks (already loaded in _load_config)"""
        return getattr(self, '_custom_health_checks', {})

    # Restart counts are now stored in config.json, no separate file needed

    def _load_quarantine(self) -> set:
        """Load quarantine list from file or return empty set"""
        try:
            if self.QUARANTINE_FILE.exists():
                with open(self.QUARANTINE_FILE, 'r') as f:
                    data = json.load(f)
                    quarantine = set(data)
                    logger.info(f"Loaded {len(quarantine)} quarantined containers from disk")
                    return quarantine
        except Exception as e:
            logger.warning(f"Failed to load quarantine list from disk: {e}")
        return set()

    def _save_quarantine(self) -> None:
        """Save quarantine list to file"""
        try:
            with open(self.QUARANTINE_FILE, 'w') as f:
                json.dump(list(self._quarantined_containers), f, indent=2)
            logger.debug(f"Saved {len(self._quarantined_containers)} quarantined containers to disk")
        except Exception as e:
            logger.error(f"Failed to save quarantine list to disk: {e}")

    def _load_maintenance_mode(self) -> None:
        """Load maintenance mode state from file"""
        try:
            if self.MAINTENANCE_FILE.exists():
                with open(self.MAINTENANCE_FILE, 'r') as f:
                    data = json.load(f)
                    self._maintenance_mode = data.get('enabled', False)
                    start_time = data.get('start_time')
                    if start_time:
                        self._maintenance_start_time = datetime.fromisoformat(start_time)
                    logger.info(f"Loaded maintenance mode state: {self._maintenance_mode}")
        except Exception as e:
            logger.warning(f"Failed to load maintenance mode from disk: {e}")

    def _save_maintenance_mode(self) -> None:
        """Save maintenance mode state to file"""
        try:
            data = {
                'enabled': self._maintenance_mode,
                'start_time': self._maintenance_start_time.isoformat() if self._maintenance_start_time else None
            }
            with open(self.MAINTENANCE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved maintenance mode state: {self._maintenance_mode}")
        except Exception as e:
            logger.error(f"Failed to save maintenance mode to disk: {e}")

    def get_config(self) -> AutoHealConfig:
        """Get current configuration (thread-safe)"""
        with self._lock:
            return self._config.model_copy(deep=True)

    def update_config(self, config: AutoHealConfig) -> None:
        """Update configuration (thread-safe)"""
        with self._lock:
            self._config = config.model_copy(deep=True)
            self._save_config()

    def update_partial_config(self, **kwargs) -> None:
        """Update specific configuration fields"""
        with self._lock:
            config_dict = self._config.model_dump()
            for key, value in kwargs.items():
                if key in config_dict:
                    setattr(self._config, key, value)
            self._save_config()

    def export_config(self) -> str:
        """Export configuration as JSON string"""
        with self._lock:
            config_dict = self._config.model_dump()
            config_dict['custom_health_checks'] = {
                cid: hc.model_dump() for cid, hc in self._custom_health_checks.items()
            }
            return json.dumps(config_dict, indent=2, default=str)

    def import_config(self, json_str: str) -> None:
        """Import configuration from JSON string"""
        with self._lock:
            config_dict = json.loads(json_str)

            # Extract and store custom health checks separately
            custom_hc = config_dict.pop('custom_health_checks', {})

            # Update main config
            self._config = AutoHealConfig(**config_dict)

            # Restore custom health checks
            self._custom_health_checks = {
                cid: HealthCheckConfig(**hc) for cid, hc in custom_hc.items()
            }

            # Persist to disk
            self._save_config()

    def add_event(self, event: AutoHealEvent) -> None:
        """Add event to log (thread-safe, with size limit)"""
        with self._lock:
            self._event_log.append(event)
            max_entries = self._config.ui.max_log_entries
            if len(self._event_log) > max_entries:
                self._event_log = self._event_log[-max_entries:]
            self._save_events()

    def get_events(self, limit: Optional[int] = None) -> List[AutoHealEvent]:
        """Get event log (thread-safe)"""
        with self._lock:
            if limit:
                return self._event_log[-limit:]
            return self._event_log.copy()

    def clear_events(self) -> None:
        """Clear all events from log (thread-safe)"""
        with self._lock:
            self._event_log.clear()
            self._save_events()
            logger.info("All events cleared")

    def add_custom_health_check(self, health_check: HealthCheckConfig) -> None:
        """Add custom health check for a container"""
        with self._lock:
            self._custom_health_checks[health_check.container_id] = health_check
            self._save_config()

    def get_custom_health_check(self, container_id: str) -> Optional[HealthCheckConfig]:
        """Get custom health check for a container"""
        with self._lock:
            return self._custom_health_checks.get(container_id)

    def remove_custom_health_check(self, container_id: str) -> None:
        """Remove custom health check for a container"""
        with self._lock:
            self._custom_health_checks.pop(container_id, None)
            self._save_config()

    def get_all_custom_health_checks(self) -> Dict[str, HealthCheckConfig]:
        """Get all custom health checks"""
        with self._lock:
            return self._custom_health_checks.copy()

    def record_restart(self, container_id: str) -> None:
        """Record a container restart - increment count in config.json"""
        with self._lock:
            if container_id not in self._config.containers.restart_counts:
                self._config.containers.restart_counts[container_id] = 0
            self._config.containers.restart_counts[container_id] += 1
            self._save_config()

    def get_restart_count(self, container_id: str, window_seconds: int) -> int:
        """Get restart count - returns total count (window filtering removed, kept for compatibility)"""
        with self._lock:
            return self._config.containers.restart_counts.get(container_id, 0)

    def get_total_restart_count(self, container_id: str) -> int:
        """Get total restart count (all time) - from config.json"""
        with self._lock:
            return self._config.containers.restart_counts.get(container_id, 0)

    def cleanup_restart_counts(self, active_container_ids: List[str]) -> None:
        """Remove restart counts for containers that no longer exist (DISABLED to preserve manual entries)"""
        # DISABLED: Auto-cleanup was removing manual entries because stable_id matching is complex
        # Users can manually edit config.json to remove old entries if needed
        pass

    def quarantine_container(self, container_id: str) -> None:
        """Mark container as quarantined"""
        with self._lock:
            self._quarantined_containers.add(container_id)
            self._save_quarantine()

    def unquarantine_container(self, container_id: str) -> None:
        """Remove container from quarantine"""
        with self._lock:
            self._quarantined_containers.discard(container_id)
            self._save_quarantine()

    def is_quarantined(self, container_id: str) -> bool:
        """Check if container is quarantined"""
        with self._lock:
            return container_id in self._quarantined_containers

    def get_quarantined_containers(self) -> set:
        """Get all quarantined containers"""
        with self._lock:
            return self._quarantined_containers.copy()

    def clear_restart_history(self, container_id: str) -> None:
        """Clear restart history for a container"""
        with self._lock:
            if container_id in self._config.containers.restart_counts:
                del self._config.containers.restart_counts[container_id]
                self._save_config()

    def enable_maintenance_mode(self) -> None:
        """Enable maintenance mode"""
        with self._lock:
            self._maintenance_mode = True
            self._maintenance_start_time = datetime.now(timezone.utc)
            self._save_maintenance_mode()

    def disable_maintenance_mode(self) -> None:
        """Disable maintenance mode"""
        with self._lock:
            self._maintenance_mode = False
            self._maintenance_start_time = None
            self._save_maintenance_mode()

    def is_maintenance_mode(self) -> bool:
        """Check if maintenance mode is enabled"""
        with self._lock:
            return self._maintenance_mode

    def get_maintenance_start_time(self) -> Optional[datetime]:
        """Get maintenance mode start time"""
        with self._lock:
            return self._maintenance_start_time


# Global configuration manager instance
config_manager = ConfigManager()
