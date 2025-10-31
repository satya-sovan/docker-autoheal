# Docker Auto-Heal - Project Structure

This document describes the reorganized project structure following industry best practices.

## 📁 Project Structure

```
docker-autoheal/
├── app/                           # Main application package
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── api/                       # REST API endpoints
│   │   ├── __init__.py
│   │   └── api.py                 # FastAPI routes and endpoints
│   ├── config/                    # Configuration management
│   │   ├── __init__.py
│   │   └── config_manager.py      # Config handling and persistence
│   ├── docker_client/             # Docker API wrapper
│   │   ├── __init__.py
│   │   └── docker_client_wrapper.py
│   ├── monitor/                   # Monitoring engine
│   │   ├── __init__.py
│   │   └── monitoring_engine.py   # Container health monitoring
│   ├── models/                    # Data models (Pydantic schemas)
│   │   └── __init__.py
│   ├── services/                  # Business logic services
│   │   └── __init__.py
│   └── utils/                     # Utility functions
│       └── __init__.py
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_auto_monitor.py       # Auto-monitoring feature tests
│   └── test_service.py            # Service integration tests
├── scripts/                       # Utility scripts
│   ├── __init__.py
│   └── demo.py                    # Demo/example scripts
├── data/                          # Persistent data storage
│   ├── config.json                # Runtime configuration
│   ├── maintenance.json           # Maintenance mode state
│   └── logs/                      # Application logs
│       └── autoheal.log
├── frontend/                      # React UI
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docs/                          # Documentation
│   └── *.md
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Multi-stage Docker build
├── Dockerfile.simple              # Simple Docker build
├── docker-compose.yml             # Docker Compose configuration
├── run.py                         # Convenience entry point script
└── README.md                      # Project README
```

## 🚀 Running the Application

### Using Docker (Recommended)
```bash
docker-compose up --build
```

### Using Python Directly
```bash
# Option 1: Using the module syntax (recommended)
python -m app.main

# Option 2: Using the convenience script
python run.py
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_service.py

# Run test scripts directly
python tests/test_service.py
```

## 📦 Module Organization

### app/main.py
- Application entry point
- Service initialization and orchestration
- Signal handling
- Logging configuration

### app/api/api.py
- FastAPI application setup
- REST API endpoints
- Request/response models
- CORS configuration

### app/config/config_manager.py
- Configuration management
- Persistent storage (JSON files)
- Thread-safe configuration updates
- Event logging

### app/docker_client/docker_client_wrapper.py
- Docker SDK wrapper
- Container operations (list, restart, stop)
- Health checks (HTTP, TCP, exec)
- Connection management

### app/monitor/monitoring_engine.py
- Container health monitoring
- Auto-healing logic
- Event listener for container starts
- Quarantine management

## 🔧 Import Examples

With the new structure, imports follow this pattern:

```python
# Main application
from app.main import main

# Configuration
from app.config.config_manager import config_manager, AutoHealConfig

# Docker client
from app.docker_client.docker_client_wrapper import DockerClientWrapper

# Monitoring
from app.monitor.monitoring_engine import MonitoringEngine

# API
from app.api.api import app, init_api
```

## 📝 Benefits of This Structure

1. **Modularity**: Each component is isolated in its own package
2. **Scalability**: Easy to add new modules (e.g., app/notifications/, app/webhooks/)
3. **Testability**: Clear separation makes unit testing easier
4. **Maintainability**: Standard Python package structure familiar to developers
5. **Import Clarity**: Explicit import paths show dependencies clearly
6. **IDE Support**: Better autocomplete and navigation in modern IDEs

## 🔄 Migration Notes

### Old Structure → New Structure
- `main.py` → `app/main.py`
- `api.py` → `app/api/api.py`
- `config.py` → `app/config/config_manager.py`
- `docker_client.py` → `app/docker_client/docker_client_wrapper.py`
- `monitor.py` → `app/monitor/monitoring_engine.py`
- `test_*.py` → `tests/test_*.py`
- `demo.py` → `scripts/demo.py`

### Import Changes
- `from config import config_manager` → `from app.config.config_manager import config_manager`
- `from docker_client import DockerClientWrapper` → `from app.docker_client.docker_client_wrapper import DockerClientWrapper`
- `from monitor import MonitoringEngine` → `from app.monitor.monitoring_engine import MonitoringEngine`
- `from api import app` → `from app.api.api import app`

## 🐳 Docker Changes

The Dockerfile has been updated to copy the `app/` directory:

```dockerfile
# Copy application code (new structure)
COPY ../app ./app/
COPY ../run.py ./

# Run the application
CMD ["python", "-m", "app.main"]
```

## 📚 Further Reading

- [Python Application Layouts](https://realpython.com/python-application-layouts/)
- [FastAPI Project Structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)

