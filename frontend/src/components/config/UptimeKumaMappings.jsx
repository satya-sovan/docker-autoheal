import { useState } from 'react';
import { Card, Table, Badge, Button, Row, Col, Form } from 'react-bootstrap';

/**
 * UptimeKumaMappings Component
 * Manages container-monitor mappings
 *
 * @param {Object} props - Component props
 * @param {Array} props.mappings - List of mappings
 * @param {Array} props.monitors - List of monitors
 * @param {Array} props.containers - List of containers
 * @param {Function} props.onAddMapping - Callback to add mapping
 * @param {Function} props.onDeleteMapping - Callback to delete mapping
 */
function UptimeKumaMappings({ mappings, monitors, containers, onAddMapping, onDeleteMapping }) {
  const [newMapping, setNewMapping] = useState({ container_id: '', monitor_friendly_name: '' });

  const getContainerName = (containerId) => {
    const container = containers.find(c => c.id === containerId || c.id.startsWith(containerId));
    return container ? container.name : containerId;
  };

  const handleAddMapping = () => {
    if (!newMapping.container_id || !newMapping.monitor_friendly_name) {
      return;
    }
    onAddMapping(newMapping);
    setNewMapping({ container_id: '', monitor_friendly_name: '' });
  };

  return (
    <Card>
      <Card.Header className="bg-light">
        <strong>Container-Monitor Mappings</strong>
      </Card.Header>
      <Card.Body>
        <p className="text-muted small">
          Map containers to Uptime-Kuma monitors. When a monitor goes DOWN, the container will be restarted automatically.
        </p>

        {mappings.length > 0 && (
          <Table striped bordered hover size="sm" className="mb-3">
            <thead>
              <tr>
                <th>Container</th>
                <th>Monitor</th>
                <th>Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {mappings.map((mapping, idx) => (
                <tr key={idx}>
                  <td><strong>{getContainerName(mapping.container_id)}</strong></td>
                  <td><strong>{mapping.monitor_friendly_name}</strong></td>
                  <td>
                    {mapping.auto_mapped ? (
                      <Badge bg="info">Auto</Badge>
                    ) : (
                      <Badge bg="secondary">Manual</Badge>
                    )}
                  </td>
                  <td>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => onDeleteMapping(mapping.container_id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}

        <h6 className="mt-3">Add New Mapping</h6>
        <Row className="align-items-end">
          <Col md={5}>
            <Form.Group>
              <Form.Label>Container</Form.Label>
              <Form.Select
                value={newMapping.container_id}
                onChange={(e) => setNewMapping({...newMapping, container_id: e.target.value})}
              >
                <option value="">Select Container...</option>
                {containers.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.status})
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={5}>
            <Form.Group>
              <Form.Label>Monitor</Form.Label>
              <Form.Select
                value={newMapping.monitor_friendly_name}
                onChange={(e) => setNewMapping({...newMapping, monitor_friendly_name: e.target.value})}
              >
                <option value="">Select Monitor...</option>
                {monitors.map(m => (
                  <option key={m.friendly_name} value={m.friendly_name}>
                    {m.friendly_name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={2}>
            <Button
              variant="primary"
              onClick={handleAddMapping}
              disabled={!newMapping.container_id || !newMapping.monitor_friendly_name}
              className="w-100"
            >
              Add
            </Button>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
}

export default UptimeKumaMappings;

