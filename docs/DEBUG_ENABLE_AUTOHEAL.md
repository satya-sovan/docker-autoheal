# Testing Enable Auto-Heal Functionality

## Issue Report
User reports that clicking "Enable Auto-Heal" button doesn't work:
1. Button click has no effect
2. Containers not added to "monitored" list
3. Containers not being restarted when they fail

## Debugging Steps

### Step 1: Check Current Containers
```powershell
$containers = Invoke-RestMethod -Uri "http://localhost:8080/api/containers"
$containers | Select-Object name, id, monitored, status | Format-Table
```

### Step 2: Try Enabling Auto-Heal via API
```powershell
# Get first container ID
$containerId = $containers[0].id

# Enable auto-heal
$body = @{
    container_ids = @($containerId)
    enabled = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/containers/select" -Method Post -Body $body -ContentType "application/json"
```

### Step 3: Check if Container is Now Monitored
```powershell
$containers = Invoke-RestMethod -Uri "http://localhost:8080/api/containers"
$containers | Where-Object { $_.id -eq $containerId } | Select-Object name, monitored
```

### Step 4: Check Configuration
```powershell
$config = Invoke-RestMethod -Uri "http://localhost:8080/api/config"
$config.containers | ConvertTo-Json
```

### Step 5: Check Logs
```powershell
docker logs docker-autoheal --tail 20
```

## Expected Behavior

1. **API Call**: POST to `/api/containers/select` with container IDs
2. **Configuration Update**: Container IDs added to `config.containers.selected`
3. **Monitoring Check**: `_should_monitor_container()` returns `True` for selected containers
4. **UI Update**: Container shows `monitored: true` in the list
5. **Auto-Healing**: If container fails, it gets restarted

## Potential Issues

### Issue 1: API Not Receiving Request
**Check**: Look for POST request in logs
**Solution**: Check network tab in browser

### Issue 2: Configuration Not Persisting
**Check**: Query `/api/config` endpoint
**Solution**: Verify config_manager.update_config() is called

### Issue 3: Monitoring Logic Not Detecting Selected Containers
**Check**: Verify `_should_monitor_container()` logic
**Solution**: Ensure container ID matches exactly

### Issue 4: Container Not in Failed State
**Check**: Container must be exited or unhealthy to trigger restart
**Solution**: Container only restarts when it fails, not on enable

## Test Sequence

1. **Enable auto-heal for a container**
2. **Verify monitored=true in UI**
3. **Stop the container**: `docker stop <container_name>`
4. **Wait 30 seconds** (monitoring interval)
5. **Check if container restarted**: Look for restart in events

## Common Misunderstandings

⚠️ **Auto-heal doesn't restart running containers**
- It only restarts containers that:
  - Exit with non-zero code
  - Become unhealthy (if health check configured)

✅ **To test auto-heal:**
1. Enable auto-heal for a container
2. Force the container to fail
3. Wait for monitoring interval (30s)
4. Check events tab for restart action

## Quick Test

```powershell
# 1. Get pihole container ID
$pihole = (Invoke-RestMethod "http://localhost:8080/api/containers") | Where-Object { $_.name -eq "pihole" }

# 2. Enable auto-heal
Invoke-RestMethod -Uri "http://localhost:8080/api/containers/select" -Method Post -Body "{`"container_ids`":[`"$($pihole.id)`"],`"enabled`":true}" -ContentType "application/json"

# 3. Check if monitored
(Invoke-RestMethod "http://localhost:8080/api/containers") | Where-Object { $_.name -eq "pihole" } | Select-Object name, monitored

# 4. Stop container to trigger restart
docker stop pihole

# 5. Wait 30 seconds and check events
Start-Sleep -Seconds 35
Invoke-RestMethod "http://localhost:8080/api/events" | Select-Object -First 5
```

