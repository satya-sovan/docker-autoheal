# Timing Validation - Quick Reference

## Quick Validation Rules

### ✅ Valid Configuration Formula
```
Max Restarts Window ≥ (Max Restarts × Cooldown)
AND
Max Restarts Window ≥ (Max Restarts × Monitor Interval)
```

## Common Error Messages & Solutions

### ❌ "Restart window is too small for restarts with cooldown"
**Problem:** Window can't fit all restart attempts based on cooldown  
**Fix:** Increase "Max Restarts Window" OR reduce "Max Restarts" OR reduce "Cooldown"

### ❌ "Restart window is too small for monitoring cycles"
**Problem:** Window can't fit all monitoring cycles  
**Fix:** Increase "Max Restarts Window" OR reduce "Max Restarts" OR reduce "Monitoring Interval"

### ⚠️ "Very short monitoring interval"
**Problem:** May cause high CPU usage  
**Fix:** Increase "Monitoring Interval" to at least 5 seconds

### ⚠️ "Short restart window"
**Problem:** May cause premature quarantine  
**Fix:** Increase "Max Restarts Window" to at least 60 seconds

### ⚠️ "Very long monitoring interval"
**Problem:** May be too slow to detect container issues  
**Fix:** Reduce "Monitoring Interval" to 300 seconds or less

## Quick Fix Cheat Sheet

| Your Goal | Recommended Settings |
|-----------|---------------------|
| **Fast Recovery** | Interval: 5s, Cooldown: 15s, Restarts: 5, Window: 120s |
| **Balanced** | Interval: 10s, Cooldown: 30s, Restarts: 3, Window: 120s |
| **Low Resource** | Interval: 30s, Cooldown: 60s, Restarts: 3, Window: 300s |
| **Aggressive** | Interval: 3s, Cooldown: 10s, Restarts: 10, Window: 180s |

## Settings Explained (One-Liner Each)

- **Monitoring Interval**: How often to check container health (lower = more responsive)
- **Cooldown**: Wait time between restart attempts (prevents rapid restart loops)
- **Max Restarts**: How many restart attempts before quarantine (higher = more chances)
- **Max Restarts Window**: Time period for counting restarts (must fit all attempts)

## Validation Trigger Points

- ✓ When clicking "Save Monitor Settings"
- ✓ When clicking "Save Restart Policy"

## What Happens on Validation Failure?

1. Save is blocked (settings not applied)
2. Modal popup appears with:
   - List of specific issues
   - Multiple solution suggestions
   - Current configuration values
   - Educational information

## Pro Tips

💡 **Start Conservative**: Use longer intervals and windows, then optimize down  
💡 **Test Changes**: Monitor system after adjusting settings  
💡 **Export Config**: Save working configurations before experimenting  
💡 **Read Suggestions**: The modal provides specific numbers, not just generic advice  

## Example: Valid Configuration

**Configuration:**
- Monitoring Interval: 30s
- Cooldown: 10s
- Max Restarts: 3
- Max Restarts Window: 600s

**Math Check:**
- Cooldown check: 600s ≥ (3 × 10s) = 600s ≥ 30s ✅
- Monitoring check: 600s ≥ (3 × 30s) = 600s ≥ 90s ✅

**Result:** Configuration is valid and will be accepted!

## Example: Fixing an Invalid Configuration

**Error:** "Restart window (60s) is too small for 5 restarts with 30s cooldown"

**Math:** 5 restarts × 30s = 150s needed, but window is only 60s

**Option 1:** Increase window to 150s (recommended)  
**Option 2:** Reduce restarts to 2 (60 ÷ 30 = 2)  
**Option 3:** Reduce cooldown to 12s (60 ÷ 5 = 12)

**Best Choice:** Usually Option 1 (increase window) provides most flexibility

## Testing Your Configuration

1. Set values in Configuration page
2. Click Save
3. If modal appears, read the suggestions
4. Adjust values based on recommendations
5. Try saving again
6. Success = Green alert at top of page!

## Need Help?

If validation blocks your save:
1. Read the "Recommended Solutions" in the modal
2. Check "Current Configuration" section
3. Apply one of the suggested values
4. Try saving again

The validation is designed to help, not frustrate - it prevents configurations that won't work properly in production!

