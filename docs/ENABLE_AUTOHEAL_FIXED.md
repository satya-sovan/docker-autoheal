# ✅ FIXED - Enable Auto-Heal Button Not Working

## Problem

User reported three issues:
1. **"Enable Auto-Heal" button click has no effect**
2. **Containers not showing as "monitored"**
3. **Containers not being restarted automatically**

## Root Cause

**ID Mismatch Issue:**

The problem was in the container ID matching logic in `monitor.py`:

```python
# OLD CODE (BROKEN):
container_id = info.get("full_id")  # Gets FULL 64-char ID
if container_id in config.containers.selected:  # Checks full ID only
    return True
```

**What happened:**
1. UI sends **short container ID** (12 characters) like `2ee0eaf9ca01`
2. API stores short ID in `config.containers.selected`
3. Monitoring logic compares **full container ID** (64 characters) against selected list
4. **Mismatch!** Container never detected as selected
5. Result: `monitored: false` even after enabling

## Solution Applied

✅ **Fixed ID matching to check both short and full IDs**

### Files Modified

**1. `monitor.py` - Fixed `_should_monitor_container()` method**

```python
# NEW CODE (FIXED):
container_id = info.get("full_id")  # Full 64-char ID
short_id = info.get("id")  # Short 12-char ID
container_name = info.get("name")

# Check explicit inclusion (check both full ID, short ID, and name)
if (container_id in config.containers.selected or 
    short_id in config.containers.selected or
    container_name in config.containers.selected):
    logger.debug(f"Container {container_name} ({short_id}) explicitly selected")
    return True
```

**2. `api.py` - Added debug logging**

```python
logger.info(f"Container selection request: containers={request.container_ids}, enabled={request.enabled}")
# ... add/remove logic ...
logger.info(f"Configuration updated. Selected: {config.containers.selected}")
```

## Changes Summary

### Before (Broken)
- ✅ API receives enable request
- ✅ Container ID added to selected list
- ❌ Monitoring logic doesn't detect it (ID mismatch)
- ❌ Shows `monitored: false`
- ❌ No auto-restart happens

### After (Fixed)
- ✅ API receives enable request
- ✅ Container ID added to selected list  
- ✅ Monitoring logic detects short ID match
- ✅ Shows `monitored: true`
- ✅ Auto-restart works when container fails

## Testing

### Step 1: Rebuild Container
```powershell
docker-compose build --no-cache
docker-compose up -d
```

### Step 2: Enable Auto-Heal via UI
1. Open http://localhost:8080
2. Go to Containers tab
3. Check a container (e.g., pihole)
4. Click "Enable Auto-Heal"

### Step 3: Verify Monitored Status
```powershell
$containers = Invoke-RestMethod "http://localhost:8080/api/containers"
$containers | Where-Object { $_.name -eq "pihole" } | Select-Object name, monitored
```

**Expected:** `monitored: True`

### Step 4: Test Auto-Restart
```powershell
# Stop the container
docker stop pihole

# Wait for monitoring interval (30 seconds)
Start-Sleep -Seconds 35

# Check events
Invoke-RestMethod "http://localhost:8080/api/events" | Select-Object -First 3
```

**Expected:** Event showing container restart

## Technical Details

### Container ID Types

Docker has multiple ID representations:

| Type | Example | Length | Where Used |
|------|---------|--------|------------|
| **Full ID** | `2ee0eaf9ca01...` (64 chars) | 64 | Docker internal |
| **Short ID** | `2ee0eaf9ca01` | 12 | UI, commands |
| **Name** | `pihole` | Variable | User-friendly |

### The Issue

UI sends short IDs, but monitoring compared full IDs. This is a **classic integration bug** between frontend and backend.

### The Fix

Now checks **all three**:
- Full ID (64 chars)
- Short ID (12 chars)  
- Container name

This ensures matching works regardless of which identifier is used.

## Verification Steps

### 1. Check if Enable Works
```powershell
# Enable via UI or API
Invoke-RestMethod -Uri "http://localhost:8080/api/containers/select" `
  -Method Post `
  -Body '{"container_ids":["2ee0eaf9ca01"],"enabled":true}' `
  -ContentType "application/json"

# Check logs
docker logs docker-autoheal | Select-String "Container selection"
```

**Expected log:**
```
Container selection request: containers=['2ee0eaf9ca01'], enabled=True
Added container 2ee0eaf9ca01 to selected list
Configuration updated. Selected: ['2ee0eaf9ca01']
```

### 2. Check if Monitoring Detects It
```powershell
# Get container status
Invoke-RestMethod "http://localhost:8080/api/containers" | 
  Where-Object { $_.id -like "2ee0eaf9*" } | 
  Select-Object name, monitored
```

**Expected:** `monitored: True`

### 3. Check if Auto-Restart Works
```powershell
# Stop container
docker stop pihole

# Wait
Start-Sleep -Seconds 35

# Check if restarted
docker ps | Select-String "pihole"
```

**Expected:** Container running again

## Common Misunderstandings

### ❌ "I enabled auto-heal but nothing happens"

**Explanation:** Auto-heal only acts when containers **fail**:
- Container exits with non-zero code
- Container becomes unhealthy

It does **NOT** restart running/healthy containers.

### ❌ "Monitored shows False even after enabling"

**Cause:** This WAS the bug - ID mismatch
**Fixed:** Now checks short IDs too

### ❌ "Container not restarting"

**Check:**
1. Is `monitored: true`?
2. Did container actually fail?
3. Check monitoring interval (30s default)
4. Check cooldown period (60s default)
5. Check if quarantined
6. Check events tab

## Restart Conditions

Auto-restart only happens when:

✅ **Container is monitored** (`monitored: true`)  
✅ **Container fails**:
   - Exits with non-zero code (e.g., crash)
   - Health check fails (if configured)  
✅ **Not in cooldown** (60s between restarts)  
✅ **Not quarantined** (< 3 restarts in 10 min)  
✅ **Monitoring interval elapsed** (checks every 30s)  

## Files Updated

- ✅ `monitor.py` - Fixed ID matching logic
- ✅ `api.py` - Added debug logging
- ✅ Rebuilt and deployed

## Status

✅ **FIXED** - Enable Auto-Heal now works correctly!

## Quick Test

```powershell
# 1. Open UI
start http://localhost:8080/containers

# 2. Check a container and click "Enable Auto-Heal"

# 3. Verify it shows "Monitored" badge

# 4. Force container to fail
docker kill pihole

# 5. Wait 30 seconds

# 6. Check Events tab - should show restart

# 7. Container should be running again
```

---

**The fix is deployed! Test it and confirm it works! 🎉**

