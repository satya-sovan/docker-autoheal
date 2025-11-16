"""
Initialize default configuration and data files on first startup
This module creates all necessary files in /data directory if they don't exist
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration dictionary"""
    return {
        "monitor": {
            "interval_seconds": 30,
            "label_key": "autoheal",
            "label_value": "true",
            "include_all": False
        },
        "containers": {
            "selected": [],
            "excluded": [],
            "restart_counts": {}
        },
        "restart": {
            "mode": "on-failure",
            "cooldown_seconds": 60,
            "max_restarts": 3,
            "max_restarts_window_seconds": 600,
            "backoff": {
                "enabled": True,
                "initial_seconds": 10,
                "multiplier": 2.0
            },
            "respect_manual_stop": True
        },
        "filters": {
            "whitelist_names": [],
            "blacklist_names": [],
            "whitelist_labels": [],
            "blacklist_labels": []
        },
        "ui": {
            "enable": True,
            "listen_address": "0.0.0.0",
            "listen_port": 3131,
            "allow_export_json": True,
            "allow_import_json": True,
            "max_log_entries": 50
        },
        "alerts": {
            "enabled": True,
            "webhook": None,
            "notify_on_quarantine": True
        },
        "observability": {
            "prometheus_enabled": True,
            "metrics_port": 9090,
            "log_format": "json",
            "log_level": "INFO"
        },
        "uptime_kuma": {
            "enabled": False,
            "server_url": "",
            "username": "",
            "api_token": "",
            "auto_restart_on_down": True
        },
        "uptime_kuma_mappings": [],
        "custom_health_checks": {}
    }


def get_default_events() -> list:
    """Get default events list (empty)"""
    return []


def get_default_quarantine() -> list:
    """Get default quarantine list (empty)"""
    return []


def get_default_maintenance() -> Dict[str, Any]:
    """Get default maintenance mode settings"""
    return {
        "enabled": False,
        "start_time": None
    }


def init_data_file(file_path: Path, default_data: Any, description: str) -> bool:
    """
    Initialize a data file if it doesn't exist

    Args:
        file_path: Path to the file
        default_data: Default data to write
        description: Description of the file for logging

    Returns:
        True if file was created, False if it already existed
    """
    if file_path.exists():
        logger.debug(f"{description} already exists at {file_path}")
        return False

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(default_data, f, indent=2)
        logger.info(f"Created default {description} at {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create {description} at {file_path}: {e}")
        return False


def initialize_defaults(data_dir: Path = Path("/data")) -> None:
    """
    Initialize all default data files if they don't exist

    Args:
        data_dir: Base data directory (default: /data)
    """
    logger.info("Initializing default data files...")

    # Ensure data directory exists
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory ready at: {data_dir}")
    except Exception as e:
        logger.error(f"Failed to create data directory {data_dir}: {e}")
        # Fallback to local directory
        data_dir = Path("./data")
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Using fallback data directory: {data_dir}")

    # Ensure logs subdirectory exists
    logs_dir = data_dir / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Logs directory ready at: {logs_dir}")
    except Exception as e:
        logger.error(f"Failed to create logs directory: {e}")

    # Initialize each data file
    files_created = 0

    # 1. config.json
    config_file = data_dir / "config.json"
    if init_data_file(config_file, get_default_config(), "config.json"):
        files_created += 1

    # 2. events.json
    events_file = data_dir / "events.json"
    if init_data_file(events_file, get_default_events(), "events.json"):
        files_created += 1

    # 3. quarantine.json
    quarantine_file = data_dir / "quarantine.json"
    if init_data_file(quarantine_file, get_default_quarantine(), "quarantine.json"):
        files_created += 1

    # 4. maintenance.json
    maintenance_file = data_dir / "maintenance.json"
    if init_data_file(maintenance_file, get_default_maintenance(), "maintenance.json"):
        files_created += 1

    if files_created > 0:
        logger.info(f"Initialization complete: {files_created} default file(s) created")
    else:
        logger.info("All data files already exist, no initialization needed")

    return data_dir


def reset_to_defaults(data_dir: Path = Path("/data")) -> None:
    """
    Reset all data files to defaults (WARNING: This will delete existing data!)

    Args:
        data_dir: Base data directory (default: /data)
    """
    logger.warning("Resetting all data files to defaults...")

    files = {
        "config.json": get_default_config(),
        "events.json": get_default_events(),
        "quarantine.json": get_default_quarantine(),
        "maintenance.json": get_default_maintenance()
    }

    for filename, default_data in files.items():
        file_path = data_dir / filename
        try:
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)
            logger.info(f"Reset {filename} to defaults")
        except Exception as e:
            logger.error(f"Failed to reset {filename}: {e}")

    logger.info("Reset to defaults complete")


if __name__ == "__main__":
    # For testing and manual initialization
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description='Initialize or reset Docker Auto-Heal data files'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all data files to defaults (WARNING: Deletes existing data!)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./data',
        help='Data directory path (default: ./data)'
    )

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if args.reset:
        confirm = input(f"WARNING: This will reset all data files in {data_dir} to defaults. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_to_defaults(data_dir)
            print("Reset complete!")
        else:
            print("Reset cancelled.")
    else:
        initialize_defaults(data_dir)
        print("Initialization complete!")

