@echo off
REM Interactive Docker Hub Publisher
REM This will guide you through publishing step by step

echo ============================================================
echo   Docker Auto-Heal - Interactive Publisher
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check Docker Hub login
docker info | findstr "Username:" >nul
if errorlevel 1 (
    echo You are NOT logged into Docker Hub
    echo.
    echo To login, you need:
    echo   1. Docker Hub username
    echo   2. Password or Access Token (recommended)
    echo.
    echo Get an access token at: https://hub.docker.com/settings/security
    echo.
    set /p LOGIN_NOW="Do you want to login now? (Y/N): "
    if /i "%LOGIN_NOW%"=="Y" (
        docker login
        if errorlevel 1 (
            echo Login failed. Please try again.
            pause
            exit /b 1
        )
    ) else (
        echo Please login manually with: docker login
        pause
        exit /b 1
    )
) else (
    echo [OK] You are logged into Docker Hub
)
echo.

REM Get username
set /p USERNAME="Enter your Docker Hub username: "
if "%USERNAME%"=="" (
    echo Username cannot be empty!
    pause
    exit /b 1
)

REM Get tag
echo.
echo Version tags (examples):
echo   - latest (default, always up-to-date)
echo   - v1.0.0 (semantic versioning)
echo   - v1.1, stable, dev, etc.
echo.
set /p TAG="Enter tag (press Enter for 'latest'): "
if "%TAG%"=="" set TAG=latest

REM Confirmation
echo.
echo ============================================================
echo   Ready to Publish
echo ============================================================
echo.
echo Image will be published as:
echo   %USERNAME%/docker-autoheal:%TAG%
echo.
echo This will:
echo   1. Build the Docker image (includes React build)
echo   2. Tag it with your username
echo   3. Push to Docker Hub
echo.
echo Estimated time: 5-10 minutes (first build)
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo   Building and Publishing...
echo ============================================================
echo.

REM Build
echo [Step 1/3] Building Docker image...
echo This may take a few minutes...
docker build -t %USERNAME%/docker-autoheal:%TAG% -f Dockerfile .
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Check the errors above.
    pause
    exit /b 1
)

echo.
echo [OK] Build successful!
echo.

REM Tag as latest if not already
if not "%TAG%"=="latest" (
    echo [Step 2/3] Tagging as latest...
    docker tag %USERNAME%/docker-autoheal:%TAG% %USERNAME%/docker-autoheal:latest
) else (
    echo [Step 2/3] Already tagged as latest
)

echo.

REM Push
echo [Step 3/3] Pushing to Docker Hub...
echo This may take a few minutes...
docker push %USERNAME%/docker-autoheal:%TAG%
if errorlevel 1 (
    echo.
    echo [ERROR] Push failed!
    echo Make sure you're logged in and have access to this repository.
    pause
    exit /b 1
)

if not "%TAG%"=="latest" (
    echo.
    echo Pushing latest tag...
    docker push %USERNAME%/docker-autoheal:latest
)

echo.
echo ============================================================
echo   SUCCESS! Your image is published!
echo ============================================================
echo.
echo Your image is now live on Docker Hub:
echo   https://hub.docker.com/r/%USERNAME%/docker-autoheal
echo.
echo Anyone can now use it with:
echo   docker pull %USERNAME%/docker-autoheal:%TAG%
echo.
echo To run it:
echo   docker run -d --name autoheal \
echo     -v /var/run/docker.sock:/var/run/docker.sock:ro \
echo     -p 8080:8080 \
echo     %USERNAME%/docker-autoheal:%TAG%
echo.
echo Next steps:
echo   1. Visit https://hub.docker.com/r/%USERNAME%/docker-autoheal
echo   2. Click 'Edit' on the Overview tab
echo   3. Copy content from DOCKER_HUB_README.md
echo   4. Save the description
echo.
pause

