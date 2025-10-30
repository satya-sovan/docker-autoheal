# 🚀 Getting Started - React UI on Port 8080

This guide will get you up and running in **2 minutes**.

## Prerequisites

- ✅ Docker installed and running
- ✅ Docker Compose installed
- ✅ Port 8080 available

That's it! No Node.js required for production.

## Quick Start

### Step 1: Build and Start

```bash
# Navigate to project directory
cd docker-autoheal

# Build and start (React builds automatically)
docker-compose up --build
```

**What happens:**
1. Docker builds the React UI (takes ~30 seconds first time)
2. Python backend starts
3. UI is served on port 8080

### Step 2: Access the UI

Open your browser:
```
http://localhost:8080
```

You should see the React dashboard with:
- Total containers count
- Monitored containers
- Service status
- Container list

### Step 3: Verify It Works

Run the test script:
```bash
python test_service.py
```

Or manually check:
```bash
# Health check
curl http://localhost:8080/health

# API status
curl http://localhost:8080/api/status

# Open UI
start http://localhost:8080
```

## That's It! 🎉

You're now running the Docker Auto-Heal Service with React UI on port 8080.

## What to Do Next

### 1. Add Containers to Monitor

Label your containers with `autoheal=true`:

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
```

### 2. Enable Auto-Heal via UI

1. Go to **Containers** tab
2. Check the containers you want to monitor
3. Click **Enable Auto-Heal**

### 3. Configure Settings

1. Go to **Configuration** tab
2. Adjust monitoring interval
3. Set restart policies
4. Export your config

### 4. Monitor Activity

1. Go to **Events** tab
2. See auto-heal actions in real-time
3. Track restart counts

## Development Mode (Optional)

Want to modify the React UI with hot reload?

### Terminal 1: Backend
```bash
docker-compose up
```

### Terminal 2: React Dev Server
```bash
cd frontend
npm install
npm run dev
```

Now access:
- Dev UI with hot reload: http://localhost:3000
- Backend API: http://localhost:8080

Make changes in `frontend/src/` and see them instantly!

## Common Commands

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker logs -f docker-autoheal

# Rebuild (after changes)
docker-compose up --build

# Restart service
docker-compose restart

# Check status
docker ps | grep autoheal
```

## Ports

| Port | Service |
|------|---------|
| **8080** | **React UI + API** ← Main access point |
| 9090 | Prometheus metrics |

## Troubleshooting

### UI shows "React UI not found"

**Solution:**
```bash
docker-compose down
docker-compose up --build
```

### Port 8080 already in use

**Solution 1 - Change port:**
Edit `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

**Solution 2 - Kill process:**
```bash
# Find process using port 8080
netstat -ano | findstr :8080

# Kill it (replace PID)
taskkill /PID <pid> /F
```

### Container not starting

**Check logs:**
```bash
docker logs docker-autoheal
```

**Common issues:**
- Docker socket not accessible
- Port 8080 in use
- Build failed

**Solution:**
```bash
docker-compose down
docker-compose up --build --force-recreate
```

## File Structure

```
docker-autoheal/
├── frontend/           # React source code
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── services/   # API client
│   │   └── styles/     # CSS
│   └── package.json
│
├── *.py                # Python backend
├── Dockerfile          # Multi-stage build
├── docker-compose.yml  # Docker Compose config
└── requirements.txt    # Python dependencies
```

## Key Features

Access these features at http://localhost:8080:

- ✅ **Dashboard** - Real-time metrics
- ✅ **Container Management** - Enable/disable auto-heal
- ✅ **Event Log** - Track all actions
- ✅ **Configuration** - Adjust settings
- ✅ **Export/Import** - Backup configs

## API Documentation

Interactive docs available at:
```
http://localhost:8080/docs
```

## Testing

Test with a sample container:

```bash
# Start nginx with autoheal label
docker run -d \
  --name test-nginx \
  --label autoheal=true \
  -p 8081:80 \
  nginx:alpine

# View in UI
# Go to http://localhost:8080
# See test-nginx in Containers tab
```

Kill it to see auto-heal in action:
```bash
docker kill test-nginx
# Check Events tab - should show restart attempt
```

## Production Deployment

For production:

1. **Review security**: Add authentication if exposing publicly
2. **Configure properly**: Adjust monitoring intervals and thresholds
3. **Export config**: Backup your configuration
4. **Set restart policy**: Ensure `restart: unless-stopped` in compose
5. **Monitor logs**: Check regularly for issues

## Getting Help

1. **Check logs**: `docker logs docker-autoheal`
2. **Run test**: `python test_service.py`
3. **Read docs**: See SETUP.md and REACT_ADDED.md
4. **API docs**: http://localhost:8080/docs

## Summary

✅ **One command**: `docker-compose up --build`  
✅ **One port**: http://localhost:8080  
✅ **React UI**: Built automatically  
✅ **No Node.js**: Required only for development  

**Start monitoring your containers now! 🚀**

