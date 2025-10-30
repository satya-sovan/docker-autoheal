# Data Storage Architecture

## Overview

The Docker Auto-Heal service uses **file-based persistence** for all runtime data. All configuration, events, restart history, quarantine lists, and logs are automatically saved to the `/data` directory and persist across container restarts.

---

## 📦 Storage Locations

### 1. **Configuration (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/config.json`  
**Persistence**: ✅ Survives container restart

```python
class ConfigManager:
    def __init__(self):
        self._config = AutoHealConfig()  # In-memory config
```

**What's Stored**:
- Monitor settings (interval, label filters)
- Restart policies (mode, cooldown, backoff)
- Health check settings
- Quarantine thresholds
- Observability settings (log level)
- UI settings (refresh rate, max log entries)

**Access Methods**:
- `config_manager.get_config()` - Get current config
- `config_manager.update_config()` - Update config
- `config_manager.export_config()` - Export as JSON
- `config_manager.import_config()` - Import from JSON

**Persistence Options**:
- Manual export via API: `GET /api/config/export`
- Manual import via API: `POST /api/config/import`
- Downloads to: User's browser (client-side)

---

### 2. **Events Log (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/events.json`  
**Persistence**: ✅ Survives container restart  
**Size Limit**: Configurable (default: 1000 entries)

```python
class ConfigManager:
    def __init__(self):
        self._event_log: List[AutoHealEvent] = []  # In-memory events
```

**What's Stored**:
- Timestamp (UTC timezone-aware)
- Container ID and name
- Event type (restart, quarantine, health_check)
- Restart count
- Status (success, failure, quarantined)
- Message description

**Access Methods**:
- `config_manager.add_event(event)` - Add new event
- `config_manager.get_events(limit)` - Get recent events
- API: `GET /api/events?limit=100`

**Size Management**:
- Automatically truncates to keep only the most recent `max_log_entries`
- Configured via: `config.ui.max_log_entries` (default: 1000)

---

### 3. **Restart History (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/restart_counts.json`  
**Persistence**: ✅ Survives container restart

```python
class ConfigManager:
    def __init__(self):
        self._container_restart_counts: Dict[str, List[datetime]] = {}
```

**What's Stored**:
- Container ID → List of restart timestamps (UTC)
- Used for quarantine threshold calculations
- Automatically cleans old timestamps outside the monitoring window

**Access Methods**:
- `config_manager.record_restart(container_id)` - Record restart
- `config_manager.get_restart_count(container_id, window_seconds)` - Get count

---

### 4. **Quarantine List (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/quarantine.json`  
**Persistence**: ✅ Survives container restart

```python
class ConfigManager:
    def __init__(self):
        self._quarantined_containers: set = set()
```

**What's Stored**:
- Set of container IDs that are quarantined
- Quarantined containers are excluded from auto-healing

**Access Methods**:
- `config_manager.quarantine_container(container_id)` - Add to quarantine
- `config_manager.unquarantine_container(container_id)` - Remove from quarantine
- `config_manager.is_quarantined(container_id)` - Check status
- API: `POST /api/containers/{container_id}/unquarantine`

---

### 5. **Custom Health Checks (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/config.json` (stored with main config)  
**Persistence**: ✅ Survives container restart

```python
class ConfigManager:
    def __init__(self):
        self._custom_health_checks: Dict[str, HealthCheckConfig] = {}
```

**What's Stored**:
- Container-specific health check configurations
- Endpoint URLs, intervals, timeouts, expected responses

**Access Methods**:
- `config_manager.add_custom_health_check(config)` - Add custom check
- `config_manager.get_custom_health_check(container_id)` - Get config
- `config_manager.remove_custom_health_check(container_id)` - Remove config

---

### 6. **Maintenance Mode State (`config.py`)**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/maintenance.json`  
**Persistence**: ✅ Survives container restart

```python
class ConfigManager:
    def __init__(self):
        self._maintenance_mode: bool = False
        self._maintenance_start_time: Optional[datetime] = None
```

**What's Stored**:
- Boolean flag for maintenance mode status
- Start timestamp (UTC timezone-aware)

**Access Methods**:
- `config_manager.enable_maintenance_mode()` - Enable mode
- `config_manager.disable_maintenance_mode()` - Disable mode
- `config_manager.is_maintenance_mode()` - Check status
- API: `POST /api/maintenance/enable` and `/api/maintenance/disable`

---

### 7. **Application Logs**

**Storage Type**: File-based (Persistent)  
**Location**: `/data/logs/autoheal.log` (inside container)  
**Host Mount**: `./data/logs/autoheal.log` (on host system)  
**Persistence**: ✅ Survives container restart

**Configuration** (`main.py`):
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console output
        logging.FileHandler('autoheal.log')  # File output
    ]
)
```

**What's Logged**:
- Service startup/shutdown
- Docker connection status
- Container health check results
- Restart attempts and results
- Quarantine actions
- Configuration changes
- API requests (when log level is DEBUG)
- Errors and warnings

**Log Levels**:
- `DEBUG`: Detailed information + HTTP access logs
- `INFO`: General operational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical failures

**Access Methods**:
- View in container: `docker exec docker-autoheal cat /data/logs/autoheal.log`
- View on host: `cat ./data/logs/autoheal.log`
- View with Docker: `docker logs docker-autoheal` (stdout only)
- Change level: Via UI Config page → Observability Settings

**Volume Mount** (`docker-compose.yml`):
```yaml
volumes:
  - ./data:/data  # Persist all data including logs to host
```

---

### 8. **Prometheus Metrics**

**Storage Type**: In-Memory (Volatile)  
**Location**: Prometheus client library metrics  
**Endpoint**: `http://localhost:9090/metrics`  
**Persistence**: ❌ Resets on restart

**Metrics Available** (`main.py`):
```python
container_restarts = Counter('autoheal_container_restarts_total', 'Total container restarts', ['container_name'])
containers_monitored = Gauge('autoheal_containers_monitored', 'Number of containers being monitored')
containers_quarantined = Gauge('autoheal_containers_quarantined', 'Number of quarantined containers')
health_checks_total = Counter('autoheal_health_checks_total', 'Total health checks performed')
health_checks_failed = Counter('autoheal_health_checks_failed', 'Failed health checks', ['container_name'])
```

---

## 🗂️ File System Structure

```
/app/                           (Container working directory)
├── *.py                       (Python source files)
├── static/                    (React UI build)
│   ├── index.html
│   ├── assets/
│   └── ...
└── requirements.txt

/data/                         (Persistent data directory)
├── config.json                (Configuration + custom health checks)
├── events.json                (Event log history)
├── restart_counts.json        (Container restart timestamps)
├── quarantine.json            (Quarantined container list)
├── maintenance.json           (Maintenance mode state)
└── logs/
    └── autoheal.log          (Application logs)

/var/run/docker.sock           (Docker socket - mounted read-only)
```

**Host Mapping** (`docker-compose.yml`):
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # Docker API access
  - ./data:/data                                    # All persistent data
```

---

## 💾 Data Persistence Summary

| Data Type | Storage | Persistent | Location | Notes |
|-----------|---------|------------|----------|-------|
| **Configuration** | File | ✅ Yes | `/data/config.json` | Auto-saved on every change |
| **Events Log** | File | ✅ Yes | `/data/events.json` | Auto-saved, limited to 1000 entries |
| **Restart History** | File | ✅ Yes | `/data/restart_counts.json` | Auto-saved, auto-cleaned |
| **Quarantine List** | File | ✅ Yes | `/data/quarantine.json` | Auto-saved |
| **Custom Health Checks** | File | ✅ Yes | `/data/config.json` | Stored with main config |
| **Maintenance Mode** | File | ✅ Yes | `/data/maintenance.json` | Auto-saved |
| **Application Logs** | File | ✅ Yes | `/data/logs/autoheal.log` | Continuously written |
| **Prometheus Metrics** | In-Memory | ❌ No | Prometheus client | External scraping needed |

---

## 🔄 Data Lifecycle

### On Container Start
1. `ConfigManager` loads all data from `/data` directory
2. Configuration restored from `config.json` (or defaults if not found)
3. Event log restored from `events.json`
4. Restart history restored from `restart_counts.json`
5. Quarantine list restored from `quarantine.json`
6. Maintenance mode state restored from `maintenance.json`
7. Application logs continue in `logs/autoheal.log`

### During Runtime
1. Configuration changes automatically saved to `config.json`
2. Events automatically saved to `events.json` (FIFO with size limit)
3. Restart timestamps automatically saved to `restart_counts.json`
4. Quarantine changes automatically saved to `quarantine.json`
5. Maintenance mode changes automatically saved to `maintenance.json`
6. Logs continuously written to `logs/autoheal.log`

### On Container Stop/Restart
1. All data is **preserved** in `/data` directory
2. On restart, all previous state is automatically restored
3. Configuration, events, restart counts, and quarantine list persist
4. Maintenance mode state is preserved
5. Application logs accumulate over time

---

## 📤 Export/Import Options

### Configuration Export
- **API**: `GET /api/config/export`
- **UI**: Config page → Export button
- **Format**: JSON file
- **Includes**: All config + custom health checks
- **Filename**: `autoheal-config-YYYYMMDD-HHMMSS.json`

### Configuration Import
- **API**: `POST /api/config/import` (with file upload)
- **UI**: Config page → Import button
- **Format**: JSON file
- **Action**: Replaces current in-memory config

---

## 🚀 Recommendations

### For Production Use

1. **Data Persistence**:
   - **REQUIRED**: Mount `./data:/data` volume for all data persistence
   - All configuration, events, and logs are automatically saved
   - No manual export/import needed for normal restarts

2. **Backup Strategy**:
   - Regularly backup the entire `./data` directory
   - Contains all configuration, events, restart history, and logs
   - Simple file-based backup - no database dumps needed

3. **Log Management**:
   - Logs accumulate in `./data/logs/autoheal.log`
   - Implement log rotation (external tool like logrotate)
   - Consider centralized logging (ELK, Splunk, etc.) for long-term storage

4. **Metrics Monitoring**:
   - Set up Prometheus to scrape `http://localhost:9090/metrics`
   - Configure alerting on quarantine/restart metrics
   - Metrics will persist in Prometheus time-series DB

5. **Volume Management**:
   - Ensure adequate disk space for `/data` directory
   - Monitor log file growth
   - Event log auto-limits to 1000 entries

### Quick Backup Script

```bash
# Backup entire data directory
tar -czf backup-data-$(date +%Y%m%d-%H%M%S).tar.gz ./data/

# Or backup specific files
cp -r ./data ./backup/data-$(date +%Y%m%d)/
```

### Restore After Data Loss

```bash
# Stop container
docker-compose down

# Restore data directory
tar -xzf backup-data-20251030-120000.tar.gz

# Start container (automatically loads all data)
docker-compose up -d
```

---

## 🔍 Viewing Data

### Configuration
```bash
# Via API
curl http://localhost:8080/api/status

# Via UI
Open: http://localhost:8080 → Config page
```

### Events
```bash
# Via API
curl http://localhost:8080/api/events?limit=100

# Via UI
Open: http://localhost:8080 → Events page
```

### Logs
```bash
# Container stdout/stderr
docker logs docker-autoheal

# Log file (if volume mounted)
tail -f ./data/logs/autoheal.log

# Inside container
docker exec docker-autoheal tail -f /data/logs/autoheal.log

# View persisted JSON data
cat ./data/config.json
cat ./data/events.json
cat ./data/quarantine.json
```

### Metrics
```bash
# Prometheus format
curl http://localhost:9090/metrics
```

---

## ⚠️ Important Notes

1. **File-Based Persistence**: All data is automatically saved to `/data` directory
2. **Automatic Restoration**: All state is restored on container restart 
3. **Volume Mount Required**: Mount `./data:/data` for persistence across container recreations
4. **Thread-Safe**: All file operations use locks for concurrent access
5. **Auto-Cleanup**: Old restart timestamps are automatically pruned and saved
6. **Size Limits**: Event log has configurable size limit (default: 1000)
7. **Backup-Friendly**: Simple JSON files - easy to backup and restore
8. **No Database**: Uses JSON files for simplicity and reliability

