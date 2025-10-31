# Clear Events Feature

## Overview
Added a new feature to clear all event logs with a single API call.

## Implementation

### Backend Changes

#### 1. Config Manager (`app/config/config_manager.py`)
Added new method `clear_events()`:
```python
def clear_events(self) -> None:
    """Clear all events from log (thread-safe)"""
    with self._lock:
        self._event_log.clear()
        self._save_events()
        logger.info("All events cleared")
```

**Features:**
- Thread-safe using lock
- Clears in-memory event log
- Persists changes to disk (events.json)
- Logs the action

#### 2. API Endpoint (`app/api/api.py`)
Added new DELETE endpoint:
```python
@app.delete("/api/events")
async def clear_events():
    """Clear all events from the log"""
    try:
        config_manager.clear_events()
        return {"status": "success", "message": "All events cleared"}
    except Exception as e:
        logger.error(f"Error clearing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Usage

### API Call
```bash
# Clear all events
curl -X DELETE http://localhost:3131/api/events
```

**Response:**
```json
{
  "status": "success",
  "message": "All events cleared"
}
```

### From Frontend
```javascript
import api from './services/api';

// Clear all events
await api.delete('/events');
```

## Benefits
1. **Cleanup**: Remove old/irrelevant events
2. **Testing**: Clear logs between test runs
3. **Maintenance**: Keep event storage manageable
4. **Privacy**: Remove historical data when needed

## Technical Details
- **Method**: DELETE
- **Endpoint**: `/api/events`
- **Thread-Safe**: Yes (uses threading lock)
- **Persistent**: Changes are saved to `/data/events.json`
- **Error Handling**: Returns 500 status on error with details

## Testing
1. **Add some events** (trigger auto-heal actions)
2. **View events**: `GET /api/events`
3. **Clear events**: `DELETE /api/events`
4. **Verify**: `GET /api/events` should return empty array

## Integration with UI
To add a "Clear All Events" button in the frontend:

```javascript
const handleClearEvents = async () => {
  try {
    await api.delete('/events');
    // Refresh events list
    fetchEvents();
    showAlert('success', 'All events cleared');
  } catch (error) {
    showAlert('danger', 'Failed to clear events');
  }
};
```

## Related Files
- `app/config/config_manager.py` - Backend logic
- `app/api/api.py` - API endpoint
- `data/events.json` - Event storage

## Status
✅ **Complete** - Feature fully implemented and tested

