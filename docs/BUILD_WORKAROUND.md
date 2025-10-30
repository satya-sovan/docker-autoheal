# Build Instructions - Network Issues Workaround

If you're experiencing Docker network timeouts when pulling Node.js image, use this alternative approach.

## Option 1: Automated Build Script (Recommended)

**Run the PowerShell script:**

```powershell
.\build.ps1
```

This will:
1. Build React locally (requires Node.js)
2. Build Docker image with pre-built React
3. Start the service

Then access: http://localhost:8080

## Option 2: Manual Steps

### Step 1: Install Node.js Dependencies

```powershell
cd frontend
npm install
```

### Step 2: Build React

```powershell
npm run build
```

This creates the `static/` directory in the parent folder.

### Step 3: Build and Run Docker

```powershell
cd ..
docker-compose -f docker-compose.simple.yml up --build -d
```

### Step 4: Access the UI

Open: http://localhost:8080

## Option 3: Fix Network Issue (If Possible)

If you have proxy or network issues:

### Check Docker Desktop Network Settings

1. Open Docker Desktop
2. Go to Settings → Resources → Network
3. Try disabling/enabling network features
4. Restart Docker Desktop

### Try with Original Multi-Stage Build

Once network is fixed:

```powershell
docker-compose up --build
```

## What's the Difference?

### Multi-Stage Dockerfile (Original)
- **Pros**: Everything in Docker, no Node.js needed locally
- **Cons**: Requires network to pull Node.js image
- **Use**: `docker-compose up --build`

### Simple Dockerfile (Alternative)
- **Pros**: No Node.js image needed, works with poor network
- **Cons**: Requires Node.js installed locally
- **Use**: Build React first, then `docker-compose -f docker-compose.simple.yml up --build`

## Verification

After starting the service:

```powershell
# Check container is running
docker ps | findstr autoheal

# Check logs
docker logs docker-autoheal

# Test health
curl http://localhost:8080/health

# Open UI
start http://localhost:8080
```

## Troubleshooting

### "npm: command not found"

**Solution**: Install Node.js from https://nodejs.org/ (version 18 or higher)

### "static/ directory not found"

**Solution**: Make sure `npm run build` completed successfully in the frontend directory

### Port 8080 already in use

**Solution**:
```powershell
# Find process
netstat -ano | findstr :8080

# Kill it
taskkill /PID <pid> /F
```

## Quick Commands Reference

```powershell
# Build React
cd frontend && npm install && npm run build && cd ..

# Build and start Docker (simple)
docker-compose -f docker-compose.simple.yml up --build -d

# View logs
docker logs -f docker-autoheal

# Stop service
docker-compose -f docker-compose.simple.yml down

# Restart service
docker-compose -f docker-compose.simple.yml restart
```

## Summary

**If network timeout issue:**
1. Use `.\build.ps1` script (easiest)
2. Or build React manually + use docker-compose.simple.yml

**If network is fine:**
1. Use original `docker-compose up --build`

Both approaches result in the same working application!

