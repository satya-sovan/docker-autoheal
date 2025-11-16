import { Card, Form, Button } from 'react-bootstrap';

/**
 * RestartPolicySettings Component
 * Manages restart policy configuration including mode, cooldown, max restarts, and backoff settings
 *
 * @param {Object} props - Component props
 * @param {Object} props.config - Restart policy configuration object
 * @param {Function} props.onConfigChange - Callback when configuration changes
 * @param {Function} props.onSubmit - Callback when form is submitted
 */
function RestartPolicySettings({ config, onConfigChange, onSubmit }) {
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
          <i className="bi bi-arrow-repeat me-2"></i>
          Restart Policy
        </h5>
      </Card.Header>
      <Card.Body>
        <Form onSubmit={handleFormSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Restart Mode</Form.Label>
            <Form.Select
              value={config.mode}
              onChange={(e) => handleChange('mode', e.target.value)}
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
              value={config.cooldown_seconds}
              onChange={(e) => handleChange('cooldown_seconds', parseInt(e.target.value))}
            />
            <Form.Text>Wait time between restart attempts</Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Max Restarts</Form.Label>
            <Form.Control
              type="number"
              min="1"
              value={config.max_restarts}
              onChange={(e) => handleChange('max_restarts', parseInt(e.target.value))}
            />
            <Form.Text>Maximum restarts before quarantine</Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Max Restarts Window (seconds)</Form.Label>
            <Form.Control
              type="number"
              min="1"
              value={config.max_restarts_window_seconds}
              onChange={(e) => handleChange('max_restarts_window_seconds', parseInt(e.target.value))}
            />
            <Form.Text>Time window for counting restarts</Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Respect Manual Stop"
              checked={config.respect_manual_stop}
              onChange={(e) => handleChange('respect_manual_stop', e.target.checked)}
            />
          </Form.Group>

          <Button type="submit" variant="primary">
            <i className="bi bi-save me-1"></i>
            Save Restart Policy
          </Button>
        </Form>
      </Card.Body>
    </Card>
  );
}

export default RestartPolicySettings;

