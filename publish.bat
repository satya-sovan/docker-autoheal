@echo off
REM Quick publish script for Docker Hub
REM Usage: publish.bat [dockerhub-username] [tag]

setlocal

REM Get username
if "%1"=="" (
    set /p DOCKER_USERNAME="Enter your Docker Hub username: "
) else (
    set DOCKER_USERNAME=%1
)

REM Get tag (default to latest)
if "%2"=="" (
    set TAG=latest
) else (
    set TAG=%2
)

set IMAGE_NAME=docker-autoheal
set FULL_IMAGE=%DOCKER_USERNAME%/%IMAGE_NAME%

echo ========================================
echo   Publishing to Docker Hub
echo ========================================
echo.
echo Username: %DOCKER_USERNAME%
echo Image: %FULL_IMAGE%
echo Tag: %TAG%
echo.

REM Check if logged in
echo [1/4] Checking Docker login...
docker info | findstr "Username:" >nul
if errorlevel 1 (
    echo Please login to Docker Hub:
    docker login
    if errorlevel 1 (
        echo ERROR: Docker login failed!
        exit /b 1
    )
)

REM Build image
echo.
echo [2/4] Building Docker image...
docker build -t %FULL_IMAGE%:%TAG% -f Dockerfile .
if errorlevel 1 (
    echo ERROR: Build failed!
    exit /b 1
)

REM Tag as latest
if not "%TAG%"=="latest" (
    echo.
    echo [3/4] Tagging as latest...
    docker tag %FULL_IMAGE%:%TAG% %FULL_IMAGE%:latest
)

REM Push image
echo.
echo [4/4] Pushing to Docker Hub...
docker push %FULL_IMAGE%:%TAG%
if errorlevel 1 (
    echo ERROR: Push failed!
    exit /b 1
)

if not "%TAG%"=="latest" (
    docker push %FULL_IMAGE%:latest
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Image published: %FULL_IMAGE%:%TAG%
echo View at: https://hub.docker.com/r/%FULL_IMAGE%
echo.
echo To use: docker pull %FULL_IMAGE%:%TAG%
echo.

endlocal

