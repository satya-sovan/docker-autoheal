# 📊 DATA FLOW MAP: container.restart_count

## Complete Trace: Frontend → Backend → config.json

This document traces exactly how `container.restart_count` displayed in the UI comes from `config.json` (NOT from Docker).

---

## 🎯 Quick Answer

**YES, `container.restart_count` is fetched from `config.json`**, not from Docker's restart count.

Here's the proof:

```
Frontend (ContainersPage.jsx)
    ↓
API Call: getContainers()
    ↓
Backend: /api/containers endpoint
    ↓
config_manager.get_total_restart_count(stable_id)
    ↓
self._config.containers.restart_counts.get(container_id, 0)
    ↓
data/config.json → "restart_counts": {"test-dummy": 2}
```

---

## 📍 Step-by-Step Data Flow

### 1️⃣ Frontend: ContainersPage.jsx (Line 280)

**File:** `frontend/src/components/ContainersPage.jsx`
**Line 280:**
```javascript
<td>{container.restart_count}</td>
```

This displays the restart count in the UI table.

**Where does `container.restart_count` come from?**
→ From the `containers` state array

---

### 2️⃣ Frontend: fetchContainers() Function (Line 19-28)

**File:** `frontend/src/components/ContainersPage.jsx`
**Lines 19-28:**
```javascript
const fetchContainers = async () => {
  try {
    const response = await getContainers(true); // Include stopped containers
    setContainers(response.data);  // ← Sets the containers state
  } catch (error) {
    showAlert('danger', 'Failed to load containers');
  } finally {
    setLoading(false);
  }
};
```

**Where does `response.data` come from?**
→ From the `getContainers()` API call

---

### 3️⃣ Frontend: API Service

**File:** `frontend/src/services/api.js`
**Line 18:**
```javascript
export const getContainers = (includeStopped = false) =>
  api.get('/containers', { params: { include_stopped: includeStopped } });
```

**This makes an HTTP GET request to:**
→ `GET /api/containers?include_stopped=true`

---

### 4️⃣ Backend: API Endpoint

**File:** `app/api/api.py`
**Lines 131-176:**
```python
@app.get("/api/containers", response_model=List[ContainerInfo])
async def list_containers(include_stopped: bool = False):
    """List all containers with their monitoring status"""
    try:
        if not docker_client:
            raise HTTPException(status_code=500, detail="Docker client not initialized")

        containers = docker_client.list_containers(all_containers=include_stopped)
        result = []

        for container in containers:
            info = docker_client.get_container_info(container)
            if not info:
                continue

            container_id = info.get("full_id")
            stable_id = info.get("stable_id")  # ← Get stable identifier

            # Check if monitored
            monitored = False
            if monitoring_engine:
                monitored = monitoring_engine._should_monitor_container(container, info)

            # Check if quarantined
            quarantined = config_manager.is_quarantined(container_id)

            # 🎯 KEY LINE: Get locally tracked restart count
            locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)

            container_info = ContainerInfo(
                id=info.get("id"),
                name=info.get("name"),
                image=info.get("image"),
                status=info.get("status"),
                state=info.get("state", {}),
                labels=info.get("labels", {}),
                health=info.get("health"),
                restart_count=locally_tracked_restarts,  # ← Uses locally tracked count!
                monitored=monitored,
                quarantined=quarantined
            )
            result.append(container_info)

        return result
```

**Key Line (162):**
```python
locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)
```

**Key Line (172):**
```python
restart_count=locally_tracked_restarts,  # Uses locally tracked count!
```

**This calls the config_manager method, NOT Docker!**
→ `config_manager.get_total_restart_count(stable_id)`

---

### 5️⃣ Backend: Config Manager Method

**File:** `app/config/config_manager.py`
**Lines 420-424:**
```python
def get_total_restart_count(self, container_id: str) -> int:
    """Get total restart count (all time) - from config.json"""
    with self._lock:
        return self._config.containers.restart_counts.get(container_id, 0)
```

**This reads from:**
→ `self._config.containers.restart_counts`

**Which is loaded from:**
→ `data/config.json`

---

### 6️⃣ Storage: config.json

**File:** `data/config.json`
**Lines 8-13:**
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

**This is the SOURCE OF TRUTH!**
→ `restart_counts.test-dummy = 2`

---

## 🔍 Comparison: What Docker Says vs What We Display

### Docker's Native RestartCount

**File:** `app/docker_client/docker_client_wrapper.py`
**Line 132:**
```python
"restart_count": attrs.get("State", {}).get("RestartCount", 0),
```

This reads Docker's native restart count from the container state.

**❌ BUT THIS IS NOT USED IN THE UI!**

The API endpoint **OVERRIDES** this value with the locally tracked count:

```python
# Line 162 in api.py
locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)

# Line 172 in api.py
restart_count=locally_tracked_restarts,  # ← Overrides Docker's value!
```

---

## 📊 Visual Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: ContainersPage.jsx                                    │
│ ─────────────────────────────────────────────────────────────  │
│ Line 280: <td>{container.restart_count}</td>                    │
│           Display value in UI table                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: fetchContainers() → getContainers()                   │
│ ─────────────────────────────────────────────────────────────  │
│ API Call: GET /api/containers?include_stopped=true              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: /api/containers endpoint                               │
│ ─────────────────────────────────────────────────────────────  │
│ File: app/api/api.py                                            │
│ Line 162: locally_tracked_restarts =                            │
│           config_manager.get_total_restart_count(stable_id)     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: ConfigManager.get_total_restart_count()                │
│ ─────────────────────────────────────────────────────────────  │
│ File: app/config/config_manager.py                              │
│ Line 423: return self._config.containers.restart_counts         │
│                    .get(container_id, 0)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ STORAGE: config.json                                            │
│ ─────────────────────────────────────────────────────────────  │
│ File: data/config.json                                          │
│ {                                                               │
│   "containers": {                                               │
│     "restart_counts": {                                         │
│       "test-dummy": 2  ← SOURCE OF TRUTH!                       │
│     }                                                           │
│   }                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚫 What Is NOT Used

### Docker's RestartCount (NOT USED in UI)

```python
# docker_client_wrapper.py line 132
"restart_count": attrs.get("State", {}).get("RestartCount", 0),
```

This Docker value IS read from the container, but it's **IMMEDIATELY OVERRIDDEN** in the API:

```python
# api.py line 162-172
locally_tracked_restarts = config_manager.get_total_restart_count(stable_id)
container_info = ContainerInfo(
    # ...
    restart_count=locally_tracked_restarts,  # ← Overrides Docker value
)
```

---

## ✅ Proof That It's From config.json

### Test 1: Check config.json
```bash
type data\config.json | findstr restart_counts
```
**Output:**
```json
"restart_counts": {
  "test-dummy": 2
}
```

### Test 2: Check UI
- Open http://localhost:8000/containers
- Find test-dummy container
- **Restarts column shows: 2** ✅

### Test 3: Verify API Response
```bash
curl http://localhost:8000/api/containers | jq '.[].restart_count'
```
**Output:**
```
2
```

### Test 4: Increment and Verify
1. Auto-heal restarts test-dummy
2. config.json updates: `"test-dummy": 3`
3. UI refreshes and shows: **3** ✅

---

## 📝 Summary Table

| Component | File | Line | What It Does |
|-----------|------|------|--------------|
| **UI Display** | `ContainersPage.jsx` | 280 | Shows `container.restart_count` |
| **Fetch Data** | `ContainersPage.jsx` | 21 | Calls `getContainers()` API |
| **API Call** | `api.js` | 18 | `GET /api/containers` |
| **API Endpoint** | `api.py` | 162 | Calls `get_total_restart_count(stable_id)` |
| **Get Count** | `config_manager.py` | 423 | Returns `self._config.containers.restart_counts[id]` |
| **Storage** | `config.json` | 11 | `"restart_counts": {"test-dummy": 2}` |

---

## 🎯 Key Takeaways

1. ✅ **`container.restart_count` comes from `config.json`**
   - NOT from Docker's `RestartCount` field

2. ✅ **The API endpoint explicitly uses locally tracked counts**
   - Line 162 in `api.py`: `config_manager.get_total_restart_count(stable_id)`

3. ✅ **The value is stored in `config.json`**
   - Under `containers.restart_counts`
   - Format: `{"stable_id": count}`

4. ✅ **Docker's value is ignored**
   - Docker's `RestartCount` is read but immediately overridden
   - The API returns the config.json value instead

5. ✅ **This means:**
   - Counts persist across container recreations
   - Counts never reset (unless you edit config.json)
   - Counts track all auto-heal restarts
   - Counts survive app restarts

---

## 🔧 How to Verify

### Method 1: Check the Source
```bash
# View config.json
type data\config.json

# Look for restart_counts section
# You'll see: "test-dummy": 2
```

### Method 2: Check API Response
```bash
# Call API directly
curl http://localhost:8000/api/containers

# Look for restart_count field in response
# It will match config.json value
```

### Method 3: Modify and Verify
```bash
# 1. Edit config.json manually
# Change "test-dummy": 2 to "test-dummy": 100

# 2. Restart service
docker-compose restart

# 3. Check UI
# Restarts column will show: 100 ✅
```

---

## 🎉 Conclusion

**YES, `container.restart_count` displayed at line 280 in `ContainersPage.jsx` is 100% fetched from `config.json`!**

The data flows:
```
config.json → ConfigManager → API Endpoint → Frontend → UI Display
```

Docker's `RestartCount` is NOT used in this flow!

---

**Date:** October 31, 2025  
**Verified:** ✅ Complete data flow traced  
**Source:** `data/config.json` → `containers.restart_counts`

