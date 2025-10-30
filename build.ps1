# Build and Run Script for Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker Auto-Heal - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build React
Write-Host "[Step 1/3] Building React frontend..." -ForegroundColor Yellow
Set-Location frontend

if (Test-Path "node_modules") {
    Write-Host "  node_modules exists, skipping npm install" -ForegroundColor Gray
} else {
    Write-Host "  Installing npm dependencies..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: npm install failed!" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

Write-Host "  Running npm build..." -ForegroundColor Gray
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: npm build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..
Write-Host "  React build complete" -ForegroundColor Green
Write-Host ""

# Step 2: Check if static directory exists
if (Test-Path "static") {
    Write-Host "[Step 2/3] React build found in static/ directory" -ForegroundColor Green
} else {
    Write-Host "ERROR: static/ directory not found after build!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Docker build and run
Write-Host "[Step 3/3] Building and starting Docker container..." -ForegroundColor Yellow
docker-compose -f docker-compose.simple.yml down 2>$null
docker-compose -f docker-compose.simple.yml up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Service is running!" -ForegroundColor White
    Write-Host "  UI: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8080/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  View logs:" -ForegroundColor White
    Write-Host "  docker logs -f docker-autoheal" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Red
    exit 1
}

