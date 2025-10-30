# React Frontend Implementation - Complete Guide

## 🎉 What's New

The Docker Auto-Heal Service now includes a **modern React-based frontend** alongside the original simple HTML/JS UI. You can choose which one to use based on your needs.

## 📦 Two UI Options

### Option 1: Simple HTML (`static/`)
✅ **No build step required**  
✅ **No Node.js needed**  
✅ **Instant deployment**  
✅ **~100KB total size**  
✅ **Works everywhere**  

**Use when:**
- Quick deployment needed
- No Node.js available
- Simplicity is priority
- Learning the codebase

### Option 2: React (`frontend/`)
✅ **Modern component architecture**  
✅ **Hot module replacement**  
✅ **TypeScript-ready**  
✅ **Code splitting**  
✅ **Better maintainability**  
✅ **Scalable for features**  

**Use when:**
- Active development
- Adding complex features
- Team collaboration
- Long-term maintenance

## 🚀 Quick Start Comparison

### Simple HTML (Option 1)
```bash
# Just start the backend
docker-compose up -d

# Access UI
http://localhost:8080
```
**Done!** No other steps needed.

### React (Option 2)

**Development:**
```bash
# Terminal 1: Backend
docker-compose up

# Terminal 2: React dev server
cd frontend
npm install
npm run dev

# Access UI
http://localhost:3000
```

**Production:**
```bash
# Build React app
cd frontend
npm install
npm run build

# Start backend (auto-serves React)
cd ..
docker-compose up

# Access UI
http://localhost:8080
```

## 🏗️ React Architecture

### Technology Stack
- **React 18** - Latest React with concurrent features
- **Vite** - Lightning-fast build tool
- **React Router** - Client-side routing
- **React Bootstrap** - UI components
- **Axios** - HTTP client
- **date-fns** - Date utilities

### Project Structure
```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── Navigation.jsx    # Top navbar with status
│   │   ├── Dashboard.jsx     # Metric cards
│   │   ├── ContainersPage.jsx # Container management
│   │   ├── EventsPage.jsx    # Event log viewer
│   │   └── ConfigPage.jsx    # Configuration forms
│   ├── services/
│   │   └── api.js            # API service layer
│   ├── styles/
│   │   └── App.css           # Global styles
│   ├── App.jsx               # Main app component
│   └── main.jsx              # Entry point
├── index.html                # HTML template
├── package.json              # Dependencies
├── vite.config.js            # Vite configuration
└── README.md                 # Frontend docs
```

### Component Breakdown

#### 1. **Navigation.jsx**
- Top navigation bar
- Real-time status badge
- Active route highlighting
- Responsive mobile menu

#### 2. **Dashboard.jsx**
- Four metric cards
- Total containers
- Monitored count
- Quarantined count
- Service status with refresh

#### 3. **ContainersPage.jsx**
- Container list table
- Checkbox selection
- Bulk enable/disable
- Manual restart buttons
- Unquarantine action
- Modal for container details
- Real-time updates every 5s

#### 4. **EventsPage.jsx**
- Event log with formatting
- Color-coded by status
- Timestamp formatting
- Auto-refresh every 5s
- Scrollable event list

#### 5. **ConfigPage.jsx**
- Monitor settings form
- Restart policy form
- Export configuration button
- Import configuration upload
- Form validation
- Real-time updates

## 🎨 Features & Benefits

### React Advantages
✅ **Component Reusability**: Write once, use everywhere  
✅ **State Management**: React hooks for clean state  
✅ **Hot Reload**: See changes instantly  
✅ **Dev Tools**: React DevTools for debugging  
✅ **TypeScript Ready**: Add types when needed  
✅ **Code Splitting**: Load only what's needed  
✅ **Testing Ready**: Jest and React Testing Library  
✅ **Modern JS**: ES6+, async/await, destructuring  

### Development Experience
- Fast refresh (< 1s)
- Error overlays
- Source maps for debugging
- ESLint integration
- Auto-formatting support

## 🐳 Docker Deployment Options

### Option A: Multi-Stage Build (Recommended)
```dockerfile
# Stage 1: Build React
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app + React build
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY *.py ./
COPY --from=frontend-builder /frontend/dist ./static-react/
EXPOSE 8080 9090
CMD ["python", "main.py"]
```

Use: `docker-compose -f docker-compose.react.yml up`

### Option B: Pre-Build React Locally
```bash
# Build React on your machine
cd frontend
npm install
npm run build

# Docker picks up static-react/
docker build -t autoheal .
docker run -p 8080:8080 autoheal
```

### Option C: Simple HTML (No React)
```bash
# Use the original Dockerfile
docker build -t autoheal .
docker run -p 8080:8080 autoheal
```

## 🔧 Configuration

### Environment Variables
Create `frontend/.env`:
```env
# API base URL (default: /api)
VITE_API_URL=http://localhost:8080/api

# Dev server port (default: 3000)
VITE_PORT=3000
```

### Vite Proxy (Development)
API calls automatically proxy to backend:
```javascript
// vite.config.js
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      }
    }
  }
})
```

## 📊 Performance Comparison

| Metric | Simple HTML | React (Dev) | React (Prod) |
|--------|------------|-------------|--------------|
| **Initial Load** | ~100KB | ~2MB | ~500KB |
| **Rebuild Time** | Instant | 1-2s | 10-15s |
| **Runtime** | Browser | Node + HMR | Browser |
| **Dependencies** | None | Node 18+ | None |
| **Caching** | Browser | Vite | Browser + Chunks |

## 🛠️ Development Workflow

### Typical Development Session
```bash
# 1. Start backend
docker-compose up

# 2. Start React dev server (new terminal)
cd frontend
npm run dev

# 3. Make changes to components
# Files in frontend/src/ hot-reload automatically

# 4. When done, build for production
npm run build

# 5. Test production build
cd ..
docker-compose restart
```

### Adding a New Component
```bash
# Create new component
touch frontend/src/components/NewFeature.jsx

# Import in App.jsx
import NewFeature from './components/NewFeature'

# Add route
<Route path="/feature" element={<NewFeature />} />

# Add navigation link
<Nav.Link as={Link} to="/feature">Feature</Nav.Link>
```

### Adding an API Endpoint
```javascript
// 1. Add to api.js
export const getNewData = () => api.get('/new-endpoint');

// 2. Use in component
import { getNewData } from '../services/api';

const fetchData = async () => {
  const response = await getNewData();
  setData(response.data);
};
```

## 🧪 Testing

### Manual Testing Checklist
```bash
✅ npm install works
✅ npm run dev starts dev server
✅ All pages load correctly
✅ API calls work (check Network tab)
✅ npm run build completes
✅ Production build serves correctly
✅ Responsive design (mobile, tablet, desktop)
✅ Browser console has no errors
✅ All features work as in simple HTML
```

### Browser Testing
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## 🐛 Troubleshooting

### Issue: npm install fails
```bash
# Solution 1: Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Solution 2: Use different registry
npm install --registry https://registry.npmjs.org/
```

### Issue: Dev server won't start
```bash
# Check port 3000 is free
netstat -an | grep 3000

# Try different port
VITE_PORT=3001 npm run dev
```

### Issue: API calls fail (CORS)
```bash
# Check Vite proxy in vite.config.js
# Verify backend is running:
curl http://localhost:8080/health
```

### Issue: Build fails
```bash
# Check Node version
node --version  # Should be 18+

# Clear and rebuild
rm -rf node_modules dist
npm install
npm run build
```

### Issue: React build not served in Docker
```bash
# Verify build exists
ls static-react/

# Check API logs
docker logs docker-autoheal | grep "Serving UI"

# Should see: "Serving UI from static-react"
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| `frontend/README.md` | Frontend-specific setup |
| `README.md` | Main project documentation |
| `QUICKSTART.md` | Quick start guide |
| `PROJECT_SUMMARY.md` | Overall project summary |
| This file | React implementation details |

## 🎯 When to Use Each UI

### Use Simple HTML (`static/`) when:
- ❤️ Quick deployment is critical
- ❤️ No Node.js environment available
- ❤️ Learning the codebase
- ❤️ Minimal dependencies preferred
- ❤️ Simple changes needed

### Use React (`frontend/`) when:
- ❤️ Building new features
- ❤️ Team collaboration
- ❤️ Long-term maintenance
- ❤️ Complex UI interactions needed
- ❤️ Modern development workflow preferred

## ✨ Future Enhancements (React)

Potential additions to React UI:
- [ ] Dark mode toggle
- [ ] WebSocket for real-time updates
- [ ] Advanced filtering and search
- [ ] Drag-and-drop config import
- [ ] Charts and visualizations (Chart.js)
- [ ] Notification system
- [ ] Container logs viewer
- [ ] Health check builder wizard
- [ ] Multi-container actions
- [ ] Config diff viewer
- [ ] Export to various formats
- [ ] Keyboard shortcuts
- [ ] Mobile app (React Native)

## 🎓 Learning Resources

### React
- [React Docs](https://react.dev/)
- [React Hooks](https://react.dev/reference/react)
- [React Router](https://reactrouter.com/)

### Vite
- [Vite Guide](https://vitejs.dev/guide/)
- [Vite Config](https://vitejs.dev/config/)

### React Bootstrap
- [Components](https://react-bootstrap.github.io/components/)
- [Layout](https://react-bootstrap.github.io/layout/grid/)

## 🤝 Contributing

To contribute to the React UI:

1. **Setup**: Follow frontend/README.md
2. **Branch**: Create feature branch
3. **Develop**: Make changes in `frontend/src/`
4. **Test**: Verify in dev mode and production build
5. **Lint**: Run `npm run lint`
6. **Build**: Ensure `npm run build` works
7. **PR**: Submit with screenshots

## 🎉 Summary

**You now have TWO options for the UI:**

1. **Simple HTML** - Ready to use immediately
2. **React** - Modern, scalable, feature-rich

**Both provide identical functionality!**

Choose based on your needs:
- **Fast deploy?** → Simple HTML
- **Active development?** → React

The backend API supports both seamlessly, automatically serving whichever UI is available.

---

**Quick Commands:**

```bash
# Start with simple HTML
docker-compose up

# Start with React (development)
docker-compose up &
cd frontend && npm run dev

# Start with React (production)
cd frontend && npm run build
cd .. && docker-compose up

# Build Docker with React
docker-compose -f docker-compose.react.yml up --build
```

**Happy coding! 🚀**

