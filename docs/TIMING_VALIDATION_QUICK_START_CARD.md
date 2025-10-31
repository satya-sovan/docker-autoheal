# ⚡ Timing Validation - Quick Start Card

## 🎯 What It Does
Prevents you from saving invalid timing configurations that would cause Monitor Settings and Restart Policy to conflict.

## 🔍 When It Activates
- When clicking **"Save Monitor Settings"**
- When clicking **"Save Restart Policy"**

## ✅ What Gets Validated

### Critical Checks (Block Save)
- ❌ **Window Too Small for Restarts**: Restart window must fit all restart attempts with cooldown
- ❌ **Window Too Small for Monitoring**: Restart window must fit all monitoring cycles

### Warning Checks (Suggest Improvements)
- ⚠️ **Too Fast**: Very short intervals (<5s) hurt performance
- ⚠️ **Too Short**: Very short windows (<60s) cause premature quarantine
- ⚠️ **Too Slow**: Very long intervals (>300s) may miss issues

## 🎬 What Happens

### ✅ Valid Configuration
```
User clicks Save → Validation passes → Settings saved → Success message
```

### ❌ Invalid Configuration
```
User clicks Save → Validation fails → Modal appears → User adjusts → Try again
```

## 📊 The Golden Formula

```
Max Restarts Window ≥ (Max Restarts × Cooldown)
AND
Max Restarts Window ≥ (Max Restarts × Monitoring Interval)
```

In other words: **The window must be large enough to accommodate BOTH all restart attempts AND all monitoring cycles.**

## 💡 Quick Fix Guide

### Problem: "Window too small for restarts"
**3 Solutions:**
1. Increase "Max Restarts Window" (recommended)
2. Reduce "Max Restarts"
3. Reduce "Cooldown"

### Problem: "Window too small for monitoring"
**3 Solutions:**
1. Increase "Max Restarts Window" (recommended)
2. Reduce "Max Restarts"
3. Reduce "Monitoring Interval"

### Problem: "Very short monitoring interval"
**Solution:** Increase to at least 5 seconds

### Problem: "Very long monitoring interval"
**Solution:** Reduce to 300 seconds or less

## 🏆 Recommended Presets

### Balanced (Start Here)
```yaml
Monitoring Interval: 10s
Cooldown: 30s
Max Restarts: 3
Restart Window: 120s
```

### Fast Recovery
```yaml
Monitoring Interval: 5s
Cooldown: 15s
Max Restarts: 5
Restart Window: 120s
```

### Low Resource
```yaml
Monitoring Interval: 30s
Cooldown: 60s
Max Restarts: 3
Restart Window: 300s
```

## 🎨 Modal Sections Explained

| Color | Section | What It Shows |
|-------|---------|---------------|
| 🔴 Red | Issues Found | What's wrong |
| 🔵 Blue | Recommendations | How to fix |
| ⚪ Gray | Current Config | Your values |
| 🟢 Green | How It Works | Education |

## 📱 Modal Actions

- **Close Button (X)**: Dismiss and adjust settings
- **ESC Key**: Quick close
- **Click Outside**: Also closes modal

## 🧪 Test It

1. Set: Interval=10s, Cooldown=30s, Restarts=5, Window=60s
2. Click "Save Restart Policy"
3. Modal appears with error
4. Change Window to 150s
5. Click "Save Restart Policy"
6. Success! ✅

## 📚 More Info

- **Full Guide**: `docs/TIMING_VALIDATION_FEATURE.md`
- **Quick Ref**: `docs/TIMING_VALIDATION_QUICK_REF.md`
- **Visual Guide**: `docs/TIMING_VALIDATION_VISUAL_GUIDE.md`
- **Implementation**: `docs/TIMING_VALIDATION_IMPLEMENTATION_SUMMARY.md`

## 💬 Key Takeaways

✅ **Can't Save Invalid Configs**: System blocks bad settings  
✅ **Multiple Solutions**: Not just one way to fix  
✅ **Specific Values**: Tells you exact numbers to use  
✅ **Educational**: Learn how settings interact  
✅ **User-Friendly**: Clear messages, helpful suggestions  

## 🎯 Remember

**The validation helps you, not frustrates you!**

It prevents configurations that would:
- Cause containers to be quarantined too quickly
- Miss restart opportunities
- Waste system resources
- Create timing conflicts

**Trust the validation - it's designed to keep your system running smoothly! 🚀**

