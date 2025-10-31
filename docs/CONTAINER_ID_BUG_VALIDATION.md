# Container ID Bug Fix - Validation Checklist

## ✅ Implementation Checklist

### Core Changes

- [x] **ConfigManager**: Updated to use container names as primary identifier
  - [x] `record_restart()` - Uses name
  - [x] `get_restart_count()` - Uses name
  - [x] `quarantine_container()` - Uses name
  - [x] `is_quarantined()` - Checks name first, then ID
  - [x] `get_custom_health_check()` - Checks name first, then ID
  
- [x] **MonitoringEngine**: Updated all tracking to use names
  - [x] `_last_restart_times` - Keyed by name
  - [x] `_backoff_delays` - Keyed by name
  - [x] `_check_single_container()` - Checks quarantine by name
  - [x] `_should_monitor_container()` - Checks name, ID, short ID
  - [x] `_evaluate_container_health()` - Looks up health check by name
  - [x] `_handle_container_restart()` - All tracking uses name
  - [x] `_process_container_start_event()` - Stores name in config

- [x] **API Endpoints**: Updated to resolve and use names
  - [x] `/api/containers/select` - Resolves IDs to names before storing
  - [x] `/api/containers/{id}/unquarantine` - Unquarantines by name
  - [x] `/api/containers/{id}` - Looks up by name first

### Data Model Updates

- [x] **HealthCheckConfig**: Added `container_name` field
- [x] **AutoHealEvent**: Made `container_name` primary, `container_id` optional
- [x] **ContainersConfig**: Updated documentation for name-based tracking

### Documentation

- [x] Created comprehensive guide: `CONTAINER_ID_BUG_FIX.md`
- [x] Created quick reference: `CONTAINER_ID_BUG_QUICK_REF.md`
- [x] Created validation checklist (this file)

## 🧪 Manual Testing Steps

### Test 1: Basic Container Recreation

```bash
# 1. Start docker-autoheal service
docker-compose up -d

# 2. Create a test container with a name
docker run -d --name test-bug-fix --label autoheal=true nginx:1.25

# 3. Verify it's being monitored
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="test-bug-fix")'

# 4. Check that it's in the selected list
curl http://localhost:3131/api/config | jq '.containers.selected'
# Should show "test-bug-fix" (name, not ID)

# 5. Stop and recreate the container (new ID!)
docker stop test-bug-fix
docker rm test-bug-fix
docker run -d --name test-bug-fix --label autoheal=true nginx:1.26

# 6. Verify monitoring persists
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="test-bug-fix")'
# Should still show monitored=true

# Expected Result: ✅ Container is still monitored despite new ID
```

### Test 2: Restart Count Persistence

```bash
# 1. Enable monitoring for a container
curl -X POST http://localhost:3131/api/containers/select \
  -H "Content-Type: application/json" \
  -d '{"container_ids": ["test-app"], "enabled": true}'

# 2. Force some restarts (simulate failures)
docker restart test-app
docker restart test-app

# 3. Check restart count
curl http://localhost:3131/api/containers/test-app | jq '.recent_restart_count'
# Should show 2

# 4. Recreate container (new ID)
docker stop test-app && docker rm test-app
docker run -d --name test-app myimage:latest

# 5. Force another restart
docker restart test-app

# 6. Check restart count
curl http://localhost:3131/api/containers/test-app | jq '.recent_restart_count'
# Should show 3 (persisted across recreation!)

# Expected Result: ✅ Restart count persists across recreations
```

### Test 3: Quarantine Persistence

```bash
# 1. Create a container that will fail repeatedly
docker run -d --name failing-app --label autoheal=true \
  alpine sh -c "exit 1"

# 2. Wait for it to get quarantined (after max_restarts)
# Check events
curl http://localhost:3131/api/events | jq '.[] | select(.container_name=="failing-app")'

# 3. Verify it's quarantined
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="failing-app") | .quarantined'
# Should show true

# 4. Recreate the container (new ID)
docker rm -f failing-app
docker run -d --name failing-app --label autoheal=true \
  alpine sh -c "sleep 3600"

# 5. Check if still quarantined
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="failing-app") | .quarantined'
# Should still show true (persisted by name!)

# 6. Unquarantine
curl -X POST http://localhost:3131/api/containers/failing-app/unquarantine

# Expected Result: ✅ Quarantine status persists, can be cleared by name
```

### Test 4: Docker Compose Recreation

```bash
# 1. Create docker-compose.yml
cat > test-compose.yml <<EOF
version: '3.8'
services:
  webapp:
    container_name: webapp
    image: nginx:1.25
    labels:
      autoheal: "true"
EOF

# 2. Start service
docker-compose -f test-compose.yml up -d

# 3. Verify monitoring
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="webapp")'

# 4. Update image version and recreate
sed -i 's/nginx:1.25/nginx:1.26/' test-compose.yml
docker-compose -f test-compose.yml up -d --force-recreate

# 5. Verify monitoring persists
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="webapp")'

# Expected Result: ✅ Monitoring persists through compose recreate
```

### Test 5: Backwards Compatibility

```bash
# 1. Manually add a container by ID (old way)
CONTAINER_ID=$(docker ps --filter "name=legacy-app" --format "{{.ID}}")
curl -X POST http://localhost:3131/api/containers/select \
  -H "Content-Type: application/json" \
  -d "{\"container_ids\": [\"$CONTAINER_ID\"], \"enabled\": true}"

# 2. Verify it works
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="legacy-app")'

# Expected Result: ✅ Old ID-based selection still works
```

### Test 6: Auto-Generated Names (Compose Services)

```bash
# 1. Create docker-compose with auto-generated names
cat > test-autogen.yml <<EOF
version: '3.8'
services:
  webapp:
    image: nginx:1.25
    labels:
      autoheal: "true"
EOF

# 2. Start with compose
docker-compose -p testproject -f test-autogen.yml up -d

# 3. Verify monitoring (should use project_service as stable ID)
curl http://localhost:3131/api/containers | jq '.[] | select(.compose_service=="webapp")'

# 4. Check config shows stable ID (not auto-generated name)
curl http://localhost:3131/api/config | jq '.containers.selected'
# Should show "testproject_webapp" (not the auto-generated name)

# 5. Recreate with different image
sed -i 's/nginx:1.25/nginx:1.26/' test-autogen.yml
docker-compose -p testproject -f test-autogen.yml up -d --force-recreate

# 6. Verify monitoring persists
curl http://localhost:3131/api/containers | jq '.[] | select(.compose_service=="webapp")'

# Expected Result: ✅ Monitoring persists despite auto-generated name changes
```

### Test 7: Explicit Monitoring ID Label

```bash
# 1. Create container with monitoring.id label
docker run -d --name test-explicit-id \
  --label monitoring.id=my-stable-service \
  --label autoheal=true \
  nginx:1.25

# 2. Verify it's tracked by monitoring.id
curl http://localhost:3131/api/config | jq '.containers.selected'
# Should show "my-stable-service"

# 3. Rename the container
docker rename test-explicit-id test-renamed

# 4. Recreate with new name but same monitoring.id
docker rm -f test-renamed
docker run -d --name completely-different-name \
  --label monitoring.id=my-stable-service \
  --label autoheal=true \
  nginx:1.26

# 5. Verify monitoring persists (same monitoring.id)
curl http://localhost:3131/api/containers | jq '.[] | select(.name=="completely-different-name")'

# Expected Result: ✅ Monitoring persists across name changes via monitoring.id
```

### Test 8: Name Conflicts Across Projects

```bash
# 1. Create same service name in different projects
cat > app-compose.yml <<EOF
version: '3.8'
services:
  webapp:
    image: nginx:latest
    labels:
      autoheal: "true"
EOF

# 2. Start in production project
docker-compose -p production -f app-compose.yml up -d

# 3. Start in staging project (same service name!)
docker-compose -p staging -f app-compose.yml up -d

# 4. Verify both are tracked separately
curl http://localhost:3131/api/config | jq '.containers.selected'
# Should show: ["production_webapp", "staging_webapp"]

# 5. Check both are monitored independently
curl http://localhost:3131/api/containers | jq '.[] | select(.compose_service=="webapp")'

# Expected Result: ✅ No conflicts, both tracked independently
```

## 🔍 Code Review Checklist

- [x] All `container_id` lookups now check `container_name` first
- [x] `_last_restart_times` dictionary uses names as keys
- [x] `_backoff_delays` dictionary uses names as keys
- [x] `config.containers.selected` stores names (not IDs)
- [x] `config.containers.excluded` stores names (not IDs)
- [x] Quarantine operations use names
- [x] Restart count tracking uses names
- [x] Custom health checks can be looked up by name
- [x] Events store both name (primary) and ID (reference)
- [x] API endpoints resolve IDs to names before storing
- [x] Backwards compatibility maintained (dual lookups)

## 📊 Success Criteria

All of the following must be true:

1. ✅ Container monitoring persists after `docker stop/rm/run` with same name
2. ✅ Restart counts persist across container recreations
3. ✅ Quarantine status persists across container recreations
4. ✅ Custom health checks persist across container recreations
5. ✅ Backoff delays persist across container recreations
6. ✅ Old ID-based configurations continue to work
7. ✅ API lookups work with both names and IDs
8. ✅ Docker Compose recreations maintain monitoring state
9. ✅ Auto-monitoring (label-based) adds containers by name
10. ✅ No breaking changes to existing functionality

## ✅ Known Limitations - NOW RESOLVED!

All three original limitations have been **solved** through the stable identifier system:

1. ✅ **Auto-generated names** - SOLVED via Docker Compose service labels
2. ✅ **Container name changes** - SOLVED via `monitoring.id` label priority
3. ✅ **Name conflicts** - SOLVED via Compose project namespacing

See [CONTAINER_ID_LIMITATIONS_RESOLVED.md](./CONTAINER_ID_LIMITATIONS_RESOLVED.md) for complete details.

## 📝 Developer Notes

### Why Names Instead of IDs?

1. **Docker assigns new IDs on recreation** - IDs are ephemeral
2. **Names persist** - When using `--name` or `container_name`, the name stays the same
3. **User-friendly** - Names are more meaningful than hash IDs
4. **Docker Compose standard** - Compose uses `container_name` explicitly

### Migration Strategy

**No manual migration needed!** The system:
- Accepts both names and IDs in API calls
- Stores names in config for new containers
- Maintains old ID-based data for backwards compatibility
- Gradually migrates as containers are updated

### Future Improvements

1. Add migration tool to convert ID-based configs to name-based
2. Support Docker labels as alternative stable identifiers
3. Add container metadata file for advanced tracking
4. Implement container name change detection and alerts

---

**Status**: ✅ **IMPLEMENTED**  
**Last Updated**: 2025-10-31  
**Version**: 1.1.0

