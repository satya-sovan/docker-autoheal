# 🗺️ CODE FLOW MAP: container.restart_count

## Line-by-Line Trace with Code Snippets

---

## ✅ CONFIRMED: restart_count comes from config.json, NOT Docker!

---

## 📍 The Complete Journey

### START → Frontend Display (Line 280)

**File:** `frontend/src/components/ContainersPage.jsx`
**Line:** 280

```javascript
<td>{container.restart_count}</td>
```

**Value:** Displays the restart count number
**Source:** `container` object from state

---

### ⬆️ Where does `container` come from?

**File:** `frontend/src/components/ContainersPage.jsx`
**Line:** 21

```javascript
const response = await getContainers(true);
setContainers(response.data);  // ← Sets containers state
```

**Source:** `response.data` from API call

---

### ⬆️ What is `getContainers()`?

**File:** `frontend/src/services/api.js`
**Line:** 18

```javascript
export const getContainers = (includeStopped = false) =>
  api.get('/containers', { params: { include_stopped: includeStopped } });
```

**HTTP Request:** `GET /api/containers?include_stopped=true`

---

### ⬆️ Backend API Endpoint

**File:** `app/api/api.py`
**Lines:** 131-176

```python
@app.get("/api/containers", response_model=List[ContainerInfo])
async def list_containers(include_stopped: bool = False):
    # ... get containers from Docker ...
    
    for container in containers:
        info = docker_client.get_container_info(container)
        
        stable_id = info.get("stable_id")  # Line 149
        
        # 🎯 THIS IS THE KEY LINE!
        locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)  # Line 162
        
        container_info = ContainerInfo(
            # ...
            restart_count=locally_tracked_restarts,  # Line 172 - FROM config.json!
            # ...
        )
```

**Key Line 162:** Calls `config_manager.get_total_restart_count(stable_id)`
**Key Line 172:** Sets `restart_count=locally_tracked_restarts` (NOT from Docker!)

---

### ⬆️ What is `get_total_restart_count()`?

**File:** `app/config/config_manager.py`
**Lines:** 420-424

```python
def get_total_restart_count(self, container_id: str) -> int:
    """Get total restart count (all time) - from config.json"""
    with self._lock:
        return self._config.containers.restart_counts.get(container_id, 0)  # Line 423
```

**Key Line 423:** Returns value from `self._config.containers.restart_counts`

---

### ⬆️ Where is `self._config` loaded from?

**File:** `app/config/config_manager.py`
**Lines:** 140-141

```python
self._config = self._load_config()  # Loads from config.json
```

**Method:** `_load_config()` reads from `data/config.json`

---

### ⬆️ Final Source: config.json

**File:** `data/config.json`
**Lines:** 8-13

```json
{
  "containers": {
    "selected": ["test-dummy"],
    "excluded": [],
    "restart_counts": {
      "test-dummy": 2
    }
  }
}
```

**🎯 SOURCE OF TRUTH!**
**Key Line 11:** `"test-dummy": 2` ← This is what gets displayed!

---

## 🔄 Complete Flow with Line Numbers

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. config.json (Line 11)                                        │
│    "restart_counts": { "test-dummy": 2 }                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ loaded by
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. config_manager.py (Line 423)                                 │
│    return self._config.containers.restart_counts.get(id, 0)     │
│    → Returns: 2                                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ called by
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. api.py (Line 162)                                            │
│    locally_tracked_restarts =                                   │
│      config_manager.get_total_restart_count(stable_id)          │
│    → Gets: 2                                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ used in
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. api.py (Line 172)                                            │
│    restart_count=locally_tracked_restarts                       │
│    → Sets: 2 in response                                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ returned to
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. ContainersPage.jsx (Line 21)                                 │
│    const response = await getContainers(true)                   │
│    setContainers(response.data)                                 │
│    → Receives: [{..., restart_count: 2, ...}]                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ displayed in
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ContainersPage.jsx (Line 280)                                │
│    <td>{container.restart_count}</td>                           │
│    → Shows: 2                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚫 What About Docker's RestartCount?

### Docker Value IS Read...

**File:** `app/docker_client/docker_client_wrapper.py`
**Line:** 132

```python
info = {
    # ...
    "restart_count": attrs.get("State", {}).get("RestartCount", 0),  # Docker's value
    # ...
}
```

Docker's native `RestartCount` IS fetched here...

---

### ...BUT It's OVERRIDDEN!

**File:** `app/api/api.py`
**Lines:** 162 + 172

```python
# Line 162: Get locally tracked count (from config.json)
locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)

# Line 172: Override Docker's value with config.json value!
container_info = ContainerInfo(
    restart_count=locally_tracked_restarts,  # ← Replaces Docker value
)
```

**Docker's value is thrown away and replaced with config.json value!**

---

## 💡 Code Evidence Summary

| Location | File | Line | Code | Value Source |
|----------|------|------|------|--------------|
| **Storage** | `config.json` | 11 | `"test-dummy": 2` | **config.json** |
| **Read** | `config_manager.py` | 423 | `return ...restart_counts.get(id, 0)` | **config.json** |
| **API** | `api.py` | 162 | `get_total_restart_count(stable_id)` | **config.json** |
| **Response** | `api.py` | 172 | `restart_count=locally_tracked_restarts` | **config.json** |
| **Frontend** | `api.js` | 18 | `api.get('/containers')` | **config.json** |
| **Display** | `ContainersPage.jsx` | 280 | `{container.restart_count}` | **config.json** |

**Every step uses config.json! Docker's value is NOT used!**

---

## 🔬 How to Prove It

### Experiment 1: Modify config.json

```bash
# 1. Edit config.json
notepad data\config.json

# 2. Change restart count
"restart_counts": {
  "test-dummy": 999  # Change to 999
}

# 3. Restart service
docker-compose restart

# 4. Check UI
# Restarts column will show: 999 ✅
```

**If it shows 999, it proves it comes from config.json!**

---

### Experiment 2: Check Docker's Value

```python
# Run in Python shell
import docker

client = docker.from_env()
container = client.containers.get('test-dummy')
container.reload()
docker_restart_count = container.attrs['State']['RestartCount']
print(f"Docker says: {docker_restart_count}")

# Check config.json
import json

with open('../data/config.json') as f:
    config = json.load(f)
    config_restart_count = config['containers']['restart_counts'].get('test-dummy', 0)
    print(f"Config says: {config_restart_count}")

# Check UI
# Open http://localhost:8000/containers
# UI will show the config value, NOT Docker's value!
```

---

## 📊 Side-by-Side Comparison

### Docker's Value (NOT USED)
```python
# docker_client_wrapper.py line 132
attrs.get("State", {}).get("RestartCount", 0)
```
- Source: Docker Engine
- Resets on container recreate
- Only counts policy-based restarts
- ❌ **NOT displayed in UI**

### Config.json Value (USED)
```python
# config_manager.py line 423
self._config.containers.restart_counts.get(container_id, 0)
```
- Source: config.json file
- Never resets (persistent)
- Counts all auto-heal restarts
- ✅ **Displayed in UI**

---

## ✅ Final Verdict

**Question:** Is `container.restart_count` (line 280) fetched from config.json or Docker?

**Answer:** **config.json** ✅

**Proof:**
1. Line 280 displays `container.restart_count`
2. Value comes from API response at line 21
3. API endpoint (line 162) calls `config_manager.get_total_restart_count()`
4. That method (line 423) returns `self._config.containers.restart_counts.get(id)`
5. Which is loaded from `data/config.json` (line 11)

**Docker's `RestartCount` is read but immediately discarded. Only config.json value is used!**

---

**Created:** October 31, 2025  
**Status:** ✅ Verified and Documented  
**Conclusion:** 100% from config.json, 0% from Docker

