# Timing Validation Visual Guide

## What Users Will See

### Scenario 1: Restart Window Too Small

#### User Configuration:
```
Monitor Settings:
  ✓ Monitoring Interval: 10 seconds
  
Restart Policy:
  ✗ Cooldown: 30 seconds
  ✗ Max Restarts: 5
  ✗ Max Restarts Window: 60 seconds
```

#### Validation Modal Appears:

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ⚠️  Invalid Restart Policy Configuration                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  The restart policy settings conflict with your monitoring config:   ║
║                                                                       ║
║  🔴 Issues Found:                                                     ║
║  ❌ Restart window (60s) is too small for 5 restarts with 30s        ║
║     cooldown                                                          ║
║                                                                       ║
║  💡 Recommended Solutions:                                            ║
║  • Increase "Max Restarts Window" to at least 150 seconds            ║
║    (5 restarts × 30s cooldown)                                       ║
║  • OR reduce "Max Restarts" to 2 or less                             ║
║  • OR reduce "Cooldown" to 12 seconds or less                        ║
║                                                                       ║
║  ℹ️  Current Configuration:                                           ║
║  Monitoring Interval: 10 seconds                                     ║
║  Cooldown: 30 seconds                                                ║
║  Max Restarts: 5                                                     ║
║  Max Restarts Window: 60 seconds                                     ║
║                                                                       ║
║  ✅ How These Settings Work Together:                                 ║
║  • Monitoring Interval: How often the system checks container health ║
║  • Cooldown: Wait time between restart attempts                      ║
║  • Max Restarts: Maximum restart attempts before quarantine          ║
║  • Max Restarts Window: Time window for counting restarts            ║
║    (must fit all restart attempts)                                   ║
║                                                                       ║
║  Formula: Max Restarts Window ≥ (Max Restarts × Cooldown) +         ║
║           (Max Restarts × Monitoring Interval)                       ║
║                                                                       ║
║                              [Close and Adjust Settings]             ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Scenario 2: Monitoring Interval Too Long

#### User Configuration:
```
Monitor Settings:
  ✗ Monitoring Interval: 60 seconds
  
Restart Policy:
  ✓ Cooldown: 30 seconds
  ✓ Max Restarts: 3
  ✓ Max Restarts Window: 120 seconds
```

#### Validation Modal Appears:

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ⚠️  Invalid Monitor Settings Configuration                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  The monitoring interval conflicts with your restart policy:         ║
║                                                                       ║
║  🔴 Issues Found:                                                     ║
║  ⚠️  Monitoring interval (60s) is longer than cooldown (30s)         ║
║  ⚠️  Limited detection cycles: Only 2 monitoring checks in 120s      ║
║      window for 3 max restarts                                       ║
║                                                                       ║
║  💡 Recommended Solutions:                                            ║
║  • This means the monitor may miss restart opportunities during      ║
║    cooldown periods                                                  ║
║  • Recommended: Set "Monitoring Interval" to 15 seconds              ║
║    (half of cooldown) for optimal detection                          ║
║  • The monitor may not detect enough failures within the restart     ║
║    window                                                            ║
║  • Recommended: Reduce "Monitoring Interval" to 20 seconds           ║
║  • OR increase "Max Restarts Window" to at least 360 seconds         ║
║                                                                       ║
║  ℹ️  Current Configuration:                                           ║
║  Monitoring Interval: 60 seconds                                     ║
║  Cooldown: 30 seconds                                                ║
║  Max Restarts: 3                                                     ║
║  Max Restarts Window: 120 seconds                                    ║
║                                                                       ║
║                              [Close and Adjust Settings]             ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Scenario 3: Very Short Monitoring Interval

#### User Configuration:
```
Monitor Settings:
  ✗ Monitoring Interval: 2 seconds
  
Restart Policy:
  ✓ Cooldown: 15 seconds
  ✓ Max Restarts: 3
  ✓ Max Restarts Window: 60 seconds
```

#### Validation Modal Appears:

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ⚠️  Invalid Monitor Settings Configuration                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  The monitoring interval conflicts with your restart policy:         ║
║                                                                       ║
║  🔴 Issues Found:                                                     ║
║  ⚠️  Very short monitoring interval (2s) may cause high CPU usage    ║
║                                                                       ║
║  💡 Recommended Solutions:                                            ║
║  • Consider setting "Monitoring Interval" to at least 5 seconds      ║
║    for better performance                                            ║
║                                                                       ║
║  ℹ️  Current Configuration:                                           ║
║  Monitoring Interval: 2 seconds                                      ║
║  Cooldown: 15 seconds                                                ║
║  Max Restarts: 3                                                     ║
║  Max Restarts Window: 60 seconds                                     ║
║                                                                       ║
║                              [Close and Adjust Settings]             ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Scenario 4: Valid Configuration ✓

#### User Configuration:
```
Monitor Settings:
  ✓ Monitoring Interval: 10 seconds
  
Restart Policy:
  ✓ Cooldown: 30 seconds
  ✓ Max Restarts: 3
  ✓ Max Restarts Window: 120 seconds
```

#### Result:
```
╔═══════════════════════════════════════════════════════════════════════╗
║  ✅ Settings Saved Successfully!                                      ║
║  Monitor configuration updated                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

No modal appears - settings are saved immediately with success message!

## Timeline Visualization

### Valid Configuration Example:

```
Monitoring Interval: 10s | Cooldown: 30s | Max Restarts: 3 | Window: 120s

Time: 0s────────────────────────────────────────────────────────────────120s
      |                                                                    |
      |─ Check 1 ──┐                                                      |
      |     10s    ├── Restart 1 (30s cooldown)                          |
      |            └───────────────────────────────┐                      |
      |                                            |                      |
      |─ Check 2 ───────────────────────────────────┐                     |
      |     10s                                     ├── Restart 2         |
      |                                             └────────────┐        |
      |                                                          |        |
      |─ Check 3 ───────────────────────────────────────────────────┐    |
      |     10s                                                     ├─ R3 |
      |                                                             └────┐|
      |                                                                  ||
      └──────────────────────────────────────────────────────────────────┘
      
✅ All 3 restarts fit within 120s window
✅ Multiple monitoring checks available (12 total)
✅ Monitoring interval (10s) < Cooldown (30s)
```

### Invalid Configuration Example:

```
Monitoring Interval: 10s | Cooldown: 30s | Max Restarts: 5 | Window: 60s

Time: 0s────────────────────────────────────────60s
      |                                          |
      |─ Check 1 ──┐                            |
      |     10s    ├── Restart 1 (30s cooldown) |
      |            └───────────────────────┐     |
      |                                    |     |
      |─ Check 2 ──────────────────────────┴──┐  |
      |     10s                               ├─ Restart 2 starts...
      |                                       └────────────┐
      |                                                    |
      └────────────────────────────────────────────────────┼─ WINDOW END!
                                                           |
      ❌ Restarts 3, 4, 5 would occur outside 60s window!  |
      ❌ Need at least 150s for 5 restarts with 30s cooldown
```

## User Flow Diagram

```
┌─────────────────────────┐
│ User adjusts timing    │
│ settings in Config page│
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ User clicks Save button │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Validation runs         │
│ automatically           │
└───────────┬─────────────┘
            │
            v
     ┌──────┴──────┐
     │   Valid?    │
     └───���──┬──────┘
        No  │  Yes
      ┌─────┴─────┐
      │           │
      v           v
┌──────────┐  ┌──────────┐
│ Show     │  │ Save     │
│ Validation│  │ Settings │
│ Modal    │  │          │
└────┬─────┘  └────┬─────┘
     │             │
     v             v
┌──────────┐  ┌──────────┐
│ User     │  │ Show     │
│ adjusts  │  │ Success  │
│ values   │  │ Alert    │
└────┬─────┘  └──────────┘
     │
     │
     └────────────┐
                  │
                  v
           ┌──────────────┐
           │ Try saving   │
           │ again        │
           └──────────────┘
```

## Color Coding in Modal

- 🟡 **Modal Header**: Warning yellow/orange background
- 🔴 **Issues Section**: Red alert box with error messages
- 🔵 **Solutions Section**: Blue info alert with recommendations  
- ⚪ **Current Config**: Gray/light background with current values
- 🟢 **How It Works**: Green success alert with educational info

## Icon Legend

- ⚠️  Warning header icon
- ❌ Critical error that blocks save
- ⚠️  Warning that should be addressed
- 💡 Suggestion/recommendation
- ℹ️  Information
- ✅ Success/validation passed
- 🔴 Red alert section
- 🔵 Blue info section
- 🟢 Green success section

## Mobile Responsiveness

The modal is responsive and will:
- Use full width on mobile devices
- Stack sections vertically
- Maintain readability on small screens
- Center on desktop displays
- Be scrollable if content is long

## Accessibility Features

- ✓ Keyboard navigable (Esc to close)
- ✓ Close button clearly visible
- ✓ Clear heading structure
- ✓ Sufficient color contrast
- ✓ Icon + text labels
- ✓ Descriptive error messages
- ✓ Actionable suggestions

## Summary

The validation modal provides:
1. **Clear Problem Identification** - Tells you exactly what's wrong
2. **Multiple Solutions** - Gives you options to fix issues
3. **Specific Values** - Suggests exact numbers, not vague advice
4. **Education** - Helps you understand how settings interact
5. **Current Context** - Shows your current values for reference

This ensures users can't accidentally configure timing settings that won't work properly in production!

