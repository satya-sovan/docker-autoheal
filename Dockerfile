# Multi-stage Dockerfile for Docker Auto-Heal Service with React UI

# ============================================
# Stage 1: Build React Frontend
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies (including dev dependencies needed for build)
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build React app
RUN npm run build

# ============================================
# Stage 2: Python Application
# ============================================
FROM python:3.11-slim

LABEL maintainer="Docker Auto-Heal Service"
LABEL description="Automated container monitoring and healing service with React UI"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (new structure)
COPY app/ ./app/
COPY run.py ./

# Copy React build from stage 1 (vite outputs to ../static which is /static in container)
COPY --from=frontend-builder /static ./static/

# Create data and log directories
RUN mkdir -p /data/logs

# Expose ports
# 8080 - Web UI (React)
# 9090 - Prometheus metrics
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3131/health || exit 1

# Run the application
CMD ["python", "-m", "app.main"]

