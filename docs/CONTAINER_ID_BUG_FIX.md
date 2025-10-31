# Container ID Bug Fix - Complete Implementation

## Problem Statement

The docker-autoheal system was tightly coupled to Docker container IDs for all configuration, monitoring, and auto-healing logic. This caused critical issues:

1. **Container ID Changes**: Docker assigns a new container ID every time a container is recreated (e.g., after an image update)
2. **Lost Monitoring State**: Containers with new IDs were treated as unmonitored, despite being in the configuration
3. **Broken Continuity**: Restart counts, quarantine status, and custom health checks were all lost
4. **Manual Intervention Required**: Users had to manually re-add containers after every recreation

## Solution Implemented

We've implemented a **container name-based tracking system** with full backwards compatibility. The system now uses **container names** as the primary identifier while maintaining support for IDs.

### Key Changes

#### 1. Primary Identifier Change
- **Before**: Used `container.id` (64-char hash) as primary key
- **After**: Use `container.name` as primary key
- **Why**: Container names persist across recreations when using `--name` or Docker Compose `container_name`

#### 2. Updated Data Models

**HealthCheckConfig**:
```python
class HealthCheckConfig(BaseModel):
    container_name: str  # Primary identifier (NEW)
    container_id: Optional[str]  # Backwards compatibility (deprecated)
    # ...other fields
```

**AutoHealEvent**:
```python
class AutoHealEvent(BaseModel):
    container_name: str  # Primary identifier (NEW)
    container_id: Optional[str]  # For reference (deprecated)
    # ...other fields
```

#### 3. Core Tracking Functions

All tracking now uses names as primary keys:

**ConfigManager methods**:
- `record_restart(container_identifier)` - Uses name
- `get_restart_count(container_identifier, window)` - Uses name
- `quarantine_container(container_identifier)` - Uses name
- `is_quarantined(container_identifier)` - Checks name first, then ID
- `get_custom_health_check(container_identifier)` - Checks name first, then ID

**MonitoringEngine tracking**:
- `_last_restart_times` - Keyed by container name
- `_backoff_delays` - Keyed by container name
- Restart counts - Stored by container name
- Quarantine list - Stored by container name

#### 4. Monitoring Logic Updates

**Container Selection** (`_should_monitor_container`):
```python
# Check explicit inclusion (by name OR ID)
if (container_name in config.containers.selected or 
    container_id in config.containers.selected or
    short_id in config.containers.selected):
    return True
```

**Health Check Lookup**:
```python
# Try by name first, then fall back to ID
custom_hc = config_manager.get_custom_health_check(container_name)
if not custom_hc:
    custom_hc = config_manager.get_custom_health_check(container_id)
```

**Restart Tracking**:
```python
# Record restart using container name
config_manager.record_restart(container_name)
self._last_restart_times[container_name] = datetime.now(timezone.utc)
```

#### 5. API Endpoint Updates

**Container Selection** (`/api/containers/select`):
- Resolves container IDs to names before storing
- Stores names in `selected` and `excluded` lists
- Maintains backwards compatibility with existing ID-based configs

**Unquarantine** (`/api/containers/{id}/unquarantine`):
- Resolves container name from ID
- Clears quarantine and restart history by name
- Also clears by ID for backwards compatibility

**Auto-Monitor** (`_process_container_start_event`):
- Detects containers with `autoheal=true` label
- Stores container name (not ID) in selected list
- Persists monitoring across container recreations

## Backwards Compatibility

The implementation maintains full backwards compatibility:

1. **Dual Lookups**: All lookups check by name first, then fall back to ID
2. **ID Storage**: Container IDs are still stored in events for reference
3. **Existing Configs**: Old configs using IDs continue to work
4. **Gradual Migration**: As containers are recreated, they automatically migrate to name-based tracking

## Usage Recommendations

### 1. Use Named Containers

**Docker CLI**:
```bash
docker run --name myapp ...
```

**Docker Compose**:
```yaml
services:
  myapp:
    container_name: myapp
    labels:
      autoheal: "true"
```

### 2. Use Consistent Names

- Use descriptive, stable names (e.g., `webapp`, `database`, `redis`)
- Avoid auto-generated names
- Names should be unique per container

### 3. Use Docker Labels

Add the `autoheal=true` label for automatic monitoring:
```yaml
services:
  myapp:
    container_name: myapp
    labels:
      autoheal: "true"
      monitoring.id: "myapp-prod"  # Optional: custom monitoring ID
```

### 4. Explicit Image Tags

Always use explicit image tags (avoid `latest`):
```yaml
services:
  myapp:
    image: myapp:1.2.3  # ✅ Good
    # image: myapp:latest  # ❌ Avoid
```

## Testing the Fix

### Test Scenario 1: Container Recreation

1. Start a monitored container:
```bash
docker run --name test-container --label autoheal=true nginx:1.25
```

2. Verify monitoring is active via the UI or API

3. Stop and recreate with new image:
```bash
docker stop test-container
docker rm test-container
docker run --name test-container --label autoheal=true nginx:1.26
```

4. **Expected Result**: Container is still monitored (new ID, same name)

### Test Scenario 2: Image Update via Compose

1. Start services with docker-compose:
```bash
docker-compose up -d
```

2. Enable monitoring for a service

3. Update image tag in docker-compose.yml

4. Recreate service:
```bash
docker-compose up -d --force-recreate
```

5. **Expected Result**: Monitoring state persists

### Test Scenario 3: Quarantine Persistence

1. Monitor a container that fails repeatedly
2. Let it get quarantined
3. Stop and recreate the container (same name)
4. **Expected Result**: Container remains quarantined

## Migration Guide

### For Existing Deployments

No manual migration needed! The system automatically handles both old and new identifiers:

1. **Old data persists**: Existing ID-based tracking continues to work
2. **New data uses names**: New containers are tracked by name
3. **Gradual transition**: As containers are recreated, they naturally move to name-based tracking

### Optional: Clean Migration

To explicitly migrate to name-based tracking:

1. Export current configuration:
```bash
curl http://localhost:3131/api/config/export > config-backup.json
```

2. Update `selected` and `excluded` arrays to use names instead of IDs

3. Import the updated configuration:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d @config-updated.json \
  http://localhost:3131/api/config/import
```

## Technical Details

### Data Persistence

All tracking data is persisted in JSON files under `/data`:

- `/data/config.json` - Selected/excluded containers (now stores names)
- `/data/restart_counts.json` - Restart history (now keyed by names)
- `/data/quarantine.json` - Quarantined containers (now stores names)
- `/data/events.json` - Event log (stores both name and ID)

### Internal Dictionaries

Runtime dictionaries now use container names as keys:

```python
# MonitoringEngine
self._last_restart_times: dict[str, datetime]  # name -> timestamp
self._backoff_delays: dict[str, int]           # name -> seconds

# ConfigManager
self._container_restart_counts: dict[str, List[datetime]]  # name -> timestamps
self._quarantined_containers: set[str]                     # set of names
self._custom_health_checks: dict[str, HealthCheckConfig]   # name -> config
```

## Benefits

1. **Persistent Monitoring**: Container monitoring survives recreations
2. **Simplified Operations**: No need to re-configure after updates
3. **Better UX**: Users see consistent monitoring state
4. **Reliable Tracking**: Restart counts and quarantine status persist
5. **Zero Downtime**: No service interruption during container updates
6. **Backwards Compatible**: Existing configurations continue to work

## Known Limitations

1. **Name Changes**: If you rename a container, it will be treated as new
2. **Name Conflicts**: Multiple containers with the same name (different networks) may conflict
3. **Auto-generated Names**: Containers without explicit names get random names that change on recreation

## Workarounds

For containers that must change names:
1. Export container state before renaming
2. Manually update configuration with new name
3. Or use Docker labels as stable identifiers

## Future Enhancements

Potential improvements for future versions:

1. **Label-based Tracking**: Support `monitoring.id` label as primary identifier
2. **Multi-key Lookup**: Support multiple identifier types simultaneously
3. **Migration Tool**: CLI tool to migrate old ID-based configs to name-based
4. **Name Mapping**: Maintain ID-to-name mapping for better backwards compatibility
5. **SQLite Backend**: Replace JSON with SQLite for better concurrency and queries

## Conclusion

This fix resolves the critical Container ID dependency bug by using container names as the primary identifier while maintaining full backwards compatibility. The system now correctly handles container recreations, image updates, and redeployments without losing monitoring state.

**Status**: ✅ **IMPLEMENTED AND TESTED**

---

*Last Updated: 2025-10-31*
*Version: 1.1.0*

