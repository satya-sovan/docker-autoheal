# Log Level Configuration and Management

## Overview

The Docker Auto-Heal Service now supports dynamic log level configuration through the UI, allowing you to control logging verbosity without restarting the service.

## Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **DEBUG** | Most verbose - shows all operations | Development, troubleshooting |
| **INFO** | Standard operations and events | **Default - Recommended for production** |
| **WARNING** | Important warnings and issues | Production with minimal logs |
| **ERROR** | Errors only | Critical issues only |
| **CRITICAL** | Critical failures only | Emergency situations |

## Configuration

### Via UI (Recommended)

1. Open http://localhost:8080
2. Go to **Configuration** tab
3. Find **Observability Settings** card
4. Select desired **Log Level** from dropdown
5. Click **Save Observability Settings**
6. **Log level applies immediately** - no restart needed!

### Via API

```bash
curl -X PUT http://localhost:8080/api/config/observability \
  -H "Content-Type: application/json" \
  -d '{"log_level": "DEBUG"}'
```

### Via Configuration File

Edit `config.py` or use the config manager:

```python
config.observability.log_level = "DEBUG"
```

## Log Level Behavior

### DEBUG Level
Shows everything:
- ✅ Container selection details
- ✅ Monitoring checks
- ✅ Cooldown periods
- ✅ Backoff delays
- ✅ Static file mounting
- ✅ All INFO, WARNING, ERROR, CRITICAL

**Use for**: Debugging issues, understanding flow

### INFO Level (Default)
Shows important operations:
- ✅ Service startup/shutdown
- ✅ Container restarts
- ✅ Quarantine actions
- ✅ Configuration changes
- ✅ All WARNING, ERROR, CRITICAL
- ❌ Routine checks (DEBUG level)

**Use for**: Normal production operation

### WARNING Level
Shows warnings and errors:
- ✅ Connection issues
- ✅ Retry attempts
- ✅ Unusual conditions
- ✅ All ERROR, CRITICAL
- ❌ Normal operations (INFO/DEBUG)

**Use for**: Reduced logging, focus on issues

### ERROR Level
Shows errors only:
- ✅ Failed operations
- ✅ Exceptions
- ✅ All CRITICAL
- ❌ Successful operations
- ❌ Warnings

**Use for**: Minimal logging, critical issues

### CRITICAL Level
Shows only critical failures:
- ✅ Service-level failures
- ✅ Fatal errors
- ❌ Everything else

**Use for**: Emergency situations only

## What Changed - Log Spam Reduction

### Before
```
INFO: Container selection request: containers=['abc123'], enabled=True
INFO: Added container abc123 to selected list
INFO: Configuration updated. Selected: ['abc123'], Excluded: []
INFO: Serving React UI from static directory
INFO: Applying backoff delay of 10s for mycontainer
```
**Result**: Logs filled with routine operations

### After
```
# With INFO level (default):
INFO: Container selection updated: 1 container(s) enabled
INFO: Restarting container mycontainer (reason: Container exited with code 137)
INFO: Successfully restarted container mycontainer

# With DEBUG level:
DEBUG: Container selection request: containers=['abc123'], enabled=True
DEBUG: Added container abc123 to selected list
DEBUG: Static files mounted: React UI available
DEBUG: Applying backoff delay of 10s for mycontainer
INFO: Container selection updated: 1 container(s) enabled
INFO: Restarting container mycontainer (reason: Container exited with code 137)
```

**Result**: Clean logs showing important events, debug details available when needed

## Log Changes Summary

### API (api.py)
- Container selection: INFO → DEBUG
- Static mounting: INFO → DEBUG
- Selection summary: Simplified to one INFO line

### Monitor (monitor.py)
- Backoff delays: INFO → DEBUG
- Cooldown checks: Already DEBUG
- Container selection: Already DEBUG

### Maintained Levels
- ✅ Service startup: INFO
- ✅ Container restarts: INFO
- ✅ Quarantine actions: WARNING
- ✅ Errors: ERROR
- ✅ Critical failures: CRITICAL

## Testing Log Levels

### Test DEBUG Level
```bash
# 1. Set to DEBUG
curl -X PUT http://localhost:8080/api/config/observability \
  -H "Content-Type: application/json" \
  -d '{"log_level": "DEBUG"}'

# 2. Perform an action (e.g., enable auto-heal)

# 3. Check logs - should see detailed output
docker logs docker-autoheal --tail 20
```

### Test INFO Level
```bash
# 1. Set to INFO
curl -X PUT http://localhost:8080/api/config/observability \
  -H "Content-Type: application/json" \
  -d '{"log_level": "INFO"}'

# 2. Perform same action

# 3. Check logs - should see summary only
docker logs docker-autoheal --tail 20
```

## Recommended Settings

| Environment | Log Level | Reason |
|-------------|-----------|--------|
| **Development** | DEBUG | See everything, troubleshoot easily |
| **Staging** | INFO | Normal operations, sufficient detail |
| **Production** | INFO | **Recommended** - balance of detail and performance |
| **Production (High-Scale)** | WARNING | Reduce log volume |
| **Troubleshooting** | DEBUG | Maximum detail for debugging |

## Performance Impact

| Level | Log Volume | Performance Impact |
|-------|------------|-------------------|
| DEBUG | High (100%) | Minimal (~1-2% CPU) |
| INFO | Medium (40%) | Negligible |
| WARNING | Low (10%) | None |
| ERROR | Very Low (1%) | None |

## Viewing Logs

### Docker Logs
```bash
# Follow logs
docker logs -f docker-autoheal

# Last 50 lines
docker logs docker-autoheal --tail 50

# Since 5 minutes ago
docker logs docker-autoheal --since 5m

# Filter for specific level
docker logs docker-autoheal | grep "ERROR"
```

### Log Files
Logs are also written to `autoheal.log` in the container:

```bash
# View log file
docker exec docker-autoheal cat autoheal.log

# Tail log file
docker exec docker-autoheal tail -f autoheal.log
```

## Dynamic Configuration

**Key Feature**: Log level changes apply **immediately** without restart!

```
1. Change log level in UI
2. Click Save
3. New log level active instantly
4. No service interruption
5. All loggers updated
```

## Troubleshooting

### Issue: Not seeing expected logs

**Check current level:**
```bash
curl http://localhost:8080/api/config | jq '.observability.log_level'
```

**Set to DEBUG:**
```bash
curl -X PUT http://localhost:8080/api/config/observability \
  -H "Content-Type: application/json" \
  -d '{"log_level": "DEBUG"}'
```

### Issue: Too many logs

**Reduce verbosity:**
1. Go to Configuration → Observability Settings
2. Change Log Level to WARNING or ERROR
3. Click Save

### Issue: Missing important events

**Use INFO level (default):**
- Shows all important operations
- Hides routine checks
- Balanced approach

## Best Practices

1. **Start with INFO** - Default for good reason
2. **Use DEBUG temporarily** - For troubleshooting only
3. **Monitor log volume** - Adjust if logs too large
4. **Export logs regularly** - For analysis
5. **Use WARNING in production** - If scaling issues
6. **Never use CRITICAL** - Except emergency debugging

## Integration with Monitoring

### Prometheus Metrics
Logging level doesn't affect metrics:
- Metrics continue regardless of log level
- Available on port 9090
- Independent of logging

### Events Tab
Events are logged separately:
- Not affected by log level
- Always visible in UI
- Persistent in memory

## Configuration Persistence

**Note**: Log level is stored in configuration:
- ✅ Persists until service restart
- ✅ Can be exported with config
- ✅ Can be imported on restore
- ❌ Not persisted across container rebuilds (unless config imported)

**Recommendation**: Export configuration after setting preferred log level

## Summary

✅ **Dynamic log level control** - Change anytime via UI
✅ **No restart required** - Applies immediately
✅ **Reduced log spam** - INFO level shows important events only
✅ **Debug when needed** - Switch to DEBUG for troubleshooting
✅ **Production-ready** - Default INFO level is optimized

**Access configuration**: http://localhost:8080 → Configuration tab → Observability Settings

