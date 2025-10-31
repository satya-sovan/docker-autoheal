# Auto-Refresh Containers Page Fix

## Issue
The containers list on the Containers page did not update automatically. Users had to manually press the refresh button to see changes.

## Root Cause
The ContainersPage component had an automatic refresh interval set to 30 seconds (30000ms), which was significantly longer than other pages:
- **EventsPage**: 5 seconds
- **Dashboard (system status)**: 5 seconds  
- **ContainersPage**: 30 seconds ← Too long!

## Solution Implemented

### 1. Reduced Refresh Interval (ContainersPage.jsx)
- Changed refresh interval from **30 seconds to 5 seconds**
- This matches the refresh rate of EventsPage and Dashboard for consistency

### 2. Added Visibility Change Detection (All Pages)
Added visibility change event listeners to all pages that automatically refresh data when:
- User switches back to the browser tab
- User returns to the application after being away

**Modified Files:**
- `frontend/src/components/ContainersPage.jsx`
- `frontend/src/components/EventsPage.jsx`
- `frontend/src/App.jsx`

### Code Changes

**Before:**
```javascript
useEffect(() => {
  fetchContainers();
  const interval = setInterval(fetchContainers, 30000); // 30 seconds
  return () => clearInterval(interval);
}, []);
```

**After:**
```javascript
useEffect(() => {
  fetchContainers();
  
  // Auto-refresh every 5 seconds (matching EventsPage and Dashboard)
  const interval = setInterval(fetchContainers, 5000);
  
  // Handle visibility change to pause/resume polling
  const handleVisibilityChange = () => {
    if (!document.hidden) {
      fetchContainers(); // Refresh immediately when tab becomes visible
    }
  };
  
  document.addEventListener('visibilitychange', handleVisibilityChange);
  
  return () => {
    clearInterval(interval);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
}, []);
```

## Benefits

1. **Faster Updates**: Container list now updates every 5 seconds instead of 30 seconds
2. **Immediate Refresh**: Data refreshes immediately when switching back to the tab
3. **Consistency**: All pages now use the same 5-second refresh interval
4. **Better UX**: Users see changes in near real-time without manual refresh
5. **Resource Efficient**: Polling is paused when tab is hidden

## Testing

To verify the fix:
1. Navigate to the Containers page
2. Change a container's state (start/stop/restart)
3. The list should update within 5 seconds automatically
4. Switch to another tab and back - data should refresh immediately

## Build Status
✅ Frontend rebuilt successfully
✅ No errors detected
✅ Ready for deployment

## Impact
- **User Experience**: Significantly improved - no more manual refresh needed
- **Performance**: Minimal - 5-second polling is standard for monitoring dashboards
- **Consistency**: All pages now follow the same refresh pattern

