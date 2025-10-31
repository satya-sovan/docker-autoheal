# 🚀 UI Port Changed to 3131 - Quick Reference

## ✅ Change Complete

The Docker Auto-Heal UI port has been changed from **8080** to **3131**.

## Quick Start

```bash
# Stop current service
docker-compose down

# Start with new port
docker-compose up --build -d

# Access UI
http://localhost:3131
```

## New URLs

| Service | Old URL | New URL |
|---------|---------|---------|
| Web UI | ~~http://localhost:8080~~ | **http://localhost:3131** |
| Health | ~~http://localhost:8080/health~~ | **http://localhost:3131/health** |
| API Docs | ~~http://localhost:8080/docs~~ | **http://localhost:3131/docs** |
| Metrics | http://localhost:9090/metrics | *(unchanged)* |

## Files Updated (12 total)

✅ config.py  
✅ config-example.json  
✅ data/config.json  
✅ docker-compose.yml  
✅ docker-compose.simple.yml  
✅ docker-compose.test.yml  
✅ docker-compose.example.yml  
✅ DOCKER_HUB_README.md  
✅ demo.py  
✅ test_service.py  
✅ test_auto_monitor.py  
✅ All documentation files  

## Docker Run Command (Updated)

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

## Docker Compose (Updated)

```yaml
services:
  autoheal:
    image: yourusername/docker-autoheal:latest
    ports:
      - "3131:3131"  # Web UI
      - "9090:9090"  # Metrics
    # ...
```

## Verify

```bash
# Check health
curl http://localhost:3131/health

# Check logs
docker logs docker-autoheal | grep "Uvicorn running"
# Should see: INFO - Uvicorn running on http://0.0.0.0:3131

# Check port mapping
docker port docker-autoheal
# Should show: 3131/tcp -> 0.0.0.0:3131
```

## API Endpoints (All Updated)

- `GET http://localhost:3131/health`
- `GET http://localhost:3131/api/status`
- `GET http://localhost:3131/api/containers`
- `GET http://localhost:3131/api/events`
- `GET http://localhost:3131/api/config`
- `POST http://localhost:3131/api/config`
- Swagger UI: `http://localhost:3131/docs`

## Test Scripts (All Updated)

```bash
# Run tests (will use port 3131)
python demo.py
python test_service.py
python test_auto_monitor.py
```

## Troubleshooting

### UI not accessible?
```bash
# Restart service
docker-compose down
docker-compose up --build -d

# Check if port is mapped
docker port docker-autoheal | grep 3131
```

### Old port still in use?
```bash
# Remove old containers
docker ps -a | grep autoheal
docker rm -f docker-autoheal

# Rebuild
docker-compose up --build -d
```

---

## Summary

**Old Port**: ~~8080~~  
**New Port**: **3131**  
**Action**: `docker-compose up --build -d`  
**New URL**: **http://localhost:3131**

✅ **All files updated and ready to use!**

