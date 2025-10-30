# 🏷️ Auto-Monitoring Feature - Label-Based Container Discovery

## Overview

The Docker Auto-Heal service now includes automatic monitoring of containers based on labels. When a container with the `autoheal=true` label starts, it is automatically added to the monitored containers list.

## How It Works

### Event Listener
- A background event listener monitors Docker events in real-time
- Specifically listens for container `start` events
- When a container starts, it checks for the `autoheal=true` label
- If found, the container is automatically added to the monitoring list

### Automatic Detection Flow

```
Container Starts
       ↓
Event Detected
       ↓
Check for autoheal=true label
       ↓
Label Found → Add to Monitored List → Log Event
       ↓
Container is now monitored for health issues
```

## Usage

### 1. Docker Run Command

Add the label when starting a container:

```bash
docker run -d \
  --name my-app \
  --label autoheal=true \
  nginx:latest
```

### 2. Docker Compose

Add the label in your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    image: nginx:latest
    labels:
      - "autoheal=true"
    
  api:
    image: my-api:latest
    labels:
      - "autoheal=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Dockerfile

Add the label in your Dockerfile:

```dockerfile
FROM nginx:latest
LABEL autoheal=true
# ... rest of your Dockerfile
```

## Features

### ✅ Automatic Discovery
- No manual configuration needed
- Containers are discovered on start
- Works with existing containers when they restart

### 📝 Event Logging
Every auto-monitored container generates an event:
- **Event Type**: `auto_monitor`
- **Status**: `enabled`
- **Message**: Details about the label detection
- **Timestamp**: When the container was added

### 🔍 Smart Filtering
The auto-monitor respects existing configuration:
- ✅ Skips containers in the **excluded list**
- ✅ Avoids duplicate entries
- ✅ Only processes containers with exact label match

### 🚨 Log Messages

When a container is auto-discovered, you'll see:

```
INFO - ✓ Auto-monitoring enabled for container 'my-app' (a1b2c3d4e5f6) - detected autoheal=true label
```

## Configuration

### Label Requirements

The label must match exactly:
- **Key**: `autoheal`
- **Value**: `true`
- Case-sensitive

### Excluded Containers

If a container is in the excluded list, it won't be auto-monitored even with the label:

```json
{
  "containers": {
    "excluded": ["my-excluded-container"]
  }
}
```

## Viewing Auto-Monitored Containers

### 1. Web UI
- Go to the **Containers** page
- Look for containers with the `autoheal=true` label
- Monitored containers will show as "Enabled for Auto-Heal"

### 2. Events Page
- Check the **Events** page
- Look for events with type `auto_monitor`
- Shows when containers were automatically added

### 3. API Endpoint

```bash
# Get all events
curl http://localhost:8080/api/events

# Filter for auto-monitor events
curl http://localhost:8080/api/events | jq '.[] | select(.event_type=="auto_monitor")'
```

## Example Scenarios

### Scenario 1: Microservices Architecture

```yaml
version: '3.8'

services:
  frontend:
    image: my-frontend:latest
    labels:
      - "autoheal=true"
  
  backend:
    image: my-backend:latest
    labels:
      - "autoheal=true"
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s
  
  database:
    image: postgres:14
    # No autoheal label - not monitored
  
  cache:
    image: redis:7
    labels:
      - "autoheal=true"
```

**Result**: Frontend, backend, and cache are automatically monitored. Database is not.

### Scenario 2: Testing Containers

```bash
# Start a test container with autoheal
docker run -d \
  --name test-app \
  --label autoheal=true \
  --label environment=test \
  my-app:test

# Container is automatically monitored
# If it crashes, it will be auto-restarted
```

### Scenario 3: Kubernetes-Style Labels

```bash
docker run -d \
  --name production-api \
  --label autoheal=true \
  --label app=api \
  --label env=production \
  --label version=v1.2.0 \
  my-api:latest
```

## Benefits

### 🚀 Zero Configuration
- Deploy and forget
- No need to manually add containers
- Works with CI/CD pipelines

### 🔄 Dynamic Updates
- New containers are automatically discovered
- Restarted containers are re-evaluated
- Scales with your infrastructure

### 📊 Better Observability
- All auto-monitoring events are logged
- Track which containers are being monitored
- Audit trail in event history

### 🛡️ Safety
- Respects excluded list
- No duplicate monitoring
- Clean error handling

## Troubleshooting

### Container Not Auto-Monitored?

**Check the label:**
```bash
docker inspect my-container | jq '.[0].Config.Labels'
```

Should show:
```json
{
  "autoheal": "true"
}
```

**Check the logs:**
```bash
docker logs docker-autoheal | grep "Auto-monitoring"
```

**Verify it's not excluded:**
```bash
curl http://localhost:8080/api/config | jq '.containers.excluded'
```

### Event Listener Not Working?

**Check service status:**
```bash
docker logs docker-autoheal | grep "Event listener"
```

Should see:
```
INFO - Event listener started for auto-monitoring containers with autoheal=true label
```

**Check Docker events:**
```bash
docker events --filter type=container --filter event=start
```

### Common Issues

1. **Label typo**: Must be exactly `autoheal=true`
2. **Container in excluded list**: Remove from excluded
3. **Docker socket not mounted**: Check volume mount
4. **Service not running**: Restart autoheal service

## Technical Details

### Implementation

The feature consists of three components:

1. **Event Listener Loop** (`_event_listener_loop`)
   - Runs in background asyncio task
   - Filters for container start events
   - Processes each event asynchronously

2. **Event Processor** (`_process_container_start_event`)
   - Extracts container information
   - Checks for autoheal label
   - Adds to monitored list if found

3. **Docker Client Method** (`get_events`)
   - Wraps Docker SDK events API
   - Provides filtered event stream
   - Handles connection errors

### Performance

- **Minimal overhead**: Events processed asynchronously
- **No polling**: Real-time event-driven
- **Efficient filtering**: Docker filters applied at API level
- **Graceful degradation**: Continues on errors

### Compatibility

- ✅ Docker Engine 19.03+
- ✅ Docker Compose v3+
- ✅ Kubernetes (with Docker runtime)
- ✅ Podman (experimental)

## Best Practices

### 1. Use with Health Checks

Combine auto-monitoring with health checks:

```yaml
services:
  api:
    image: my-api:latest
    labels:
      - "autoheal=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2. Label Critical Services Only

Not every container needs auto-healing:

```yaml
services:
  # Critical - needs autoheal
  payment-service:
    labels:
      - "autoheal=true"
  
  # Ephemeral - no autoheal needed
  migration-job:
    labels:
      - "autoheal=false"
```

### 3. Document Your Labels

Add comments in docker-compose.yml:

```yaml
services:
  api:
    image: my-api:latest
    labels:
      # Enable automatic health monitoring
      - "autoheal=true"
      # Application metadata
      - "app=api"
      - "team=backend"
```

### 4. Monitor the Monitor

Check autoheal logs regularly:

```bash
# View recent auto-monitor events
docker logs docker-autoheal | grep "Auto-monitoring" | tail -n 20
```

## API Integration

### Get Auto-Monitored Containers

```python
import requests

# Get all events
response = requests.get('http://localhost:8080/api/events')
events = response.json()

# Filter auto-monitor events
auto_monitored = [
    e for e in events 
    if e['event_type'] == 'auto_monitor'
]

for event in auto_monitored:
    print(f"{event['container_name']} - {event['timestamp']}")
```

### Remove from Monitoring

```python
import requests

# Get container ID
container_id = "abc123def456"

# Get current config
config = requests.get('http://localhost:8080/api/config').json()

# Remove from selected list
config['containers']['selected'].remove(container_id)

# Update config
requests.post('http://localhost:8080/api/config', json=config)
```

## Future Enhancements

Potential improvements:

- [ ] Support for label patterns (e.g., `autoheal=*`)
- [ ] Multiple label keys support
- [ ] Auto-remove when label is removed
- [ ] Label-based configuration overrides
- [ ] Webhook notifications for auto-monitoring

## Summary

The auto-monitoring feature makes Docker Auto-Heal even more powerful by eliminating manual configuration. Simply add `autoheal=true` to your containers, and they'll be automatically monitored when they start.

**Key Points:**
- ✅ Label-based automatic discovery
- ✅ Real-time event processing
- ✅ Comprehensive logging
- ✅ Zero configuration required
- ✅ Works with existing infrastructure

---

**Need help?** Check the main documentation or open an issue on GitHub.

