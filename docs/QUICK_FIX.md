# Quick Fix - Step by Step Instructions

## ✅ FIXED - Service is Running!

**If you followed the steps or ran `.\build.ps1`, your service should now be working at:**
```
http://localhost:8080
```

**Verify with:** `python test_service.py`

---

## The Issue (RESOLVED)
Docker cannot download the Node.js image due to network timeout.

## The Solution
Build React locally first, then use Docker.

## Steps to Follow

### 1. Build React Locally

Open PowerShell and run:

```powershell
cd frontend
npm install
npm run build
cd ..
```

**What this does:**
- Installs React dependencies
- Builds optimized React bundle
- Creates `static/` directory with the build

### 2. Verify Build

Check that `static/` directory exists:

```powershell
dir static
```

You should see files like `index.html` and an `assets/` folder.

### 3. Build and Start Docker

```powershell
docker-compose -f docker-compose.simple.yml up --build -d
```

**What this does:**
- Uses Dockerfile.simple (no Node.js image needed)
- Builds Python container
- Copies pre-built React from `static/`
- Starts the service

### 4. Access the UI

Open your browser:
```
http://localhost:8080
```

## If You Get Errors

### "npm: command not found"

**Install Node.js:**
1. Download from: https://nodejs.org/
2. Install version 18 or higher
3. Restart PowerShell
4. Try again

### "Cannot find module"

```powershell
cd frontend
rm -r node_modules
npm install
npm run build
cd ..
```

### "Port 8080 in use"

```powershell
# Stop existing container
docker-compose -f docker-compose.simple.yml down

# Or kill the process
netstat -ano | findstr :8080
taskkill /PID <pid> /F
```

### "static/ not found"

Make sure you're in the correct directory:
```powershell
# Should show: frontend/, *.py files, Dockerfile
dir
```

If `frontend/` is missing, you're in the wrong directory.

## One-Line Command (After React is Built)

```powershell
docker-compose -f docker-compose.simple.yml up --build -d && start http://localhost:8080
```

## Check If It's Working

```powershell
# Check container
docker ps | findstr autoheal

# Check logs
docker logs docker-autoheal

# Test health
curl http://localhost:8080/health
```

You should see:
```json
{
  "status": "healthy",
  "docker_connected": true,
  "monitoring_active": true
}
```

## Stop the Service

```powershell
docker-compose -f docker-compose.simple.yml down
```

## Summary

**The automated script `.\build.ps1` does all these steps for you.**

If it's running, just wait for it to complete. It will:
1. Install npm dependencies (~2-3 minutes)
2. Build React (~30 seconds)
3. Build Docker (~1-2 minutes)
4. Start the service

**Total time: ~5 minutes**

Then open http://localhost:8080 and you're done!

