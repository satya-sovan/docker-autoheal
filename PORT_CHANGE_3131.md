# ✅ UI Port Changed from 8080 to 3131

## Summary

The Web UI port has been changed from **8080** to **3131** throughout the entire project.

## Files Updated

### Configuration Files
1. ✅ `config.py` - Default port changed to 3131
2. ✅ `config-example.json` - Example port updated
3. ✅ `data/config.json` - Active config updated

### Docker Compose Files
4. ✅ `docker-compose.yml` - Port mapping updated to `3131:3131`
5. ✅ `docker-compose.yml` - Health check URL updated
6. ✅ `docker-compose.simple.yml` - Port and health check updated
7. ✅ `docker-compose.test.yml` - Port and health check updated
8. ✅ `docker-compose.example.yml` - Port updated

### Documentation Files
9. ✅ `DOCKER_HUB_README.md` - All port references updated (10+ locations)

### Test Scripts
10. ✅ `demo.py` - BASE_URL updated
11. ✅ `test_service.py` - BASE_URL updated
12. ✅ `test_auto_monitor.py` - All API URLs updated (4 locations)

## What Changed

### Before
```yaml
ports:
  - "8080:8080"  # Web UI
```
```python
listen_port: int = Field(default=8080)
```
```bash
curl http://localhost:8080/health
```

### After
```yaml
ports:
  - "3131:3131"  # Web UI
```
```python
listen_port: int = Field(default=3131)
```
```bash
curl http://localhost:3131/health
```

## How to Apply

### If Service is Running
```bash
# Stop the service
docker-compose down

# Start with new port
docker-compose up --build -d

# Verify UI loads on new port
curl http://localhost:3131/health
```

### Access the UI
- **Old URL**: ~~http://localhost:8080~~
- **New URL**: http://localhost:3131

## Quick Test

```bash
# Check service is running
docker ps | grep docker-autoheal

# Test health endpoint
curl http://localhost:3131/health

# Should return:
# {"status":"healthy","timestamp":"...","docker_connected":true,"monitoring_active":true}

# Open in browser
# http://localhost:3131
```

## Port Mapping Reference

| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 3131 | React web interface and API |
| Metrics | 9090 | Prometheus metrics endpoint |

## Docker Commands with New Port

### Docker Run
```bash
docker run -d \
  --name docker-autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./data:/data \
  -p 3131:3131 \
  -p 9090:9090 \
  --restart unless-stopped \
  yourusername/docker-autoheal:latest
```

### Health Check
```bash
docker run --rm \
  --network container:docker-autoheal \
  curlimages/curl:latest \
  curl -f http://localhost:3131/health
```

## API Endpoints

All API endpoints now use port 3131:

- **Health**: `http://localhost:3131/health`
- **API Docs**: `http://localhost:3131/docs`
- **Status**: `http://localhost:3131/api/status`
- **Containers**: `http://localhost:3131/api/containers`
- **Events**: `http://localhost:3131/api/events`
- **Config**: `http://localhost:3131/api/config`

## Browser Bookmarks

Update your bookmarks:
- Dashboard: `http://localhost:3131`
- API Docs: `http://localhost:3131/docs`
- Metrics: `http://localhost:9090/metrics`

## Troubleshooting

### Port Already in Use?

```bash
# Check what's using port 3131
netstat -ano | findstr :3131

# On Linux/Mac
lsof -i :3131
```

### Old Port Still Working?

```bash
# Make sure old containers are removed
docker-compose down
docker ps -a | grep autoheal
docker rm -f docker-autoheal

# Rebuild and restart
docker-compose up --build -d
```

### Can't Access UI?

```bash
# Check service is listening
docker logs docker-autoheal | grep "Uvicorn running"

# Should see:
# INFO - Uvicorn running on http://0.0.0.0:3131

# Check port mapping
docker port docker-autoheal

# Should show:
# 3131/tcp -> 0.0.0.0:3131
# 9090/tcp -> 0.0.0.0:9090
```

## Summary

✅ **Port changed from 8080 to 3131**  
✅ **All files updated (12 files)**  
✅ **Docker Compose files updated**  
✅ **Documentation updated**  
✅ **Test scripts updated**  
✅ **Health checks updated**  

## Next Steps

1. **Restart the service**:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

2. **Access new URL**:
   ```
   http://localhost:3131
   ```

3. **Update any external tools**:
   - Monitoring dashboards
   - Reverse proxies
   - CI/CD pipelines
   - Documentation

---

**Status**: ✅ COMPLETE

**New UI URL**: http://localhost:3131

**Action Required**: Restart service with `docker-compose up --build -d`

