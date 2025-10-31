# Container Details Storage - Quick Visual Guide

## 📁 Storage Location: `/data/` Directory

```
📂 /data/
│
├── 📄 config.json              ← Main configuration
│   ├── Selected containers     ← Containers to monitor
│   ├── Excluded containers     ← Containers to ignore
│   ├── Custom health checks    ← Per-container health configs
│   └── All settings            ← Monitoring intervals, restart policies, etc.
│
├── 📄 events.json              ← Event history
│   └── Restart events          ← Timestamps, success/failure, reasons
│       Quarantine events       ← When containers quarantined
│       Health check failures   ← Health check events
│       Auto-monitor events     ← When containers auto-added
│
├── 📄 restart_counts.json      ← Restart tracking
│   └── Per-container timestamps ← Used for rate limiting
│       (cleaned up automatically)
│
├── 📄 quarantine.json          ← Quarantined containers
│   └── List of stable IDs      ← Containers that exceeded restart limits
│
├── 📄 maintenance.json         ← Maintenance mode
│   └── Enabled/disabled state  ← Pauses all monitoring when enabled
│
└── 📂 logs/
    └── 📄 docker-autoheal.log  ← Application logs
```

---

## 🔑 What Keys Are Used?

### OLD System (Container IDs) ❌
```json
{
  "selected": ["abc123def456789..."],
  "restart_counts": {
    "abc123def456789...": [...]
  }
}
```
**Problem**: ID changes on recreation → Data lost!

### NEW System (Stable Identifiers) ✅
```json
{
  "selected": ["myproject_webapp"],
  "restart_counts": {
    "myproject_webapp": [...]
  }
}
```
**Solution**: Stable ID persists → Data preserved!

---

## 🎯 Stable Identifier Priority

```
1️⃣ monitoring.id label
   Example: "prod-api-v2"
   ✅ Best for production
   ✅ Survives renames
   
2️⃣ compose_project_service
   Example: "myproject_webapp"
   ✅ Auto-generated names
   ✅ Multi-environment safe
   
3️⃣ container_name
   Example: "webapp"
   ✅ Explicit names
   ✅ Simple approach
   
4️⃣ container_id (fallback)
   Example: "abc123def456..."
   ⚠️ Backwards compatibility only
```

---

## 📊 Example: Container Lifecycle

```
┌─────────────────────────────────────────────┐
│ 1. Container Created                        │
│    docker run --name webapp --label         │
│    autoheal=true nginx:1.25                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 2. System Detects                           │
│    Stable ID: "webapp"                      │
│    Container ID: "abc123..."                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. Stored in config.json                    │
│    { "selected": ["webapp"] }               │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. Container Fails & Restarts (2x)          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 5. Stored in restart_counts.json            │
│    {                                        │
│      "webapp": [                            │
│        "2025-10-31T10:00:00Z",             │
│        "2025-10-31T10:05:00Z"              │
│      ]                                      │
│    }                                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 6. Stored in events.json                    │
│    [                                        │
│      {                                      │
│        "container_name": "webapp",         │
│        "event_type": "restart",            │
│        "status": "success"                 │
│      }                                      │
│    ]                                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 7. Container RECREATED (Image Update)       │
│    docker stop webapp && docker rm webapp   │
│    docker run --name webapp --label         │
│    autoheal=true nginx:1.26                 │
│    NEW Container ID: "xyz789..."            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 8. System Detects SAME Stable ID            │
│    Stable ID: "webapp" ✅ (matches!)        │
│    Container ID: "xyz789..." (different)    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 9. Finds in config.json                     │
│    { "selected": ["webapp"] } ✅ Found!     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 10. Finds restart history                   │
│     { "webapp": [...] } ✅ Found!           │
│     Restart count: 2 (preserved!)           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ ✅ MONITORING CONTINUES SEAMLESSLY!         │
│    All history preserved!                   │
└─────────────────────────────────────────────┘
```

---

## 💾 Data Examples

### config.json (Actual Format)
```json
{
  "containers": {
    "selected": [
      "webapp",                    // ← Simple name
      "myproject_database",        // ← Compose: project_service
      "prod-api-v2"               // ← monitoring.id label
    ],
    "excluded": [
      "pihole_pihole"
    ]
  },
  "custom_health_checks": {
    "webapp": {
      "container_name": "webapp",
      "check_type": "http",
      "http_endpoint": "http://localhost:8080/health"
    }
  }
}
```

### restart_counts.json (Actual Format)
```json
{
  "webapp": [
    "2025-10-31T10:00:00.123456+00:00",
    "2025-10-31T10:05:00.654321+00:00"
  ],
  "myproject_database": [
    "2025-10-31T09:30:00.111111+00:00"
  ]
}
```

### quarantine.json (Actual Format)
```json
[
  "failing-app",
  "myproject_buggy-service"
]
```

### events.json (Actual Format)
```json
[
  {
    "timestamp": "2025-10-31T10:30:00Z",
    "container_name": "webapp (webapp)",
    "container_id": "abc123def456",
    "event_type": "restart",
    "restart_count": 1,
    "status": "success",
    "message": "Restart successful: Container exited with code 1"
  }
]
```

---

## 🔍 Quick Access

### View Current Data

```bash
# View all monitored containers
cat /data/config.json | jq '.containers.selected'

# View restart counts
cat /data/restart_counts.json | jq .

# View quarantined containers
cat /data/quarantine.json | jq .

# View recent events (last 5)
cat /data/events.json | jq '.[-5:]'
```

### Via API

```bash
# Get configuration
curl http://localhost:3131/api/config

# Get all containers with status
curl http://localhost:3131/api/containers

# Get specific container details
curl http://localhost:3131/api/containers/webapp

# Get events
curl http://localhost:3131/api/events
```

---

## ✅ Key Takeaways

1. **Everything stored in `/data/` directory**
   - JSON files for all tracking data
   - Persistent across restarts

2. **Stable identifiers as keys**
   - Uses names, compose services, or monitoring.id
   - NOT ephemeral Docker IDs

3. **Data persists across recreation**
   - ✅ Selected/excluded list
   - ✅ Restart counts
   - ✅ Quarantine status
   - ✅ Custom health checks
   - ✅ Event history

4. **Immediate persistence**
   - Every change saved to disk immediately
   - Thread-safe operations
   - No data loss

5. **Easy to inspect**
   - Human-readable JSON
   - Can be edited manually (if needed)
   - Can be backed up easily

---

## 📚 See Also

- [Full Storage Guide](./CONTAINER_STORAGE_GUIDE.md) - Complete details
- [Container ID Bug Fix](./CONTAINER_ID_BUG_FIX.md) - Why stable IDs matter
- [Limitations Resolved](./CONTAINER_ID_LIMITATIONS_RESOLVED.md) - How edge cases are handled

---

**Location**: `/data/`  
**Format**: JSON  
**Keys**: Stable Identifiers  
**Persists**: ✅ YES (across recreations!)

*Last Updated: 2025-10-31*

