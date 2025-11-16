"""
Unit tests for configuration initialization
Tests the automatic creation of default configuration files
"""

import json
import tempfile
import shutil
from pathlib import Path
import pytest

from app.config.init_defaults import (
    initialize_defaults,
    reset_to_defaults,
    get_default_config,
    get_default_events,
    get_default_quarantine,
    get_default_maintenance
)


class TestInitDefaults:
    """Test configuration initialization"""

    def setup_method(self):
        """Create a temporary directory for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temporary directory after each test"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialize_creates_all_files(self):
        """Test that initialize_defaults creates all required files"""
        initialize_defaults(self.temp_dir)

        # Check all files were created
        assert (self.temp_dir / "config.json").exists()
        assert (self.temp_dir / "events.json").exists()
        assert (self.temp_dir / "quarantine.json").exists()
        assert (self.temp_dir / "maintenance.json").exists()
        assert (self.temp_dir / "logs").exists()
        assert (self.temp_dir / "logs").is_dir()

    def test_initialize_does_not_overwrite(self):
        """Test that initialize_defaults doesn't overwrite existing files"""
        config_file = self.temp_dir / "config.json"

        # Create a custom config
        custom_data = {"test": "custom_value"}
        with open(config_file, 'w') as f:
            json.dump(custom_data, f)

        # Run initialization
        initialize_defaults(self.temp_dir)

        # Verify custom config was not overwritten
        with open(config_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == custom_data

    def test_default_config_structure(self):
        """Test that default config has all required fields"""
        config = get_default_config()

        # Check top-level keys
        assert "monitor" in config
        assert "containers" in config
        assert "restart" in config
        assert "filters" in config
        assert "ui" in config
        assert "alerts" in config
        assert "observability" in config
        assert "uptime_kuma" in config

        # Check monitor settings
        assert config["monitor"]["interval_seconds"] == 30
        assert config["monitor"]["label_key"] == "autoheal"
        assert config["monitor"]["label_value"] == "true"
        assert config["monitor"]["include_all"] is False

        # Check restart settings
        assert config["restart"]["mode"] == "on-failure"
        assert config["restart"]["max_restarts"] == 3
        assert config["restart"]["cooldown_seconds"] == 60

        # Check UI settings
        assert config["ui"]["enable"] is True
        assert config["ui"]["listen_port"] == 3131

        # Check observability settings
        assert config["observability"]["prometheus_enabled"] is True
        assert config["observability"]["metrics_port"] == 9090
        assert config["observability"]["log_level"] == "INFO"

    def test_default_events_is_empty_list(self):
        """Test that default events is an empty list"""
        events = get_default_events()
        assert events == []
        assert isinstance(events, list)

    def test_default_quarantine_is_empty_list(self):
        """Test that default quarantine is an empty list"""
        quarantine = get_default_quarantine()
        assert quarantine == []
        assert isinstance(quarantine, list)

    def test_default_maintenance_structure(self):
        """Test that default maintenance has correct structure"""
        maintenance = get_default_maintenance()
        assert "enabled" in maintenance
        assert "start_time" in maintenance
        assert maintenance["enabled"] is False
        assert maintenance["start_time"] is None

    def test_config_json_is_valid(self):
        """Test that created config.json is valid JSON"""
        initialize_defaults(self.temp_dir)
        config_file = self.temp_dir / "config.json"

        with open(config_file, 'r') as f:
            data = json.load(f)  # Should not raise exception

        assert isinstance(data, dict)

    def test_events_json_is_valid(self):
        """Test that created events.json is valid JSON"""
        initialize_defaults(self.temp_dir)
        events_file = self.temp_dir / "events.json"

        with open(events_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list)

    def test_reset_to_defaults(self):
        """Test that reset_to_defaults overwrites existing files"""
        # Create initial config
        initialize_defaults(self.temp_dir)

        # Modify config
        config_file = self.temp_dir / "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        config["monitor"]["interval_seconds"] = 99
        with open(config_file, 'w') as f:
            json.dump(config, f)

        # Reset to defaults
        reset_to_defaults(self.temp_dir)

        # Verify config was reset
        with open(config_file, 'r') as f:
            config = json.load(f)
        assert config["monitor"]["interval_seconds"] == 30

    def test_logs_directory_created(self):
        """Test that logs subdirectory is created"""
        initialize_defaults(self.temp_dir)
        logs_dir = self.temp_dir / "logs"

        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_creates_nested_directories(self):
        """Test that initialization creates nested directories if needed"""
        nested_dir = self.temp_dir / "nested" / "path"
        initialize_defaults(nested_dir)

        assert nested_dir.exists()
        assert (nested_dir / "config.json").exists()

    def test_json_formatting(self):
        """Test that JSON files are properly formatted (indented)"""
        initialize_defaults(self.temp_dir)
        config_file = self.temp_dir / "config.json"

        with open(config_file, 'r') as f:
            content = f.read()

        # Check that JSON is indented (not minified)
        assert "\n" in content  # Has newlines
        assert "  " in content  # Has indentation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

