/**
 * Custom hook for validating configuration timing settings
 * Ensures monitoring interval, cooldown, and restart window are properly configured
 */
export function useConfigValidation(config) {
  const validateTimingConfiguration = () => {
    const monitorInterval = config.monitor.interval_seconds;
    const cooldown = config.restart.cooldown_seconds;
    const maxRestarts = config.restart.max_restarts;
    const restartWindow = config.restart.max_restarts_window_seconds;
    const backoffEnabled = config.restart.backoff.enabled;
    const backoffInitial = config.restart.backoff.initial_seconds;
    const backoffMultiplier = config.restart.backoff.multiplier;

    const errors = [];
    const suggestions = [];

    // Validation 1: Restart window must be larger than the time needed for max restarts (based on cooldown)
    const minRestartWindowForCooldown = maxRestarts * cooldown;
    if (restartWindow < minRestartWindowForCooldown) {
      errors.push(`Restart window (${restartWindow}s) is too small for ${maxRestarts} restarts with ${cooldown}s cooldown`);
      suggestions.push(`Increase "Max Restarts Window" to at least ${minRestartWindowForCooldown} seconds (${maxRestarts} restarts × ${cooldown}s cooldown)`);
      suggestions.push(`OR reduce "Max Restarts" to ${Math.floor(restartWindow / Math.max(cooldown, 1))} or less`);
      suggestions.push(`OR reduce "Cooldown" to ${Math.floor(restartWindow / maxRestarts)} seconds or less`);
    }

    // Validation 2: Restart window must be larger than the time needed for monitoring cycles
    const minRestartWindowForMonitoring = maxRestarts * monitorInterval;
    if (restartWindow < minRestartWindowForMonitoring) {
      errors.push(`Restart window (${restartWindow}s) is too small for ${maxRestarts} monitoring cycles with ${monitorInterval}s interval`);
      suggestions.push(`Increase "Max Restarts Window" to at least ${minRestartWindowForMonitoring} seconds (${maxRestarts} cycles × ${monitorInterval}s interval)`);
      suggestions.push(`OR reduce "Max Restarts" to ${Math.floor(restartWindow / monitorInterval)} or less`);
      suggestions.push(`OR reduce "Monitoring Interval" to ${Math.floor(restartWindow / maxRestarts)} seconds or less`);
    }

    // Validation 3: Exponential backoff vs window timing (CRITICAL)
    if (backoffEnabled && backoffMultiplier > 1.0) {
      // Calculate estimated time for max_restarts with exponential backoff
      let totalTime = 0;
      let currentBackoff = backoffInitial;

      for (let i = 0; i < maxRestarts; i++) {
        totalTime += currentBackoff + cooldown + monitorInterval;
        currentBackoff = currentBackoff * backoffMultiplier;
      }

      // Calculate what the backoff would be for the last restart
      let finalBackoff = backoffInitial * Math.pow(backoffMultiplier, maxRestarts - 1);

      // If exponential backoff causes restarts to spread beyond the window, warn user
      if (totalTime > restartWindow * 1.2) { // 20% buffer to account for timing variations
        errors.push(`⚠️ CRITICAL: Exponential backoff will prevent quarantine! With backoff enabled, container may NEVER be quarantined.`);
        suggestions.push(`🔴 The ${maxRestarts} restarts will take ~${Math.round(totalTime)}s, but your window is only ${restartWindow}s`);
        suggestions.push(`By the time restart #${maxRestarts + 1} occurs, early restarts will expire from the ${restartWindow}s window`);
        suggestions.push(`📊 Final backoff delay will be ${Math.round(finalBackoff)}s (${backoffInitial}s × ${backoffMultiplier}^${maxRestarts - 1})`);
        suggestions.push(`\nRECOMMENDED FIXES:`);
        suggestions.push(`   1. Increase window to ${Math.round(totalTime * 1.5)}s+ (covers all restarts with buffer)`);
        suggestions.push(`   2. Reduce max_restarts to ${Math.max(2, maxRestarts - 2)} or less`);
        suggestions.push(`   3. Disable backoff for faster quarantine (restarts every ~${cooldown + monitorInterval}s)`);
        suggestions.push(`   4. Use slower multiplier (1.5 instead of ${backoffMultiplier})`);
        suggestions.push(`\n⚠️ Current config = INFINITE RETRY LOOP (container never quarantines)`);
      } else if (totalTime > restartWindow * 0.95) {
        // Close to the edge - warn but not critical
        errors.push(`⚠️ WARNING: Exponential backoff timing is very tight with your window`);
        suggestions.push(`The ${maxRestarts} restarts will take ~${Math.round(totalTime)}s vs ${restartWindow}s window (${Math.round((totalTime/restartWindow)*100)}% utilization)`);
        suggestions.push(`Consider increasing window to ${Math.round(totalTime * 1.3)}s for safety margin`);
      }
    }

    // Validation 4: Extremely short monitoring interval warning (performance concern)
    if (monitorInterval < 5) {
      errors.push(`⚠️ Very short monitoring interval (${monitorInterval}s) may cause high CPU usage`);
      suggestions.push(`Consider setting "Monitoring Interval" to at least 5 seconds for better performance`);
    }

    // Validation 5: Very short restart window warning (may cause premature quarantine)
    if (restartWindow < 60) {
      errors.push(`⚠️ Short restart window (${restartWindow}s) may cause premature quarantine`);
      suggestions.push(`Consider setting "Max Restarts Window" to at least 60 seconds for more stable operation`);
    }

    // Validation 6: Extremely long monitoring interval warning (may be too slow to detect issues)
    if (monitorInterval > 300) {
      errors.push(`⚠️ Very long monitoring interval (${monitorInterval}s) may be slow to detect container issues`);
      suggestions.push(`Consider reducing "Monitoring Interval" to 60 seconds or less for more responsive monitoring`);
    }

    return { isValid: errors.length === 0, errors, suggestions };
  };

  return { validateTimingConfiguration };
}

