import { Card, Form, Button } from 'react-bootstrap';

/**
 * ObservabilitySettings Component
 * Manages observability configuration including log level and Prometheus metrics
 *
 * @param {Object} props - Component props
 * @param {Object} props.config - Observability configuration object
 * @param {Function} props.onConfigChange - Callback when configuration changes
 * @param {Function} props.onSubmit - Callback when form is submitted
 */
function ObservabilitySettings({ config, onConfigChange, onSubmit }) {
  const handleChange = (field, value) => {
    onConfigChange({
      ...config,
      [field]: value
    });
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <Card>
      <Card.Header>
        <h5 className="mb-0">
          <i className="bi bi-eye me-2"></i>
          Observability Settings
        </h5>
      </Card.Header>
      <Card.Body>
        <Form onSubmit={handleFormSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Log Level</Form.Label>
            <Form.Select
              value={config.log_level}
              onChange={(e) => handleChange('log_level', e.target.value)}
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
              checked={config.prometheus_enabled}
              onChange={(e) => handleChange('prometheus_enabled', e.target.checked)}
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
  );
}

export default ObservabilitySettings;

