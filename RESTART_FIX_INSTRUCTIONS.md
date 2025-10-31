# Restart Count Fix - Action Items

## ✅ FIXED

The issue with wrong restart count numbers in the UI has been fixed!

### What Was Changed

**File:** `app/docker_client/docker_client_wrapper.py` (line 132)

The restart count is now correctly read from Docker's container State object:
```python
"restart_count": attrs.get("State", {}).get("RestartCount", 0),
```

## 📋 NEXT STEPS

To apply this fix, you need to restart your docker-autoheal service:

### Option 1: If running with Docker Compose
```bash
docker-compose down
docker-compose up -d --build
```

### Option 2: If running as standalone Docker container
```bash
docker restart docker-autoheal
# Or rebuild:
docker stop docker-autoheal
docker rm docker-autoheal
docker build -t docker-autoheal .
docker run -d --name docker-autoheal ...
```

### Option 3: If running directly with Python
```bash
# Stop the current process (Ctrl+C)
# Then restart:
python run.py
```

## 🔍 VERIFY THE FIX

After restarting:

1. **Open the Web UI** (usually at http://localhost:8000)
2. **Go to Containers page**
3. **Check the "Restarts" column** - you should now see correct numbers
4. **Click on a container** to view details
5. **Verify both restart counts** show proper values:
   - `Restart Count`: Docker's native restart counter
   - `Recent Restarts`: Auto-heal tracked restarts

## 📊 WHAT THE NUMBERS MEAN

- **restart_count** (Docker's native counter):
  - Tracks automatic restarts by Docker's restart policy
  - Resets when container is recreated
  - Does NOT include manual `docker restart` commands
  
- **recent_restart_count** (Auto-heal tracking):
  - Tracks restarts performed by auto-heal system
  - Within configured time window (default: 300 seconds)
  - Persists in `data/restart_counts.json`

## ❓ TROUBLESHOOTING

If you still see wrong numbers after restarting:

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check application logs:**
   ```bash
   docker logs docker-autoheal
   ```

3. **Verify the fix was applied:**
   Look for this line in `app/docker_client/docker_client_wrapper.py`:
   ```python
   "restart_count": attrs.get("State", {}).get("RestartCount", 0),
   ```

4. **Clear browser cache** and refresh the UI

---

**Note:** Docker must be running for the application to work properly.

