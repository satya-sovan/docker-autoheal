# Quick Fix Summary: Restart Count Display Issue

## Problem
Container restart counts were showing wrong numbers (usually 0) in the UI.

## Solution
Fixed the path to read Docker's `RestartCount` from the correct location:

**File:** `app/docker_client/docker_client_wrapper.py` (line 132)

**Before:**
```python
"restart_count": attrs.get("RestartCount", 0),  # ❌ Wrong - not at root level
```

**After:**
```python
"restart_count": attrs.get("State", {}).get("RestartCount", 0),  # ✅ Correct - inside State object
```

## Why This Fixes It

Docker stores container restart counts in the `State` object of the container attributes, not at the root level. The old code was looking in the wrong place and always getting 0 or None.

## How to Test

1. Restart your docker-autoheal application
2. Navigate to the Containers page in the UI
3. Check the "Restarts" column - it should now show correct values
4. Click on a container to view details - both `restart_count` and `recent_restart_count` should display properly

## What Gets Fixed

- ✅ Container table "Restarts" column shows correct Docker restart counts
- ✅ Container details modal displays accurate restart information
- ✅ Dashboard stats reflect proper restart tracking
- ✅ No more confusing "0" restart counts for containers that have actually restarted

---

**Date:** October 31, 2025  
**Impact:** UI display only - no behavioral changes to monitoring or healing logic  
**Breaking Changes:** None - this is a bug fix

