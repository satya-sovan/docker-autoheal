# Restart Count Bug Fix

## Issue
The UI was displaying incorrect restart count numbers for containers. The restart count was always showing 0 or wrong values.

## Root Cause
The `restart_count` field was being read from the wrong location in Docker's container attributes structure.

**Incorrect code (before fix):**
```python
"restart_count": attrs.get("RestartCount", 0),
```

This was trying to read `RestartCount` from the root level of the container attributes, but Docker doesn't store it there.

## Solution
Docker stores the `RestartCount` inside the `State` object of the container attributes.

**Fixed code:**
```python
"restart_count": attrs.get("State", {}).get("RestartCount", 0),
```

## Docker Container Attributes Structure

According to Docker API documentation, the container inspect response has this structure:

```json
{
  "Id": "container_id",
  "Name": "/container_name",
  "State": {
    "Status": "running",
    "Running": true,
    "RestartCount": 5,      // ← This is where RestartCount lives
    "ExitCode": 0,
    "StartedAt": "...",
    "FinishedAt": "..."
  },
  "Config": { ... },
  "HostConfig": { ... }
}
```

## What RestartCount Represents

Docker's `RestartCount` field tracks:
- The number of times the container has been restarted **by Docker's restart policy**
- This includes automatic restarts due to:
  - Container crashes/exits when restart policy is set (e.g., `restart: always`, `restart: on-failure`)
  - Health check failures that trigger automatic restarts
  
**Important Notes:**
- This is Docker's native restart counter
- It does NOT include manual restarts triggered by `docker restart` commands
- It resets to 0 when the container is recreated (e.g., via `docker-compose up --force-recreate`)
- It persists across container stops/starts but not across container removal/recreation

## Application-Tracked Restarts

The docker-autoheal application also tracks its own restart history separately in:
- `data/restart_counts.json` (persists across application restarts)
- Accessible via `config_manager.get_restart_count(container_id, window_seconds)`

This is displayed as `recent_restart_count` in the container details modal and tracks restarts performed by the auto-heal system within a configurable time window.

## Files Changed

1. **app/docker_client/docker_client_wrapper.py** (line 132)
   - Changed: `attrs.get("RestartCount", 0)`
   - To: `attrs.get("State", {}).get("RestartCount", 0)`

## Testing

After this fix:
1. The UI should display correct restart counts from Docker
2. Containers with restart policies will show accurate restart counts
3. The count reflects Docker's native restart tracking

## Related Fields

The container info now properly includes:
- `restart_count`: Docker's native restart counter from `State.RestartCount`
- `recent_restart_count`: Application-tracked restarts within configured window
- `restart_policy`: Container's restart policy configuration

Both values are displayed in the container details modal for complete visibility.

