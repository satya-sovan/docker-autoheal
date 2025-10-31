# Overlapping Modal Fix - Test Guide

## Quick Verification Steps

Follow these steps to verify the overlapping modal issue is fixed:

---

## Test 1: Basic Validation Error ✅

**Setup:**
1. Open web UI: http://localhost:3131
2. Go to Configuration tab
3. Set the following:
   - Monitoring Interval: 30 seconds
   - Cooldown: 60 seconds
   - Max Restarts: 5
   - Max Restarts Window: 600 seconds
   - Backoff enabled: Yes
   - Initial backoff: 10 seconds
   - Multiplier: 2.0

**Test:**
1. Click "Update Restart Settings"
2. A modal should appear with validation warning

**Expected Result:**
- ✅ **EXACTLY ONE modal appears**
- ✅ Modal shows critical backoff warning
- ✅ No duplicate modals behind it
- ✅ Modal stays open (doesn't flicker)

**Pass/Fail:** ________

---

## Test 2: Rapid Button Clicks ✅

**Setup:**
Use the same configuration from Test 1

**Test:**
1. Click "Update Restart Settings" rapidly 5-10 times (fast clicks)
2. Observe modal behavior

**Expected Result:**
- ✅ **Only ONE modal appears** (no stacking)
- ✅ Modal doesn't flicker or reopen
- ✅ No console errors

**Pass/Fail:** ________

---

## Test 3: Close and Reopen ✅

**Setup:**
Use the same configuration from Test 1

**Test:**
1. Click "Update Restart Settings" - modal opens
2. Click "Close and Adjust Settings" button
3. Immediately click "Update Restart Settings" again

**Expected Result:**
- ✅ First modal opens correctly
- ✅ Modal closes completely when close button clicked
- ✅ Second modal opens correctly with same validation errors
- ✅ No stale data or duplicate modals

**Pass/Fail:** ________

---

## Test 4: Multiple Validation Errors ✅

**Setup:**
1. Set the following intentionally bad config:
   - Monitoring Interval: 30 seconds
   - Cooldown: 60 seconds
   - Max Restarts: 10
   - Max Restarts Window: 100 seconds (too small!)
   - Backoff enabled: Yes
   - Initial backoff: 10 seconds
   - Multiplier: 3.0 (very aggressive!)

**Test:**
1. Click "Update Restart Settings"
2. Modal should appear

**Expected Result:**
- ✅ **One modal with MULTIPLE errors listed**:
  - "Restart window too small for restarts with cooldown"
  - "Exponential backoff will prevent quarantine"
- ✅ All errors shown in same modal
- ✅ No duplicate modals

**Pass/Fail:** ________

---

## Test 5: ESC Key Close ✅

**Setup:**
Use configuration from Test 1

**Test:**
1. Click "Update Restart Settings" - modal opens
2. Press ESC key on keyboard

**Expected Result:**
- ✅ Modal closes when ESC pressed
- ✅ No errors in console
- ✅ Clean close (modal doesn't reappear)

**Pass/Fail:** ________

---

## Test 6: Try to Click Outside ⚠️

**Setup:**
Use configuration from Test 1

**Test:**
1. Click "Update Restart Settings" - modal opens
2. Click on the darkened background (outside the modal)

**Expected Result:**
- ✅ Modal **DOES NOT close** (backdrop is static)
- ✅ Must use close button or ESC to close
- ✅ This is intentional - user must acknowledge validation errors

**Pass/Fail:** ________

---

## Test 7: Monitor Settings Validation ✅

**Setup:**
1. Set these values:
   - Monitoring Interval: 600 seconds (very long!)
   - Keep other settings as before

**Test:**
1. Click "Update Monitor Settings"
2. Modal should appear with warning

**Expected Result:**
- ✅ One modal appears
- ✅ Warning about long monitoring interval (>300s)
- ✅ No duplicate modals

**Pass/Fail:** ________

---

## Test 8: Browser Console Check ✅

**Test:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Perform Test 1 (click Update Restart Settings)
4. Observe console output

**Expected Result:**
- ✅ No error messages
- ✅ No warnings about React rendering
- ✅ No "maximum update depth exceeded" errors
- ✅ Clean console (only info logs if any)

**Pass/Fail:** ________

---

## Known Behaviors (Not Bugs)

### React StrictMode Double Logs (Development Only)
In development mode, you might see some logs appear twice. This is **NORMAL** and expected with React StrictMode. Example:
```
Component rendering...
Component rendering...  // ← This is expected in dev mode
```

**What to check:** The modal itself should only appear **once**, even if logs appear twice.

### Static Backdrop
The modal will NOT close when clicking outside. This is **INTENTIONAL** to ensure users acknowledge validation errors. Use:
- Close button
- ESC key
- X button in header

---

## Visual Checklist

When modal is open, verify:

- ✅ Modal is centered on screen
- ✅ Background is darkened
- ✅ Only ONE modal visible (no stacking)
- ✅ Modal has warning header (yellow/orange background)
- ✅ Validation errors listed clearly
- ✅ Suggestions section shows recommended fixes
- ✅ Current configuration values shown at bottom
- ✅ "How These Settings Work Together" explanation visible
- ✅ Close button at bottom

---

## Troubleshooting

### If you still see overlapping modals:

1. **Clear browser cache**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   
2. **Check React is running in dev mode**
   - Look for "React StrictMode" in console
   - This is normal and shouldn't cause issues after fix

3. **Verify file was saved**
   - Check `ConfigPage.jsx` has the changes
   - Look for `closeValidationModal` function
   - Look for guards: `if (validationModal.show) return;`

4. **Restart development server**
   - Stop the dev server (Ctrl+C)
   - Run `npm run dev` again
   - Hard refresh browser

### If modal won't close:

1. **Try ESC key** - Should always work
2. **Try X button in header** - Should work
3. **Try Close button** - Should work
4. **Check console for errors** - Might indicate a different issue

---

## Success Criteria

All tests must pass with these results:

- ✅ Only ONE modal ever appears at a time
- ✅ Rapid clicks don't create duplicates
- ✅ Modal closes cleanly (no stale data)
- ✅ Modal reopens correctly
- ✅ Multiple errors show in same modal
- ✅ Static backdrop prevents accidental closure
- ✅ ESC key still works
- ✅ No console errors

---

## Test Results Summary

Fill in after testing:

| Test | Status | Notes |
|------|--------|-------|
| 1. Basic validation | ⬜ Pass ⬜ Fail | |
| 2. Rapid clicks | ⬜ Pass ⬜ Fail | |
| 3. Close and reopen | ⬜ Pass ⬜ Fail | |
| 4. Multiple errors | ⬜ Pass ⬜ Fail | |
| 5. ESC key | ⬜ Pass ⬜ Fail | |
| 6. Click outside | ⬜ Pass ⬜ Fail | |
| 7. Monitor settings | ⬜ Pass ⬜ Fail | |
| 8. Console check | ⬜ Pass ⬜ Fail | |

**Overall Result:** ⬜ ALL PASS ⬜ SOME FAILURES

---

## Report Issues

If any test fails:

1. Note which test failed
2. Describe what happened vs what was expected
3. Check browser console for errors
4. Take screenshot if possible
5. Check `OVERLAPPING_MODAL_FIX.md` for troubleshooting

---

**Test Date:** _______________  
**Tester:** _______________  
**Browser:** _______________  
**Environment:** ⬜ Development ⬜ Production

