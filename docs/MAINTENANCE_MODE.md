# Maintenance Mode Feature

## Overview
Maintenance mode allows administrators to temporarily pause all auto-healing operations while keeping the monitoring dashboard active. This is useful during system maintenance, debugging, or when manual container management is required.

## Features

### Backend Implementation
- **State Management**: Maintenance mode state is stored in-memory in ConfigManager
- **Timestamp Tracking**: Records when maintenance mode was enabled
- **Auto-Healing Suspension**: Monitor continues running but skips all restart operations
- **Persistent State**: State survives page refreshes (tracked on backend)

### API Endpoints

#### Enable Maintenance Mode
```
POST /api/maintenance/enable
```
Response:
```json
{
  "status": "success",
  "message": "Maintenance mode enabled",
  "maintenance_mode": true,
  "maintenance_start_time": "2025-10-30T12:00:00"
}
```

#### Disable Maintenance Mode
```
POST /api/maintenance/disable
```
Response:
```json
{
  "status": "success",
  "message": "Maintenance mode disabled",
  "maintenance_mode": false
}
```

#### Get Maintenance Status
```
GET /api/maintenance/status
```
Response:
```json
{
  "maintenance_mode": true,
  "maintenance_start_time": "2025-10-30T12:00:00"
}
```

### UI Implementation

#### Dashboard Button
- Located in the dashboard header next to the title
- **Yellow "Enter Maintenance Mode" button** when inactive
- **Green "Exit Maintenance" button** when active
- One-click toggle functionality

#### Maintenance Modal
When maintenance mode is active:
- **Modal overlay** appears over the entire UI
- **Live timer** shows elapsed time in maintenance mode (HH:MM:SS format)
- **Warning icon** and clear messaging
- **Gray-out effect** on background content (50% opacity, pointer-events disabled)
- **"Exit Maintenance Mode" button** to dismiss and resume auto-healing

#### State Persistence
- Maintenance state survives page refreshes
- Modal automatically reappears if maintenance mode is active
- Timer resumes from the original start time
- Closing browser and reopening maintains state

### Monitor Integration
The monitoring engine checks maintenance mode before each container check:
```python
if config_manager.is_maintenance_mode():
    logger.debug("Maintenance mode is enabled, skipping container checks")
    return
```

## User Flow

### Entering Maintenance Mode
1. User clicks "Enter Maintenance Mode" button on dashboard
2. API call enables maintenance mode on backend
3. Modal appears with live timer
4. Background UI becomes grayed out and non-interactive
5. Auto-healing is paused

### During Maintenance Mode
- Timer counts up continuously
- Dashboard still visible (grayed out)
- Manual operations still available via API
- No automatic container restarts occur
- Monitor loop continues but skips healing actions

### Exiting Maintenance Mode
1. User clicks "Exit Maintenance Mode" button in modal
2. API call disables maintenance mode
3. Modal dismisses
4. Background UI becomes active again
5. Auto-healing resumes normal operation

## Technical Details

### Backend Changes
- `config.py`: Added maintenance mode state variables and methods
  - `enable_maintenance_mode()`
  - `disable_maintenance_mode()`
  - `is_maintenance_mode()`
  - `get_maintenance_start_time()`

- `api.py`: Added maintenance endpoints and updated SystemStatus model
  - Added `maintenance_mode` and `maintenance_start_time` to status response

- `monitor.py`: Added maintenance check in `_check_single_container()`
  - Skips all container checks when maintenance mode is active

### Frontend Changes
- `services/api.js`: Added maintenance mode API functions
- `components/MaintenanceModal.jsx`: New component for maintenance overlay
- `components/Dashboard.jsx`: Added maintenance toggle button
- `App.jsx`: Integrated maintenance state and modal display
- `styles/App.css`: Added maintenance mode styling

## Benefits
1. **Safe Maintenance**: Prevents auto-healing during manual interventions
2. **Time Tracking**: Know how long system has been in maintenance
3. **State Persistence**: Survives page refreshes and browser restarts
4. **Clear Visual Feedback**: Obvious indication of maintenance status
5. **Easy Toggle**: One-click activation and deactivation
6. **Non-Destructive**: Doesn't stop monitoring, only healing actions

## Testing
1. Start the application: `docker-compose up --build`
2. Access UI at http://localhost:8080
3. Click "Enter Maintenance Mode" button
4. Verify modal appears with timer
5. Verify background is grayed out
6. Refresh page - verify modal persists
7. Close browser and reopen - verify state maintained
8. Click "Exit Maintenance Mode"
9. Verify auto-healing resumes

## Future Enhancements
- Schedule maintenance windows
- Maintenance mode history/audit log
- Email notifications when entering/exiting maintenance
- API-based maintenance mode scheduling
- Maintenance mode reason/notes field

