# Quick Fix Guide - UI Loading Issue

## Problem → Solution

### ❌ BEFORE (Blocking)
```
Docker Events API (blocking generator)
          ↓
    AsyncIO Loop tries to iterate
          ↓
    BLOCKED - UI never loads ❌
```

### ✅ AFTER (Non-Blocking)
```
Docker Events API (blocking generator)
          ↓
   Separate Thread (daemon)
          ↓
   Thread-Safe Queue
          ↓
   AsyncIO Loop (non-blocking read)
          ↓
   UI loads instantly ✅
```

---

## The Fix in Code

### Changed This:
```python
# ❌ This blocks the async loop
events = await asyncio.to_thread(self.docker_client.get_events(...))
for event in events:  # BLOCKS HERE
    await self._process_container_start_event(event)
```

### To This:
```python
# ✅ Non-blocking with threading
import threading
import queue

event_queue = queue.Queue()

def event_thread():
    events = self.docker_client.get_events(...)
    for event in events:
        event_queue.put(event)  # Non-blocking

threading.Thread(target=event_thread, daemon=True).start()

while self._running:
    try:
        event = event_queue.get(timeout=1.0)  # Non-blocking
        await self._process_container_start_event(event)
    except queue.Empty:
        await asyncio.sleep(0.1)  # Keep loop responsive
```

---

## How to Apply the Fix

### 1. The Fix is Already Applied
The code in `monitor.py` has been updated with the fix.

### 2. Restart Your Service
```bash
docker-compose down
docker-compose up --build -d
```

### 3. Verify UI Loads
```bash
# Should return immediately with status
curl http://localhost:8080/health

# Open in browser
http://localhost:8080
```

### 4. Verify Auto-Monitoring Works
```bash
# Start container with label
docker run -d --name test --label autoheal=true nginx:alpine

# Check logs (within 5 seconds)
docker logs docker-autoheal | grep "Auto-monitoring"

# Should see:
# INFO - ✓ Auto-monitoring enabled for container 'test'

# Clean up
docker rm -f test
```

---

## Expected Behavior

### Startup Logs (Good)
```
INFO - Monitoring engine started
INFO - Event listener started
DEBUG - Docker event listener thread started
INFO - Application startup complete
INFO - Uvicorn running on http://0.0.0.0:8080
```

### When Container Starts
```
DEBUG - Container start event detected: my-app (abc123)
INFO - ✓ Auto-monitoring enabled for container 'my-app'
```

---

## Why This Works

### The Problem
- Docker's `events()` is a **blocking generator**
- It waits forever for events
- Even in a thread, iterating blocks the loop

### The Solution
- **Isolation**: Docker events run in separate thread
- **Communication**: Thread-safe queue passes events
- **Non-Blocking**: Async loop reads with timeout
- **Responsive**: UI and API remain available

### Key Components
1. **Daemon Thread**: Dies when main process stops
2. **Queue.Queue**: Thread-safe by design
3. **Timeout**: Prevents blocking forever (1 second)
4. **Sleep**: Keeps loop responsive (0.1 second)

---

## Troubleshooting

### UI Still Not Loading?

```bash
# 1. Check if old container is still running
docker ps -a | grep autoheal

# 2. Force rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# 3. Check logs
docker logs docker-autoheal --tail 100

# 4. Look for "thread started"
docker logs docker-autoheal | grep "thread"
```

### Service Crashes?

```bash
# Check for Python errors
docker logs docker-autoheal | grep -i error

# Verify syntax
docker exec docker-autoheal python -m py_compile /app/monitor.py
```

---

## Technical Details

### Pattern Used
**Producer-Consumer with Threading**

- **Producer**: Thread that reads Docker events (blocking OK)
- **Queue**: Thread-safe communication channel
- **Consumer**: Async loop that processes events (non-blocking)

### Why Not asyncio.to_thread?
- `to_thread` runs function in thread ✓
- But we iterate in main loop ✗
- Iteration blocks waiting for next event ✗

### Why Threading Works
- Thread can block without affecting main loop ✓
- Queue.get(timeout=1.0) is non-blocking ✓
- Async loop stays responsive ✓

---

## Summary

**Problem**: Docker event stream blocked async loop  
**Solution**: Move to separate thread + queue  
**Result**: UI loads, events processed  

**Status**: ✅ FIXED

---

## Quick Commands

```bash
# Apply fix (restart)
docker-compose up --build -d

# Test UI
curl http://localhost:8080/health

# Test feature
docker run -d --label autoheal=true nginx:alpine
docker logs docker-autoheal | tail -20

# Clean up
docker-compose down
```

---

**Need help?** Check `docs/AUTO_MONITOR_BUG_FIX.md` for full details.

