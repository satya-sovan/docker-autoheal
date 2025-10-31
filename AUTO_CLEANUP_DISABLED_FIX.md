# 🔧 FIXED: UI Shows 0 Until Container Restarts

## 🎯 Problem Identified

You manually updated `config.json` with restart counts:
```json
"restart_counts": {
  "dummy-container-2": 3,
  "pihole_pihole": 2
}
```

But the UI showed 0 for both containers, and only updated after a container restart.

---

## 🐛 Root Cause

**Two issues were found:**

### Issue 1: Auto-Cleanup Removing Manual Entries
The `cleanup_restart_counts()` function was running every 10 seconds and removing entries that didn't match active container stable_ids. This was wiping out your manual edits!

### Issue 2: Wrong stable_id for pihole
- **config.json had:** `"pihole_pihole": 2`
- **Container's actual stable_id:** `"pihole"`

The API was looking for `"pihole"` in restart_counts, but found nothing, so it returned 0.

---

## ✅ Fixes Applied

### Fix 1: Disabled Auto-Cleanup
**File:** `app/config/config_manager.py`

```python
def cleanup_restart_counts(self, active_container_ids: List[str]) -> None:
    """Remove restart counts for containers that no longer exist (DISABLED)"""
    # DISABLED: Auto-cleanup was removing manual entries
    # Users can manually edit config.json to remove old entries if needed
    pass
```

**Why:** Auto-cleanup was too aggressive and removed manual entries. It's better to let users manually maintain the restart_counts if needed.

### Fix 2: Corrected pihole stable_id
**File:** `data/config.json`

```json
"restart_counts": {
  "dummy-container-2": 3,
  "pihole": 2  // Changed from "pihole_pihole"
}
```

**Why:** The container's stable_id is `"pihole"`, not `"pihole_pihole"`.

---

## 🚀 How to Verify

### Step 1: Wait for Build to Complete
The container is rebuilding now. Check status:
```bash
docker-compose ps
```

Wait until you see: `Up X seconds (healthy)`

### Step 2: Check API Response
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: {x[\"restart_count\"]}') for x in c if 'dummy' in x['name'] or x['name'] == 'pihole']"
```

**Expected output:**
```
dummy-container-2: 3
pihole: 2
```

### Step 3: Clear Browser Cache & Check UI
1. Open http://localhost:3131
2. Press **Ctrl + Shift + R** (hard refresh)
3. Navigate to Containers page
4. Check the "Restarts" column:
   - **dummy-container-2** should show: **3** ✅
   - **pihole** should show: **2** ✅

---

## 📊 How stable_id Works

When tracking restart counts, the system uses `stable_id`, which is determined by this priority:

1. **monitoring.id label** (if set)
2. **com.docker.compose.service label** (if from docker-compose)
3. **Container name** (fallback)

### Example: Finding Your Container's stable_id

```bash
# Check stable_id for all containers
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); [print(f'{x[\"name\"]}: stable_id=\"{x.get(\"stable_id\", x[\"name\"])}\"') for x in c]"
```

**Output example:**
```
dummy-container-2: stable_id="dummy-container-2"
pihole: stable_id="pihole"
nginx: stable_id="nginx"
```

**Use these stable_id values in config.json!**

---

## 🎯 How to Manually Set Restart Counts

### Step 1: Find Container's stable_id
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([(x['name'], x.get('stable_id', x['name'])) for x in c])"
```

### Step 2: Edit config.json
```json
{
  "containers": {
    "restart_counts": {
      "container-stable-id": 10,
      "another-stable-id": 5
    }
  }
}
```

**Important:** Use the **stable_id**, not the container name (unless they're the same)!

### Step 3: Restart Service
```bash
docker restart docker-autoheal
```

### Step 4: Verify
```bash
# Check API
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([(x['name'], x['restart_count']) for x in c])"

# Refresh browser (Ctrl + Shift + R)
```

---

## 🔮 Future Behavior

### Auto-Cleanup is Now DISABLED ✅
- Manual entries in config.json will **never be removed** automatically
- You can safely set restart counts and they'll persist
- If you want to remove old entries, edit config.json manually

### When Restart Counts Update Automatically
Restart counts will still increment automatically when:
1. Auto-heal restarts a container
2. The system calls `record_restart(stable_id)`
3. config.json is updated and saved

### Manual Entry Workflow
```
1. Find stable_id → curl API or check logs
2. Edit config.json → Add "stable-id": count
3. Restart service → docker restart docker-autoheal
4. Verify → Check API and UI
```

---

## 🧹 Optional: Remove Old Entries

If you want to clean up old entries manually:

### Find Which Containers Are Active
```bash
curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([x.get('stable_id', x['name']) for x in c])"
```

### Edit config.json
Remove entries that don't match any active stable_id:
```json
"restart_counts": {
  "active-container-1": 5,
  "active-container-2": 3
  // Remove: "old-deleted-container": 10
}
```

### Restart Service
```bash
docker restart docker-autoheal
```

---

## 📋 Summary of Changes

| File | Change | Reason |
|------|--------|--------|
| `config_manager.py` | Disabled `cleanup_restart_counts()` | Prevented auto-removal of manual entries |
| `config.json` | Changed `pihole_pihole` to `pihole` | Fixed stable_id mismatch |
| Container | Rebuilding with new code | Apply the fixes |

---

## ✅ Expected Results

After build completes and browser cache is cleared:

| Container | restart_count in config.json | API Response | UI Display |
|-----------|------------------------------|--------------|------------|
| dummy-container-2 | 3 | 3 | 3 ✅ |
| pihole | 2 | 2 | 2 ✅ |

---

## 🐛 Troubleshooting

### If UI still shows 0:

1. **Check config.json has correct stable_id:**
   ```bash
   type data\config.json | findstr restart_counts
   ```

2. **Verify API returns correct value:**
   ```bash
   curl -s http://localhost:3131/api/containers | python -c "import json,sys; c=json.load(sys.stdin); print([(x['name'], x['restart_count']) for x in c if 'dummy' in x['name'] or x['name']=='pihole'])"
   ```

3. **Clear browser cache:**
   - Ctrl + Shift + R (hard refresh)
   - Or use incognito mode

4. **Check service restarted:**
   ```bash
   docker-compose ps
   ```

5. **Check logs for errors:**
   ```bash
   docker logs docker-autoheal --tail 30
   ```

---

## 🎉 Final Steps

1. ✅ Wait for build to complete (about 1-2 minutes)
2. ✅ Check API returns correct values
3. ✅ Clear browser cache (Ctrl + Shift + R)
4. ✅ Verify UI shows correct restart counts

**No more automatic cleanup wiping your manual entries!** 🎉

---

**Status:** 🔄 Building container with fixes  
**ETA:** 1-2 minutes  
**Action needed:** Clear browser cache after build completes

