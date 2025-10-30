# Docker Auto-Heal Service

![Version](https://img.shields.io/badge/version-1.1-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A comprehensive, automated Docker container monitoring and healing service with a **modern React UI**. This service monitors Docker containers for failures and unhealthy states, automatically restarting them based on configurable policies.

## 🚀 Quick Start

```bash
docker-compose up --build
```

**Access the UI:** http://localhost:8080

React builds automatically inside Docker - no Node.js installation required!

## 🌟 Features

### Core Functionality
- **Automated Container Monitoring**: Continuously monitors Docker containers for failures and health issues
- **🏷️ Auto-Monitoring (NEW)**: Automatically monitors containers with `autoheal=true` label when they start - no manual configuration needed!
- **Label-Based Filtering**: Monitor containers with `autoheal=true` label (configurable)
- **Smart Restart Logic**: 
  - Restart on non-zero exit codes
  - Restart on health check failures (Docker native + custom)
  - Configurable cooldown periods and backoff strategies
- **Quarantine System**: Automatically quarantine containers that restart too frequently
- **Custom Health Checks**: Support for HTTP, TCP, Exec, and Docker native health checks

### Modern React Web UI
- **React 18** with Vite for fast builds
- **Component-based architecture** for maintainability
- **Hot module replacement** for development
- **Automatic build** in Docker (no Node.js required for production)
- **Responsive design** works on desktop and mobile

**UI Features:**
- **Interactive Dashboard**: View all containers with real-time status
- **Container Management**: Enable/disable auto-heal per container
- **Configuration Management**: Adjust all settings through the web interface
- **Event Log**: View history of auto-heal actions and decisions
- **Config Export/Import**: Backup and restore configurations as JSON
- **Real-time Updates**: Auto-refresh every 5-10 seconds

### Advanced Features
- **Exponential Backoff**: Progressively longer delays between restart attempts
- **Restart Thresholds**: Prevent infinite restart loops
- **Whitelist/Blacklist**: Fine-grained control over which containers to monitor
- **Prometheus Metrics**: Built-in metrics endpoint for monitoring
- **Webhook Alerts**: Send notifications on quarantine events

## 📋 Requirements

- Docker Engine (Linux) or Docker Desktop (Windows/Mac)
- Python 3.9+ (for local development)
- Docker Compose (recommended)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd docker-autoheal
```

2. Start the service:
```bash
docker-compose up -d
```

3. Access the Web UI:
```
http://localhost:8080
```

### Using Docker

```bash
docker build -t docker-autoheal .

docker run -d \
  --name autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 8080:8080 \
  -p 9090:9090 \
  docker-autoheal
```

### Local Development

**Backend:**
1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

**React Frontend (Optional):**
1. Install Node.js 18+ and npm
2. Setup frontend:
```bash
cd frontend
npm install
npm run dev
```
3. Access React dev server at `http://localhost:3000`

**Note:** The simple HTML UI at `http://localhost:8080` works without React setup.

## 📖 Usage

### 🏷️ Auto-Monitoring Feature (Easiest Way)

Simply add the `autoheal=true` label to your containers, and they'll be **automatically monitored** when they start - no manual configuration needed!

**Docker Run:**
```bash
docker run -d \
  --name my-app \
  --label autoheal=true \
  nginx:alpine
```

**Docker Compose:**
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

**Dockerfile:**
```dockerfile
FROM nginx:alpine
LABEL autoheal=true
```

When containers with `autoheal=true` start, they're automatically:
- ✅ Added to the monitored list
- ✅ Logged in the events page
- ✅ Protected with auto-restart on failures

**See detailed documentation:** [Auto-Monitoring Feature Guide](./AUTO_MONITOR_FEATURE.md)

### Web UI Navigation

1. **Containers Tab**: 
   - View all running containers
   - Select containers to enable/disable auto-heal
   - Manually restart containers
   - Add custom health checks
   - Unquarantine containers

2. **Events Tab**:
   - View auto-heal event history
   - Monitor restart attempts and outcomes
   - Track quarantine events

3. **Configuration Tab**:
   - Adjust monitoring interval
   - Configure restart policies
   - Set cooldown and threshold values
   - Export/import configuration

### Configuration

#### Monitor Settings
- **Interval**: How often to check containers (default: 30s)
- **Label Key/Value**: Filter containers by label (default: `autoheal=true`)
- **Include All**: Monitor all containers regardless of labels

#### Restart Policy
- **Mode**: 
  - `on-failure`: Restart only on non-zero exit codes
  - `health`: Restart only on health check failures
  - `both`: Restart on either condition (default)
- **Cooldown**: Minimum time between restarts (default: 60s)
- **Max Restarts**: Maximum restarts within window (default: 3)
- **Max Restarts Window**: Time window for counting restarts (default: 600s)
- **Backoff**: Exponential backoff configuration

### Custom Health Checks

Add custom health checks via the UI or API:

**HTTP Health Check:**
```json
{
  "container_id": "my-container",
  "check_type": "http",
  "http_endpoint": "http://localhost:8080/health",
  "http_expected_status": 200,
  "interval_seconds": 30,
  "timeout_seconds": 10,
  "retries": 3
}
```

**TCP Health Check:**
```json
{
  "container_id": "my-container",
  "check_type": "tcp",
  "tcp_port": 8080,
  "interval_seconds": 30,
  "timeout_seconds": 5,
  "retries": 3
}
```

**Exec Health Check:**
```json
{
  "container_id": "my-container",
  "check_type": "exec",
  "exec_command": ["curl", "-f", "http://localhost/health"],
  "interval_seconds": 30,
  "timeout_seconds": 10,
  "retries": 3
}
```

## 🔧 API Documentation

Interactive API documentation is available at: `http://localhost:8080/docs`

### Key Endpoints

- `GET /api/status` - Get system status
- `GET /api/containers` - List all containers
- `POST /api/containers/select` - Enable/disable auto-heal for containers
- `POST /api/containers/{id}/restart` - Manually restart a container
- `POST /api/containers/{id}/unquarantine` - Remove container from quarantine
- `GET /api/config` - Get current configuration
- `PUT /api/config` - Update configuration
- `GET /api/config/export` - Export configuration as JSON
- `POST /api/config/import` - Import configuration from JSON
- `GET /api/events` - Get event log
- `POST /api/healthchecks` - Add custom health check

## 📊 Monitoring

### Prometheus Metrics

Metrics are exposed at `http://localhost:9090/metrics`:

- `autoheal_container_restarts_total` - Total container restarts
- `autoheal_containers_monitored` - Number of monitored containers
- `autoheal_containers_quarantined` - Number of quarantined containers
- `autoheal_health_checks_total` - Total health checks performed
- `autoheal_health_checks_failed` - Failed health checks

### Logs

Application logs are written to:
- Console (stdout)
- `autoheal.log` file
- Docker logs: `docker logs autoheal`

## 🏗️ Architecture

```
docker-autoheal/
├── main.py              # Application entry point
├── api.py               # FastAPI REST API
├── config.py            # Configuration management
├── docker_client.py     # Docker API wrapper
├── monitor.py           # Core monitoring engine
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Docker Compose configuration
├── static/
│   ├── index.html      # Web UI
│   └── app.js          # UI JavaScript
└── README.md           # This file
```

### Component Overview

1. **Configuration Manager** (`config.py`):
   - Thread-safe in-memory configuration
   - JSON export/import support
   - Event logging
   - Container state tracking

2. **Docker Client Wrapper** (`docker_client.py`):
   - Docker SDK integration
   - Container operations (list, restart, inspect)
   - Health check implementations
   - Connection retry logic

3. **Monitoring Engine** (`monitor.py`):
   - Async monitoring loop
   - Container health evaluation
   - Restart decision logic
   - Cooldown and backoff management
   - Quarantine system

4. **REST API** (`api.py`):
   - FastAPI endpoints
   - Container management
   - Configuration updates
   - Event log access

5. **Web UI** (`static/`):
   - Bootstrap 5 responsive design
   - Real-time container status
   - Interactive configuration
   - Event log viewer

## ⚙️ Configuration Schema

Default configuration (can be modified via UI or JSON import):

```json
{
  "monitor": {
    "interval_seconds": 30,
    "label_key": "autoheal",
    "label_value": "true",
    "include_all": false
  },
  "containers": {
    "selected": [],
    "excluded": []
  },
  "restart": {
    "mode": "both",
    "cooldown_seconds": 60,
    "max_restarts": 3,
    "max_restarts_window_seconds": 600,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0
    },
    "respect_manual_stop": true
  },
  "filters": {
    "whitelist_names": [],
    "blacklist_names": [],
    "whitelist_labels": [],
    "blacklist_labels": []
  },
  "ui": {
    "enable": true,
    "listen_address": "0.0.0.0",
    "listen_port": 8080,
    "allow_export_json": true,
    "allow_import_json": true,
    "max_log_entries": 50
  },
  "alerts": {
    "enabled": true,
    "webhook": null,
    "notify_on_quarantine": true
  },
  "observability": {
    "prometheus_enabled": true,
    "metrics_port": 9090,
    "log_format": "json"
  }
}
```

## 🔐 Security Considerations

1. **Docker Socket Access**: The service requires read/write access to Docker socket
2. **Network Isolation**: Consider running on a private network
3. **Authentication**: Current version has no authentication (add reverse proxy with auth if needed)
4. **Container Permissions**: Service runs with Docker socket privileges

### Recommended Security Practices

- Use `--restart=unless-stopped` for the auto-heal container
- Label the auto-heal container with `autoheal=false` to prevent self-monitoring
- Run behind a reverse proxy (nginx, traefik) with authentication
- Limit network access to trusted IPs
- Regularly export and backup configurations

## 🐛 Troubleshooting

### Service won't start
```bash
# Check Docker socket permissions
ls -l /var/run/docker.sock

# View logs
docker logs autoheal

# Check if port is already in use
netstat -tulpn | grep 8080
```

### Containers not being monitored
1. Verify container has `autoheal=true` label
2. Check if container is excluded in configuration
3. Review filters (whitelist/blacklist)
4. Check event log for decision reasons

### Health checks failing
1. Verify health check endpoint is accessible
2. Check container network configuration
3. Review timeout and retry settings
4. Test health check manually in container

### Cannot access Web UI
1. Verify port mapping: `docker ps | grep autoheal`
2. Check firewall rules
3. Ensure service is running: `docker ps`
4. Check service health: `curl http://localhost:8080/health`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by [willfarrell/docker-autoheal](https://github.com/willfarrell/docker-autoheal)
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Bootstrap 5](https://getbootstrap.com/)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review API documentation at `/docs`

---

**Version**: 1.1.0  
**Author**: Auto-Heal Team  
**Date**: October 30, 2025

