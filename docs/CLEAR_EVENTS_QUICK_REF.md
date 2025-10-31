# Clear Events - Quick Reference

## API Endpoint
```
DELETE /api/events
```

## Response
```json
{
  "status": "success",
  "message": "All events cleared"
}
```

## Usage Examples

### cURL
```bash
curl -X DELETE http://localhost:3131/api/events
```

### JavaScript
```javascript
await fetch('/api/events', { method: 'DELETE' });
```

### Python
```python
requests.delete('http://localhost:3131/api/events')
```

## What It Does
- Clears all events from memory
- Saves empty event list to `/data/events.json`
- Thread-safe operation
- Logs the action

## Files Modified
- `app/config/config_manager.py` - Added `clear_events()` method
- `app/api/api.py` - Added DELETE endpoint

## Test
```bash
python app\tests\test_clear_events_api.py
```

## Status
✅ Complete and ready to use

