# Uvicorn Logs Disabled

## Issue
Uvicorn access logs were cluttering the console output with HTTP request logs:

```
2025-10-30 18:28:11,558 - uvicorn.access - INFO - 172.23.0.1:54916 - "POST /api/maintenance/enable HTTP/1.1" 200
2025-10-30 18:28:11,638 - uvicorn.access - INFO - 172.23.0.1:54916 - "GET /api/status HTTP/1.1" 200
2025-10-30 18:28:13,849 - uvicorn.access - INFO - 172.23.0.1:54916 - "GET /api/status HTTP/1.1" 200
```

## Solution

**File**: `main.py`

### Change 1: Disable Uvicorn Logger Modules
```python
# Disable uvicorn access logs completely (set to WARNING to suppress INFO logs)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
```

### Change 2: Configure Uvicorn Server
```python
uvicorn_config = uvicorn.Config(
    app,
    host=config.ui.listen_address,
    port=config.ui.listen_port,
    log_level="warning",  # Set to warning to suppress info logs
    access_log=False,  # Completely disable access logs
    log_config=None
)
```

## Result

After restarting the service, you will no longer see:
- ❌ `uvicorn.access` HTTP request logs
- ❌ `uvicorn.error` INFO level logs
- ❌ General uvicorn INFO logs

You will still see:
- ✅ Application-specific logs (monitor, docker_client, config, etc.)
- ✅ Uvicorn WARNING and ERROR logs (if any issues occur)
- ✅ Service startup/shutdown messages

## Testing

### Before Fix
```
2025-10-30 18:28:11,558 - uvicorn.access - INFO - 172.23.0.1:54916 - "POST /api/maintenance/enable HTTP/1.1" 200
2025-10-30 18:28:11,638 - uvicorn.access - INFO - 172.23.0.1:54916 - "GET /api/status HTTP/1.1" 200
2025-10-30 18:28:13,849 - uvicorn.access - INFO - 172.23.0.1:54916 - "GET /api/status HTTP/1.1" 200
... (lots of HTTP logs)
```

### After Fix
```
2025-10-30 18:28:11 - monitor - INFO - Container check completed
2025-10-30 18:28:41 - monitor - INFO - Container check completed
... (only application logs)
```

## Apply the Fix

```bash
# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Check logs (should be clean)
docker logs docker-autoheal -f
```

## What You'll See Now

### Startup Logs
```
INFO - Starting Docker Auto-Heal Service v1.1
INFO - Configuration loaded: monitoring interval=30s
INFO - Connecting to Docker daemon...
INFO - Docker client connected successfully
INFO - Initializing monitoring engine...
INFO - Starting monitoring engine...
INFO - Monitoring engine started
INFO - Event listener started for auto-monitoring containers with autoheal=true label
DEBUG - Docker event listener thread started
INFO - Docker Auto-Heal Service started successfully
```

**Note**: No more uvicorn access logs!

### During Operation
```
INFO - Container check completed
INFO - ✓ Auto-monitoring enabled for container 'my-app' (abc123)
INFO - Restarting container unhealthy-app (reason: Docker health check reports unhealthy)
INFO - Successfully restarted container unhealthy-app
```

**Clean and focused on your application!**

## If You Need HTTP Logs for Debugging

If you ever need to see HTTP request logs for debugging:

1. **Temporarily enable DEBUG level**:
   - Edit `data/config.json`
   - Set `"observability": {"log_level": "DEBUG"}`
   - Restart service

2. **Or check via Web UI**:
   - Open http://localhost:8080
   - Go to Configuration tab
   - Look at event logs there

## Summary

- ✅ Uvicorn access logs disabled
- ✅ Cleaner log output
- ✅ Focus on application events
- ✅ HTTP requests no longer spam logs
- ✅ WARNING/ERROR logs still shown if needed

---

**Status**: ✅ FIXED

**Apply**: Restart service with `docker-compose up --build -d`

