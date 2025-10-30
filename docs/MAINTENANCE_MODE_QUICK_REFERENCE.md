# Maintenance Mode - Quick Reference

## What is Maintenance Mode?

Maintenance mode temporarily pauses all automatic container restarts while keeping the dashboard active. This allows you to:
- Perform system maintenance safely
- Manually manage containers without auto-healing interference
- Debug container issues without automatic restarts
- Update configurations without triggering healing actions

## How to Use

### Entering Maintenance Mode

1. Navigate to the dashboard (http://localhost:8080)
2. Click the **"Enter Maintenance Mode"** button in the dashboard header
3. A modal will appear showing:
   - Warning that auto-healing is suspended
   - Live timer showing elapsed time
   - "Exit Maintenance Mode" button

### While in Maintenance Mode

- ⏸️ **Auto-healing is paused** - No automatic container restarts
- 👁️ **Dashboard still visible** - Background content is grayed out
- ⏱️ **Timer is running** - Shows how long you've been in maintenance
- 🔒 **State persists** - Survives page refresh and browser restart
- 🔧 **Manual operations still work** - API calls still function

### Exiting Maintenance Mode

**Option 1:** Click "Exit Maintenance Mode" button in the modal
**Option 2:** Click "Exit Maintenance" button in dashboard header (if visible)

Once exited:
- ✅ Auto-healing resumes immediately
- ✅ Dashboard becomes interactive again
- ✅ Timer resets
- ✅ Normal operations continue

## Visual Indicators

### When Active
- 🟡 Modal overlay with warning icon
- ⏱️ Live timer (HH:MM:SS format)
- 🔒 Grayed out background (50% opacity)
- 🚫 Non-interactive UI behind modal

### Button States
- **Inactive**: Yellow "Enter Maintenance Mode" button with tools icon
- **Active**: Green "Exit Maintenance" button with play icon

## State Persistence

Maintenance mode state is stored on the backend and persists through:
- ✅ Page refreshes
- ✅ Browser close/reopen
- ✅ Tab switching
- ✅ Network reconnections

## Important Notes

⚠️ **Auto-healing is completely paused** - No containers will be restarted automatically

⚠️ **Manual restarts still work** - You can still restart containers via API or manually

⚠️ **Monitoring continues** - The system still monitors containers but doesn't take action

⚠️ **Remember to exit** - Auto-healing won't resume until you explicitly exit maintenance mode

## API Usage

If you want to control maintenance mode programmatically:

### Enable Maintenance Mode
```bash
curl -X POST http://localhost:8080/api/maintenance/enable
```

### Disable Maintenance Mode
```bash
curl -X POST http://localhost:8080/api/maintenance/disable
```

### Check Status
```bash
curl http://localhost:8080/api/maintenance/status
```

## Use Cases

### System Maintenance
Enter maintenance mode before performing system updates or configuration changes to prevent auto-healing from interfering.

### Debugging
When investigating container issues, maintenance mode prevents automatic restarts that might hide problems.

### Manual Container Management
If you need to manually stop/start/restart containers, maintenance mode ensures auto-heal doesn't conflict.

### Configuration Testing
Test new configurations without auto-healing triggering during the testing period.

## Troubleshooting

**Q: I refreshed the page and the modal is gone, but auto-healing isn't working**
A: Check if maintenance mode is still active. The modal should reappear automatically. If not, refresh again.

**Q: I closed the browser - is maintenance mode still active?**
A: Yes! Maintenance mode persists on the backend. When you reopen the dashboard, the modal will reappear.

**Q: How do I know if maintenance mode is active?**
A: Look for the modal overlay or check the dashboard header button. The system status also shows maintenance mode state.

**Q: Can I use the dashboard while in maintenance mode?**
A: The background UI is grayed out and non-interactive, but you can still see the dashboard through it. Click "Exit Maintenance Mode" to interact with the dashboard again.

**Q: What happens to containers that fail during maintenance mode?**
A: They will remain in their failed state. Auto-healing will not attempt to restart them until you exit maintenance mode.

