# 🚀 Auto-Monitoring Quick Start

## What is Auto-Monitoring?

Auto-monitoring automatically adds containers to the monitoring list when they start, if they have the `autoheal=true` label. No manual configuration needed!

## Quick Start

### 1. Add the Label

**Docker Run:**
```bash
docker run -d --name my-app --label autoheal=true nginx:alpine
```

**Docker Compose:**
```yaml
services:
  my-app:
    image: nginx:alpine
    labels:
      - "autoheal=true"
```

### 2. That's It!

The container is now automatically monitored. Check the logs:

```bash
docker logs docker-autoheal | grep "Auto-monitoring"
```

You should see:
```
INFO - ✓ Auto-monitoring enabled for container 'my-app' (abc123def456) - detected autoheal=true label
```

## How It Works

```
Container Starts → Event Detected → Label Check → Auto-Add to Monitoring
```

## Examples

### Example 1: Single Container
```bash
docker run -d \
  --name web-server \
  --label autoheal=true \
  -p 8080:80 \
  nginx:alpine
```

### Example 2: Multiple Services
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
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
  
  database:
    image: postgres:14
    # No label - not monitored
```

### Example 3: With Health Check
```bash
docker run -d \
  --name api \
  --label autoheal=true \
  --health-cmd "curl -f http://localhost/health || exit 1" \
  --health-interval 30s \
  --health-retries 3 \
  my-api:latest
```

## Verification

### Check Events (Web UI)
1. Open http://localhost:8080
2. Go to **Events** tab
3. Look for `auto_monitor` events

### Check Events (API)
```bash
curl http://localhost:8080/api/events | jq '.[] | select(.event_type=="auto_monitor")'
```

### Check Monitored List
```bash
curl http://localhost:8080/api/config | jq '.containers.selected'
```

## Troubleshooting

### Container Not Auto-Monitored?

**1. Check the label:**
```bash
docker inspect my-app | jq '.[0].Config.Labels.autoheal'
```
Should return: `"true"`

**2. Check autoheal logs:**
```bash
docker logs docker-autoheal | grep -i "auto-monitor"
```

**3. Verify container started:**
```bash
docker ps -f name=my-app
```

**4. Check if excluded:**
```bash
curl http://localhost:8080/api/config | jq '.containers.excluded'
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Label typo | Must be exactly `autoheal=true` |
| Container in excluded list | Remove from excluded |
| Autoheal service not running | Check `docker ps \| grep autoheal` |
| Docker socket not mounted | Add `-v /var/run/docker.sock:/var/run/docker.sock:ro` |

## Testing

Run the test script:
```bash
python test_auto_monitor.py
```

This will:
1. Start a container with `autoheal=true`
2. Verify it's auto-monitored
3. Start a container without the label
4. Verify it's NOT auto-monitored

## Benefits

✅ **Zero Configuration** - Just add a label  
✅ **Works with CI/CD** - Deploy and forget  
✅ **Dynamic** - Containers added on start  
✅ **Auditable** - All actions logged  
✅ **Safe** - Respects excluded list  

## Next Steps

- [Full Auto-Monitoring Guide](./AUTO_MONITOR_FEATURE.md)
- [Main Documentation](./README.md)
- [Configuration Guide](./GETTING_STARTED.md)

## Summary

```bash
# That's all you need!
docker run -d --label autoheal=true my-app:latest
```

Your container is now automatically monitored for failures and will be auto-restarted if needed!

