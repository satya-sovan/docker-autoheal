import { Card, Form, Button } from 'react-bootstrap';

/**
 * MonitorSettings Component
 * Manages monitoring configuration including interval, label filters, and include_all option
 *
 * @param {Object} props - Component props
 * @param {Object} props.config - Monitor configuration object
 * @param {Function} props.onConfigChange - Callback when configuration changes
 * @param {Function} props.onSubmit - Callback when form is submitted
 */
function MonitorSettings({ config, onConfigChange, onSubmit }) {
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
          <i className="bi bi-gear me-2"></i>
          Monitor Settings
        </h5>
      </Card.Header>
      <Card.Body>
        <Form onSubmit={handleFormSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Monitoring Interval (seconds)</Form.Label>
            <Form.Control
              type="number"
              min="1"
              value={config.interval_seconds}
              onChange={(e) => handleChange('interval_seconds', parseInt(e.target.value))}
            />
            <Form.Text>How often to check containers</Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Label Key</Form.Label>
            <Form.Control
              type="text"
              value={config.label_key}
              onChange={(e) => handleChange('label_key', e.target.value)}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Label Value</Form.Label>
            <Form.Control
              type="text"
              value={config.label_value}
              onChange={(e) => handleChange('label_value', e.target.value)}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Monitor All Containers (ignore label filter)"
              checked={config.include_all}
              onChange={(e) => handleChange('include_all', e.target.checked)}
            />
          </Form.Group>

          <Button type="submit" variant="primary">
            <i className="bi bi-save me-1"></i>
            Save Monitor Settings
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
}

export default MonitorSettings;

