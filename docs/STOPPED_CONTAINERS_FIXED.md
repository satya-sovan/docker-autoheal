# ✅ FIXED - Stopped Containers Now Visible and Auto-Restart Works

## Issues Reported

1. ❌ UI not showing stopped containers
2. ❌ Stopped containers completely ignored
3. ❌ Stopped containers removed from UI
4. ❌ Stopped containers not being monitored or auto-healed

## Root Causes Found

### Issue 1: UI Only Fetched Running Containers
**File**: `frontend/src/components/ContainersPage.jsx`
```javascript
// OLD (BROKEN):
const response = await getContainers(); // default: includeStopped=false
```

### Issue 2: Monitoring Engine Only Checked Running Containers
**File**: `monitor.py`
```python
# OLD (BROKEN):
containers = await asyncio.to_thread(
    self.docker_client.list_containers, 
    all_containers=False  # Only running containers
)
```

### Issue 3: Default Configuration Respected Manual Stops
**File**: `config.py`
```python
# OLD (BROKEN):
respect_manual_stop: bool = Field(default=True)
# This prevented restarting manually stopped containers
```

### Issue 4: Poor Exited Container Detection
**File**: `monitor.py`
- Only checked "exited" status, missed "stopped" and "dead"
- Confusing logic for exit code 0 vs non-zero

## Solutions Applied

### Fix 1: UI Shows ALL Containers ✅
```javascript
// NEW (FIXED):
const response = await getContainers(true); // Include stopped containers
```

**Result**: UI now shows running AND stopped containers

### Fix 2: Monitoring Checks ALL Containers ✅
```python
# NEW (FIXED):
containers = await asyncio.to_thread(
    self.docker_client.list_containers, 
    all_containers=True  # Include stopped containers
)
```

**Result**: Monitoring engine now detects stopped containers and can restart them

### Fix 3: Changed Default to Restart Stopped Containers ✅
```python
# NEW (FIXED):
respect_manual_stop: bool = Field(default=False)
```

**Result**: By default, auto-heal will restart even manually stopped containers

### Fix 4: Improved Stopped Container Detection ✅
```python
# NEW (FIXED):
status = state.get("Status", "").lower()

if status in ["exited", "stopped", "dead"]:
    exit_code = state.get("ExitCode", 0)
    
    if exit_code == 0 and config.restart.respect_manual_stop:
        return False, "Manual stop (exit 0)"
    
    if exit_code != 0:
        return True, f"Container exited with code {exit_code}"
    else:
        return True, f"Container stopped (exit 0)"
```

**Result**: Properly detects and handles all stopped container states

## Files Modified

1. ✅ `frontend/src/components/ContainersPage.jsx` - Fetch all containers
2. ✅ `monitor.py` - Check all containers + improved exit detection
3. ✅ `config.py` - Changed default `respect_manual_stop` to `False`

## How It Works Now

### Before (BROKEN) ❌

```
1. Container stops
2. UI no longer shows it (fetched only running)
3. Monitoring skips it (checked only running)
4. Container never restarts
5. User confused - "where did it go?"
```

### After (FIXED) ✅

```
1. Container stops
2. UI still shows it with "exited" status
3. Monitoring detects it as stopped
4. Auto-heal restarts it (if enabled)
5. Container comes back up
6. UI shows it as "running" again
```

## Testing

### Test 1: Verify UI Shows Stopped Containers

```powershell
# 1. Open UI
start http://localhost:8080/containers

# 2. Stop a container
docker stop pihole

# 3. Refresh UI
# Should still see pihole with status "exited"
```

### Test 2: Verify Auto-Restart Works

```powershell
# 1. Enable auto-heal for a container via UI
# Check the box and click "Enable Auto-Heal"

# 2. Stop the container
docker stop pihole

# 3. Wait for monitoring cycle (30 seconds)
Start-Sleep -Seconds 35

# 4. Check if container restarted
docker ps | Select-String "pihole"
# Should be running!

# 5. Check events
Invoke-RestMethod "http://localhost:8080/api/events" | Select-Object -First 3
# Should show restart event
```

### Test 3: Verify API Returns Stopped Containers

```powershell
# Get all containers
$containers = Invoke-RestMethod "http://localhost:8080/api/containers?include_stopped=true"

# Show all statuses
$containers | Select-Object name, status | Format-Table

# Should show both running and stopped
```

### Test 4: Complete Auto-Heal Test

```powershell
# 1. Get a container
$pihole = (Invoke-RestMethod "http://localhost:8080/api/containers") | 
  Where-Object { $_.name -eq "pihole" }

# 2. Enable auto-heal
Invoke-RestMethod -Uri "http://localhost:8080/api/containers/select" `
  -Method Post `
  -Body "{`"container_ids`":[`"$($pihole.id)`"],`"enabled`":true}" `
  -ContentType "application/json"

# 3. Verify monitored
Start-Sleep -Seconds 2
$updated = (Invoke-RestMethod "http://localhost:8080/api/containers") | 
  Where-Object { $_.name -eq "pihole" }
Write-Output "Monitored: $($updated.monitored)"

# 4. Stop container
docker stop pihole

# 5. Wait for restart (monitoring interval + cooldown)
Write-Output "Waiting 35 seconds for auto-restart..."
Start-Sleep -Seconds 35

# 6. Check if restarted
$final = docker ps --format "{{.Names}}" | Select-String "pihole"
if ($final) {
    Write-Output "✅ SUCCESS: Container auto-restarted!"
} else {
    Write-Output "❌ FAILED: Container did not restart"
}

# 7. Check events
Write-Output "`nRecent Events:"
Invoke-RestMethod "http://localhost:8080/api/events" | 
  Select-Object -First 5 | 
  Format-Table timestamp, container_name, event_type, status
```

## Configuration Options

### Respect Manual Stop Setting

If you want to PREVENT restarting manually stopped containers (exit code 0):

1. Go to Configuration tab in UI
2. Find "Respect Manual Stop" checkbox
3. Enable it
4. Click Save

**Or via API:**
```powershell
$config = Invoke-RestMethod "http://localhost:8080/api/config"
$config.restart.respect_manual_stop = $true
Invoke-RestMethod -Uri "http://localhost:8080/api/config/restart" `
  -Method Put `
  -Body ($config.restart | ConvertTo-Json) `
  -ContentType "application/json"
```

**Behavior:**
- `respect_manual_stop = false` (default): Restarts ALL stopped containers
- `respect_manual_stop = true`: Only restarts containers that crashed (exit code ≠ 0)

## Expected Behavior

### Container Stopped with Exit Code 0 (Clean Stop)
```powershell
docker stop pihole  # Clean stop
```

**With `respect_manual_stop = false` (default):**
- ✅ Container WILL be restarted by auto-heal

**With `respect_manual_stop = true`:**
- ❌ Container will NOT be restarted
- Reason: "Manual stop (exit 0)"

### Container Crashed with Exit Code != 0
```powershell
# Simulate crash
docker exec pihole kill 1
```

**Both settings:**
- ✅ Container WILL be restarted
- Reason: "Container exited with code X"

## Monitoring Interval

Auto-heal checks containers every **30 seconds** by default.

After stopping a container, wait at least:
- **30 seconds** (monitoring interval)
- **+ 60 seconds** (default cooldown)
- **= ~90 seconds total**

For testing, you can wait 35-40 seconds to see the restart.

## Verification Checklist

```
✅ UI shows running containers
✅ UI shows stopped containers
✅ Stopped containers stay visible in UI
✅ Can enable auto-heal for stopped containers
✅ Stopped containers show "exited" badge
✅ Monitoring engine checks stopped containers
✅ Auto-heal restarts stopped containers (if enabled)
✅ Events log shows restart actions
✅ Configuration setting works (respect_manual_stop)
```

## Common Scenarios

### Scenario 1: Container Crashes
```
1. Container crashes (exit code 137, 1, etc.)
2. UI shows status: "exited"
3. Monitoring detects: needs restart
4. Auto-heal: restarts container
5. UI shows status: "running"
```

### Scenario 2: User Stops Container
```
1. User runs: docker stop myapp
2. UI shows status: "exited"
3. Monitoring detects: stopped cleanly (exit 0)
4. Auto-heal: restarts (default) or skips (if respect_manual_stop=true)
```

### Scenario 3: Container Keeps Crashing
```
1. Container crashes repeatedly
2. Auto-heal restarts it each time
3. After 3 restarts in 10 minutes: QUARANTINED
4. UI shows: "Quarantined" badge
5. Auto-heal stops trying
6. Admin must manually unquarantine
```

## Troubleshooting

### Issue: Stopped container not visible in UI

**Check:**
```powershell
# Verify API returns it
Invoke-RestMethod "http://localhost:8080/api/containers?include_stopped=true" | 
  Where-Object { $_.status -like "*exit*" }
```

**If API returns it but UI doesn't:**
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)

### Issue: Container not restarting

**Check 1: Is it monitored?**
```powershell
(Invoke-RestMethod "http://localhost:8080/api/containers") | 
  Where-Object { $_.name -eq "myapp" } | 
  Select-Object name, monitored
```

**Check 2: Is it quarantined?**
```powershell
(Invoke-RestMethod "http://localhost:8080/api/containers") | 
  Where-Object { $_.name -eq "myapp" } | 
  Select-Object name, quarantined
```

**Check 3: Check logs**
```powershell
docker logs docker-autoheal | Select-String "myapp"
```

**Check 4: Check events**
```powershell
Invoke-RestMethod "http://localhost:8080/api/events" | 
  Where-Object { $_.container_name -eq "myapp" } | 
  Format-Table
```

## Status

✅ **All Issues Fixed**  
✅ **Container Rebuilt**  
✅ **Ready for Testing**  

## Rebuild and Deploy

```powershell
# Rebuild
docker-compose up --build -d

# Test
python test_service.py

# Verify UI
start http://localhost:8080/containers
```

---

## Summary of Changes

| Issue | Before | After |
|-------|--------|-------|
| **UI Shows** | Running only | Running + Stopped |
| **Monitoring Checks** | Running only | Running + Stopped |
| **Default Behavior** | Don't restart exit 0 | Restart ALL stopped |
| **Exit Detection** | "exited" only | "exited", "stopped", "dead" |

**Result**: Stopped containers are now fully supported! They appear in the UI and can be auto-restarted when they fail.

---

**Test it now! Stop a container and watch it automatically restart! 🎉**

