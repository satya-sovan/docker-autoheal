# Migration Guide: Reorganized Project Structure

This guide explains how to work with the new industry-standard folder structure for Docker Auto-Heal.

## ✅ What Was Changed

The project has been reorganized from a flat structure to a proper Python package structure:

### Before (Old Structure)
```
docker-autoheal/
├── main.py
├── api.py
├── config.py
├── docker_client.py
├── monitor.py
├── demo.py
├── test_auto_monitor.py
├── test_service.py
└── ...
```

### After (New Structure)
```
docker-autoheal/
├── app/                          # ← Main application package
│   ├── main.py
│   ├── api/
│   │   └── api.py
│   ├── config/
│   │   └── config_manager.py
│   ├── docker_client/
│   │   └── docker_client_wrapper.py
│   └── monitor/
│       └── monitoring_engine.py
├── tests/                        # ← Tests in dedicated folder
│   ├── test_auto_monitor.py
│   └── test_service.py
├── scripts/                      # ← Utility scripts
│   └── demo.py
└── run.py                        # ← Convenience entry point
```

## 🚀 How to Run the Application

### Method 1: Using Docker (Recommended) ✨
Nothing changes! Just run as before:
```bash
docker-compose up --build
```

The Dockerfile has been updated automatically to use the new structure.

### Method 2: Using Python Module Syntax
```bash
python -m app.main
```

### Method 3: Using the Convenience Script
```bash
python run.py
```

## 🔧 Verifying the Migration

### Step 1: Test the New Structure
Before cleaning up old files, test that everything works:

```bash
# Test with Docker
docker-compose up --build

# Or test directly with Python
python -m app.main
```

### Step 2: Run Tests
```bash
# Run the test suite
python tests/test_service.py
python tests/test_auto_monitor.py
```

### Step 3: Clean Up Old Files (Optional)
Once you've verified everything works, you can remove the old root-level files:

**Windows:**
```bash
cleanup-old-files.bat
```

**Linux/Mac:**
```bash
chmod +x cleanup-old-files.sh
./cleanup-old-files.sh
```

## 📝 What Files Were Created

### New Files
- `app/__init__.py` - Makes app a Python package
- `app/api/__init__.py` - API package marker
- `app/config/__init__.py` - Config package marker
- `app/docker_client/__init__.py` - Docker client package marker
- `app/monitor/__init__.py` - Monitor package marker
- `app/models/__init__.py` - Models package marker
- `app/services/__init__.py` - Services package marker
- `app/utils/__init__.py` - Utils package marker
- `tests/__init__.py` - Tests package marker
- `scripts/__init__.py` - Scripts package marker
- `run.py` - Convenience entry point
- `PROJECT_STRUCTURE.md` - Structure documentation
- `MIGRATION_GUIDE.md` - This file
- `cleanup-old-files.bat` - Windows cleanup script
- `cleanup-old-files.sh` - Linux/Mac cleanup script

### Copied and Updated Files
- `app/main.py` - From `main.py` (imports updated)
- `app/api/api.py` - From `api.py` (imports updated)
- `app/config/config_manager.py` - From `config.py` (imports updated)
- `app/docker_client/docker_client_wrapper.py` - From `docker_client.py` (imports updated)
- `app/monitor/monitoring_engine.py` - From `monitor.py` (imports updated)
- `tests/test_auto_monitor.py` - From `test_auto_monitor.py`
- `tests/test_service.py` - From `test_service.py`
- `scripts/demo.py` - From `demo.py`

### Modified Files
- `Dockerfile` - Updated to copy app/ directory and use `python -m app.main`
- `Dockerfile.simple` - Same updates as Dockerfile

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:** Make sure you're running from the project root directory:
```bash
cd /path/to/docker-autoheal
python -m app.main
```

### Issue: Old imports still being used

**Solution:** The old root-level files still exist. Either:
1. Delete them using the cleanup script, OR
2. Make sure you're using the new files in app/

### Issue: Docker build fails

**Solution:** Rebuild the Docker image:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Issue: Cannot find configuration or data files

**Solution:** The data directory remains in the same location (`./data/` or `/data/`). This hasn't changed.

## 🎯 Benefits of the New Structure

1. **Industry Standard**: Follows Python packaging best practices
2. **Better IDE Support**: Improved autocomplete and navigation
3. **Clearer Dependencies**: Import paths show relationships
4. **Easier Testing**: Tests are isolated in their own directory
5. **Scalable**: Easy to add new modules as the project grows
6. **Professional**: Structure used by major Python projects

## 📚 Import Changes Reference

If you're developing or extending the code, here's how imports changed:

| Old Import | New Import |
|------------|------------|
| `from config import config_manager` | `from app.config.config_manager import config_manager` |
| `from docker_client import DockerClientWrapper` | `from app.docker_client.docker_client_wrapper import DockerClientWrapper` |
| `from monitor import MonitoringEngine` | `from app.monitor.monitoring_engine import MonitoringEngine` |
| `from api import app, init_api` | `from app.api.api import app, init_api` |

## 🔄 Rollback (If Needed)

If you need to rollback to the old structure:

1. The old files are still in the root directory
2. Simply revert the Dockerfile changes:
   ```dockerfile
   COPY *.py ./
   CMD ["python", "main.py"]
   ```
3. Use `python main.py` instead of `python -m app.main`

However, we recommend keeping the new structure for long-term maintainability.

## ✅ Next Steps

1. ✅ Test the application with the new structure
2. ✅ Run your test suite
3. ✅ Update any CI/CD pipelines if needed
4. ✅ Clean up old files using the cleanup script
5. ✅ Update any documentation that references file locations
6. ✅ Commit the changes to version control

## 📞 Need Help?

If you encounter any issues with the migration:

1. Check that all `__init__.py` files exist in each package
2. Verify you're running commands from the project root
3. Check the `PROJECT_STRUCTURE.md` for detailed structure info
4. Review the Dockerfile to ensure it's using the new structure

---

**Note:** The old root-level Python files (`main.py`, `api.py`, etc.) are still present for safety. You can remove them after verifying the new structure works correctly using the provided cleanup scripts.

