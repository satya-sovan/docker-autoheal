# Manual Stop Respect Fix

## Issue Fixed
The Docker Auto-Heal service was restarting containers that exited with code 0 (clean shutdown), which typically indicates a manual stop or successful completion.

## Solution
Changed the default value of `respect_manual_stop` from `False` to `True` in the `RestartConfig` class.

### Configuration Change
In `config.py`, line 38:
```python
# Before
respect_manual_stop: bool = Field(default=False, description="Respect manual container stops (exit code 0)")

# After  
respect_manual_stop: bool = Field(default=True, description="Respect manual container stops (exit code 0)")
```

## Behavior After Fix
- **Exit Code 0**: Container will NOT be restarted (respects manual stop)
- **Non-zero Exit Code**: Container will be restarted (indicates failure)
- **Unhealthy Status**: Container will be restarted based on health checks

## How to Override
If you want the service to restart containers even after clean shutdowns, you can set:
```json
{
  "restart": {
    "respect_manual_stop": false
  }
}
```

## Monitoring Logic
The logic in `monitor.py` checks:
1. If container exited with code 0 AND `respect_manual_stop` is True → No restart
2. If container exited with non-zero code → Restart  
3. If container is unhealthy → Restart (based on health check mode)

This ensures that manually stopped containers or containers that completed successfully are not unnecessarily restarted.
