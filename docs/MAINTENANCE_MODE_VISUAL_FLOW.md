# Maintenance Mode - Visual Flow Diagram

## User Interface Flow

```
┌────────────────────────────────────────────────────────────┐
│                     DASHBOARD HEADER                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Dashboard                    [Enter Maintenance]   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
                            │
                            │ Click Button
                            ▼
┌────────────────────────────────────────────────────────────┐
│           MAINTENANCE MODE ACTIVATED                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Dashboard                    [Exit Maintenance] ✓   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ╔════════════════════════════════════════════════╗  │  │
│  │  ║   ⚠️  MAINTENANCE MODE ACTIVE                  ║  │  │
│  │  ║                                                 ║  │  │
│  │  ║   Auto-Healing Suspended                       ║  │  │
│  │  ║                                                 ║  │  │
│  │  ║   TIME IN MAINTENANCE                          ║  │  │
│  │  ║   ┌─────────────────────────┐                 ║  │  │
│  │  ║   │      00:05:42            │                 ║  │  │
│  │  ║   └─────────────────────────┘                 ║  │  │
│  │  ║                                                 ║  │  │
│  │  ║   [Exit Maintenance Mode]                      ║  │  │
│  │  ╚════════════════════════════════════════════════╝  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────┐ (50%     │
│  │  Dashboard Content (Grayed Out)             │  opacity) │
│  │  - Metrics                                   │           │
│  │  - Containers                                │           │
│  │  - Events                                    │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────┘
                            │
                            │ Click "Exit Maintenance Mode"
                            ▼
┌────────────────────────────────────────────────────────────┐
│                  NORMAL MODE RESTORED                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Dashboard                    [Enter Maintenance]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Dashboard Content (Active)                         │   │
│  │  - Metrics                                           │   │
│  │  - Containers                                        │   │
│  │  - Events                                            │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## State Diagram

```
                ┌─────────────────┐
                │  Normal Mode    │
                │  Auto-healing:  │
                │     ACTIVE      │
                └────────┬────────┘
                         │
            Click "Enter Maintenance Mode"
                         │
                         ▼
                ┌─────────────────┐
                │ Maintenance Mode│
                │  Auto-healing:  │
                │     PAUSED      │
                │                 │
                │ Timer: Running  │
                │ UI: Grayed Out  │
                │ Modal: Visible  │
                └────────┬────────┘
                         │
            Click "Exit Maintenance Mode"
                         │
                         ▼
                ┌─────────────────┐
                │  Normal Mode    │
                │  Auto-healing:  │
                │     RESUMED     │
                └─────────────────┘
```

## Backend State Flow

```
┌──────────────────────────────────────────────────┐
│         ConfigManager                             │
│  ┌────────────────────────────────────────────┐  │
│  │  _maintenance_mode: False                   │  │
│  │  _maintenance_start_time: None              │  │
│  └────────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────────┘
                 │
      POST /api/maintenance/enable
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│         ConfigManager                             │
│  ┌────────────────────────────────────────────┐  │
│  │  _maintenance_mode: True                    │  │
│  │  _maintenance_start_time: 2025-10-30T12:00 │  │
│  └────────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────────┘
                 │
                 ├──────────────────┐
                 │                  │
                 ▼                  ▼
    ┌─────────────────┐   ┌──────────────────┐
    │ Monitor Engine  │   │  API Response    │
    │                 │   │                  │
    │ Checks:         │   │  Returns:        │
    │ is_maintenance  │   │  maintenance:    │
    │    = True       │   │    true          │
    │                 │   │  start_time:     │
    │ Action:         │   │    timestamp     │
    │ Skip healing    │   │                  │
    └─────────────────┘   └──────────────────┘
                 │
      POST /api/maintenance/disable
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│         ConfigManager                             │
│  ┌────────────────────────────────────────────┐  │
│  │  _maintenance_mode: False                   │  │
│  │  _maintenance_start_time: None              │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Frontend State Management

```
┌─────────────────────────────────────────────────┐
│              App Component                       │
│  ┌───────────────────────────────────────────┐  │
│  │  State:                                    │  │
│  │  - systemStatus: null                      │  │
│  │  - showMaintenanceModal: false             │  │
│  └───────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
       useEffect → fetchSystemStatus()
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│       GET /api/status                            │
│  ┌───────────────────────────────────────────┐  │
│  │  Response:                                 │  │
│  │  {                                         │  │
│  │    maintenance_mode: true,                 │  │
│  │    maintenance_start_time: "...",          │  │
│  │    ...                                     │  │
│  │  }                                         │  │
│  └───────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              App Component                       │
│  ┌───────────────────────────────────────────┐  │
│  │  State:                                    │  │
│  │  - systemStatus: {..., maintenance: true}  │  │
│  │  - showMaintenanceModal: true              │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Render:                                   │  │
│  │  - Container (opacity: 0.5)                │  │
│  │  - MaintenanceModal (show: true)           │  │
│  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Timer Calculation Flow

```
┌─────────────────────────────────────────────────┐
│      MaintenanceModal Component                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Props:                                    │  │
│  │  - startTime: "2025-10-30T12:00:00"        │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  useEffect: setInterval every 1000ms             │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Calculate:                                │  │
│  │  1. Parse startTime → Date object          │  │
│  │  2. Get current time → Date object         │  │
│  │  3. Calculate diff in seconds              │  │
│  │  4. Convert to HH:MM:SS format             │  │
│  │  5. Update state → trigger re-render       │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Display:                                  │  │
│  │                                            │  │
│  │         ┌─────────────────┐               │  │
│  │         │   00:05:42       │               │  │
│  │         └─────────────────┘               │  │
│  │                                            │  │
│  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘

Updates every second:
00:00:00 → 00:00:01 → 00:00:02 → ... → 00:05:42
```

## Complete Request Flow

```
User Action: Click "Enter Maintenance Mode"
    │
    ▼
┌─────────────────────────────────────┐
│  Frontend: handleMaintenanceToggle()│
└───────────────┬─────────────────────┘
                │
                ▼
    POST /api/maintenance/enable
                │
                ▼
┌─────────────────────────────────────┐
│  Backend: API Endpoint               │
│  - config_manager.enable_maintenance│
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  ConfigManager                       │
│  - _maintenance_mode = True          │
│  - _maintenance_start_time = now()   │
└───────────────┬─────────────────────┘
                │
                ▼
    Response: { status: "success", ... }
                │
                ▼
┌─────────────────────────────────────┐
│  Frontend: Update State              │
│  - setShowMaintenanceModal(true)     │
│  - fetchSystemStatus()               │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  UI Updates                          │
│  - Modal appears                     │
│  - Timer starts                      │
│  - Background grays out              │
│  - Button changes to "Exit"          │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Monitor Loop                        │
│  - Checks is_maintenance_mode()      │
│  - Returns early (skips healing)     │
└─────────────────────────────────────┘
```

## Page Refresh Flow

```
Page Refresh (F5)
    │
    ▼
┌─────────────────────────────────────┐
│  Frontend: useEffect runs            │
│  - fetchSystemStatus()               │
└───────────────┬─────────────────────┘
                │
                ▼
    GET /api/status
                │
                ▼
┌─────────────────────────────────────┐
│  Backend: get_system_status()        │
│  - Returns maintenance_mode: true    │
│  - Returns maintenance_start_time    │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Frontend: State Updated             │
│  - systemStatus.maintenance_mode ✓   │
│  - setShowMaintenanceModal(true)     │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  UI Restores                         │
│  - Modal reappears                   │
│  - Timer resumes from start time     │
│  - Background grayed out again       │
└─────────────────────────────────────┘
```

## Component Hierarchy

```
App
├── Navigation (not affected by maintenance)
│
├── Container (grayed out during maintenance)
│   ├── Dashboard
│   │   └── Maintenance Toggle Button
│   │
│   └── Routes
│       ├── ContainersPage
│       ├── EventsPage
│       └── ConfigPage
│
└── MaintenanceModal (overlays everything)
    ├── Warning Icon
    ├── Live Timer
    └── Exit Button
```

