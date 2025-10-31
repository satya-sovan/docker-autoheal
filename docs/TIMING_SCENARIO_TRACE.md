# Complete Timing Scenario Trace

## Configuration Settings
```json
{
  "monitor": { 
    "interval_seconds": 30 
  },
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

## Key Parameters
- **Monitoring Interval**: 30 seconds (how often containers are checked)
- **Cooldown**: 60 seconds (minimum time between restarts)
- **Max Restarts**: 5 restarts allowed
- **Window**: 600 seconds (10 minutes sliding window)
- **Backoff**: Starts at 10s, doubles each time (10s → 20s → 40s → 80s → 160s)

---

## Scenario: Container Becomes Unhealthy and Stays Unhealthy

### Assumptions
- Container "my-app" becomes unhealthy at time 0:00
- Container remains unhealthy throughout (worst case)
- Health check always fails
- Restart attempts are successful but container immediately becomes unhealthy again

---

## Complete Timeline

| Clock Time | Event | Action Taken | Restart Count in Window | Backoff Delay | Cooldown Active? | Notes |
|------------|-------|--------------|------------------------|---------------|------------------|-------|
| **0:00** | Monitoring check #1 | Container detected unhealthy | 0 | - | No | First detection |
| **0:00** | Restart decision | ✅ RESTART APPROVED | 0→1 | 10s | - | No previous restarts |
| **0:00-0:10** | Backoff delay | Waiting... | 1 | 10s | - | Applying initial backoff |
| **0:10** | Restart executed | Container restarted | 1 | - | Starts | Cooldown timer starts |
| **0:10-1:10** | Cooldown period | - | 1 | - | Yes (60s) | Cannot restart during this time |
| **0:30** | Monitoring check #2 | Still unhealthy, in cooldown | 1 | - | Yes | ⏭️ Skip restart (cooldown active) |
| **1:00** | Monitoring check #3 | Still unhealthy, in cooldown | 1 | - | Yes | ⏭️ Skip restart (cooldown active) |
| **1:10** | Cooldown expires | - | 1 | - | No | Ready for next restart |
| **1:30** | Monitoring check #4 | Still unhealthy, cooldown expired | 1 | - | No | Check passes cooldown |
| **1:30** | Restart decision | ✅ RESTART APPROVED | 1→2 | 20s | - | Backoff doubled: 10s × 2 |
| **1:30-1:50** | Backoff delay | Waiting... | 2 | 20s | - | Exponential backoff |
| **1:50** | Restart executed | Container restarted | 2 | - | Starts | Cooldown timer starts |
| **1:50-2:50** | Cooldown period | - | 2 | - | Yes (60s) | Cannot restart |
| **2:00** | Monitoring check #5 | Still unhealthy, in cooldown | 2 | - | Yes | ⏭️ Skip restart |
| **2:30** | Monitoring check #6 | Still unhealthy, in cooldown | 2 | - | Yes | ⏭️ Skip restart |
| **2:50** | Cooldown expires | - | 2 | - | No | Ready for next restart |
| **3:00** | Monitoring check #7 | Still unhealthy, cooldown expired | 2 | - | No | Check passes cooldown |
| **3:00** | Restart decision | ✅ RESTART APPROVED | 2→3 | 40s | - | Backoff doubled: 20s × 2 |
| **3:00-3:40** | Backoff delay | Waiting... | 3 | 40s | - | Exponential backoff |
| **3:40** | Restart executed | Container restarted | 3 | - | Starts | Cooldown timer starts |
| **3:40-4:40** | Cooldown period | - | 3 | - | Yes (60s) | Cannot restart |
| **4:00** | Monitoring check #8 | Still unhealthy, in cooldown | 3 | - | Yes | ⏭️ Skip restart |
| **4:30** | Monitoring check #9 | Still unhealthy, in cooldown | 3 | - | Yes | ⏭️ Skip restart |
| **4:40** | Cooldown expires | - | 3 | - | No | Ready for next restart |
| **5:00** | Monitoring check #10 | Still unhealthy, cooldown expired | 3 | - | No | Check passes cooldown |
| **5:00** | Restart decision | ✅ RESTART APPROVED | 3→4 | 80s | - | Backoff doubled: 40s × 2 |
| **5:00-6:20** | Backoff delay | Waiting... | 4 | 80s | - | Exponential backoff |
| **5:30** | Monitoring check #11 | In backoff delay | 4 | - | - | ⏭️ Skip (backoff in progress) |
| **6:00** | Monitoring check #12 | In backoff delay | 4 | - | - | ⏭️ Skip (backoff in progress) |
| **6:20** | Restart executed | Container restarted | 4 | - | Starts | Cooldown timer starts |
| **6:20-7:20** | Cooldown period | - | 4 | - | Yes (60s) | Cannot restart |
| **6:30** | Monitoring check #13 | Still unhealthy, in cooldown | 4 | - | Yes | ⏭️ Skip restart |
| **7:00** | Monitoring check #14 | Still unhealthy, in cooldown | 4 | - | Yes | ⏭️ Skip restart |
| **7:20** | Cooldown expires | - | 4 | - | No | Ready for next restart |
| **7:30** | Monitoring check #15 | Still unhealthy, cooldown expired | 4 | - | No | Check passes cooldown |
| **7:30** | Restart decision | ✅ RESTART APPROVED | 4→5 | 160s | - | Backoff doubled: 80s × 2 |
| **7:30-10:10** | Backoff delay | Waiting... | 5 | 160s | - | Long exponential backoff! |
| **8:00** | Monitoring check #16 | In backoff delay | 5 | - | - | ⏭️ Skip (backoff in progress) |
| **8:30** | Monitoring check #17 | In backoff delay | 5 | - | - | ⏭️ Skip (backoff in progress) |
| **9:00** | Monitoring check #18 | In backoff delay | 5 | - | - | ⏭️ Skip (backoff in progress) |
| **9:30** | Monitoring check #19 | In backoff delay | 5 | - | - | ⏭️ Skip (backoff in progress) |
| **10:00** | Monitoring check #20 | In backoff delay | 5 | - | - | ⏭️ Skip (backoff in progress) |
| **10:00** | **Window check** | First restart (0:10) expires from window! | 4 | - | - | Sliding window cleanup |
| **10:10** | Restart executed | Container restarted (5th restart) | 5 | - | Starts | Cooldown timer starts |
| **10:10-11:10** | Cooldown period | - | 5 | - | Yes (60s) | Cannot restart |
| **10:30** | Monitoring check #21 | Still unhealthy, in cooldown | 5 | - | Yes | ⏭️ Skip restart |
| **11:00** | Monitoring check #22 | Still unhealthy, in cooldown | 5 | - | Yes | ⏭️ Skip restart |
| **11:10** | Cooldown expires | - | 5 | - | No | Ready for next restart |
| **11:30** | Monitoring check #23 | Still unhealthy, cooldown expired | 5 | - | No | Check passes cooldown |
| **11:30** | Restart decision | ❌ **QUARANTINED!** | 5 | - | - | Max restarts (5) reached in window |
| **11:30+** | Container quarantined | No more restarts | 5 | - | - | Requires manual intervention |

---

## Key Decision Points

### Why wasn't the container quarantined earlier?

The container accumulated 5 restarts over time:
1. **0:10** - 1st restart
2. **1:50** - 2nd restart (1:40 after 1st)
3. **3:40** - 3rd restart (1:50 after 2nd)
4. **6:20** - 4th restart (2:40 after 3rd)
5. **10:10** - 5th restart (3:50 after 4th)

At **10:10**, when the 5th restart occurred:
- All 5 restarts were still within the 600-second (10-minute) window
- The first restart at 0:10 was exactly 10:00 minutes old
- All 5 restarts counted in the sliding window

At **11:30**, when attempting a 6th restart:
- The system checks: "How many restarts in the last 600 seconds?"
- Restarts within window: 1:50, 3:40, 6:20, 10:10, (and potentially 11:30)
- Count = 5 restarts still in window
- **5 >= max_restarts (5)** → QUARANTINE!

---

## Restart Count in Window Over Time

| Time | Restart Timestamps in 600s Window | Count |
|------|-----------------------------------|-------|
| 0:10 | [0:10] | 1 |
| 1:50 | [0:10, 1:50] | 2 |
| 3:40 | [0:10, 1:50, 3:40] | 3 |
| 6:20 | [0:10, 1:50, 3:40, 6:20] | 4 |
| 10:00 | [0:10, 1:50, 3:40, 6:20] | 4 (0:10 about to expire) |
| 10:10 | [1:50, 3:40, 6:20, 10:10] | 4 (0:10 dropped, 10:10 added) |
| 11:30 | [1:50, 3:40, 6:20, 10:10] | 4 (1:50 still within 600s) |
| 11:50 | [3:40, 6:20, 10:10] | 3 (1:50 expired) |

**Wait, correction!** Let me recalculate at 11:30:
- Current time: 11:30 (690 seconds from start)
- Window: 690s - 600s = 90s cutoff
- Restarts after 90s: 1:50 (110s), 3:40 (220s), 6:20 (380s), 10:10 (610s)
- Count = 4 restarts in window

Actually, at 10:10 (610 seconds):
- Window starts at: 610s - 600s = 10s
- Restart at 0:10 (10s) is right at the edge
- Typically excluded if exactly at boundary

Let me recalculate more carefully...

---

## Corrected Analysis

At **10:10** (attempting 5th restart):
- Current time: 610 seconds from start
- Window looks back: 610s - 600s = 10s
- Restarts since 10s: 0:10 (10s), 1:50 (110s), 3:40 (220s), 6:20 (380s)
- Count in window = 4 previous restarts
- **4 < 5** → ✅ RESTART APPROVED (becomes 5th)

At **11:30** (attempting 6th restart):
- Current time: 690 seconds from start  
- Window looks back: 690s - 600s = 90s
- Restarts since 90s: 1:50 (110s), 3:40 (220s), 6:20 (380s), 10:10 (610s)
- Count in window = 4 previous restarts
- But wait... this should still allow restart?

**Issue found!** The code checks `restart_count >= config.restart.max_restarts` BEFORE recording the new restart.

So at 11:30:
- Previous restart count in window = 4
- Check: 4 >= 5? NO → Proceed with restart
- Record restart → count becomes 5
- Container restarts successfully

At **next check after 11:30** (let's say 13:30):
- Current time: 810 seconds
- Window: 810s - 600s = 210s
- Restarts since 210s: 3:40 (220s), 6:20 (380s), 10:10 (610s), 11:30 (690s) 
- But 3:40 is at 220s, outside the window (need > 210s)
- Actually: 6:20 (380s), 10:10 (610s), 11:30 (690s) = 3 restarts
- Hmm, wait...

Let me recalculate with proper timestamps...

---

## Corrected Timeline (Proper Window Calculation)

The sliding window counts restarts where: `(now - restart_time) <= window_seconds`

### At 11:30 (690s elapsed):
Looking back 600 seconds = from second 90 onward
- Restart at 0:10 = 10s ❌ (too old, 690-10=680s > 600s)
- Restart at 1:50 = 110s ✅ (690-110=580s < 600s)
- Restart at 3:40 = 220s ✅ (690-220=470s < 600s)
- Restart at 6:20 = 380s ✅ (690-380=310s < 600s)
- Restart at 10:10 = 610s ✅ (690-610=80s < 600s)

**Count = 4 restarts in window**
- Check: 4 >= 5? **NO** → ✅ RESTART APPROVED

### After restart at 11:30, next check at 13:30 (810s elapsed):
Looking back 600 seconds = from second 210 onward
- Restart at 1:50 = 110s ❌ (too old, 810-110=700s > 600s)
- Restart at 3:40 = 220s ✅ (810-220=590s < 600s)
- Restart at 6:20 = 380s ✅ (810-380=430s < 600s)
- Restart at 10:10 = 610s ✅ (810-610=200s < 600s)
- Restart at 11:30 = 690s ✅ (810-690=120s < 600s)

Wait, that's still 4... Let me recalculate 11:30:
- 11:30 in seconds = 11*60 + 30 = 690 seconds ✅

Actually, I need to include the CURRENT restart attempt!

---

## Final Corrected Timeline

### The Issue: When is the count checked?

Looking at the code:
```python
restart_count = config_manager.get_restart_count(
    container_id,
    config.restart.max_restarts_window_seconds
)

if restart_count >= config.restart.max_restarts:
    # Quarantine
```

The check happens **BEFORE** recording the new restart. So:
- If count = 4, and max = 5, then 4 >= 5 is FALSE → restart proceeds
- After restart, count becomes 5
- Next time: count = 5, and 5 >= 5 is TRUE → QUARANTINE!

### So the container will be quarantined on the 6th restart attempt:

| Restart # | Time | Count Before | Check | Result |
|-----------|------|--------------|-------|--------|
| 1 | 0:10 | 0 | 0 >= 5? No | ✅ Restart |
| 2 | 1:50 | 1 | 1 >= 5? No | ✅ Restart |
| 3 | 3:40 | 2 | 2 >= 5? No | ✅ Restart |
| 4 | 6:20 | 3 | 3 >= 5? No | ✅ Restart |
| 5 | 10:10 | 4 | 4 >= 5? No | ✅ Restart |
| 6 | ~13:30 | 5 | 5 >= 5? YES | ❌ **QUARANTINED** |

### When would the 6th attempt occur?

After 5th restart at 10:10:
- Cooldown: 60s → expires at 11:10
- Next backoff: 160s × 2 = 320s (5 minutes 20 seconds!)
- Next monitoring check after cooldown: 11:30
- Backoff delay: 320s
- Restart would be at: 11:30 + 320s = 11:30 + 5:20 = **16:50**

But container would still be in backoff during checks at:
- 11:30 (monitoring check, starts backoff)
- 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

At **16:50**, restart would execute, but FIRST it checks count:
- Restarts in window (looking back 600s from 16:50 = 1010s elapsed):
  - Need restarts after second 410
  - 6:20 = 380s ❌ (1010-380=630s > 600s)
  - 10:10 = 610s ✅ (1010-610=400s < 600s)
  - (hypothetical 11:30 would be here if it happened)
  
Hmm, restarts are expiring from the window...

---

## Realistic Outcome

Given the exponential backoff and 10-minute window, here's what actually happens:

**With your settings, the container will likely NEVER be quarantined** because:
1. Backoff delays grow exponentially: 10s, 20s, 40s, 80s, 160s, 320s...
2. The 320s (5min 20s) backoff means restarts are spread out
3. By the time the 6th restart would occur, early restarts have expired from the 600s window

### The container reaches steady-state retry loop:
- Restarts every ~7-8 minutes (cooldown 60s + backoff 320s + monitoring 30s)
- 600-second window only catches 1-2 recent restarts
- Never hits the max_restarts threshold
- **Continues retrying indefinitely**

---

## To Actually Quarantine with These Settings

You would need the container to restart 5 times within 600 seconds. Given:
- Minimum time between restarts: 60s (cooldown) + 10-160s (backoff)

The fastest possible 5 restarts:
1. 0:10 (10s backoff)
2. 1:50 (60s cooldown + 20s backoff + 30s detection)
3. 3:40 (60s cooldown + 40s backoff + 30s detection)
4. 6:20 (60s cooldown + 80s backoff + 30s detection)
5. 10:10 (60s cooldown + 160s backoff + 30s detection)

Total time: ~10 minutes = 600 seconds

**The container reaches exactly 5 restarts right at the window limit!**

6th attempt would be at ~16:50 (10:10 + 60s + 320s + monitoring)
- By then, restart #1 at 0:10 has expired
- Count in window = 4
- **6th restart proceeds!**

### Conclusion

**Your configuration will NOT quarantine the container** because exponential backoff spreads restarts beyond the 600-second window. The container will retry indefinitely with progressively longer delays.

---

## Recommendations

To ensure quarantine with exponential backoff:

### Option 1: Increase the window
```json
"max_restarts_window_seconds": 1200  // 20 minutes
```

### Option 2: Reduce max restarts
```json
"max_restarts": 3  // Quarantine faster
```

### Option 3: Cap the backoff multiplier
```json
"backoff": {
  "enabled": true,
  "initial_seconds": 10,
  "multiplier": 1.5,  // Slower growth
  "max_seconds": 120   // Cap at 2 minutes (requires code change)
}
```

### Option 4: Disable backoff for faster quarantine
```json
"backoff": { "enabled": false }
```

With backoff disabled and your settings:
- Restarts every ~90s (60s cooldown + 30s monitoring)
- 5 restarts in ~450 seconds
- **Quarantine occurs around 7-8 minutes** ✅

---

## Validation Protection Added ✅

The frontend configuration validation now **automatically detects** this infinite retry loop scenario!

When you try to save a configuration with exponential backoff that spreads restarts beyond the window, you'll see:

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

This validation prevents accidental misconfiguration that would result in containers retrying indefinitely.

### See Also

- **[EXPONENTIAL_BACKOFF_VALIDATION.md](./EXPONENTIAL_BACKOFF_VALIDATION.md)** - Detailed explanation of the validation algorithm
- **[TIMING_VALIDATION_TEST_RESULTS.md](./TIMING_VALIDATION_TEST_RESULTS.md)** - Test cases for validation logic


