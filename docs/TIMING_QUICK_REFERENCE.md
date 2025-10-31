# Quick Reference: Restart Timing & Exponential Backoff

## TL;DR - Key Finding

⚠️ **Exponential backoff can prevent containers from EVER being quarantined!**

When backoff delays grow exponentially, restarts spread out over time. By the time the 6th restart would occur, early restarts have expired from the sliding window, so the count never reaches the threshold.

**Result:** Container retries indefinitely with progressively longer delays.

---

## Configuration Settings Explained

| Setting | Description | Impact on Timing |
|---------|-------------|------------------|
| `monitor.interval_seconds` | How often containers are checked | Determines detection speed |
| `restart.cooldown_seconds` | Min time between restarts (per container) | Hard minimum delay between restarts |
| `restart.max_restarts` | Max restarts allowed in window | Quarantine threshold |
| `restart.max_restarts_window_seconds` | Sliding time window | How far back to count restarts |
| `restart.backoff.enabled` | Enable exponential backoff | Adds progressive delays |
| `restart.backoff.initial_seconds` | Starting backoff delay | First restart delay |
| `restart.backoff.multiplier` | Backoff growth rate | How fast delays increase |

---

## Timing Formula

### Without Backoff
```
Time per restart = cooldown + monitorInterval
Total time for N restarts ≈ N × (cooldown + monitorInterval)
```

**Example:** 5 restarts × (60s + 30s) = 450 seconds

### With Exponential Backoff
```
Restart i delay = initial × (multiplier ^ i) + cooldown + monitorInterval
Total time = sum of all restart delays
```

**Example:** 
- 1st: 10s + 60s + 30s = 100s
- 2nd: 20s + 60s + 30s = 110s
- 3rd: 40s + 60s + 30s = 130s
- 4th: 80s + 60s + 30s = 170s
- 5th: 160s + 60s + 30s = 250s
- **Total: ~760 seconds**

---

## Common Configurations

### ✅ SAFE: Quick Quarantine (No Backoff)
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
- Restarts every ~90s
- Quarantines in ~7-8 minutes
- **Use for:** Production systems where you want fast failure detection

---

### ✅ SAFE: Conservative Backoff
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 3,
    "max_restarts_window_seconds": 600,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 1.5
    }
  }
}
```
- Backoff: 10s → 15s → 22.5s
- Quarantines after 3 restarts in ~6 minutes
- **Use for:** Moderate restart attempts with gentle backoff

---

### ✅ SAFE: Long Window with Aggressive Backoff
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 1200,
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0
    }
  }
}
```
- Window extended to 20 minutes
- Backoff: 10s → 20s → 40s → 80s → 160s
- Quarantines after 5 restarts
- **Use for:** When you want exponential backoff AND quarantine guarantee

---

### ❌ UNSAFE: Infinite Retry Loop
```json
{
  "monitor": { "interval_seconds": 30 },
  "restart": {
    "cooldown_seconds": 60,
    "max_restarts": 5,
    "max_restarts_window_seconds": 600,  // TOO SHORT!
    "backoff": {
      "enabled": true,
      "initial_seconds": 10,
      "multiplier": 2.0  // TOO AGGRESSIVE!
    }
  }
}
```
- Total time for 5 restarts: ~760s
- Window: only 600s
- **Result:** Container NEVER quarantines (infinite retry loop)
- ⚠️ **Validation will warn you about this!**

---

## Decision Tree: Which Config to Use?

```
Do you want containers to quarantine on persistent failures?
│
├─ YES → Is exponential backoff important?
│   │
│   ├─ NO → Use "Quick Quarantine" config (backoff disabled)
│   │        ✅ Fast failure detection
│   │        ✅ Guaranteed quarantine
│   │
│   └─ YES → Use "Long Window" config OR "Conservative Backoff"
│            ✅ Exponential backoff for transient issues
│            ✅ Guaranteed quarantine for persistent issues
│
└─ NO → Use aggressive backoff with short window
         ⚠️ Container will retry indefinitely
         ⚠️ Only use if you WANT infinite retries
```

---

## Validation Quick Check

The UI will warn you if:

### 🔴 CRITICAL (Config won't work as expected)
- **Exponential backoff spreads restarts beyond window**
  - Fix: Increase window, reduce restarts, or disable backoff
- **Window too small for restarts with cooldown**
  - Fix: Increase window or reduce cooldown
- **Window too small for monitoring cycles**
  - Fix: Increase window or reduce interval

### ⚠️ WARNING (Suboptimal but functional)
- **Very short monitoring interval** (<5s)
  - Impact: High CPU usage
- **Very short restart window** (<60s)
  - Impact: May quarantine too quickly
- **Very long monitoring interval** (>300s)
  - Impact: Slow to detect failures
- **Exponential backoff timing is tight**
  - Impact: Close to the edge, may be unreliable

---

## Key Insights

### 1. Sliding Window is Dynamic
The restart count looks back from "now" for `window_seconds`. Old restarts automatically expire.

### 2. Quarantine Check Happens BEFORE Restart
```python
if restart_count >= max_restarts:
    quarantine()  # Block this restart
else:
    restart()     # Allow restart, then increment count
```

This means the container can perform `max_restarts` attempts before quarantine.

### 3. Backoff is Applied BEFORE Restart
The monitoring loop detects an issue, starts backoff delay, then restarts. During backoff, subsequent monitoring checks skip the container.

### 4. Cooldown vs Backoff
- **Cooldown**: Enforced AFTER every restart (prevents rapid restarts)
- **Backoff**: Applied BEFORE restart attempt (gives more time to recover)
- **Both** contribute to the total time between restarts

### 5. Monitoring Doesn't Pause
The monitoring loop runs continuously every `interval_seconds`. It just skips containers that are in cooldown or backoff.

---

## Formulas for Quick Calculation

### Minimum Window Without Backoff
```
window >= max_restarts × (cooldown + monitorInterval)
```

### Minimum Window With Backoff
```
totalTime = 0
backoff = initial
for i in range(max_restarts):
    totalTime += backoff + cooldown + monitorInterval
    backoff *= multiplier

window >= totalTime × 1.2  // 20% safety margin
```

### Time Until Quarantine (Without Backoff)
```
time ≈ max_restarts × (cooldown + monitorInterval)
```

### Time Until Quarantine (With Backoff)
Use the loop calculation above - no simple formula due to exponential growth.

---

## Testing Your Configuration

1. **Open the web UI** (default: http://localhost:3131)
2. **Go to Configuration** tab
3. **Adjust restart settings**
4. **Look for validation warnings** at the top
5. **If you see critical warnings**, adjust settings until they clear

The validation automatically calculates whether your config will work as expected!

---

## Related Documentation

- **[TIMING_SCENARIO_TRACE.md](./TIMING_SCENARIO_TRACE.md)** - Complete step-by-step trace with example config
- **[EXPONENTIAL_BACKOFF_VALIDATION.md](./EXPONENTIAL_BACKOFF_VALIDATION.md)** - Validation algorithm details
- **[TIMING_VALIDATION_TEST_RESULTS.md](./TIMING_VALIDATION_TEST_RESULTS.md)** - Test cases

---

## Quick Fix Cheat Sheet

| Problem | Quick Fix |
|---------|-----------|
| "Backoff will prevent quarantine" | Set `backoff.enabled: false` |
| "Window too small for restarts" | Increase `max_restarts_window_seconds` |
| Want faster quarantine | Reduce `max_restarts` to 3 |
| Want gentler backoff | Set `multiplier: 1.5` instead of 2.0 |
| Infinite retry loop | Disable backoff or increase window to 1200s+ |
| Too aggressive | Increase cooldown to 120s |
| Too slow to detect failures | Reduce `interval_seconds` to 15s |

---

**Last Updated:** Based on analysis completed October 31, 2025

