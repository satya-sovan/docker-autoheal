# Quick Publish Guide - Docker Hub

## ⚡ Super Quick Start (5 minutes)

### Windows PowerShell
```powershell
# 1. Login to Docker Hub
docker login

# 2. Run the publish script
.\publish.ps1 -Username YOUR_DOCKERHUB_USERNAME

# That's it! ✅
```

### Windows Command Prompt
```cmd
# 1. Login to Docker Hub
docker login

# 2. Run the batch file
publish.bat YOUR_DOCKERHUB_USERNAME

# Done! ✅
```

---

## 📋 Before You Start

1. **Create Docker Hub Account** (if you don't have one)
   - Go to: https://hub.docker.com/signup
   - It's free!

2. **Get Docker Hub Token** (optional but recommended)
   - Go to: https://hub.docker.com/settings/security
   - Click "New Access Token"
   - Copy the token (you'll use this instead of password)

---

## 🎯 Step-by-Step Instructions

### Step 1: Open Terminal
- **Windows**: PowerShell or Command Prompt (Run as Administrator recommended)
- **Mac/Linux**: Terminal

### Step 2: Navigate to Project
```bash
cd C:\Users\satya\OneDrive\Desktop\Dev\docker-autoheal
```

### Step 3: Login to Docker Hub
```bash
docker login
```
- Username: your_dockerhub_username
- Password: your_password_or_token

### Step 4: Choose Your Method

#### Option A: Automated Script (Easiest)
```powershell
.\publish.ps1 -Username YOUR_USERNAME
```

#### Option B: With Version Tag
```powershell
.\publish.ps1 -Username YOUR_USERNAME -Tag v1.1.0
```

#### Option C: Manual Commands
```bash
# Build
docker build -t YOUR_USERNAME/docker-autoheal:latest .

# Push
docker push YOUR_USERNAME/docker-autoheal:latest
```

---

## 🎉 After Publishing

### Verify It Worked
1. Visit: `https://hub.docker.com/r/YOUR_USERNAME/docker-autoheal`
2. You should see your image!

### Test Your Published Image
```bash
# Pull your image
docker pull YOUR_USERNAME/docker-autoheal:latest

# Run it
docker run -d \
  --name test-autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 8080:8080 \
  YOUR_USERNAME/docker-autoheal:latest

# Check it's working
# Visit: http://localhost:8080
```

### Share With Others
```bash
# Anyone can now use your image:
docker pull YOUR_USERNAME/docker-autoheal:latest
```

---

## 🔧 Troubleshooting

### "docker login" fails
- **Solution**: Use access token instead of password
- Get token from: https://hub.docker.com/settings/security

### Build fails
- **Solution**: Make sure Docker Desktop is running
- Check you have enough disk space (need ~2GB)
- Increase Docker memory in Docker Desktop settings

### Push denied
- **Solution**: 
  1. Verify username is correct
  2. Make sure you're logged in: `docker login`
  3. Check image name: `YOUR_USERNAME/docker-autoheal` (not someone else's username)

### "Cannot connect to Docker daemon"
- **Solution**: Start Docker Desktop
- Wait for it to fully start (green indicator)

---

## 📊 Publishing Checklist

Before publishing, verify:
- [ ] Docker Desktop is running
- [ ] You're logged into Docker Hub (`docker login`)
- [ ] Build works locally (`docker build -t test .`)
- [ ] Image runs successfully (`docker run test`)
- [ ] Web UI loads at http://localhost:8080

After publishing:
- [ ] Image appears on Docker Hub
- [ ] Image can be pulled (`docker pull YOUR_USERNAME/docker-autoheal`)
- [ ] Update README.md on Docker Hub with description
- [ ] Test image on clean system

---

## 🚀 Advanced: Automated Publishing

### GitHub Actions (Automatic)
If you have a GitHub repository:

1. Add secrets to GitHub:
   - Go to: Settings → Secrets and variables → Actions
   - Add: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`

2. Push a version tag:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

3. GitHub will automatically build and publish! 🎉

---

## 💡 Tips

1. **Version Your Releases**
   - Use semantic versioning: v1.0.0, v1.1.0, v2.0.0
   - Always tag both version AND latest

2. **Multi-Platform Support**
   - Use `docker buildx` for ARM and AMD64 support
   - See DOCKER_HUB_PUBLISH.md for details

3. **Update Description**
   - Copy content from DOCKER_HUB_README.md
   - Paste into Docker Hub repository description
   - Makes it easier for others to use your image

4. **Monitor Usage**
   - Docker Hub shows pull statistics
   - Track which versions are most popular

---

## 📞 Need Help?

- Full documentation: `docs/DOCKER_HUB_PUBLISH.md`
- Docker Hub docs: https://docs.docker.com/docker-hub/
- Issues: Create a GitHub issue

---

**Remember**: Replace `YOUR_USERNAME` with your actual Docker Hub username! 🎯

