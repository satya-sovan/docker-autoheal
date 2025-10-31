# Exponential Backoff Validation Logic

## Overview

The validation logic now includes a **critical check** for exponential backoff timing that prevents containers from being quarantined when the backoff spreads restarts beyond the sliding window.

## The Problem

When exponential backoff is enabled with a multiplier > 1.0, the delay between restarts grows exponentially:
- 1st restart: `initial_seconds` (e.g., 10s)
- 2nd restart: `initial_seconds × multiplier` (e.g., 20s)
- 3rd restart: `initial_seconds × multiplier²` (e.g., 40s)
- 4th restart: `initial_seconds × multiplier³` (e.g., 80s)
- 5th restart: `initial_seconds × multiplier⁴` (e.g., 160s)
- 6th restart: `initial_seconds × multiplier⁵` (e.g., 320s)

**Result:** By the time later restarts occur, early restarts have **expired from the sliding window**, preventing quarantine from ever being triggered.

---

## Validation Algorithm

### Step 1: Calculate Total Time for All Restarts

For each restart attempt (0 to max_restarts - 1):
```javascript
totalTime = 0
currentBackoff = initial_seconds

for (i = 0; i < max_restarts; i++):
    totalTime += currentBackoff + cooldown + monitorInterval
    currentBackoff = currentBackoff × multiplier
```

This gives the **estimated time span** for `max_restarts` to occur.

### Step 2: Calculate Final Backoff Delay

```javascript
finalBackoff = initial_seconds × (multiplier ^ (max_restarts - 1))
```

This is the backoff delay that would be applied before the last allowed restart.

### Step 3: Compare to Window

**Critical Warning** if:
```javascript
totalTime > restartWindow × 1.2  // 20% buffer
```

**Close Warning** if:
```javascript
totalTime > restartWindow × 0.95  // 95% utilization
```

---

## Example Validation Results

### Example 1: Your Original Configuration (FAILS)

```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 600,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0
    }
  }
}
```

**Calculation:**
| Restart | Backoff | + Cooldown | + Monitor | Cumulative Time |
|---------|---------|------------|-----------|-----------------|
| 1st     | 10s     | 60s        | 30s       | 100s            |
| 2nd     | 20s     | 60s        | 30s       | 210s            |
| 3rd     | 40s     | 60s        | 30s       | 340s            |
| 4th     | 80s     | 60s        | 30s       | 510s            |
| 5th     | 160s    | 60s        | 30s       | 760s            |

**Total Time: ~760 seconds (12.6 minutes)**
**Window: 600 seconds (10 minutes)**
**Final Backoff: 160s**

**Result:**
```
⚠️ CRITICAL: Exponential backoff will prevent quarantine!
🔴 The 5 restarts will take ~760s, but your window is only 600s
By the time restart #6 occurs, early restarts will expire from the 600s window
📊 Final backoff delay will be 160s (10s × 2.0^4)

✅ RECOMMENDED FIXES:
   1. Increase window to 1140s+ (covers all restarts with buffer)
   2. Reduce max_restarts to 3 or less
   3. Disable backoff for faster quarantine (restarts every ~90s)
   4. Use slower multiplier (1.5 instead of 2.0)

⚠️ Current config = INFINITE RETRY LOOP (container never quarantines)
```

---

### Example 2: Fixed Configuration (PASSES)

**Option A: Disable Backoff**
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 600,
    "backoff": { "enabled": false }
  }
}
```

**Calculation:**
- Time per restart: ~90s (60s cooldown + 30s monitor)
- Total for 5 restarts: ~450s
- Window: 600s ✅
- **Result: Container quarantines in ~7-8 minutes**

---

**Option B: Increase Window**
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 1200,  // 20 minutes
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0
    }
  }
}
```

**Calculation:**
- Total time for 5 restarts: ~760s
- Window: 1200s ✅
- Utilization: 63%
- **Result: Container quarantines after 5 restarts**

---

**Option C: Reduce Max Restarts**
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 3,  // Reduced from 5
    "max_restarts_window_seconds": 600,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0
    }
  }
}
```

**Calculation:**
- Total for 3 restarts: ~340s
- Window: 600s ✅
- Utilization: 57%
- **Result: Container quarantines after 3 restarts in ~6 minutes**

---

**Option D: Slower Multiplier**
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 600,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 1.5  // Reduced from 2.0
    }
  }
}
```

**Calculation:**
- Backoff sequence: 10s, 15s, 22.5s, 33.75s, 50.6s
- Total for 5 restarts: ~582s
- Window: 600s ✅
- Utilization: 97% (tight but acceptable)
- **Result: Container quarantines after 5 restarts**

---

## When Validation Fires

### Critical Warning (Red)
**Condition:** `totalTime > restartWindow × 1.2`

**Meaning:** The configuration will **definitely** result in an infinite retry loop. Container will never be quarantined.

**Action Required:** User must fix configuration before saving.

### Close Warning (Yellow)
**Condition:** `totalTime > restartWindow × 0.95`

**Meaning:** The configuration is cutting it very close. Minor timing variations could prevent quarantine.

**Action Recommended:** User should increase window for safety margin.

---

## UI Implementation

The validation runs when:
1. User changes any restart configuration
2. User clicks "Update Monitor Settings" or "Update Restart Settings"
3. Before submitting configuration to backend

If validation fails:
1. Modal dialog shows errors and suggestions
2. Configuration is **not saved** until user fixes or dismisses warning
3. User can override warning but sees prominent alert

---

## Benefits

1. **Prevents misconfiguration** that leads to infinite retry loops
2. **Educates users** about exponential backoff behavior
3. **Provides actionable recommendations** with specific values
4. **Catches edge cases** automatically (no manual calculation needed)
5. **Validates on-the-fly** as user adjusts settings

---

## Technical Notes

### Why 20% Buffer?
The 1.2× multiplier accounts for:
- Monitoring cycle timing variations
- Container startup time
- System scheduling delays
- Clock drift

### Why Not Block Invalid Config?
The validation shows warnings but allows override because:
- Some users may want infinite retry behavior
- Advanced users may have specific use cases
- Provides educational value without being overly restrictive

### Accuracy
The calculation is an **estimate** because:
- Actual monitoring may not align perfectly with intervals
- Container health checks have their own timing
- Cooldown is enforced strictly, but detection has variance

However, the estimate is **conservative** and catches genuine problems reliably.

---

## Related Documentation

- [TIMING_SCENARIO_TRACE.md](./TIMING_SCENARIO_TRACE.md) - Complete trace of timing behavior
- [TIMING_VALIDATION_TEST_RESULTS.md](./TIMING_VALIDATION_TEST_RESULTS.md) - Test cases for validation
- [AUTO_MONITOR_FEATURE.md](./AUTO_MONITOR_FEATURE.md) - Auto-monitoring feature

---

## Code Reference

**Frontend Validation:**
`frontend/src/components/ConfigPage.jsx` - `validateTimingConfiguration()` function

**Backend Logic:**
`app/monitor/monitoring_engine.py` - `_handle_container_restart()` method

**Config Models:**
`app/config/config_manager.py` - `RestartConfig` and `BackoffConfig` classes

