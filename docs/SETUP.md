# 🚀 Docker Auto-Heal Service - React UI Setup

## Quick Start (Docker)

The easiest way to run the application with React UI:

```bash
# Build and start the service
docker-compose up --build

# Access the UI
http://localhost:8080
```

That's it! The React UI is built automatically inside Docker and served on port 8080.

## What Changed

✅ **Removed** Simple HTML/JavaScript UI  
✅ **React is now the only UI**  
✅ **Single `docker-compose up` command** builds everything  
✅ **UI accessible on port 8080**  

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Container                 │
│                                          │
│  ┌────────────────────────────────┐    │
│  │   React UI (port 8080)         │    │
│  │   - Built with Vite            │    │
│  │   - Served by FastAPI          │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │   FastAPI Backend              │    │
│  │   - REST API                   │    │
│  │   - Docker monitoring          │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │   Prometheus Metrics (9090)    │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Docker Build Process

The Dockerfile uses multi-stage build:

1. **Stage 1: Build React**
   - Uses Node.js 18 Alpine
   - Installs dependencies
   - Builds optimized React bundle
   - Output: `dist/` folder

2. **Stage 2: Python Application**
   - Uses Python 3.11 slim
   - Installs Python dependencies
   - Copies React build to `static/`
   - Exposes ports 8080 and 9090

## Usage

### Production (Docker)

```bash
# Build and start
docker-compose up --build -d

# View logs
docker logs -f docker-autoheal

# Stop
docker-compose down
```

### Development (Local)

**Backend:**
```bash
# Start backend
python main.py
# Runs on http://localhost:8080
```

**Frontend (separate terminal):**
```bash
# Start React dev server with hot reload
cd frontend
npm install
npm run dev
# Opens http://localhost:3000
```

In development mode:
- Backend runs on port 8080
- React dev server on port 3000
- API calls proxy from 3000 → 8080
- Hot reload enabled

## Building React Locally (Optional)

If you want to build React outside Docker:

```bash
cd frontend
npm install
npm run build
```

This creates the `static/` directory with optimized React build.

Then start the backend:
```bash
python main.py
# Serves React at http://localhost:8080
```

## Ports

| Port | Service |
|------|---------|
| 8080 | React UI + API |
| 9090 | Prometheus metrics |

## File Structure

```
docker-autoheal/
├── frontend/                # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   ├── styles/         # CSS
│   │   ├── App.jsx         # Main app
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Dependencies
│   ├── vite.config.js      # Vite config
│   └── index.html          # HTML template
│
├── static/                  # React build output (gitignored)
│   ├── index.html
│   ├── assets/
│   └── ...
│
├── *.py                     # Python backend
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Docker Compose config
└── requirements.txt         # Python dependencies
```

## Features

All features available through React UI on port 8080:

- ✅ **Dashboard** - Real-time metrics and status
- ✅ **Containers** - List, select, manage containers
- ✅ **Events** - View auto-heal event history
- ✅ **Configuration** - Adjust settings, export/import
- ✅ **Auto-heal** - Enable/disable per container
- ✅ **Manual Actions** - Restart, unquarantine
- ✅ **Custom Health Checks** - HTTP, TCP, Exec, Docker

## Environment Variables

Optional configuration via environment variables:

```yaml
# docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  # Add more as needed
```

## Troubleshooting

### UI not loading

**Check if container is running:**
```bash
docker ps | grep autoheal
```

**Check logs:**
```bash
docker logs docker-autoheal
```

**Should see:**
```
Serving React UI from static directory
Web UI available at http://0.0.0.0:8080
```

### Build fails

**Clear and rebuild:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Port 8080 already in use

**Change port in docker-compose.yml:**
```yaml
ports:
  - "8081:8080"  # Changed from 8080:8080
```

Then access: `http://localhost:8081`

### Development mode issues

**Backend not accessible:**
```bash
# Make sure backend is running
python main.py

# Check it responds
curl http://localhost:8080/health
```

**React proxy not working:**
```bash
# Check vite.config.js has correct proxy settings
# Should proxy /api to http://localhost:8080
```

## API Documentation

Interactive API docs available at:
```
http://localhost:8080/docs
```

## Metrics

Prometheus metrics available at:
```
http://localhost:9090/metrics
```

## Health Check

Service health endpoint:
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T...",
  "docker_connected": true,
  "monitoring_active": true
}
```

## Testing with Sample Containers

Uncomment the nginx-test service in `docker-compose.yml`:

```yaml
  nginx-test:
    image: nginx:alpine
    container_name: nginx-test
    restart: unless-stopped
    ports:
      - "8081:80"
    labels:
      - "autoheal=true"
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 10s
      timeout: 5s
      retries: 3
```

Then:
```bash
docker-compose up -d
```

Now you can see nginx-test in the UI and enable auto-heal for it.

## Updating React UI

To update the UI:

1. **Make changes** in `frontend/src/`
2. **Test locally**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Rebuild Docker**:
   ```bash
   docker-compose up --build
   ```

## Performance

- **Initial load**: ~500KB (gzipped)
- **Build time**: ~30 seconds
- **Runtime**: Minimal overhead
- **Updates**: Automatic refresh every 5-10s

## Security

- ✅ React build is optimized and minified
- ✅ No source maps in production
- ✅ API served from same origin (no CORS issues)
- ⚠️ Add authentication if exposing publicly

## Next Steps

1. **Start the service**: `docker-compose up --build`
2. **Access UI**: http://localhost:8080
3. **Add containers**: Label them with `autoheal=true`
4. **Configure**: Use the Configuration tab
5. **Monitor**: Check Events tab for activity

## Documentation

- **Full docs**: See other markdown files in the repo
- **API Reference**: http://localhost:8080/docs
- **Frontend docs**: `frontend/README.md`

## Support

If you encounter issues:

1. Check `docker logs docker-autoheal`
2. Verify React build exists in container
3. Check port 8080 is not in use
4. Try rebuilding: `docker-compose up --build --force-recreate`

---

**The UI is now React-only and accessible at http://localhost:8080 when you run `docker-compose up`! 🚀**

