import { useState } from 'react';
import { Card, Form, Button, Spinner, Badge, Table, Row, Col } from 'react-bootstrap';
import UptimeKumaConnectionForm from './UptimeKumaConnectionForm';
import UptimeKumaMonitorsList from './UptimeKumaMonitorsList';
import UptimeKumaMappings from './UptimeKumaMappings';

/**
 * UptimeKumaIntegration Component
 * Main component for Uptime Kuma integration management
 *
 * @param {Object} props - Component props
 * @param {Object} props.config - Uptime Kuma configuration
 * @param {Array} props.monitors - List of available monitors
 * @param {Array} props.containers - List of available containers
 * @param {Array} props.mappings - List of container-monitor mappings
 * @param {Function} props.onConfigChange - Callback when config changes
 * @param {Function} props.onTestConnection - Callback to test connection
 * @param {Function} props.onEnableIntegration - Callback to enable integration
 * @param {Function} props.onDisableIntegration - Callback to disable integration
 * @param {Function} props.onAddMapping - Callback to add mapping
 * @param {Function} props.onDeleteMapping - Callback to delete mapping
 * @param {Function} props.onShowDisableModal - Callback to show disable modal
 */
function UptimeKumaIntegration({
  config,
  monitors,
  containers,
  mappings,
  onConfigChange,
  onTestConnection,
  onEnableIntegration,
  onDisableIntegration,
  onAddMapping,
  onDeleteMapping,
  onShowDisableModal
}) {
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTested, setConnectionTested] = useState(false);
  const [enablingIntegration, setEnablingIntegration] = useState(false);

  const handleTestConnection = async () => {
    setTestingConnection(true);
    const success = await onTestConnection();
    setConnectionTested(success);
    setTestingConnection(false);
  };

  const handleEnableIntegration = async () => {
    setEnablingIntegration(true);
    await onEnableIntegration();
    setEnablingIntegration(false);
  };

  const isEnabled = config?.enabled;

  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">
          <i className="bi bi-link-45deg me-2"></i>
          Uptime-Kuma Integration
          {isEnabled ? (
            <Badge bg="success" className="ms-2">Active</Badge>
          ) : (
            <Badge bg="secondary" className="ms-2">Disabled</Badge>
          )}
        </h5>
        {isEnabled && (
          <Button
            variant="danger"
            size="sm"
            onClick={onShowDisableModal}
          >
            <i className="bi bi-toggle-off me-1"></i>
            Disable Integration
          </Button>
        )}
      </Card.Header>
      <Card.Body>
        {!isEnabled ? (
          <UptimeKumaConnectionForm
            config={config}
            onConfigChange={onConfigChange}
            onTestConnection={handleTestConnection}
            onEnableIntegration={handleEnableIntegration}
            testingConnection={testingConnection}
            connectionTested={connectionTested}
            enablingIntegration={enablingIntegration}
          />
        ) : (
          <>
            <div className="mb-3 p-3 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              <div className="mt-2 small text-muted">
                <div><strong>Server:</strong> {config.server_url}</div>
                <div><strong>Monitors:</strong> {monitors.length} | <strong>Mappings:</strong> {mappings.length}</div>
              </div>
            </div>

            {monitors.length > 0 && (
              <UptimeKumaMonitorsList
                monitors={monitors}
                mappings={mappings}
                containers={containers}
              />
            )}

            <UptimeKumaMappings
              mappings={mappings}
              monitors={monitors}
              containers={containers}
              onAddMapping={onAddMapping}
              onDeleteMapping={onDeleteMapping}
            />
          </>
        )}
      </Card.Body>
    </Card>
  );
}

export default UptimeKumaIntegration;

