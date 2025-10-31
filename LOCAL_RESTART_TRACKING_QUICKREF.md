# Local Restart Tracking - Quick Reference

## ✅ What Changed

**Before:** UI showed Docker's native RestartCount (always 0 for manual/auto-heal restarts)  
**After:** UI shows locally tracked restart count (persists forever, never resets)

## 📂 Where Data is Stored

**File:** `data/restart_counts.json`

**Example:**
```json
{
  "nginx-proxy": [
    "2025-10-31T13:57:51.076821+00:00",
    "2025-10-31T14:23:15.123456+00:00"
  ],
  "redis-cache": [
    "2025-10-31T15:45:30.987654+00:00"
  ]
}
```

## 🔧 How It Works

1. **Auto-heal restarts a container** → Timestamp added to `restart_counts.json`
2. **UI requests container list** → API reads from `restart_counts.json`
3. **Display shows count** → Number of timestamps = restart count

## 🎯 What You'll See

### Container List
- **"Restarts" column** = Total restarts tracked locally (all time)

### Container Details Modal
- **"Restart Count"** = Total restarts (all time)
- **"Recent Restarts"** = Restarts in last X seconds (configurable)

## 🚀 To Apply Changes

Restart the docker-autoheal service:

```bash
# Docker Compose
docker-compose restart

# Or rebuild
docker-compose up -d --build

# Python (direct)
# Ctrl+C to stop, then:
python run.py
```

## 🧪 Testing

1. **Check current data:**
   ```bash
   type data\restart_counts.json
   ```

2. **Trigger a restart:**
   - Make a container unhealthy
   - Wait for auto-heal to restart it

3. **Verify count incremented:**
   - Refresh UI
   - Check "Restarts" column
   - Check the JSON file again

4. **Verify persistence:**
   - Restart the auto-heal app
   - Counts should remain the same

## 📊 View Restart Data

```bash
# Windows
type data\restart_counts.json

# Linux/Mac
cat data/restart_counts.json

# Pretty print
python -m json.tool data\restart_counts.json
```

## 🔄 Reset Counts (if needed)

```bash
# Clear all restart counts
echo {} > data\restart_counts.json

# Or delete (will be auto-created)
del data\restart_counts.json
```

## 🐛 Troubleshooting

**Problem:** Count still shows 0  
**Solution:** 
1. Check if container has been restarted by auto-heal (not manually)
2. Verify `data/restart_counts.json` exists and has entries
3. Restart the auto-heal service to load changes

**Problem:** Count not incrementing  
**Solution:**
1. Check logs: `type logs\autoheal.log | findstr restart`
2. Verify container name/stable_id matches JSON file
3. Ensure auto-heal is actually restarting (not just detecting)

**Problem:** Wrong container name in JSON  
**Solution:**
The system uses `stable_id` which can be:
- Container name
- `monitoring.id` label
- `com.docker.compose.service` label

Check container labels to see which ID is being used.

## 📋 Files Changed

✅ `app/config/config_manager.py` - Added `get_total_restart_count()`  
✅ `app/api/api.py` - Use local counts instead of Docker's  
✅ `data/restart_counts.json` - Storage file (auto-managed)

## ✨ Benefits

- ✅ **Never resets** - Survives container recreations
- ✅ **Accurate** - Tracks all auto-heal restarts
- ✅ **Persistent** - Stored on disk
- ✅ **Simple** - Just a JSON file
- ✅ **Historical** - Keeps all timestamps

---

**Ready to use!** Just restart the service and restart counts will be tracked locally.

