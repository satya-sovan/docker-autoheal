# Unquarantine Bug Fix

## Problem
The unquarantine API endpoint was showing "successfully unquarantined" messages, but containers were not actually being removed from the quarantine list.

## Root Cause
**Container ID Mismatch:**

1. **When Quarantining**: The monitoring engine uses the **full container ID** (64 characters) when adding containers to quarantine
2. **When Unquarantining**: The API endpoint was receiving a **short container ID** (12 characters) from the frontend and passing it directly to `config_manager.unquarantine_container()`
3. **Result**: The set operation `self._quarantined_containers.discard(container_id)` was trying to remove the short ID from a set containing full IDs, which had no effect

## Example
- Quarantine list contains: `"c9963b4cdaae8f5c3d4e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c"`
- Unquarantine tries to remove: `"c9963b4cdaae"`
- Nothing gets removed because the strings don't match!

## Solution
Modified **five API endpoints** to resolve the full container ID before performing operations:

### 1. `/api/containers/{container_id}/unquarantine`
```python
# Before
config_manager.unquarantine_container(container_id)  # Uses short ID from API parameter

# After
container = docker_client.get_container(container_id)  # Docker resolves short to full
full_container_id = container.id
config_manager.unquarantine_container(full_container_id)  # Uses full ID
```

### 2. `/api/containers/{container_id}` (Get Container Details)
```python
# Before
config_manager.is_quarantined(container_id)  # Uses short ID from API parameter

# After
full_container_id = info.get("full_id")  # Get full ID from container info
config_manager.is_quarantined(full_container_id)  # Uses full ID
```

### 3. `/api/healthchecks` (POST - Add Health Check)
```python
# Before
config_manager.add_custom_health_check(health_check)  # Uses short ID from request

# After
container = docker_client.get_container(health_check.container_id)
health_check.container_id = container.id  # Update to full ID
config_manager.add_custom_health_check(health_check)
```

### 4. `/api/healthchecks/{container_id}` (GET - Get Health Check)
```python
# Before
config_manager.get_custom_health_check(container_id)  # Uses short ID

# After
container = docker_client.get_container(container_id)
full_container_id = container.id
config_manager.get_custom_health_check(full_container_id)  # Uses full ID
```

### 5. `/api/healthchecks/{container_id}` (DELETE - Remove Health Check)
```python
# Before
config_manager.remove_custom_health_check(container_id)  # Uses short ID

# After
container = docker_client.get_container(container_id)
full_container_id = container.id
config_manager.remove_custom_health_check(full_container_id)  # Uses full ID
```

## Files Modified
- `app/api/api.py` - Fixed **5 endpoints** to use full container IDs
- `app/tests/test_unquarantine_fix.py` - Added demonstration test

## Testing
To verify the fix works:

1. **Check Current Quarantine List**:
   ```bash
   # Look at the quarantine.json file
   cat /data/quarantine.json
   ```

2. **Unquarantine a Container**:
   ```bash
   curl -X POST http://localhost:3131/api/containers/c9963b4cdaae/unquarantine
   ```

3. **Verify Removal**:
   ```bash
   # Check the quarantine.json file again - should be empty or container removed
   cat /data/quarantine.json
   ```

4. **Frontend Test**:
   - Go to the Containers page
   - Find a quarantined container
   - Click "Unquarantine"
   - Refresh the page - quarantine badge should be gone

## Prevention
All API endpoints that perform operations on containers should:
1. Accept any form of container ID (short or full)
2. Resolve to the full container ID using `docker_client.get_container()`
3. Use the full ID for all config_manager operations

## Related Code Patterns
The monitoring engine correctly uses full IDs:
```python
container_id = info.get("full_id")  # Always use full_id from info
config_manager.is_quarantined(container_id)
```

All API endpoints should follow this pattern when interacting with config_manager.

## Status
✅ **Fixed** - Containers can now be successfully unquarantined via the API and UI

