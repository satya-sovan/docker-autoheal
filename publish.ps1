# Publish Script for Docker Hub
# Usage: .\publish.ps1 -Username <your-dockerhub-username> [-Tag <version>]

param(
    [Parameter(Mandatory=$false)]
    [string]$Username = "",

    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest",

    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild = $false,

    [Parameter(Mandatory=$false)]
    [switch]$PushLatest = $true
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker Auto-Heal - Publish to Docker Hub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get Docker Hub username if not provided
if ([string]::IsNullOrEmpty($Username)) {
    Write-Host "Please enter your Docker Hub username:" -ForegroundColor Yellow
    $Username = Read-Host
    if ([string]::IsNullOrEmpty($Username)) {
        Write-Host "ERROR: Username is required!" -ForegroundColor Red
        exit 1
    }
}

# Image names
$ImageName = "docker-autoheal"
$FullImageName = "${Username}/${ImageName}"

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Docker Hub Username: $Username" -ForegroundColor Gray
Write-Host "  Image Name: $FullImageName" -ForegroundColor Gray
Write-Host "  Tag: $Tag" -ForegroundColor Gray
Write-Host "  Push Latest: $PushLatest" -ForegroundColor Gray
Write-Host ""

# Step 1: Check if logged in to Docker Hub
Write-Host "[Step 1/5] Checking Docker Hub login..." -ForegroundColor Yellow
$dockerInfo = docker info 2>&1 | Select-String "Username:"
if (-not $dockerInfo) {
    Write-Host "  Not logged in to Docker Hub. Please login..." -ForegroundColor Yellow
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker login failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  Already logged in to Docker Hub" -ForegroundColor Green
}
Write-Host ""

# Step 2: Build the Docker image (if not skipped)
if (-not $SkipBuild) {
    Write-Host "[Step 2/5] Building Docker image..." -ForegroundColor Yellow
    Write-Host "  Building: $FullImageName`:$Tag" -ForegroundColor Gray

    docker build -t "${FullImageName}:${Tag}" -f Dockerfile .

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Build successful" -ForegroundColor Green
} else {
    Write-Host "[Step 2/5] Skipping build (using existing image)" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Tag as latest if requested and tag is not already latest
if ($PushLatest -and $Tag -ne "latest") {
    Write-Host "[Step 3/5] Tagging as latest..." -ForegroundColor Yellow
    docker tag "${FullImageName}:${Tag}" "${FullImageName}:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to tag as latest!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Tagged as latest" -ForegroundColor Green
} else {
    Write-Host "[Step 3/5] Skip tagging (already latest or not requested)" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Push the versioned tag
Write-Host "[Step 4/5] Pushing image to Docker Hub..." -ForegroundColor Yellow
Write-Host "  Pushing: $FullImageName`:$Tag" -ForegroundColor Gray

docker push "${FullImageName}:${Tag}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push image!" -ForegroundColor Red
    exit 1
}
Write-Host "  Push successful: $FullImageName`:$Tag" -ForegroundColor Green
Write-Host ""

# Step 5: Push latest tag if applicable
if ($PushLatest -and $Tag -ne "latest") {
    Write-Host "[Step 5/5] Pushing latest tag..." -ForegroundColor Yellow
    Write-Host "  Pushing: $FullImageName`:latest" -ForegroundColor Gray

    docker push "${FullImageName}:latest"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to push latest tag!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Push successful: $FullImageName`:latest" -ForegroundColor Green
} else {
    Write-Host "[Step 5/5] Skip pushing latest (already latest or not requested)" -ForegroundColor Yellow
}
Write-Host ""

# Success message
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Image published to Docker Hub:" -ForegroundColor White
Write-Host "  $FullImageName`:$Tag" -ForegroundColor Cyan
if ($PushLatest -and $Tag -ne "latest") {
    Write-Host "  $FullImageName`:latest" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "To use this image:" -ForegroundColor White
Write-Host "  docker pull $FullImageName`:$Tag" -ForegroundColor Gray
Write-Host "  docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 8080:8080 $FullImageName`:$Tag" -ForegroundColor Gray
Write-Host ""
Write-Host "View on Docker Hub:" -ForegroundColor White
Write-Host "  https://hub.docker.com/r/$FullImageName" -ForegroundColor Cyan
Write-Host ""

