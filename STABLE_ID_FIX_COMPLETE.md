# ✅ COMPLETE FIX: stable_id Consistency for Docker Stack/Compose Containers

## 🎯 Problem Identified and Fixed

### The Issue
For Docker Compose/Stack containers, the `stable_id` was being generated inconsistently:

**monitoring_engine.py** (where restarts/quarantine are recorded):
```python
stable_id = f"{compose_project}_{compose_service}"  # Returns "pihole_pihole"
```

**docker_client_wrapper.py** (where container info is returned to API):
```python
stable_id = labels.get("com.docker.compose.service")  # Returns "pihole" only
```

**Result:** Your config.json had `"pihole_pihole": 1` (correct!) but the API was looking for just `"pihole"`, so restart counts and quarantine never worked for compose containers.

---

## ✅ Solution Applied

Updated `docker_client_wrapper.py` to match `monitoring_engine.py` logic exactly:

**File:** `app/docker_client/docker_client_wrapper.py` (lines 105-118)

**Now uses the same priority:**
1. **monitoring.id label** → Custom stable ID
2. **compose project + service** → `"project_service"` format ✅
3. **Container name** → Fallback for standalone containers

---

## 📊 How stable_id Works Now (Consistent Everywhere)

### Docker Compose Container
```yaml
# docker-compose.yml in /pihole/ directory
services:
  pihole:
    image: pihole/pihole
```

**Container name:** `pihole` (or `pihole-pihole-1`)  
**compose.project:** `pihole`  
**compose.service:** `pihole`  
**stable_id:** `"pihole_pihole"` ✅

### Docker Stack Container
```yaml
# stack.yml
version: "3.8"
services:
  web:
    image: nginx
```

**Deployed as:** `docker stack deploy -c stack.yml mystack`  
**Container name:** `mystack_web.1.xyz`  
**compose.project:** `mystack`  
**compose.service:** `web`  
**stable_id:** `"mystack_web"` ✅

### Standalone Docker Container
```bash
docker run --name nginx nginx
```

**Container name:** `nginx`  
**No compose labels**  
**stable_id:** `"nginx"` ✅

### Container with Custom Label
```bash
docker run --label monitoring.id=my-custom-id nginx
```

**monitoring.id:** `my-custom-id`  
**stable_id:** `"my-custom-id"` ✅ (highest priority)

---

## 🎯 Your config.json Was Actually CORRECT!

```json
{
  "containers": {
    "selected": [
      "test-dummy",
      "dummy-container-2",
      "pihole_pihole"  // ✅ This was correct!
    ],
    "restart_counts": {
      "dummy-container-2": 2,    // ✅ Standalone container
      "pihole_pihole": 1          // ✅ Compose container
    }
  }
}
```

**The code was wrong, not your config!** Now both monitoring_engine and docker_client_wrapper use the same `project_service` format.

---

## 🧪 Verification Steps

### Step 1: Check Service is Running
```bash
docker-compose ps
```
Wait for `(healthy)` status.

### Step 2: Verify stable_id Format
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]:<30} stable_id: {x.get(\"stable_id\")}') for x in c]"
```

**Expected output:**
```
pihole                         stable_id: pihole_pihole
dummy-container-2              stable_id: dummy-container-2
```

### Step 3: Verify Restart Counts Work
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: restart_count={x[\"restart_count\"]}') for x in c if x.get(\"stable_id\") in [\"pihole_pihole\", \"dummy-container-2\"]]"
```

**Expected output:**
```
pihole: restart_count=1
dummy-container-2: restart_count=2
```

Should match your config.json values!

### Step 4: Check UI
1. Open http://localhost:3131
2. Press **Ctrl + Shift + R** (hard refresh)
3. Go to Containers page
4. Verify restart counts:
   - **pihole:** Shows **1** ✅
   - **dummy-container-2:** Shows **2** ✅

---

## 📋 Format Reference

### config.json Format
```json
{
  "containers": {
    "restart_counts": {
      "compose_format": "project_service",
      "example_1": "pihole_pihole",
      "example_2": "mystack_web",
      "example_3": "nginx_frontend",
      "standalone_format": "container_name",
      "example_4": "nginx",
      "example_5": "redis-cache",
      "custom_format": "monitoring.id_value",
      "example_6": "my-custom-id"
    }
  }
}
```

### quarantine.json Format
```json
[
  "pihole_pihole",
  "mystack_web",
  "standalone-nginx",
  "my-custom-id"
]
```

---

## 🔍 How to Find Correct stable_id

After the service is running:

```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'Container: {x[\"name\"]:<30} → Use in config: \"{x.get(\"stable_id\")}\"') for x in c]"
```

**Example output:**
```
Container: pihole                        → Use in config: "pihole_pihole"
Container: dummy-container-2             → Use in config: "dummy-container-2"
Container: mystack_web.1.abc123          → Use in config: "mystack_web"
Container: nginx                         → Use in config: "nginx"
```

**Copy the stable_id values and use them in config.json and quarantine.json!**

---

## 🔄 Migration Guide

If you had old entries with wrong format:

### Before (Wrong - Service Only)
```json
{
  "containers": {
    "restart_counts": {
      "pihole": 5,           // ❌ Wrong for compose
      "web": 3               // ❌ Wrong for compose
    }
  }
}
```

### After (Correct - Project_Service)
```json
{
  "containers": {
    "restart_counts": {
      "pihole_pihole": 5,    // ✅ Correct
      "mystack_web": 3       // ✅ Correct
    }
  }
}
```

**Your current config.json already has the correct format!** No migration needed. ✅

---

## 🎯 What This Fixes

| Issue | Before Fix | After Fix |
|-------|------------|-----------|
| Compose container restart counts | Always 0 | Shows correct value ✅ |
| Compose container quarantine | Never showed badge | Shows badge ✅ |
| Stack container restart counts | Always 0 | Shows correct value ✅ |
| Stack container quarantine | Never showed badge | Shows badge ✅ |
| Standalone containers | Worked | Still works ✅ |
| Custom labeled containers | Worked | Still works ✅ |

---

## 📚 Technical Details

### The Bug
Two different implementations of the same function:

**monitoring_engine.py (lines 38-72):**
```python
def _get_stable_identifier(self, info: dict) -> str:
    labels = info.get("labels", {})
    
    if "monitoring.id" in labels:
        return labels["monitoring.id"]
    
    compose_project = labels.get("com.docker.compose.project")
    compose_service = labels.get("com.docker.compose.service")
    if compose_project and compose_service:
        return f"{compose_project}_{compose_service}"  # ✅ Correct
    
    return info.get("name")
```

**docker_client_wrapper.py (line 108 - BEFORE FIX):**
```python
stable_id = labels.get("monitoring.id") or labels.get("com.docker.compose.service") or container.name
# ❌ Wrong - only returns service name, not project_service
```

**docker_client_wrapper.py (lines 105-118 - AFTER FIX):**
```python
if "monitoring.id" in labels:
    stable_id = labels["monitoring.id"]
else:
    compose_project = labels.get("com.docker.compose.project")
    compose_service = labels.get("com.docker.compose.service")
    if compose_project and compose_service:
        stable_id = f"{compose_project}_{compose_service}"  # ✅ Now matches!
    else:
        stable_id = container.name
```

---

## 🐛 Troubleshooting

### Issue: Restart counts still 0 for compose containers

**Check 1: Service restarted?**
```bash
docker-compose ps
```

**Check 2: API returns project_service format?**
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print({x['name']: x.get('stable_id') for x in c})"
```

Should show `"pihole_pihole"` not `"pihole"`.

**Check 3: config.json matches?**
```bash
type data\config.json | findstr restart_counts
```

Should have `"pihole_pihole": 1`.

**Check 4: Clear cache**
- Ctrl + Shift + R

### Issue: How to tell if container is compose or standalone?

```bash
docker inspect <container_name> | findstr "com.docker.compose.project\|com.docker.compose.service"
```

If it shows labels, it's compose/stack. Use `project_service` format.

---

## ✅ Summary

**Problem:** stable_id mismatch between monitoring_engine and docker_client_wrapper  
**Root Cause:** Different implementations for compose containers  
**Solution:** Made docker_client_wrapper match monitoring_engine exactly  

**Result:**
- ✅ Compose containers: stable_id is now `"project_service"` everywhere
- ✅ Stack containers: stable_id is now `"project_service"` everywhere
- ✅ Your config.json entries are correct and will work
- ✅ Restart counts work for all container types
- ✅ Quarantine works for all container types

**Your config.json with:**
- `"pihole_pihole": 1` ✅ CORRECT
- `"dummy-container-2": 2` ✅ CORRECT

**Was always correct! The code is now fixed to match.** 🎉

---

## 🚀 Quick Commands

```bash
# Check stable_ids
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: {x.get(\"stable_id\")}') for x in c]"

# Check restart counts
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: {x[\"restart_count\"]}') for x in c]"

# View config.json
type data\config.json

# Restart service
docker restart docker-autoheal
```

---

**Status:** ✅ Fixed and container rebuilt  
**Action needed:** Clear browser cache (Ctrl + Shift + R)  
**Expected:** Restart counts and quarantine work for compose/stack containers!

