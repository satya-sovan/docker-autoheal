# Quick Start Guide - Docker Auto-Heal Service

This guide will help you get the Docker Auto-Heal Service up and running in 5 minutes.

## Prerequisites

✅ Docker installed and running  
✅ Docker Compose installed (optional but recommended)  
✅ Internet connection to pull images  

## Step 1: Start the Service

### Option A: Using Docker Compose (Recommended)

```bash
# Start the service
docker-compose up -d

# Check if it's running
docker ps | grep autoheal
```

### Option B: Using Docker directly

```bash
# Build the image
docker build -t docker-autoheal .

# Run the container
docker run -d \
  --name autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 8080:8080 \
  -p 9090:9090 \
  --restart unless-stopped \
  docker-autoheal
```

## Step 2: Access the Web UI

Open your browser and navigate to:

```
http://localhost:8080
```

You should see the Docker Auto-Heal dashboard with:
- Total containers count
- Monitored containers
- Quarantined containers
- Service status

## Step 3: Test with Sample Containers

### Start test containers

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# This will start:
# - autoheal service
# - nginx-healthy (monitored, should stay healthy)
# - failing-container (will exit, should be restarted)
# - http-test (Python HTTP server with health check)
# - redis-test (Redis with health check)
# - nginx-no-autoheal (not monitored)
```

### Watch the magic happen

```bash
# Watch container status
watch docker ps

# View autoheal logs
docker logs -f autoheal

# Check events in the UI
# Navigate to Events tab in http://localhost:8080
```

## Step 4: Enable Auto-Heal for a Container

### Via Web UI (Easy):

1. Go to **Containers** tab
2. Find your container in the list
3. Check the checkbox next to it
4. Click **Enable Auto-Heal** button

### Via Docker Labels (Production):

Add label when creating container:

```bash
docker run -d \
  --name my-app \
  --label autoheal=true \
  nginx:alpine
```

Or in docker-compose.yml:

```yaml
services:
  my-app:
    image: nginx:alpine
    labels:
      - "autoheal=true"
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Step 5: Configure Settings

### Adjust Monitoring Interval

1. Go to **Configuration** tab
2. Under **Monitor Settings**:
   - Set **Monitoring Interval** (e.g., 30 seconds)
   - Choose label filters
3. Click **Save Monitor Settings**

### Configure Restart Policy

1. In **Configuration** tab
2. Under **Restart Policy**:
   - **Mode**: `both` (restart on failure OR unhealthy)
   - **Cooldown**: 60 seconds (wait between restarts)
   - **Max Restarts**: 3 (before quarantine)
   - **Max Restarts Window**: 600 seconds
3. Click **Save Restart Policy**

## Common Use Cases

### Use Case 1: Monitor All Running Containers

```bash
# Via UI:
# Configuration → Monitor Settings → Check "Monitor All Containers" → Save
```

### Use Case 2: Add Custom HTTP Health Check

```bash
# Via UI:
# Containers → Find container → Click heart icon → Select HTTP
# Enter: http://localhost:8080/health
# Set status code: 200
# Click Save
```

### Use Case 3: Unquarantine a Container

```bash
# Via UI:
# Containers → Find quarantined container → Click unlock icon

# Via command line:
curl -X POST http://localhost:8080/api/containers/{container_id}/unquarantine
```

### Use Case 4: Export Configuration

```bash
# Via UI:
# Configuration → Click "Export Configuration" → Downloads JSON file

# Via API:
curl -O http://localhost:8080/api/config/export
```

## Monitoring

### View Metrics (Prometheus)

```
http://localhost:9090/metrics
```

### View API Documentation

```
http://localhost:8080/docs
```

### View Logs

```bash
# Container logs
docker logs autoheal

# Follow logs
docker logs -f autoheal

# Last 100 lines
docker logs --tail 100 autoheal
```

## Troubleshooting

### Service won't start

```bash
# Check if Docker is running
docker info

# Check socket permissions (Linux)
ls -l /var/run/docker.sock

# View error logs
docker logs autoheal
```

### Container not being monitored

1. ✅ Check container has `autoheal=true` label:
   ```bash
   docker inspect container_name | grep -A 5 Labels
   ```

2. ✅ Check Configuration → filters (whitelist/blacklist)

3. ✅ Check Events tab for monitoring decisions

### UI not accessible

```bash
# Check if port 8080 is available
netstat -an | grep 8080

# Check container is running
docker ps | grep autoheal

# Check health
curl http://localhost:8080/health
```

## Next Steps

✅ Add `autoheal=true` label to your production containers  
✅ Configure custom health checks for your services  
✅ Set up Prometheus monitoring  
✅ Export and backup your configuration  
✅ Review the full documentation in README.md  

## Clean Up (When Testing)

```bash
# Stop and remove test containers
docker-compose -f docker-compose.test.yml down

# Stop and remove autoheal
docker-compose down

# Remove all (including volumes)
docker-compose down -v
```

---

## Quick Reference - Common Commands

```bash
# Start service
docker-compose up -d

# View logs
docker logs -f autoheal

# Stop service
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View all containers with autoheal label
docker ps --filter "label=autoheal=true"

# Check service health
curl http://localhost:8080/health

# View events via API
curl http://localhost:8080/api/events | jq

# Restart a container manually via API
curl -X POST http://localhost:8080/api/containers/{id}/restart
```

---

**Need help?** Check the full README.md or visit the API docs at http://localhost:8080/docs

