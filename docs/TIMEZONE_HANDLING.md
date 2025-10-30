# Backend Timezone Handling

## Overview

The Docker Auto-Heal backend now uses **UTC timezone-aware datetimes** consistently across the entire application.

## Timezone Standard

**All timestamps in the backend use UTC (Coordinated Universal Time)**

- ✅ Timezone-aware: `datetime.now(timezone.utc)`
- ❌ Avoided: `datetime.now()` (local/naive datetime)

## Why UTC?

1. **Consistency**: All servers use the same reference time regardless of their physical location
2. **No DST Issues**: UTC doesn't have daylight saving time changes
3. **ISO 8601 Compliance**: When serialized with `.isoformat()`, includes timezone info (e.g., `2025-10-30T10:30:00+00:00`)
4. **Frontend Compatibility**: JavaScript automatically converts UTC timestamps to local time

## Files Updated

### config.py
- `enable_maintenance_mode()`: Uses `datetime.now(timezone.utc)` for maintenance start time
- `record_restart()`: Records restart timestamps in UTC
- `get_restart_count()`: Calculates time windows using UTC

### monitor.py
- `_attempt_restart()`: Records restart times and events in UTC
- Cooldown calculations use UTC timestamps
- Quarantine events use UTC timestamps

### api.py
- Health check endpoint returns UTC timestamp
- Config export filenames use UTC timestamp

### demo.py
- Config backup filenames use UTC timestamp

## API Response Format

All datetime fields in API responses are ISO 8601 formatted with timezone info:

```json
{
  "maintenance_start_time": "2025-10-30T10:30:00+00:00",
  "timestamp": "2025-10-30T10:30:00+00:00"
}
```

## Frontend Handling

The frontend automatically handles timezone conversion:

```javascript
// Backend sends: "2025-10-30T10:30:00+00:00" (UTC)
const start = new Date(startTime);
// JavaScript automatically converts to local timezone

// Time difference calculation works correctly
const now = new Date();
const diff = now - start; // Correct elapsed time
```

## Benefits

1. **Accurate Time Calculations**: No double conversion or timezone offset issues
2. **Global Compatibility**: Works correctly regardless of server or client location
3. **Maintenance Mode Timer**: Shows correct elapsed time across all timezones
4. **Event Timestamps**: All events are timestamped consistently
5. **Restart History**: Accurate tracking of restart windows

## Migration Notes

If you had the application running before this change with existing restart history:
- Old timestamps were timezone-naive (local time)
- New timestamps are timezone-aware (UTC)
- This is backward compatible - time calculations still work
- Consider clearing restart history after deployment: Clear through UI or restart the container

## Testing Timezone Handling

To verify timezone handling works correctly:

1. Enable maintenance mode
2. Check the elapsed time display in the browser
3. It should show the correct elapsed time regardless of your local timezone
4. Compare with server time to verify UTC is being used

## Example Scenario

**Server Location**: New York (EST, UTC-5)
**User Location**: Tokyo (JST, UTC+9)

1. User enables maintenance mode at 10:00 AM Tokyo time
2. Backend stores: `2025-10-30T01:00:00+00:00` (UTC)
3. Frontend receives this timestamp
4. JavaScript converts to Tokyo time: 10:00 AM
5. Timer shows correct elapsed time
6. Another user in London sees the same accurate timer

