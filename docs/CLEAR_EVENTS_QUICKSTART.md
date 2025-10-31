# Clear Events - Quick Start Guide

## For End Users

### How to Clear All Events

1. **Open Docker Auto-Heal UI**
   - Navigate to `http://localhost:3131`

2. **Go to Events Page**
   - Click "Events" in the navigation menu

3. **Clear Events**
   - Click the red **"Clear All"** button in the top-right corner
   - Confirm the action when prompted
   - ✅ Done! All events are cleared

### When to Use

- 🧹 **Regular Cleanup**: Clear old/irrelevant events
- 🧪 **Testing**: Start with a clean slate
- 📊 **Before Demo**: Show only relevant events
- 🔒 **Privacy**: Remove historical data

---

## For Developers

### API Endpoint
```bash
# Clear all events
curl -X DELETE http://localhost:3131/api/events

# Response
{"status": "success", "message": "All events cleared"}
```

### JavaScript
```javascript
import { clearEvents } from './services/api';

await clearEvents();
```

### Python
```python
import requests
requests.delete('http://localhost:3131/api/events')
```

---

## Quick Test

### Test the Feature
```bash
# 1. View events
curl http://localhost:3131/api/events

# 2. Clear events
curl -X DELETE http://localhost:3131/api/events

# 3. Verify (should return empty array)
curl http://localhost:3131/api/events
```

### Expected Result
```json
[]
```

---

## Troubleshooting

### Button is Disabled
- **Reason**: No events to clear
- **Solution**: Add some events first (restart containers)

### Error Message Appears
- **Reason**: API connection failed
- **Solution**: Check if the backend service is running

### Events Not Clearing
- **Reason**: Browser cache or stale data
- **Solution**: Hard refresh the page (Ctrl+F5)

---

## Features

✅ Confirmation dialog (prevents accidents)
✅ Success/error feedback
✅ Auto-dismiss alerts
✅ Thread-safe backend
✅ Persists to disk

---

## Files Involved

- **Backend**: `app/api/api.py`, `app/config/config_manager.py`
- **Frontend**: `frontend/src/components/EventsPage.jsx`
- **Data**: `/data/events.json`

---

## Need Help?

See detailed documentation:
- `docs/CLEAR_EVENTS_FULL_SUMMARY.md` - Complete guide
- `docs/CLEAR_EVENTS_VISUAL_GUIDE.md` - UI screenshots
- `docs/CLEAR_EVENTS_QUICK_REF.md` - API reference

---

**Status**: ✅ Ready to Use

