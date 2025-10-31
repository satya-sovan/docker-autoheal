import { useState, useEffect } from 'react';
import { Card, Row, Col, Form, Button, Alert, Spinner, Modal } from 'react-bootstrap';
import {
  getConfig,
  updateMonitorConfig,
  updateRestartConfig,
  updateObservabilityConfig,
  exportConfig,
  importConfig
} from '../services/api';

function ConfigPage() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [showInfoAlert, setShowInfoAlert] = useState(true);
  const [validationModal, setValidationModal] = useState({ show: false, title: '', message: '', errors: [], suggestions: [] });

  // Helper function to close and reset validation modal
  const closeValidationModal = () => {
    setValidationModal({ show: false, title: '', message: '', errors: [], suggestions: [] });
  };

  const fetchConfig = async () => {
    try {
      const response = await getConfig();
      setConfig(response.data);
    } catch (error) {
      showAlert('danger', 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const showAlert = (variant, message) => {
    setAlert({ variant, message });
    // Success alerts stay longer (7 seconds), errors stay for 5 seconds
    const timeout = variant === 'success' ? 7000 : 5000;
    setTimeout(() => setAlert(null), timeout);
  };

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
      errors.push(`❌ Restart window (${restartWindow}s) is too small for ${maxRestarts} restarts with ${cooldown}s cooldown`);
      suggestions.push(`Increase "Max Restarts Window" to at least ${minRestartWindowForCooldown} seconds (${maxRestarts} restarts × ${cooldown}s cooldown)`);
      suggestions.push(`OR reduce "Max Restarts" to ${Math.floor(restartWindow / Math.max(cooldown, 1))} or less`);
      suggestions.push(`OR reduce "Cooldown" to ${Math.floor(restartWindow / maxRestarts)} seconds or less`);
    }

    // Validation 2: Restart window must be larger than the time needed for monitoring cycles
    const minRestartWindowForMonitoring = maxRestarts * monitorInterval;
    if (restartWindow < minRestartWindowForMonitoring) {
      errors.push(`❌ Restart window (${restartWindow}s) is too small for ${maxRestarts} monitoring cycles with ${monitorInterval}s interval`);
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
        suggestions.push(`\n✅ RECOMMENDED FIXES:`);
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

  const handleMonitorConfigSubmit = async (e) => {
    e.preventDefault();

    // Validate timing configuration
    const validation = validateTimingConfiguration();
    if (!validation.isValid) {
      // Prevent opening multiple modals
      if (validationModal.show) {
        return;
      }
      setValidationModal({
        show: true,
        title: 'Invalid Monitor Settings Configuration',
        message: 'The monitoring interval conflicts with your restart policy settings:',
        errors: validation.errors,
        suggestions: validation.suggestions
      });
      return;
    }

    try {
      await updateMonitorConfig(config.monitor);
      showAlert('success', 'Monitor configuration updated');
      fetchConfig();
    } catch (error) {
      showAlert('danger', 'Failed to update monitor configuration');
    }
  };

  const handleRestartConfigSubmit = async (e) => {
    e.preventDefault();

    // Validate timing configuration
    const validation = validateTimingConfiguration();
    if (!validation.isValid) {
      // Prevent opening multiple modals
      if (validationModal.show) {
        return;
      }
      setValidationModal({
        show: true,
        title: 'Invalid Restart Policy Configuration',
        message: 'The restart policy settings conflict with your monitoring configuration:',
        errors: validation.errors,
        suggestions: validation.suggestions
      });
      return;
    }

    try {
      await updateRestartConfig(config.restart);
      showAlert('success', 'Restart policy updated');
      fetchConfig();
    } catch (error) {
      showAlert('danger', 'Failed to update restart policy');
    }
  };

  const handleExportConfig = async () => {
    try {
      const response = await exportConfig();
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autoheal-config-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showAlert('success', 'Configuration exported successfully');
    } catch (error) {
      showAlert('danger', 'Failed to export configuration');
    }
  };

  const handleImportConfig = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      await importConfig(file);
      showAlert('success', 'Configuration imported successfully');
      fetchConfig();
      e.target.value = '';
    } catch (error) {
      showAlert('danger', 'Failed to import configuration');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <div className="mt-2">Loading configuration...</div>
      </div>
    );
  }

  if (!config) {
    return <Alert variant="danger">Failed to load configuration</Alert>;
  }

  return (
    <>
      {/* Red banner at page top */}
      {showInfoAlert && (
        <div
          className="d-flex align-items-center justify-content-between px-3 py-2 text-white mb-4"
          style={{
            backgroundColor: '#dc3545',
            fontSize: '0.875rem',
            borderRadius: '0.375rem'
          }}
        >
          <div className="d-flex align-items-center">
            <i className="bi bi-info-circle-fill me-2"></i>
            <span><strong>Note:</strong> Configuration is stored in memory. Export regularly to backup your settings.</span>
          </div>
          <button
            type="button"
            onClick={() => setShowInfoAlert(false)}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '0 0.5rem',
              lineHeight: '1'
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>
      )}

      {alert && (
        <Alert
          variant={alert.variant}
          dismissible
          onClose={() => setAlert(null)}
          className="mb-4 d-flex align-items-center"
          style={{ fontSize: '1.1rem', fontWeight: '500' }}
        >
          {alert.variant === 'success' && <i className="bi bi-check-circle-fill me-2 fs-4"></i>}
          {alert.variant === 'danger' && <i className="bi bi-exclamation-circle-fill me-2 fs-4"></i>}
          <span>{alert.message}</span>
        </Alert>
      )}

      <Row className="g-4">
        {/* Monitor Settings */}
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="bi bi-gear me-2"></i>
                Monitor Settings
              </h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleMonitorConfigSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Monitoring Interval (seconds)</Form.Label>
                  <Form.Control
                    type="number"
                    min="1"
                    value={config.monitor.interval_seconds}
                    onChange={(e) => setConfig({
                      ...config,
                      monitor: { ...config.monitor, interval_seconds: parseInt(e.target.value) }
                    })}
                  />
                  <Form.Text>How often to check containers</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Label Key</Form.Label>
                  <Form.Control
                    type="text"
                    value={config.monitor.label_key}
                    onChange={(e) => setConfig({
                      ...config,
                      monitor: { ...config.monitor, label_key: e.target.value }
                    })}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Label Value</Form.Label>
                  <Form.Control
                    type="text"
                    value={config.monitor.label_value}
                    onChange={(e) => setConfig({
                      ...config,
                      monitor: { ...config.monitor, label_value: e.target.value }
                    })}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Monitor All Containers (ignore label filter)"
                    checked={config.monitor.include_all}
                    onChange={(e) => setConfig({
                      ...config,
                      monitor: { ...config.monitor, include_all: e.target.checked }
                    })}
                  />
                </Form.Group>

                <Button type="submit" variant="primary">
                  <i className="bi bi-save me-1"></i>
                  Save Monitor Settings
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        {/* Restart Policy */}
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="bi bi-arrow-repeat me-2"></i>
                Restart Policy
              </h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleRestartConfigSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Restart Mode</Form.Label>
                  <Form.Select
                    value={config.restart.mode}
                    onChange={(e) => setConfig({
                      ...config,
                      restart: { ...config.restart, mode: e.target.value }
                    })}
                  >
                    <option value="on-failure">On Failure (exit code != 0)</option>
                    <option value="health">Health Check</option>
                    <option value="both">Both</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Cooldown (seconds)</Form.Label>
                  <Form.Control
                    type="number"
                    min="0"
                    value={config.restart.cooldown_seconds}
                    onChange={(e) => setConfig({
                      ...config,
                      restart: { ...config.restart, cooldown_seconds: parseInt(e.target.value) }
                    })}
                  />
                  <Form.Text>Wait time between restart attempts</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Max Restarts</Form.Label>
                  <Form.Control
                    type="number"
                    min="1"
                    value={config.restart.max_restarts}
                    onChange={(e) => setConfig({
                      ...config,
                      restart: { ...config.restart, max_restarts: parseInt(e.target.value) }
                    })}
                  />
                  <Form.Text>Maximum restarts before quarantine</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Max Restarts Window (seconds)</Form.Label>
                  <Form.Control
                    type="number"
                    min="1"
                    value={config.restart.max_restarts_window_seconds}
                    onChange={(e) => setConfig({
                      ...config,
                      restart: { ...config.restart, max_restarts_window_seconds: parseInt(e.target.value) }
                    })}
                  />
                  <Form.Text>Time window for counting restarts</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Respect Manual Stop"
                    checked={config.restart.respect_manual_stop}
                    onChange={(e) => setConfig({
                      ...config,
                      restart: { ...config.restart, respect_manual_stop: e.target.checked }
                    })}
                  />
                </Form.Group>

                <Button type="submit" variant="primary">
                  <i className="bi bi-save me-1"></i>
                  Save Restart Policy
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        {/* Observability Settings */}
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="bi bi-eye me-2"></i>
                Observability Settings
              </h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await updateObservabilityConfig(config.observability);
                  showAlert('success', `✅ Settings Saved Successfully! Log level changed to ${config.observability.log_level}. Changes are now active.`);
                  fetchConfig();
                } catch (error) {
                  showAlert('danger', '❌ Failed to update observability settings. Please try again.');
                }
              }}>
                <Form.Group className="mb-3">
                  <Form.Label>Log Level</Form.Label>
                  <Form.Select
                    value={config.observability.log_level}
                    onChange={(e) => setConfig({
                      ...config,
                      observability: { ...config.observability, log_level: e.target.value }
                    })}
                  >
                    <option value="DEBUG">DEBUG (Most verbose)</option>
                    <option value="INFO">INFO (Recommended)</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL (Least verbose)</option>
                  </Form.Select>
                  <Form.Text>Controls logging verbosity. DEBUG shows all logs, CRITICAL shows only critical errors.</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Enable Prometheus Metrics"
                    checked={config.observability.prometheus_enabled}
                    onChange={(e) => setConfig({
                      ...config,
                      observability: { ...config.observability, prometheus_enabled: e.target.checked }
                    })}
                  />
                  <Form.Text className="d-block">Export metrics on port 9090</Form.Text>
                </Form.Group>

                <Button type="submit" variant="primary">
                  <i className="bi bi-save me-1"></i>
                  Save Observability Settings
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        {/* Export/Import */}
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="bi bi-file-earmark-code me-2"></i>
                Configuration Export/Import
              </h5>
            </Card.Header>


            <Card.Body>
              <div className="mb-3">
                <Button
                  variant="success"
                  className="w-100 mb-2"
                  onClick={handleExportConfig}
                >
                  <i className="bi bi-download me-1"></i>
                  Export Configuration
                </Button>
                <Form.Text className="d-block">
                  Download current configuration as JSON file
                </Form.Text>
              </div>

              <div className="mb-3">
                <Form.Control
                  type="file"
                  accept=".json"
                  onChange={handleImportConfig}
                  id="importFile"
                />
                <Form.Text className="d-block mt-2">
                  Upload configuration JSON file to restore settings
                </Form.Text>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Validation Modal */}
      <Modal
        show={validationModal.show}
        onHide={closeValidationModal}
        size="lg"
        centered
        backdrop="static"
        keyboard={true}
      >
        <Modal.Header closeButton className="bg-warning text-dark">
          <Modal.Title>
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {validationModal.title}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <p className="fw-bold mb-2">{validationModal.message}</p>
            {validationModal.errors && validationModal.errors.length > 0 && (
              <div className="alert alert-danger mb-3">
                <strong>Issues Found:</strong>
                <ul className="mb-0 mt-2">
                  {validationModal.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {validationModal.suggestions && validationModal.suggestions.length > 0 && (
            <div className="alert alert-info">
              <strong><i className="bi bi-lightbulb-fill me-2"></i>Recommended Solutions:</strong>
              <ul className="mb-0 mt-2">
                {validationModal.suggestions.map((suggestion, index) => (
                  <li key={index} className="mb-1">{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="alert alert-light border mt-3">
            <strong><i className="bi bi-info-circle me-2"></i>Current Configuration:</strong>
            <div className="mt-2 small">
              <div><strong>Monitoring Interval:</strong> {config?.monitor.interval_seconds} seconds</div>
              <div><strong>Cooldown:</strong> {config?.restart.cooldown_seconds} seconds</div>
              <div><strong>Max Restarts:</strong> {config?.restart.max_restarts}</div>
              <div><strong>Max Restarts Window:</strong> {config?.restart.max_restarts_window_seconds} seconds</div>
            </div>
          </div>

          <div className="alert alert-success border mt-3">
            <strong><i className="bi bi-check-circle me-2"></i>How These Settings Work Together:</strong>
            <ul className="mb-0 mt-2 small">
              <li><strong>Monitoring Interval:</strong> How often the system checks container health</li>
              <li><strong>Cooldown:</strong> Wait time between restart attempts</li>
              <li><strong>Max Restarts:</strong> Maximum restart attempts before quarantine</li>
              <li><strong>Max Restarts Window:</strong> Time window for counting restarts (must fit all restart attempts)</li>
            </ul>
            <div className="mt-2 small text-muted">
              <em>Formula: Max Restarts Window ≥ MAX(Max Restarts × Cooldown, Max Restarts × Monitoring Interval)</em>
            </div>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={closeValidationModal}
          >
            <i className="bi bi-x-circle me-1"></i>
            Close and Adjust Settings
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default ConfigPage;

