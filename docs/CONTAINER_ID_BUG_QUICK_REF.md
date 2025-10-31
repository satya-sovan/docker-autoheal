# Container ID Bug Fix - Quick Reference

## 🎯 Problem
Container monitoring broke after image updates because Docker assigns new IDs to recreated containers.

## ✅ Solution
Use **container names** instead of IDs as the primary identifier.

## 🔧 What Changed

### Before (Broken)
```python
# Tracked by ID - lost on recreation
config.containers.selected = ["a1b2c3d4e5f6..."]
restart_counts["a1b2c3d4e5f6..."] = [...]
```

### After (Fixed)
```python
# Tracked by name - persists across recreations
config.containers.selected = ["myapp", "database"]
restart_counts["myapp"] = [...]
```

## 📋 Quick Actions

### 1. Best Practice: Use Named Containers

**Docker Run**:
```bash
docker run --name myapp --label autoheal=true myimage:1.0
```

**Docker Compose**:
```yaml
services:
  myapp:
    container_name: myapp
    image: myapp:1.0
    labels:
      autoheal: "true"
```

### 2. Test the Fix

```bash
# Start container
docker run --name test-app --label autoheal=true nginx:1.25

# Enable monitoring (via UI or API)

# Recreate container (new ID, same name)
docker stop test-app && docker rm test-app
docker run --name test-app --label autoheal=true nginx:1.26

# ✅ Monitoring should persist!
```

### 3. Verify Monitoring

```bash
# Check monitored containers
curl http://localhost:3131/api/containers | jq '.[] | select(.monitored==true)'

# Check events
curl http://localhost:3131/api/events | jq '.[] | select(.event_type=="restart")'
```

## 🔍 What's Tracked by Name Now

- ✅ Selected containers (`config.containers.selected`)
- ✅ Excluded containers (`config.containers.excluded`)
- ✅ Restart counts (persists across recreations)
- ✅ Quarantine status (persists across recreations)
- ✅ Custom health checks (persists across recreations)
- ✅ Backoff delays (persists across recreations)
- ✅ Cooldown timers (persists across recreations)

## 📊 Backwards Compatibility

| Feature | Old (ID-based) | New (Name-based) | Status |
|---------|---------------|------------------|--------|
| Existing configs | ✅ Works | ✅ Works | Both supported |
| New containers | ⚠️ Breaks on recreate | ✅ Persists | Name preferred |
| API lookups | ✅ Still works | ✅ Primary method | Dual lookup |
| Events | ✅ Stored for reference | ✅ Primary key | Both stored |

## 🚀 Migration

**No action needed!** The system automatically:
1. Continues to work with old ID-based configs
2. Uses names for all new containers
3. Gradually migrates as containers are recreated

## ⚠️ Important Notes

### ✅ DO:
- Use explicit container names (`--name` or `container_name`)
- Use explicit image tags (`nginx:1.25` not `nginx:latest`)
- Use the `autoheal=true` label for auto-monitoring
- Use consistent, descriptive names

### ❌ DON'T:
- Rely on auto-generated container names
- Change container names frequently
- Use `latest` tag without a name
- Skip naming in Docker Compose

## 🐛 Troubleshooting

### Monitoring Lost After Recreation?

**Check 1**: Does the container have a name?
```bash
docker inspect <container> | jq '.[0].Name'
```
If it's auto-generated (e.g., `/eloquent_einstein`), use `--name` instead.

**Check 2**: Is the name in the config?
```bash
curl http://localhost:3131/api/config | jq '.containers.selected'
```

**Check 3**: Was the container recreated with a different name?
```bash
docker ps -a --format '{{.Names}}'
```

### Container Still Quarantined After Fix?

```bash
# Unquarantine by name
curl -X POST http://localhost:3131/api/containers/<container-name>/unquarantine

# Or by ID (backwards compatible)
curl -X POST http://localhost:3131/api/containers/<container-id>/unquarantine
```

## 📖 Full Documentation

See [CONTAINER_ID_BUG_FIX.md](./CONTAINER_ID_BUG_FIX.md) for complete details.

---

**Status**: ✅ **FIXED** - Container monitoring now persists across recreations!

