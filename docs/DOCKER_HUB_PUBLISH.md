# Publishing Docker Auto-Heal to Docker Hub

This guide explains how to publish the Docker Auto-Heal image to Docker Hub.

## Prerequisites

1. **Docker Hub Account**: Create a free account at [hub.docker.com](https://hub.docker.com)
2. **Docker Desktop**: Ensure Docker is installed and running
3. **Command Line**: PowerShell (Windows) or Terminal (Mac/Linux)

## Quick Publish

### Option 1: Using PowerShell Script (Recommended for Windows)

```powershell
# Publish latest version
.\publish.ps1 -Username <your-dockerhub-username>

# Publish with specific version tag
.\publish.ps1 -Username <your-dockerhub-username> -Tag v1.1

# Skip build and push existing image
.\publish.ps1 -Username <your-dockerhub-username> -Tag v1.1 -SkipBuild

# Push only versioned tag (not latest)
.\publish.ps1 -Username <your-dockerhub-username> -Tag v1.1 -PushLatest:$false
```

### Option 2: Using Batch File (Simple)

```cmd
# Publish with default tag (latest)
publish.bat <your-dockerhub-username>

# Publish with specific tag
publish.bat <your-dockerhub-username> v1.1
```

### Option 3: Manual Commands

If you prefer to run commands manually:

```bash
# 1. Login to Docker Hub
docker login

# 2. Build the image
docker build -t <username>/docker-autoheal:latest -f Dockerfile .

# 3. Tag with version (optional)
docker tag <username>/docker-autoheal:latest <username>/docker-autoheal:v1.1

# 4. Push to Docker Hub
docker push <username>/docker-autoheal:latest
docker push <username>/docker-autoheal:v1.1
```

## Step-by-Step Guide

### Step 1: Login to Docker Hub

First, login to your Docker Hub account:

```bash
docker login
```

Enter your Docker Hub username and password (or access token) when prompted.

### Step 2: Build the Image

Build the Docker image with your Docker Hub username:

```bash
docker build -t <your-username>/docker-autoheal:latest .
```

**Note**: The multi-stage Dockerfile will automatically:
- Build the React frontend
- Install Python dependencies
- Package everything into a production-ready image

### Step 3: Tag the Image (Optional)

Tag your image with a version number:

```bash
docker tag <your-username>/docker-autoheal:latest <your-username>/docker-autoheal:v1.1
```

### Step 4: Push to Docker Hub

Push the image(s) to Docker Hub:

```bash
# Push latest
docker push <your-username>/docker-autoheal:latest

# Push versioned tag
docker push <your-username>/docker-autoheal:v1.1
```

### Step 5: Verify Publication

Visit your Docker Hub repository:
```
https://hub.docker.com/r/<your-username>/docker-autoheal
```

## Using Published Image

Once published, anyone can use your image:

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  autoheal:
    image: <your-username>/docker-autoheal:latest
    container_name: docker-autoheal
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/data
    ports:
      - "8080:8080"
      - "9090:9090"
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

### Docker Run

```bash
docker run -d \
  --name docker-autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./data:/data \
  -p 8080:8080 \
  -p 9090:9090 \
  --restart unless-stopped \
  <your-username>/docker-autoheal:latest
```

## Versioning Strategy

### Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** (v2.0.0): Breaking changes
- **MINOR** (v1.1.0): New features, backward compatible
- **PATCH** (v1.0.1): Bug fixes

### Tagging Examples

```bash
# Development/testing
docker-autoheal:dev
docker-autoheal:test

# Release versions
docker-autoheal:v1.0.0
docker-autoheal:v1.1.0
docker-autoheal:v1.1.1

# Always tag stable releases as latest
docker-autoheal:latest
```

## Best Practices

### 1. Multi-Architecture Builds

To support multiple architectures (amd64, arm64):

```bash
# Create and use buildx builder
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t <username>/docker-autoheal:latest \
  -t <username>/docker-autoheal:v1.1 \
  --push .
```

### 2. Automated Builds with GitHub Actions

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Publish Docker Image

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: <username>/docker-autoheal
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### 3. README on Docker Hub

Create a Docker Hub README by:
1. Going to your repository on Docker Hub
2. Click "Edit" on the Overview tab
3. Add comprehensive documentation

## Troubleshooting

### Build Fails

**Issue**: Frontend build fails
```
Error: npm install failed
```

**Solution**: Ensure Docker has enough memory (4GB+ recommended)
```bash
# Check Docker resources in Docker Desktop settings
# Increase memory allocation if needed
```

### Push Permission Denied

**Issue**: 
```
denied: requested access to the resource is denied
```

**Solution**: 
1. Verify you're logged in: `docker login`
2. Check image name matches your username
3. Verify repository exists on Docker Hub

### Large Image Size

**Issue**: Image is too large (>1GB)

**Solution**: 
- Already using multi-stage build ✓
- Already using slim base images ✓
- Clean npm cache in Dockerfile if needed

## Additional Resources

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)

## Example: Complete Publish Workflow

```powershell
# 1. Update version in README.md
# 2. Test build locally
docker build -t myusername/docker-autoheal:v1.1 .

# 3. Test the image
docker run -d --name test-autoheal myusername/docker-autoheal:v1.1
docker logs test-autoheal
# Visit http://localhost:8080

# 4. Publish to Docker Hub
.\publish.ps1 -Username myusername -Tag v1.1

# 5. Clean up test container
docker stop test-autoheal
docker rm test-autoheal
```

## Publishing Checklist

- [ ] Code is tested and working
- [ ] Documentation is updated
- [ ] Version number is incremented
- [ ] Logged into Docker Hub
- [ ] Image builds successfully
- [ ] Image tested locally
- [ ] Pushed to Docker Hub
- [ ] Verified on Docker Hub
- [ ] README updated on Docker Hub
- [ ] Release notes created

## Support

For issues or questions:
- GitHub Issues: [Your repository URL]
- Docker Hub: https://hub.docker.com/r/<username>/docker-autoheal

