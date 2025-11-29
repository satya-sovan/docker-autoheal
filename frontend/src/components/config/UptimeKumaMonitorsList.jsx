import { Card, Table, Badge } from 'react-bootstrap';

/**
 * UptimeKumaMonitorsList Component
 * Displays available Uptime Kuma monitors and their mapping status
 *
 * @param {Object} props - Component props
 * @param {Array} props.monitors - List of monitors
 * @param {Array} props.mappings - List of mappings
 * @param {Array} props.containers - List of containers
 */
function UptimeKumaMonitorsList({ monitors, mappings, containers }) {
  const getMonitorStatus = (status) => {
    switch(status) {
      case 1: return <Badge bg="success">UP</Badge>;
      case 0: return <Badge bg="danger">DOWN</Badge>;
      case 2: return <Badge bg="warning">PENDING</Badge>;
      case 3: return <Badge bg="info">MAINTENANCE</Badge>;
      default: return <Badge bg="secondary">UNKNOWN</Badge>;
    }
  };

  const getContainerName = (containerId) => {
    const container = containers.find(c => c.id === containerId || c.id.startsWith(containerId));
    return container ? container.name : containerId;
  };

  return (
    <Card className="mb-3">
      <Card.Header>
        <strong>Available Uptime-Kuma Monitors</strong>
      </Card.Header>
      <Card.Body>
        <Table striped bordered hover size="sm">
          <thead>
            <tr>
              <th>Monitor Name</th>
              <th>Status</th>
              <th>Mapping Status</th>
            </tr>
          </thead>
          <tbody>
            {monitors.map((monitor, idx) => {
              const mapping = mappings.find(m => m.monitor_friendly_name === monitor.friendly_name);

              return (
                <tr key={idx}>
                  <td><strong>{monitor.friendly_name}</strong></td>
                  <td>{getMonitorStatus(monitor.status)}</td>
                  <td>
                    {mapping ? (
                      <span>
                        <Badge bg="success" className="me-1">Mapped</Badge>
                        <small className="text-muted">→ <strong>{getContainerName(mapping.container_id)}</strong></small>
                      </span>
                    ) : (
                      <Badge bg="secondary">Not Mapped</Badge>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
}

export default UptimeKumaMonitorsList;

