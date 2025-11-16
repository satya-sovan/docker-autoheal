import { Form, Button, Spinner, InputGroup } from 'react-bootstrap';
import { useState } from 'react';
/**
 * UptimeKumaConnectionForm Component
 * Form for configuring and testing Uptime Kuma connection
 *
 * @param {Object} props - Component props
 * @param {Object} props.config - Uptime Kuma configuration
 * @param {Function} props.onConfigChange - Callback when config changes
 * @param {Function} props.onTestConnection - Callback to test connection
 * @param {Function} props.onEnableIntegration - Callback to enable integration
 * @param {boolean} props.testingConnection - Whether connection is being tested
 * @param {boolean} props.connectionTested - Whether connection was successfully tested
 * @param {boolean} props.enablingIntegration - Whether integration is being enabled
 */
function UptimeKumaConnectionForm({
  config,
  onConfigChange,
  onTestConnection,
  onEnableIntegration,
  testingConnection,
  connectionTested,
  enablingIntegration
}) {
  const handleChange = (field, value) => {
    onConfigChange({
      ...config,
      [field]: value
    });
  };

  const isFormValid = config?.server_url && config?.api_token;
  const [showApiToken, setShowApiToken] = useState(false);

  return (
    <>
      <p className="text-muted mb-3">
        Configure your Uptime-Kuma server connection. You can use either API Key authentication (recommended) or basic username/password authentication.
      </p>

      <Form>
        <Form.Group className="mb-3">
          <Form.Label>Uptime-Kuma Server URL</Form.Label>
          <Form.Control
            type="text"
            placeholder="http://localhost:3001"
            value={config?.server_url || ''}
            onChange={(e) => handleChange('server_url', e.target.value)}
          />
          <Form.Text>Enter the base URL of your Uptime-Kuma instance</Form.Text>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>API Key</Form.Label>
          <InputGroup>
            <Form.Control
              type={showApiToken ? "text" : "password"}
              placeholder="Enter your API key (e.g., uk3_xxxxx) or password"
              value={config?.api_token || ''}
              onChange={(e) => handleChange('api_token', e.target.value)}
            />
            <Button
              variant="outline-secondary"
              onClick={() => setShowApiToken(!showApiToken)}
              aria-label={showApiToken ? "Hide API key" : "Show API key"}
            >
              <i className={`bi bi-eye${showApiToken ? '-slash' : ''}`}></i>
            </Button>
          </InputGroup>
          <Form.Text className="text-muted">
            <strong>API Key Auth:</strong> Enter API key here (Settings → Security → API Keys)
          </Form.Text>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Check
            type="checkbox"
            label="Auto-restart containers when monitors are DOWN"
            checked={config?.auto_restart_on_down ?? true}
            onChange={(e) => handleChange('auto_restart_on_down', e.target.checked)}
          />
        </Form.Group>

        {!connectionTested ? (
          <Button
            variant="primary"
            onClick={onTestConnection}
            disabled={testingConnection || !isFormValid}
          >
            {testingConnection ? (
              <>
                <Spinner size="sm" className="me-1" /> Testing...
              </>
            ) : (
              <>
                <i className="bi bi-check-circle me-1"></i>Test Connection
              </>
            )}
          </Button>
        ) : (
          <div className="d-flex align-items-center gap-2">
            <Button
              variant="success"
              onClick={onEnableIntegration}
              disabled={enablingIntegration}
            >
              {enablingIntegration ? (
                <>
                  <Spinner size="sm" className="me-1" /> Enabling...
                </>
              ) : (
                <>
                  <i className="bi bi-toggle-on me-1"></i>Enable Integration
                </>
              )}
            </Button>
            <Button
              variant="outline-secondary"
              size="sm"
              onClick={onTestConnection}
              disabled={testingConnection}
            >
              <i className="bi bi-arrow-repeat me-1"></i>
              Test Again
            </Button>
          </div>
        )}
      </Form>
    </>
  );
}

export default UptimeKumaConnectionForm;

