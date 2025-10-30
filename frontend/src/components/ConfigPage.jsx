import { useState, useEffect } from 'react';
import { Card, Row, Col, Form, Button, Alert, Spinner } from 'react-bootstrap';
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

  const handleMonitorConfigSubmit = async (e) => {
    e.preventDefault();
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
    </>
  );
}

export default ConfigPage;

