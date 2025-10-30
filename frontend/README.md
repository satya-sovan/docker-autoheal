# React Frontend Setup Guide

This document explains how to set up and use the React-based frontend for the Docker Auto-Heal Service.

## 📦 What's Included

The application now supports **two UI options**:

1. **Simple HTML/JS** (`static/` directory) - No build step required
2. **Modern React** (`frontend/` directory) - Component-based with hot-reload

## 🚀 Quick Start - React Development

### Prerequisites

- Node.js 18+ and npm
- Docker Auto-Heal backend running on port 8080

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The React app will open at `http://localhost:3000` with:
- ✅ Hot module replacement
- ✅ API proxy to backend
- ✅ Fast refresh
- ✅ Dev tools

### Development Workflow

```bash
# Terminal 1: Start backend
cd ..
docker-compose up

# Terminal 2: Start React dev server
cd frontend
npm run dev
```

Now you can:
- Edit React components in `frontend/src/`
- Changes hot-reload automatically
- Backend API proxied from `http://localhost:8080`

## 🏗️ Building for Production

### Build React App

```bash
cd frontend
npm run build
```

This creates optimized production files in `static-react/` directory.

### The API automatically serves:
1. React build (`static-react/`) if available
2. Falls back to simple HTML (`static/`) if not

### Test Production Build

```bash
# Build React app
cd frontend
npm run build

# Start backend (will auto-detect React build)
cd ..
docker-compose up

# Open browser
http://localhost:8080
```

## 🐳 Docker Deployment

### Option 1: Multi-Stage Build (Recommended)

Update `Dockerfile`:

```dockerfile
# Stage 1: Build React app
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.11-slim

WORKDIR /app

# Copy backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./

# Copy React build from stage 1
COPY --from=frontend-builder /frontend/dist ./static-react/

EXPOSE 8080 9090

CMD ["python", "main.py"]
```

### Option 2: Pre-build React

```bash
# Build React locally
cd frontend
npm run build

# Build Docker image (includes static-react/)
cd ..
docker build -t docker-autoheal .
```

### Option 3: Simple HTML (No Build)

```bash
# Just use the simple HTML UI
docker build -t docker-autoheal .
# Uses static/ directory automatically
```

## 📁 Frontend Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Navigation.jsx
│   │   ├── Dashboard.jsx
│   │   ├── ContainersPage.jsx
│   │   ├── EventsPage.jsx
│   │   └── ConfigPage.jsx
│   ├── services/        # API service layer
│   │   └── api.js
│   ├── styles/          # CSS files
│   │   └── App.css
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── index.html           # HTML template
├── package.json         # Dependencies
└── vite.config.js       # Vite configuration
```

## 🎨 React Features

### Modern Stack
- ⚡ **Vite** - Fast build tool and dev server
- ⚛️ **React 18** - Latest React with concurrent features
- 🎨 **Bootstrap 5** - UI components via react-bootstrap
- 🛣️ **React Router** - Client-side routing
- 📡 **Axios** - HTTP client with interceptors
- 📅 **date-fns** - Date formatting

### Component Features
- ✅ Real-time data updates (5-10s refresh)
- ✅ Responsive design (mobile-friendly)
- ✅ Loading states and spinners
- ✅ Error handling and alerts
- ✅ Modal dialogs for details
- ✅ Form validation
- ✅ File upload/download

### Developer Experience
- 🔥 Hot Module Replacement
- 🔍 ESLint for code quality
- 📦 Code splitting and lazy loading
- 🎯 TypeScript-ready (JSDoc hints)

## 🔧 Configuration

### Environment Variables

Create `frontend/.env` for custom settings:

```env
# API URL (default: /api for proxy)
VITE_API_URL=http://localhost:8080/api

# Development port (default: 3000)
VITE_PORT=3000
```

### Vite Proxy

API calls automatically proxy to backend during development:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/health': 'http://localhost:8080',
    }
  }
})
```

## 📝 Available Scripts

```bash
# Development
npm run dev          # Start dev server with hot-reload

# Production
npm run build        # Build optimized production bundle
npm run preview      # Preview production build locally

# Code Quality
npm run lint         # Run ESLint
```

## 🎯 Comparison: React vs Simple HTML

| Feature | React (`frontend/`) | Simple HTML (`static/`) |
|---------|---------------------|-------------------------|
| **Setup** | npm install required | No dependencies |
| **Development** | Hot reload, dev tools | Manual refresh |
| **Performance** | Code splitting, lazy loading | Single file load |
| **Maintenance** | Component-based, reusable | Inline JS |
| **Build Step** | Yes (npm run build) | No |
| **Bundle Size** | ~500KB (minified) | ~100KB |
| **Browser Support** | Modern browsers | All browsers |
| **Best For** | Active development, scalability | Quick deployment, simplicity |

## 🚀 Deployment Scenarios

### Scenario 1: Development (React with hot-reload)
```bash
# Terminal 1
docker-compose up

# Terminal 2
cd frontend && npm run dev
```
Access: `http://localhost:3000`

### Scenario 2: Production (React optimized)
```bash
cd frontend && npm run build
docker-compose up
```
Access: `http://localhost:8080`

### Scenario 3: Simple Deploy (No Node.js)
```bash
# Don't build React, use simple HTML
docker-compose up
```
Access: `http://localhost:8080` (serves `static/`)

### Scenario 4: Docker with React Build
```dockerfile
# Multi-stage Dockerfile
# Builds React inside Docker
docker build -t autoheal .
docker run -p 8080:8080 autoheal
```

## 🐛 Troubleshooting

### Issue: npm install fails
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Issue: API calls fail in development
```bash
# Check backend is running
curl http://localhost:8080/health

# Check Vite proxy config in vite.config.js
```

### Issue: Build fails
```bash
# Check Node.js version
node --version  # Should be 18+

# Update dependencies
npm update
```

### Issue: React build not served
```bash
# Verify build directory exists
ls static-react/

# Check API logs
docker logs docker-autoheal | grep "Serving UI"
```

## 📚 Learn More

### React Resources
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [React Bootstrap](https://react-bootstrap.github.io/)

### Project Resources
- Main README: `../README.md`
- API Documentation: `http://localhost:8080/docs`
- Quick Start: `../QUICKSTART.md`

## 🎓 Next Steps

1. **Customize Components**: Edit files in `src/components/`
2. **Add Features**: Create new components for health check UI
3. **Style**: Modify `src/styles/App.css`
4. **Extend API**: Add new endpoints in `src/services/api.js`
5. **Deploy**: Build and deploy with Docker

---

**Choose Your Path:**
- 🚀 **Fast Deploy?** Use simple HTML (`static/`)
- 🛠️ **Active Development?** Use React (`frontend/`)
- 🐳 **Production?** Build React and deploy with Docker

Both UIs provide the same functionality - pick what works for your workflow!

