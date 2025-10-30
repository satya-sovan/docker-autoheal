# Docker Auto-Heal Service

[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/docker-autoheal)](https://hub.docker.com/r/yourusername/docker-autoheal)
[![Docker Image Size](https://img.shields.io/docker/image-size/yourusername/docker-autoheal/latest)](https://hub.docker.com/r/yourusername/docker-autoheal)
[![Version](https://img.shields.io/badge/version-1.1-blue)](https://github.com/yourusername/docker-autoheal)

A production-ready Docker container monitoring and auto-healing service with a modern React web interface. Automatically monitors your Docker containers for failures and unhealthy states, restarting them intelligently based on configurable policies.

## 🚀 Quick Start

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

**Access the Web UI:** http://localhost:3131

## 📦 What's Included

- **Python 3.11** backend with FastAPI
- **React 18** modern web interface with Vite
- **Automated health monitoring** for all Docker containers
- **Smart restart logic** with exponential backoff
- **Prometheus metrics** endpoint on port 9090
- **Persistent storage** in `/data` volume

## 🌟 Key Features

### Core Monitoring
- ✅ Monitor containers by label (`autoheal=true`) or all containers
- ✅ React to Docker health checks and container exit codes
- ✅ Configurable health check intervals and timeouts
- ✅ Custom health checks (HTTP, TCP, Exec)

### Smart Restart Logic
- ✅ Exponential backoff to prevent restart storms
- ✅ Configurable cooldown periods between restarts
- ✅ Maximum restart thresholds to prevent infinite loops
- ✅ Automatic quarantine for containers that restart too frequently
- ✅ Respect manual stops (exit code 0)

### Web Interface
- ✅ Real-time dashboard with all container statuses
- ✅ Per-container auto-heal enable/disable
- ✅ Live event log with restart history
- ✅ Full configuration management through UI
- ✅ Config export/import as JSON
- ✅ Maintenance mode support

### Enterprise Features
- ✅ Persistent state across restarts (stored in `/data`)
- ✅ Prometheus metrics for monitoring
- ✅ Webhook alerts for critical events
- ✅ Structured JSON logging
- ✅ Configurable log levels (DEBUG, INFO, WARNING, ERROR)

## 📋 Requirements

- Docker Engine 20.10+
- Docker socket access (`/var/run/docker.sock`)
- Recommended: 2GB RAM, 1 CPU core

## 🔧 Usage

### Docker Run (Basic)

```bash
docker run -d \
  --name docker-autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 3131:3131 \
  yourusername/docker-autoheal:latest
```

### Docker Run (Full Options)

```bash
docker run -d \
  --name docker-autoheal \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /path/to/data:/data \
  -p 3131:3131 \
  -p 9090:9090 \
  -e AUTOHEAL_INTERVAL=30 \
  -e AUTOHEAL_LOG_LEVEL=INFO \
  yourusername/docker-autoheal:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  autoheal:
    image: yourusername/docker-autoheal:latest
    container_name: docker-autoheal
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/data  # Persist configuration and state
    ports:
      - "3131:3131"  # Web UI
      - "9090:9090"  # Prometheus metrics
    environment:
      - AUTOHEAL_INTERVAL=30
      - AUTOHEAL_LOG_LEVEL=INFO

  # Example monitored container
  webapp:
    image: nginx:latest
    labels:
      autoheal: "true"  # Enable auto-healing for this container
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Then start:
```bash
docker-compose up -d
```

## 🏷️ Container Labels

Enable auto-healing on specific containers using labels:

```yaml
services:
  myapp:
    image: myapp:latest
    labels:
      autoheal: "true"  # Enable monitoring
      autoheal.stop.timeout: "30"  # Custom stop timeout
```

### Available Labels

| Label | Description | Default |
|-------|-------------|---------|
| `autoheal` | Enable monitoring (`true` or `false`) | Matches config |
| `autoheal.stop.timeout` | Seconds to wait before force-stopping | 10 |

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTOHEAL_INTERVAL` | Monitoring interval in seconds | 30 |
| `AUTOHEAL_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `AUTOHEAL_LABEL_KEY` | Label key to filter containers | autoheal |
| `AUTOHEAL_LABEL_VALUE` | Label value to filter containers | true |

### Web UI Configuration

All settings can be configured through the web interface at `http://localhost:3131`:

- **Monitor Settings**: Interval, label filtering
- **Restart Policies**: Cooldowns, max restarts, backoff strategies  
- **Container Selection**: Whitelist/blacklist containers
- **Alerts**: Webhook configuration
- **Observability**: Metrics and logging settings

### Config File

Configuration is automatically persisted to `/data/config.json`. You can:
- Export config as JSON from the web UI
- Edit the file directly
- Import config from JSON backup

## 📊 Monitoring & Metrics

### Prometheus Metrics

Metrics are exposed on port 9090 at `/metrics`:

```bash
curl http://localhost:9090/metrics
```

Available metrics:
- Container restart counts
- Health check failures
- Quarantine events
- Processing times

### Health Check

Service health endpoint:
```bash
curl http://localhost:3131/health
```

### Logs

View logs:
```bash
docker logs -f docker-autoheal
```

Logs are also persisted to `/data/logs/autoheal.log`

## 🔍 Troubleshooting

### Container Not Being Monitored

1. Check if container has the `autoheal=true` label (if label filtering is enabled)
2. Verify container is not in the exclusion list
3. Check logs: `docker logs docker-autoheal`
4. Enable DEBUG logging: Set `AUTOHEAL_LOG_LEVEL=DEBUG`

### Auto-Heal Service Won't Start

1. Verify Docker socket is accessible:
   ```bash
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock alpine ls -l /var/run/docker.sock
   ```
2. Check port availability (3131, 9090)
3. Review logs for specific errors

### Container Quarantined

When a container restarts too frequently, it's automatically quarantined:
1. View quarantined containers in the Web UI
2. Investigate the root cause of failures
3. Fix the underlying issue
4. Unquarantine from the UI or API

## 🔐 Security

### Docker Socket Access

This service requires read-only access to the Docker socket. While necessary for monitoring, this grants significant privileges. Best practices:

- Use read-only socket mount: `:ro`
- Run in isolated network segment
- Limit access to the web UI (use reverse proxy with auth)
- Review container logs regularly

### Production Deployment

For production:
1. Use TLS for the web UI (reverse proxy recommended)
2. Implement authentication (OAuth, basic auth via reverse proxy)
3. Use Prometheus for metrics collection
4. Set up alerting for quarantine events
5. Regular config backups

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Docker Auto-Heal Container             │
│                                          │
│  ┌────────────┐      ┌──────────────┐   │
│  │ React UI   │─────►│ FastAPI      │   │
│  │ (Port 3131)│      │ Backend      │   │
│  └────────────┘      └──────┬───────┘   │
│                             │           │
│  ┌──────────────────────────▼────────┐  │
│  │  Monitor Service                  │  │
│  │  - Health checks                  │  │
│  │  - Restart logic                  │  │
│  │  - Event logging                  │  │
│  └──────────────────┬────────────────┘  │
│                     │                   │
└─────────────────────┼───────────────────┘
                      │
                      ▼
            /var/run/docker.sock
                      │
                      ▼
            ┌─────────────────┐
            │ Docker Engine   │
            │ (Host System)   │
            └─────────────────┘
```

## 📚 Additional Resources

- **Documentation**: Full docs at [GitHub Repository]
- **API Reference**: `http://localhost:3131/docs` (Swagger UI)
- **Issues & Support**: [GitHub Issues]
- **Changelog**: See GitHub releases

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please see the GitHub repository for guidelines.

---

**Built with ❤️ using Python, FastAPI, React, and Docker**

