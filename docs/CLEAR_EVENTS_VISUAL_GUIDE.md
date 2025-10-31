# Clear Events Button - Visual Guide

## Button Location
The "Clear All" button is located in the Events page header, next to the Refresh button.

```
╔══════════════════════════════════════════════════════════════╗
║  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
╠════════════════════════════════════════════��═════════════════╣
║                                                              ║
║  [Events displayed here]                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## UI States

### State 1: No Events (Button Disabled)
```
╔══════════════════════════════════════════════════════════════╗
���  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
║                                              ^^^^^^^^          ║
║                                              (grayed out)     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║              No events recorded yet                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### State 2: With Events (Button Enabled)
```
╔══════════════════════════════════════════════════════════════╗
║  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
║                                              ^^^^^^^^          ║
║                                              (red/active)     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ 🔄 my-web-server                    restart | success│   ║
║  │ Oct 31, 2024, 2:30:15 PM                             │   ║
║  │ Message: Container restarted successfully            │   ║
║  │ Container ID: c9963b4cdaae                           │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ 🔒 database                      quarantine | warning│   ║
║  │ Oct 31, 2024, 2:28:45 PM                             │   ║
║  │ Message: Container quarantined: exceeded 3 restarts  │   ║
║  │ Container ID: abc123def456                           │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### State 3: Confirmation Modal
```
╔══════════════════════════════════════════════════════════════╗
║  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║     ┌────────────────────────────────────────────────────┐  ║
║     │  ⚠️  Confirm Clear Events                      [X] │  ║
║     ├────────────────────────────────────────────────────┤  ║
║     │                                                    │  ║
║     │  Are you sure you want to clear all events?       │  ║
║     │  This action cannot be undone.                    │  ║
║     │                                                    │  ║
║     │  ℹ️ 25 events will be permanently deleted.        │  ║
║     │                                                    │  ║
║     ├────────────────────────────────────────────────────┤  ║
║     │                 [Cancel]  [Clear All Events]      │  ║
║     └────────────────────────────────────────────────────┘  ║
║                                                              ║
║  [Events shown but with modal overlay/dimmed]               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### State 4: Success (After Clearing)
```
╔══════════════════════════════════════════════════════════════╗
║  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
║                                              ^^^^^^^^          ║
║                                              (grayed out)     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ ✅ All events cleared successfully!              [X] │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║              No events recorded yet                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
                     ↑
              (auto-dismisses after 3 seconds)
```

### State 5: Error (If API Fails)
```
╔══════════════════════════════════════════════════════════════╗
║  📅 Event Log              [🔄 Refresh]  [🗑️ Clear All]      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ ❌ Failed to clear events. Please try again.    [X] │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  [Events remain unchanged]                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
                     ↑
              (auto-dismisses after 5 seconds)
```

## Button Styling Details

### Clear All Button
```
┌─────────────────┐
│ 🗑️  Clear All  │  <- Red background (danger)
└─────────────────┘
     ↑       ↑
   Icon    Text
```

**Properties:**
- Background: Red (`btn-danger`)
- Size: Small (`btn-sm`)
- Icon: Bootstrap trash icon (`bi-trash`)
- Text: "Clear All"
- Margin: 8px left spacing from Refresh button

### Disabled State
```
┌─────────────────┐
│ 🗑️  Clear All  │  <- Gray background (disabled)
└─────────────────┘
   Not clickable
```

## Alert Styling

### Success Alert
```
┌────────────────────────────────────────────────────┐
│ ✅ All events cleared successfully!            [X] │
└────────────────────────────────────────────────────┘
 ↑                                               ↑
Green background                          Close button
```

### Error Alert
```
┌────────────────────────────────────────────────────┐
│ ❌ Failed to clear events. Please try again.  [X] │
└────────────────────────────────────────────────────┘
 ↑                                               ↑
Red background                            Close button
```

## Interaction Flow Diagram

```
┌─────────────┐
│   Start     │
│ (View Page) │
└──────┬──────┘
       │
       ▼
┌─────────────┐      No Events      ┌──────────────┐
│   Events    ├────────────────────►│ Button       │
│   Exist?    │                     │ DISABLED     │
└──────┬──────┘                     └──────────────┘
       │ Yes
       ▼
┌─────────────┐
│   Button    │
│   ENABLED   │
└──────┬──────┘
       │ Click
       ▼
┌─────────────┐
│   Show      │
│   Modal     │
│ (Overlay)   │
└──────┬──────┘
       │
       ├──────► Cancel/Close ──┐
       │                       │
       ▼ Confirm               │
┌─────────────┐                │
│ Close Modal │                │
│  API Call   │                │
│   DELETE    │                │
└──────┬──────┘                │
       │                       │
    Success                    │
       │                       │
       ▼                       │
┌─────────────┐                │
│   Clear UI  │                │
│ Show Success│                │
└──────┬──────┘                │
       │                       │
       │◄──────────────────────┘
       │
       ▼
┌─────────────┐
│  Auto-      │
│  Dismiss    │
│  (3 sec)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Button     │
│  DISABLED   │
└─────────────┘
```

## Code Snippet - Button Component

```jsx
<Button 
  variant="danger"              // Red color
  size="sm"                     // Small size
  onClick={handleClearEvents}   // Handler function
  disabled={events.length === 0} // Disabled when no events
>
  <i className="bi bi-trash me-1"></i>  {/* Icon */}
  Clear All                              {/* Text */}
</Button>
```

## Mobile Responsive Design

### Desktop (Wide Screen)
```
┌────────────────────────────────────────┐
│ Event Log   [Refresh] [Clear All]      │
└────────────────────────────────────────┘
```

### Mobile (Narrow Screen)
```
┌──────────────────────┐
│ Event Log            │
│ [Refresh]            │
│ [Clear All]          │
└──────────────────────┘
```
(Buttons stack vertically on small screens)

## Color Palette

- **Button (Active)**: `#dc3545` (Bootstrap danger red)
- **Button (Disabled)**: `#6c757d` (Bootstrap secondary gray)
- **Success Alert**: `#d1e7dd` (Light green background)
- **Error Alert**: `#f8d7da` (Light red background)
- **Icon Color**: Matches button text color

## Usage Tips

1. **Regular Cleanup**: Use this to clear old events periodically
2. **Testing**: Clear events before starting new tests
3. **Privacy**: Remove sensitive event data when needed
4. **Performance**: Keep event log from growing too large

## Keyboard Shortcuts (Future Enhancement)
- `Ctrl + Shift + Delete`: Clear all events
- `Esc`: Close alert message
- `Enter`: Confirm in dialog

---

**Note**: This visual guide shows the UI design. The actual implementation uses React Bootstrap components which provide consistent styling across all browsers and devices.

