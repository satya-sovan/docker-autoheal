# Container Details Storage - Complete Guide

## 📍 Storage Location

All container tracking data is stored in **JSON files** in the `/data` directory.

### Directory Structure

```
/data/
├── config.json              # Main configuration + selected/excluded containers
├── events.json              # Event history (restarts, quarantines, etc.)
├── restart_counts.json      # Restart timestamps per container
├── quarantine.json          # List of quarantined containers
├── maintenance.json         # Maintenance mode state
└── logs/                    # Application logs
    └── docker-autoheal.log
```

---

## 📄 What's Stored in Each File

### 1. `/data/config.json`

**Contains**: Main configuration + container selection lists + custom health checks

**What container data is stored**:
- ✅ **Selected containers** - Containers explicitly enabled for monitoring
- ✅ **Excluded containers** - Containers explicitly disabled from monitoring
- ✅ **Custom health checks** - Per-container health check configurations

**Example**:
```json
{
  "containers": {
    "selected": [
      "webapp",              // Container name (new approach)
      "myproject_database",  // Compose: project_service (new approach)
      "prod-api-v2"         // monitoring.id label (new approach)
    ],
    "excluded": [
      "pihole_pihole"
    ]
  },
  "custom_health_checks": {
    "webapp": {
      "container_name": "webapp",
      "check_type": "http",
      "http_endpoint": "http://localhost:8080/health",
      "interval_seconds": 30
    }
  }
}
```

**Identifier Used**: Now uses **stable identifiers** (names, compose service, or monitoring.id)

---

### 2. `/data/events.json`

**Contains**: Event history for all monitored containers

**What container data is stored**:
- ✅ Container name + stable ID
- ✅ Container ID (at time of event)
- ✅ Event type (restart, quarantine, health_check_failed)
- ✅ Timestamp
- ✅ Restart count
- ✅ Status (success/failure)
- ✅ Message

**Example**:
```json
[
  {
    "timestamp": "2025-10-31T10:30:00Z",
    "container_name": "webapp (myproject_webapp)",
    "container_id": "abc123def456",
    "event_type": "restart",
    "restart_count": 1,
    "status": "success",
    "message": "Restart successful: Container exited with code 1"
  },
  {
    "timestamp": "2025-10-31T11:00:00Z",
    "container_name": "database (prod-postgres)",
    "container_id": "xyz789uvw012",
    "event_type": "quarantine",
    "restart_count": 3,
    "status": "quarantined",
    "message": "Container quarantined: exceeded 3 restarts in 600s window"
  }
]
```

**Identifier Used**: Stores both **container name with stable_id** and **current container ID**

---

### 3. `/data/restart_counts.json`

**Contains**: Restart timestamps for each container (used for rate limiting)

**What container data is stored**:
- ✅ Stable identifier as key
- ✅ Array of restart timestamps (ISO format)

**Example**:
```json
{
  "myproject_webapp": [
    "2025-10-31T10:30:00.123456+00:00",
    "2025-10-31T10:35:00.654321+00:00",
    "2025-10-31T10:40:00.987654+00:00"
  ],
  "prod-api-v2": [
    "2025-10-31T11:00:00.111111+00:00"
  ]
}
```

**Identifier Used**: **Stable identifier** (persists across container recreations!)

**How it works**:
- System records timestamp on each restart
- Old timestamps outside the window are automatically cleaned up
- Used to enforce `max_restarts` within `max_restarts_window_seconds`

---

### 4. `/data/quarantine.json`

**Contains**: List of containers currently in quarantine

**What container data is stored**:
- ✅ Stable identifiers of quarantined containers

**Example**:
```json
[
  "failing-app",
  "myproject_buggy-service",
  "prod-unstable-api"
]
```

**Identifier Used**: **Stable identifier** (persists across container recreations!)

**How it works**:
- Container added when it exceeds `max_restarts`
- Remains quarantined even if container is recreated (same stable ID)
- Must be manually unquarantined via API

---

### 5. `/data/maintenance.json`

**Contains**: Maintenance mode state

**What's stored**:
- ✅ Maintenance mode enabled/disabled
- ✅ Start timestamp

**Example**:
```json
{
  "enabled": false,
  "start_time": null
}
```

**Not container-specific**, but affects all container monitoring.

---

## 🔑 Key Identifier System

### What Gets Stored as Keys?

The system now uses **stable identifiers** as keys in all storage:

**Priority Order** (automatic):
1. `monitoring.id` label → e.g., `"prod-api-v2"`
2. Compose project + service → e.g., `"myproject_webapp"`
3. Container name → e.g., `"webapp"`
4. Container ID (legacy fallback) → e.g., `"abc123def456..."`

### Why Stable Identifiers?

**Before** (Old System):
```json
{
  "restart_counts": {
    "abc123def456...": [...]  // ❌ Changes on recreation
  }
}
```

**After** (New System):
```json
{
  "restart_counts": {
    "myproject_webapp": [...]  // ✅ Persists across recreations!
  }
}
```

---

## 💾 Data Persistence

### When Data is Saved

Data is persisted to disk **immediately** on every change:

| Action | Files Updated |
|--------|---------------|
| Enable/disable monitoring | `config.json` |
| Container restart | `restart_counts.json`, `events.json` |
| Container quarantined | `quarantine.json`, `events.json` |
| Health check added | `config.json` |
| Event logged | `events.json` |
| Maintenance mode toggled | `maintenance.json` |

### Atomic Operations

All file writes are:
- ✅ **Thread-safe** (using locks)
- ✅ **Atomic** (write to temp, then rename)
- ✅ **Immediate** (no buffering delay)

---

## 📊 Data Relationships

### How Container Tracking Works

```
Container Created
    ↓
System extracts stable_id
    ↓
┌─────────────────────────────────────┐
│ config.json                         │
│ - Add to "selected" list            │
│ - Store stable_id                   │
└─────────────────────────────────────┘
    ↓
Container Monitored
    ↓
Container Fails/Restarts
    ↓
┌─────────────────────────────────────┐
│ restart_counts.json                 │
│ - Record timestamp                  │
│ - Key: stable_id                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ events.json                         │
│ - Log restart event                 │
│ - Store stable_id + current ID      │
└─────────────────────────────────────┘
    ↓
If exceeds max_restarts
    ↓
┌─────────────────────────────────────┐
│ quarantine.json                     │
│ - Add stable_id to list             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ events.json                         │
│ - Log quarantine event              │
└─────────────────────────────────────┘
```

---

## 🔄 Container Recreation Flow

**Before (Old System)**:
```
Container ID: abc123
  ↓
config.json: { "selected": ["abc123"] }
restart_counts.json: { "abc123": [...] }
  ↓
Container Recreated (new ID: xyz789)
  ↓
config.json: { "selected": ["abc123"] }  // ❌ Old ID!
restart_counts.json: { "abc123": [...] }  // ❌ Lost!
  ↓
Result: Monitoring LOST ❌
```

**After (New System)**:
```
Container: myproject_webapp_1 (ID: abc123)
  ↓
System extracts: stable_id = "myproject_webapp"
  ↓
config.json: { "selected": ["myproject_webapp"] }
restart_counts.json: { "myproject_webapp": [...] }
  ↓
Container Recreated: myproject_webapp_2 (ID: xyz789)
  ↓
System extracts: stable_id = "myproject_webapp"  // ✅ Same!
  ↓
config.json: { "selected": ["myproject_webapp"] }  // ✅ Match!
restart_counts.json: { "myproject_webapp": [...] }  // ✅ Found!
  ↓
Result: Monitoring PERSISTS ✅
```

---

## 🛠️ Accessing the Data

### Via API

```bash
# Get all monitored containers
curl http://localhost:3131/api/containers

# Get configuration (shows selected/excluded)
curl http://localhost:3131/api/config

# Get events
curl http://localhost:3131/api/events

# Get specific container details (includes restart count, quarantine status)
curl http://localhost:3131/api/containers/{container_id_or_name}
```

### Via Files (Direct Access)

```bash
# View configuration
cat /data/config.json | jq .

# View recent events
cat /data/events.json | jq '.[-10:]'

# View restart counts
cat /data/restart_counts.json | jq .

# View quarantined containers
cat /data/quarantine.json | jq .
```

### Via Docker Volume

If running in Docker, data is in a volume:

```bash
# List volumes
docker volume ls | grep autoheal

# Inspect volume
docker volume inspect docker-autoheal_data

# Access data
docker run --rm -v docker-autoheal_data:/data alpine cat /data/config.json
```

---

## 🔍 Example: Full Container Tracking

Let's trace a container through the system:

### 1. Container Created

```bash
docker run -d --name webapp --label autoheal=true nginx:latest
```

### 2. System Detection

- Container detected via Docker events
- Stable ID extracted: `"webapp"` (from container name)

### 3. Storage Created

**`/data/config.json`**:
```json
{
  "containers": {
    "selected": ["webapp"]  // Added here
  }
}
```

### 4. Container Fails and Restarts

**`/data/restart_counts.json`**:
```json
{
  "webapp": [
    "2025-10-31T10:00:00Z",
    "2025-10-31T10:05:00Z"
  ]
}
```

**`/data/events.json`**:
```json
[
  {
    "container_name": "webapp (webapp)",
    "event_type": "restart",
    "restart_count": 1,
    "status": "success"
  }
]
```

### 5. Container Recreated (Image Update)

```bash
docker stop webapp && docker rm webapp
docker run -d --name webapp --label autoheal=true nginx:1.26
```

### 6. System Reconnection

- New container ID: `xyz789...`
- Stable ID extracted: `"webapp"` (same!)
- Looks up in config: Found in `selected` ✅
- Looks up restart counts: Found `"webapp"` ✅
- **Monitoring continues seamlessly!**

---

## 📋 Data Cleanup

### Automatic Cleanup

- **Old restart timestamps**: Cleaned up when outside the window
- **Old events**: Kept up to `max_log_entries` (configurable)

### Manual Cleanup

```bash
# Clear restart history for a container
curl -X DELETE http://localhost:3131/api/containers/{container}/restart-history

# Unquarantine a container
curl -X POST http://localhost:3131/api/containers/{container}/unquarantine

# Clear all events
curl -X DELETE http://localhost:3131/api/events
```

---

## ✅ Summary

| What | Where | Key Type | Persists Across Recreation? |
|------|-------|----------|----------------------------|
| Selected/Excluded containers | `/data/config.json` | Stable ID | ✅ YES |
| Custom health checks | `/data/config.json` | Stable ID | ✅ YES |
| Restart timestamps | `/data/restart_counts.json` | Stable ID | ✅ YES |
| Quarantine list | `/data/quarantine.json` | Stable ID | ✅ YES |
| Event history | `/data/events.json` | Name + ID | ✅ YES (by name) |
| Maintenance mode | `/data/maintenance.json` | N/A | ✅ YES |

**Key Innovation**: Using **stable identifiers** (monitoring.id, compose service, or name) instead of ephemeral Docker IDs ensures all data persists across container recreations! 🎉

---

*Last Updated: 2025-10-31*  
*Version: 1.2.0*

