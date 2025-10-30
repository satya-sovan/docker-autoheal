# 🚀 Quick Reference - Docker Auto-Heal with React UI

## One-Line Start

```bash
docker-compose up --build
```

**Access:** http://localhost:8080

---

## Essential Commands

```bash
# Start (detached)
docker-compose up -d --build

# View logs
docker logs -f docker-autoheal

# Stop
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose up --build --force-recreate
```

---

## Ports

| Port | Service |
|------|---------|
| **8080** | React UI + API |
| 9090 | Prometheus Metrics |

---

## Key URLs

```
UI:          http://localhost:8080
API Docs:    http://localhost:8080/docs
Health:      http://localhost:8080/health
API Status:  http://localhost:8080/api/status
Metrics:     http://localhost:9090/metrics
```

---

## Development Mode

### Terminal 1 - Backend
```bash
docker-compose up
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

**Dev UI:** http://localhost:3000 (hot reload)  
**Backend:** http://localhost:8080

---

## Directory Structure

```
frontend/src/
├── components/     ← Edit React components here
├── services/       ← API client
└── styles/         ← CSS

*.py               ← Python backend
Dockerfile         ← Multi-stage build
docker-compose.yml ← Production config
```

---

## Common Tasks

### Add Container to Monitor

**Option 1: Label (Automatic)**
```yaml
labels:
  - "autoheal=true"
```

**Option 2: UI (Manual)**
1. Go to Containers tab
2. Check container
3. Click "Enable Auto-Heal"

### Export Configuration
1. Go to Configuration tab
2. Click "Export Configuration"
3. Saves JSON file

### View Events
Go to Events tab → See auto-heal history

---

## Troubleshooting

### UI Not Loading
```bash
docker-compose down
docker-compose up --build
```

### Port 8080 In Use
```bash
# Check what's using it
netstat -ano | findstr :8080

# Kill process (replace PID)
taskkill /PID <pid> /F
```

### Container Not Starting
```bash
# Check logs
docker logs docker-autoheal

# Force rebuild
docker-compose down
docker-compose up --build --force-recreate
```

---

## Quick Test

```bash
# Test all endpoints
python test_service.py

# Or manually
curl http://localhost:8080/health
curl http://localhost:8080/api/status
```

---

## Build Process

```
Docker Build → Node.js Stage → Build React → Python Stage → Copy to static/ → Serve on 8080
```

---

## Features

✅ Dashboard with metrics  
✅ Container management  
✅ Enable/disable auto-heal  
✅ Event log  
✅ Configuration  
✅ Export/import config  
✅ Manual restart  
✅ Unquarantine  

---

## Files to Edit

**React UI:**
- `frontend/src/components/*.jsx`
- `frontend/src/styles/App.css`

**Backend:**
- `*.py` files
- `requirements.txt`

**Config:**
- `docker-compose.yml`
- `Dockerfile`

---

## Documentation

- `GETTING_STARTED.md` - Quick start (2 min)
- `SETUP.md` - Detailed setup
- `CHANGES_SUMMARY.md` - What changed
- `REACT_ADDED.md` - React implementation

---

## Remember

- ✅ React builds **inside Docker**
- ✅ No Node.js needed for production
- ✅ UI accessible on **port 8080**
- ✅ Single command: `docker-compose up --build`

---

**Need help? Check logs: `docker logs docker-autoheal`**

