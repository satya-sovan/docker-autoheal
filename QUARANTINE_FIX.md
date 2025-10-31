# 🔧 FIXED: Quarantine Not Showing in UI

## 🎯 Problem

Quarantined containers were not showing in the UI with the "Quarantined" badge, and the "Unquarantine" button wasn't appearing even though containers were stored in `quarantine.json`.

---

## 🐛 Root Cause

**Mismatch between how quarantine is stored vs how it's checked:**

### How Quarantine is Stored (Monitoring Engine)
```python
# monitoring_engine.py line 429
config_manager.quarantine_container(stable_id)  # Uses stable_id!
```

### How Quarantine was Checked (API - WRONG)
```python
# api.py line 156 - BEFORE FIX
quarantined = config_manager.is_quarantined(container_id)  # Uses full Docker ID ❌
```

**Result:** The API was looking for the full Docker ID in quarantine.json, but the file contained stable_ids (container names). They never matched, so UI always showed `quarantined: false`.

---

## ✅ Fixes Applied

### Fix 1: Container List Endpoint
**File:** `app/api/api.py` (line 156)

**Before:**
```python
quarantined = config_manager.is_quarantined(container_id)  # Wrong - uses Docker ID
```

**After:**
```python
quarantined = config_manager.is_quarantined(stable_id)  # Correct - uses stable_id
```

### Fix 2: Container Details Endpoint
**File:** `app/api/api.py` (line 211)

**Before:**
```python
quarantined = config_manager.is_quarantined(container_name) or config_manager.is_quarantined(full_container_id)
```

**After:**
```python
quarantined = config_manager.is_quarantined(stable_id)  # Correct - uses stable_id
```

### Fix 3: Unquarantine Endpoint
**File:** `app/api/api.py` (line 368-379)

**Before:**
```python
config_manager.unquarantine_container(container_name)
config_manager.unquarantine_container(full_container_id)
config_manager.clear_restart_history(container_name)
config_manager.clear_restart_history(full_container_id)
```

**After:**
```python
stable_id = info.get("stable_id")
config_manager.unquarantine_container(stable_id)  # Use stable_id
config_manager.clear_restart_history(stable_id)    # Use stable_id
```

---

## 📊 Data Flow - Before vs After

### Before (Broken) ❌
```
Monitoring Engine:
  Quarantines → stable_id="pihole"
  Saves to quarantine.json → ["pihole"]

API List Containers:
  Checks → container_id="a1b2c3d4e5f6..." (Docker ID)
  Looks in quarantine.json → "pihole" not found
  Returns → quarantined: false ❌

UI:
  Shows → No "Quarantined" badge ❌
  Shows → No "Unquarantine" button ❌
```

### After (Fixed) ✅
```
Monitoring Engine:
  Quarantines → stable_id="pihole"
  Saves to quarantine.json → ["pihole"]

API List Containers:
  Checks → stable_id="pihole"
  Looks in quarantine.json → "pihole" found!
  Returns → quarantined: true ✅

UI:
  Shows → "Quarantined" badge ✅
  Shows → "Unquarantine" button ✅
```

---

## 🧪 How to Test

### Step 1: Quarantine a Container Manually
```bash
# Edit quarantine.json
echo ["pihole", "dummy-container-2"] > data\quarantine.json

# Or using Python
python -c "import json; json.dump(['pihole', 'dummy-container-2'], open('data/quarantine.json', 'w'))"
```

### Step 2: Restart Service
```bash
docker restart docker-autoheal
```

### Step 3: Check API Response
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: quarantined={x[\"quarantined\"]}') for x in c if x['name'] in ['pihole', 'dummy-container-2']]"
```

**Expected Output:**
```
pihole: quarantined=True
dummy-container-2: quarantined=True
```

### Step 4: Check UI
1. Open http://localhost:3131
2. Press **Ctrl + Shift + R** (hard refresh)
3. Go to Containers page
4. Look for containers in quarantine:
   - Should show **"Quarantined"** badge ✅
   - Hover/click container
   - Should show **"Unquarantine"** button ✅

### Step 5: Test Unquarantine
1. Click the "Unquarantine" button
2. Container should be removed from quarantine
3. Badge should disappear
4. Check `data/quarantine.json` - container should be removed

---

## 📋 Quarantine File Format

**File:** `data/quarantine.json`

**Format:**
```json
[
  "pihole",
  "dummy-container-2",
  "nginx"
]
```

**Important:** Use **stable_id**, not Docker container ID!

---

## 🔍 Finding Container stable_ids

To add containers to quarantine manually, you need their stable_id:

```bash
# Get all stable_ids
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: stable_id=\"{x.get(\"stable_id\", x[\"name\"])}\"') for x in c]"
```

**Example Output:**
```
pihole: stable_id="pihole"
dummy-container-2: stable_id="dummy-container-2"
nginx-proxy: stable_id="nginx-proxy"
```

Use these stable_id values in `quarantine.json`!

---

## 🎯 Manual Quarantine Workflow

### Quarantine a Container Manually

**Step 1: Get stable_id**
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([x['name'] + ':' + x.get('stable_id') for x in c])"
```

**Step 2: Edit quarantine.json**
```json
[
  "container-stable-id-1",
  "container-stable-id-2"
]
```

**Step 3: Restart service**
```bash
docker restart docker-autoheal
```

**Step 4: Verify**
```bash
# Check API
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([(x['name'], x['quarantined']) for x in c])"

# Refresh browser (Ctrl + Shift + R)
```

### Unquarantine via UI
1. Find quarantined container in UI (yellow "Quarantined" badge)
2. Click the "Unquarantine" button
3. Container is removed from quarantine
4. Restart history is cleared

### Unquarantine via API
```bash
curl -X POST http://localhost:3131/api/containers/{container_id}/unquarantine
```

### Unquarantine Manually
```bash
# Edit quarantine.json - remove the container's stable_id
# Before: ["pihole", "nginx"]
# After:  ["nginx"]

# Restart service
docker restart docker-autoheal
```

---

## 🔮 How Auto-Quarantine Works

When a container hits the restart limit:

1. **Monitoring Engine detects excessive restarts**
   ```python
   if restart_count >= config.restart.max_restarts:
       config_manager.quarantine_container(stable_id)
   ```

2. **Saved to quarantine.json**
   ```json
   ["pihole"]
   ```

3. **Container stops being monitored**
   - Auto-heal won't restart it anymore
   - Prevents infinite restart loops

4. **UI shows quarantine status**
   - Yellow "Quarantined" badge appears
   - "Unquarantine" button becomes available

5. **Admin can unquarantine**
   - Click "Unquarantine" button in UI
   - Or manually edit quarantine.json
   - Restart history is cleared
   - Container resumes normal monitoring

---

## 📊 Summary of Changes

| File | Lines | Change | Impact |
|------|-------|--------|--------|
| `api.py` | 156 | Use `stable_id` for quarantine check | List endpoint ✅ |
| `api.py` | 211 | Use `stable_id` for quarantine check | Details endpoint ✅ |
| `api.py` | 368-379 | Use `stable_id` for unquarantine | Unquarantine works ✅ |

---

## ✅ Expected Results

After rebuild and browser cache clear:

### UI Container List
```
┌──────────────────┬──────────┬──────────┬────────────────┐
│ Container Name   │ Status   │ Restarts │ Badges         │
├──────────────────┼──────────┼──────────┼────────────────┤
│ pihole           │ running  │    5     │ 🟡 Quarantined │ ✅
│ nginx            │ running  │    2     │                │
└──────────────────┴──────────┴──────────┴────────────────┘
```

### UI Container Details (Quarantined Container)
```
Container: pihole
Status: running
Quarantined: Yes
Restart Count: 5

[Unquarantine] button visible ✅
```

### quarantine.json
```json
[
  "pihole"
]
```

---

## 🐛 Troubleshooting

### Issue: Quarantine badge not showing

**Check 1: quarantine.json has correct stable_id**
```bash
type data\quarantine.json
```
Should contain stable_id, not Docker ID.

**Check 2: stable_id matches**
```bash
# Get stable_id from API
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print({x['name']: x.get('stable_id') for x in c})"

# Compare with quarantine.json
type data\quarantine.json
```

**Check 3: Service restarted**
```bash
docker restart docker-autoheal
```

**Check 4: API returns quarantined=true**
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([(x['name'], x['quarantined']) for x in c])"
```

**Check 5: Clear browser cache**
- Ctrl + Shift + R

### Issue: Unquarantine button not appearing

**The button only appears for quarantined containers.**

Check if container is actually quarantined:
```bash
curl -s http://localhost:3131/api/containers/{container_id} | python -c "import json,sys; print(json.load(sys.stdin)['quarantined'])"
```

Should return `True`.

### Issue: Unquarantine not working

**Check logs:**
```bash
docker logs docker-autoheal --tail 50 | findstr unquarantine
```

**Verify stable_id is being used:**
```bash
# Check what's in quarantine.json after unquarantine
type data\quarantine.json
```

Should be removed from the list.

---

## 🚀 Quick Commands

```bash
# Check quarantine status
type data\quarantine.json

# Get all stable_ids
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(x.get('stable_id')) for x in c]"

# Check API quarantine status
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: {x[\"quarantined\"]}') for x in c]"

# Manually quarantine
echo ["pihole"] > data\quarantine.json && docker restart docker-autoheal

# Manually unquarantine
echo [] > data\quarantine.json && docker restart docker-autoheal

# View logs
docker logs docker-autoheal --tail 30
```

---

**Status:** ✅ Fixed - Quarantine now uses stable_id consistently  
**Build Status:** 🔄 Container rebuilding  
**Action Needed:** Clear browser cache after build completes  
**Expected:** Quarantine badges and unquarantine buttons will work correctly!

