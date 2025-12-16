# Changelog - Notification System

## [v1.3.0] - 2025-12-16

### Added - Auto-Unquarantine Feature 🔄

#### Overview
When a container is quarantined (exceeded max restarts), the system now continuously monitors it. If the container becomes healthy again (e.g., manual fix or automatic recovery), it is **automatically removed from quarantine**.

#### Features
- **Automatic Quarantine Removal**: Containers that auto-heal are automatically unquarantined
- **Health Verification**: The system checks:
  - Container is running
  - Docker native health check (if configured) reports "healthy"
  - Custom health checks pass (if configured)
- **Restart Counter Reset**: When auto-unquarantined, the restart counter is cleared
- **Event Logging**: Creates `auto_unquarantine` event in the event log
- **Notification Support**: Sends notification when container is auto-unquarantined
- **New Event Type**: `auto_unquarantine` added to default notification filters

#### Event Details
The `auto_unquarantine` event includes:
- Container name and stable ID
- Timestamp
- Status: "success"
- Message: "Container automatically removed from quarantine - auto-healed and now healthy"

#### How It Works
1. Container exceeds max restarts → Quarantined
2. Each health check cycle, quarantined containers are checked
3. If container is healthy (running + passes health checks):
   - Removed from quarantine
   - Restart count cleared
   - Backoff delay reset
   - Event logged
   - Notification sent (if enabled)
4. Container returns to normal monitoring

#### Testing
- Added `test_auto_unquarantine.py` with comprehensive unit tests
- Tests cover all health status scenarios
- Tests verify event creation and notification flow

---

## [v1.2.0] - 2025-11-29

### Added - Notification System 🔔

#### Features
- **Multi-Service Notification Support**: Send alerts to 7 different services
  - Generic Webhook (JSON POST)
  - Discord (with rich embeds)
  - Slack (with formatted blocks)
  - Telegram (via bot)
  - Ntfy (push notifications)
  - Gotify (self-hosted)
  - Pushover (cross-platform)

- **Event-Based Notifications**: Get alerts for:
  - Container restarts
  - Container quarantines
  - Health check failures
  - Auto-monitoring events
  - Container unquarantines

- **Smart Event Filtering**: Choose which events trigger notifications
  - Configurable per-event-type
  - Reduces notification noise
  - Empty filter = notify on all events

- **Web UI Management**: 
  - New "Notifications" page with intuitive interface
  - Toggle notification system on/off
  - Interactive event filter badges
  - Add/Edit/Delete notification services
  - Test notifications before saving
  - Real-time validation and feedback

- **Comprehensive API**:
  - `GET /api/notifications/config` - Get configuration
  - `PUT /api/notifications/config` - Update configuration  
  - `POST /api/notifications/services` - Add service
  - `PUT /api/notifications/services/{name}` - Update service
  - `DELETE /api/notifications/services/{name}` - Delete service
  - `POST /api/notifications/test/{name}` - Test service

- **Priority-Based Notifications**:
  - Low: auto_monitor events
  - Normal: restart events
  - High: quarantine, health_check_failed events
  - Priority affects appearance in supported services

- **Async Processing**:
  - Non-blocking notification delivery
  - Queue-based worker pattern
  - Zero impact on monitoring performance
  - Graceful error handling

#### Technical Implementation

- **Backend**: 
  - New notification manager with async worker
  - Configuration models with Pydantic validation
  - Integrated with monitoring engine
  - Automatic notification on all events

- **Frontend**:
  - React component with full CRUD operations
  - Service-specific form fields
  - Real-time testing capability
  - Bootstrap UI components

- **Configuration**:
  - Stored in `data/config.json`
  - Persists across restarts
  - API and UI both update same config

#### Documentation

- `docs/NOTIFICATIONS.md` - Complete reference guide
- `docs/NOTIFICATION_QUICKSTART.md` - 5-minute setup guide
- `NOTIFICATION_IMPLEMENTATION.md` - Technical details
- `NOTIFICATION_COMPLETE.md` - Feature overview

#### Testing

- Added `test_notifications.py` - Automated test suite
- Validates all core functionality
- Tests event filtering
- Verifies async processing

### Changed

- Updated navigation menu with "Notifications" link
- Extended config manager with notification models
- Enhanced monitoring engine to send notifications
- Expanded API with notification endpoints

### Dependencies

- No new dependencies (aiohttp already included)

### Migration

No migration needed - notifications are disabled by default.
To enable:
1. Navigate to `/notifications` in UI
2. Toggle "Enable Notifications"
3. Add at least one notification service

### Notes

- Notifications are opt-in (disabled by default)
- All notification code is non-blocking
- Failed notifications are logged but don't affect monitoring
- Multiple services can be configured simultaneously
- Test functionality helps validate configuration before enabling

### Breaking Changes

None - This is a purely additive feature.

### Security

- Webhook URLs and tokens stored in `data/config.json`
- Ensure proper file permissions on config file
- All services support HTTPS
- No credentials logged or exposed

### Performance

- Minimal CPU overhead (< 1%)
- Async queue processing
- No impact on monitoring latency
- Efficient batch processing

---

**Upgrade Note**: This is a major feature addition. Existing installations will continue to work without any changes. To use notifications, simply enable them in the UI.

