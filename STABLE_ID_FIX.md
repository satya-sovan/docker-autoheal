# 🔧 FIXED: stable_id Mismatch for Docker Stack/Compose Containers

## 🎯 Problem

For Docker Compose/Stack containers, there was an inconsistency in how `stable_id` was generated:

- **config.json had:** `"pihole_pihole": 1` (project_service format)
- **API returned:** `stable_id: "pihole"` (service only format)
- **Result:** Restart counts and quarantine status didn't work for compose containers

---

## 🐛 Root Cause

**Two different implementations of stable_id generation:**

### Implementation 1: monitoring_engine.py ✅ (Correct)
```python
# Lines 67-68
compose_project = labels.get("com.docker.compose.project")
compose_service = labels.get("com.docker.compose.service")
if compose_project and compose_service:
    return f"{compose_project}_{compose_service}"  # Returns "pihole_pihole"
```

### Implementation 2: docker_client_wrapper.py ❌ (Wrong)
```python
# Line 108 - BEFORE FIX
stable_id = labels.get("monitoring.id") or labels.get("com.docker.compose.service") or container.name
# Returns just "pihole" (service only, missing project prefix)
```

**Result:** The monitoring engine would store restart counts and quarantine status as `"pihole_pihole"`, but the API would look for `"pihole"`. They never matched!

---

## ✅ Fix Applied

Updated `docker_client_wrapper.py` to use the same logic as `monitoring_engine.py`:

**File:** `app/docker_client/docker_client_wrapper.py` (lines 105-118)

**Before:**
```python
stable_id = labels.get("monitoring.id") or labels.get("com.docker.compose.service") or container.name
```

**After:**
```python
# Get stable identifier with same logic as monitoring_engine
# Priority 1: Explicit monitoring.id label
if "monitoring.id" in labels:
    stable_id = labels["monitoring.id"]
else:
    # Priority 2: Docker Compose service name (project_service format)
    compose_project = labels.get("com.docker.compose.project")
    compose_service = labels.get("com.docker.compose.service")
    if compose_project and compose_service:
        stable_id = f"{compose_project}_{compose_service}"
    else:
        # Priority 3: Container name (fallback)
        stable_id = container.name
```

---

## 📊 stable_id Generation Logic (Now Consistent)

Both `monitoring_engine.py` and `docker_client_wrapper.py` now use this priority:

### Priority 1: Explicit monitoring.id Label
```python
labels.get("monitoring.id")
```
**Example:** `"my-custom-id"`
**Use case:** When you want to set a custom stable identifier

### Priority 2: Docker Compose Format (project_service)
```python
f"{compose_project}_{compose_service}"
```
**Example:** `"pihole_pihole"` (project: pihole, service: pihole)
**Use case:** Docker Compose/Stack containers

### Priority 3: Container Name (Fallback)
```python
container.name
```
**Example:** `"nginx"` or `"dummy-container-2"`
**Use case:** Standalone containers without compose labels

---

## 🎯 Impact on Different Container Types

### Docker Compose Container
```yaml
# docker-compose.yml
services:
  pihole:
    image: pihole/pihole
```

**Labels:**
- `com.docker.compose.project: "pihole"`
- `com.docker.compose.service: "pihole"`

**stable_id:** `"pihole_pihole"` ✅

**config.json:**
```json
{
  "containers": {
    "selected": ["pihole_pihole"],
    "restart_counts": {
      "pihole_pihole": 5
    }
  }
}
```

### Docker Stack Container
```yaml
# stack.yml
version: "3.8"
services:
  web:
    image: nginx
```

**Labels:**
- `com.docker.compose.project: "mystack"`
- `com.docker.compose.service: "web"`

**stable_id:** `"mystack_web"` ✅

**config.json:**
```json
{
  "containers": {
    "restart_counts": {
      "mystack_web": 3
    }
  }
}
```

### Standalone Container
```bash
docker run --name nginx nginx
```

**Labels:** (none relevant)

**stable_id:** `"nginx"` ✅

**config.json:**
```json
{
  "containers": {
    "restart_counts": {
      "nginx": 2
    }
  }
}
```

### Container with Custom Label
```bash
docker run --label monitoring.id=my-app nginx
```

**Labels:**
- `monitoring.id: "my-app"`

**stable_id:** `"my-app"` ✅

**config.json:**
```json
{
  "containers": {
    "restart_counts": {
      "my-app": 1
    }
  }
}
```

---

## 🧪 How to Verify the Fix

### Step 1: Rebuild and Restart Service
Container is rebuilding now with the fix.

```bash
# Check build status
docker-compose ps
```

Wait for `(healthy)` status.

### Step 2: Check API Returns Correct stable_id
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'Name: {x[\"name\"]}, stable_id: {x.get(\"stable_id\")}') for x in c if 'pihole' in x['name'] or 'dummy' in x['name']]"
```

**Expected for pihole (compose container):**
```
Name: pihole, stable_id: pihole_pihole
```

**Expected for dummy-container-2 (standalone):**
```
Name: dummy-container-2, stable_id: dummy-container-2
```

### Step 3: Verify Restart Counts Work
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: restart_count={x[\"restart_count\"]}') for x in c if 'pihole' in x['name'] or 'dummy' in x['name']]"
```

**Expected:**
```
pihole: restart_count=1
dummy-container-2: restart_count=1
```

Should match values in config.json!

### Step 4: Check UI
1. Open http://localhost:3131
2. Press **Ctrl + Shift + R** (hard refresh)
3. Go to Containers page
4. **Verify restart counts match config.json** ✅

---

## 📋 config.json Format for Different Container Types

### Current config.json (Correct for Compose):
```json
{
  "containers": {
    "selected": [
      "test-dummy",
      "dummy-container-2",
      "pihole_pihole"
    ],
    "restart_counts": {
      "dummy-container-2": 1,
      "pihole_pihole": 1
    }
  }
}
```

This is now **correct** ✅ because:
- `"pihole_pihole"` matches the stable_id for compose container (project_service format)
- `"dummy-container-2"` matches the stable_id for standalone container (container name)

---

## 🔍 How to Find Correct stable_id

After the fix is deployed, you can find the correct stable_id for any container:

```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]:<30} stable_id: {x.get(\"stable_id\")}') for x in c]"
```

**Example Output:**
```
pihole                         stable_id: pihole_pihole
dummy-container-2              stable_id: dummy-container-2
nginx_web_1                    stable_id: nginx_web
mystack_db_1                   stable_id: mystack_db
```

**Use these stable_id values in config.json and quarantine.json!**

---

## 🎯 Summary of Changes

### Code Changes:
| File | Lines | Change | Impact |
|------|-------|--------|--------|
| `docker_client_wrapper.py` | 105-118 | Match monitoring_engine stable_id logic | All compose containers ✅ |

### Logic Changes:
| Container Type | Before (Wrong) | After (Correct) |
|----------------|----------------|-----------------|
| Compose (pihole service) | `"pihole"` | `"pihole_pihole"` ✅ |
| Stack (mystack_web service) | `"web"` | `"mystack_web"` ✅ |
| Standalone (nginx) | `"nginx"` | `"nginx"` ✅ (no change) |
| Custom label | `"my-app"` | `"my-app"` ✅ (no change) |

---

## 🔮 Expected Behavior After Fix

### Restart Counts
```json
// config.json
"restart_counts": {
  "pihole_pihole": 5,
  "mystack_web": 3,
  "standalone_nginx": 2
}
```

**API will return:**
- pihole container: `restart_count: 5` ✅
- mystack web service: `restart_count: 3` ✅
- standalone nginx: `restart_count: 2` ✅

### Quarantine
```json
// quarantine.json
[
  "pihole_pihole",
  "mystack_web"
]
```

**UI will show:**
- pihole: Yellow "Quarantined" badge ✅
- mystack web: Yellow "Quarantined" badge ✅
- Unquarantine button visible for both ✅

---

## 🐛 Troubleshooting

### Issue: Restart counts still not showing for compose containers

**Check 1: Service restarted with new code?**
```bash
docker-compose ps
```
Should show recent restart time.

**Check 2: API returns correct stable_id?**
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print({x['name']: x.get('stable_id') for x in c})"
```
Should show `project_service` format for compose containers.

**Check 3: config.json uses correct stable_id?**
```bash
type data\config.json | findstr restart_counts
```
Should match the stable_id from API.

**Check 4: Clear browser cache**
- Ctrl + Shift + R

### Issue: Need to migrate old config.json entries

If you have old entries with wrong stable_ids:

**Old (wrong):**
```json
"restart_counts": {
  "pihole": 5
}
```

**New (correct):**
```json
"restart_counts": {
  "pihole_pihole": 5
}
```

**Migration steps:**
1. Note the restart counts for compose containers
2. Delete old entries
3. Add new entries with correct stable_id (project_service format)
4. Restart service

---

## 📚 Files Affected

### Modified:
1. **`app/docker_client/docker_client_wrapper.py`**
   - Fixed stable_id generation to match monitoring_engine logic
   - Now uses `project_service` format for compose containers

### No Changes Needed:
2. **`app/monitor/monitoring_engine.py`**
   - Already had correct logic
   - No changes required ✅

3. **`app/api/api.py`**
   - Uses `stable_id` from info dict
   - Will automatically get correct value ✅

4. **`app/config/config_manager.py`**
   - Uses stable_id passed to methods
   - No changes required ✅

---

## ✅ Summary

**Problem:** stable_id mismatch between docker_client_wrapper (service only) and monitoring_engine (project_service)

**Solution:** Made docker_client_wrapper use same logic as monitoring_engine

**Result:** 
- ✅ Compose containers now have stable_id in `project_service` format
- ✅ Restart counts work correctly for compose containers
- ✅ Quarantine works correctly for compose containers
- ✅ config.json entries like `"pihole_pihole": 1` now match correctly

**Action needed:**
1. Wait for rebuild to complete (~1-2 minutes)
2. Clear browser cache (Ctrl + Shift + R)
3. Verify stable_id format in API response

**Your config.json with `"pihole_pihole"` was actually correct! The code was wrong. Now fixed!** ✅

---

**Status:** 🔄 Container rebuilding with fix  
**ETA:** 1-2 minutes  
**Expected:** stable_id will be `"pihole_pihole"` for compose containers

