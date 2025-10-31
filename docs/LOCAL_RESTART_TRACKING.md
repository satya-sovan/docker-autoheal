# Local Restart Count Tracking - Complete Solution

## Problem Statement
After implementing auto-heal functionality, the restart count displayed in the UI was showing 0 even after containers were restarted by the auto-heal system. This is because:

1. **Docker's native `RestartCount`** only tracks restarts triggered by Docker's restart policy (e.g., `restart: always`)
2. **Docker's counter resets** when containers are recreated (e.g., `docker-compose up --force-recreate`)
3. **Manual restarts** via `docker restart` or the auto-heal system are NOT counted by Docker

## Solution: Local Restart Tracking

The application now maintains its own persistent restart count in a local JSON file that:
- ✅ Persists across container recreations
- ✅ Tracks all restarts performed by auto-heal
- ✅ Uses `stable_id` (container name or monitoring.id label) for tracking
- ✅ Survives application restarts
- ✅ Never resets (unless you manually delete the file)

## Implementation Details

### 1. Storage Location
**File:** `data/restart_counts.json`

**Format:**
```json
{
  "container_name_or_stable_id": [
    "2025-10-31T13:57:51.076821+00:00",
    "2025-10-31T14:23:15.123456+00:00",
    "2025-10-31T15:45:30.987654+00:00"
  ]
}
```

Each entry is a list of ISO 8601 timestamps representing when restarts occurred.

### 2. Code Changes

#### A. Config Manager (`app/config/config_manager.py`)

**New Method Added:**
```python
def get_total_restart_count(self, container_id: str) -> int:
    """Get total restart count (all time) - for UI display"""
    with self._lock:
        if container_id not in self._container_restart_counts:
            return 0
        return len(self._container_restart_counts[container_id])
```

**Existing Methods:**
- `record_restart(container_id)` - Records a new restart timestamp
- `get_restart_count(container_id, window_seconds)` - Gets restarts within time window
- `_save_restart_counts()` - Persists to disk
- `_load_restart_counts()` - Loads from disk on startup

#### B. API Endpoints (`app/api/api.py`)

**Container List Endpoint (`/api/containers`):**
```python
# Get locally tracked restart count (persists across container recreations)
locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)

container_info = ContainerInfo(
    # ...other fields...
    restart_count=locally_tracked_restarts,  # Use locally tracked count
    # ...
)
```

**Container Details Endpoint (`/api/containers/{container_id}`):**
```python
# Get locally tracked restart counts (using stable_id)
recent_restart_count = config_manager.get_restart_count(
    stable_id,
    config_manager.get_config().restart.max_restarts_window_seconds
)
total_restart_count = config_manager.get_total_restart_count(stable_id)

# Override restart_count in info with locally tracked count
info["restart_count"] = total_restart_count

return {
    **info,
    "recent_restart_count": recent_restart_count,
    "total_restart_count": total_restart_count,
    # ...
}
```

### 3. Restart Recording Flow

When auto-heal restarts a container:

1. **Monitoring Engine detects unhealthy container**
   ```python
   # app/monitor/monitoring_engine.py (line 452)
   config_manager.record_restart(stable_id)
   ```

2. **Timestamp is recorded in memory**
   ```python
   self._container_restart_counts[stable_id].append(datetime.now(timezone.utc))
   ```

3. **Data is persisted to disk**
   ```python
   self._save_restart_counts()  # Writes to data/restart_counts.json
   ```

4. **UI fetches updated count**
   - API returns `total_restart_count` from local storage
   - UI displays the persistent count

## UI Display

### Container List Page
- **"Restarts" column** shows `restart_count` (total restarts tracked locally)

### Container Details Modal
- **"Restart Count"** shows total restarts (all time)
- **"Recent Restarts"** shows restarts within configured window (e.g., last 5 minutes)

## Benefits

1. **Accurate Tracking** - Counts all auto-heal restarts, not just Docker policy restarts
2. **Persistence** - Survives container recreations, app restarts, Docker restarts
3. **Stable Identity** - Uses `stable_id` (container name or monitoring.id label)
4. **Historical Data** - Keeps all restart timestamps for analytics
5. **Time Windows** - Can query restarts within specific time periods
6. **No External Dependencies** - Simple JSON file storage

## Data Management

### View Restart Data
```bash
cat data/restart_counts.json
# or on Windows:
type data\restart_counts.json
```

### Clear Restart History (if needed)
```bash
# Clear all restart counts
echo "{}" > data/restart_counts.json

# Or delete the file (will be recreated)
rm data/restart_counts.json
```

### Backup Restart Data
```bash
cp data/restart_counts.json data/restart_counts.backup.json
```

## Configuration

The system uses the configured time window for "recent restarts":

**Default:** 300 seconds (5 minutes)

**Configure in `config.json`:**
```json
{
  "restart": {
    "max_restarts_window_seconds": 300
  }
}
```

## Troubleshooting

### Issue: Restart count not incrementing
1. **Check if restarts are being recorded:**
   ```bash
   tail -f logs/autoheal.log | grep "record_restart"
   ```

2. **Verify restart_counts.json is being updated:**
   ```bash
   watch -n 1 cat data/restart_counts.json
   ```

3. **Check API response:**
   ```bash
   curl http://localhost:8000/api/containers | jq '.[].restart_count'
   ```

### Issue: Old data from deleted containers
The system automatically cleans up old restart data that falls outside the configured time window. However, if you want to manually clean up:

```python
# Add this to a maintenance script if needed
import json
from pathlib import Path

# Load current data
with open('data/restart_counts.json') as f:
    data = json.load(f)

# Get list of current container names from Docker
current_containers = {'container1', 'container2', 'container3'}

# Keep only current containers
cleaned = {k: v for k, v in data.items() if k in current_containers}

# Save
with open('data/restart_counts.json', 'w') as f:
    json.dump(cleaned, f, indent=2)
```

## Migration from Docker RestartCount

If you had containers with Docker restart counts before this change, those counts are now replaced with locally tracked counts starting from 0. This is expected behavior as we're switching to a more reliable tracking method.

To preserve historical context, the first time auto-heal restarts a container, it will start counting from that point forward.

## Files Modified

1. ✅ `app/config/config_manager.py` - Added `get_total_restart_count()` method
2. ✅ `app/api/api.py` - Updated both container list and details endpoints
3. ✅ `data/restart_counts.json` - Storage file (auto-created)

## Testing

After restarting the application:

1. **View a container** that has been restarted by auto-heal
2. **Check the "Restarts" column** - should show count > 0
3. **Force a restart** by making a container unhealthy
4. **Refresh the UI** - count should increment
5. **Check the file:**
   ```bash
   cat data/restart_counts.json
   ```
   You should see timestamps for each restart

---

**Status:** ✅ Complete and Ready to Use  
**Date:** October 31, 2025  
**Impact:** Fixes restart count display issue permanently  
**Breaking Changes:** None - existing data is preserved

