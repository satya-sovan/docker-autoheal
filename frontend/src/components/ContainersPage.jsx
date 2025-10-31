import { useState, useEffect } from 'react';
import { Card, Table, Button, Badge, Form, Spinner, Modal, Alert } from 'react-bootstrap';
import {
  getContainers,
  updateContainerSelection,
  restartContainer,
  unquarantineContainer,
  getContainerDetails
} from '../services/api';

function ContainersPage() {
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContainers, setSelectedContainers] = useState(new Set());
  const [showModal, setShowModal] = useState(false);
  const [modalContainer, setModalContainer] = useState(null);
  const [alert, setAlert] = useState(null);
  const [confirmModal, setConfirmModal] = useState({ show: false, title: '', message: '', onConfirm: null });

  const fetchContainers = async () => {
    try {
      const response = await getContainers(true); // Include stopped containers
      setContainers(response.data);
    } catch (error) {
      showAlert('danger', 'Failed to load containers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContainers();

    // Auto-refresh every 5 seconds (matching EventsPage and Dashboard)
    const interval = setInterval(fetchContainers, 5000);

    // Handle visibility change to pause/resume polling
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchContainers(); // Refresh immediately when tab becomes visible
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const showAlert = (variant, message) => {
    setAlert({ variant, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const showConfirm = (title, message, onConfirm) => {
    setConfirmModal({ show: true, title, message, onConfirm });
  };

  const handleConfirm = () => {
    if (confirmModal.onConfirm) {
      confirmModal.onConfirm();
    }
    setConfirmModal({ show: false, title: '', message: '', onConfirm: null });
  };

  const handleCancelConfirm = () => {
    setConfirmModal({ show: false, title: '', message: '', onConfirm: null });
  };

  const toggleSelection = (containerId) => {
    const newSelection = new Set(selectedContainers);
    if (newSelection.has(containerId)) {
      newSelection.delete(containerId);
    } else {
      newSelection.add(containerId);
    }
    setSelectedContainers(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedContainers.size === containers.length) {
      setSelectedContainers(new Set());
    } else {
      setSelectedContainers(new Set(containers.map(c => c.id)));
    }
  };

  const handleEnableAutoheal = async () => {
    try {
      await updateContainerSelection(Array.from(selectedContainers), true);
      showAlert('success', `Enabled auto-heal for ${selectedContainers.size} container(s)`);
      setSelectedContainers(new Set());
      fetchContainers();
    } catch (error) {
      showAlert('danger', 'Failed to enable auto-heal');
    }
  };

  const handleDisableAutoheal = async () => {
    try {
      await updateContainerSelection(Array.from(selectedContainers), false);
      showAlert('success', `Disabled auto-heal for ${selectedContainers.size} container(s)`);
      setSelectedContainers(new Set());
      fetchContainers();
    } catch (error) {
      showAlert('danger', 'Failed to disable auto-heal');
    }
  };

  const handleRestart = async (containerId, containerName) => {
    showConfirm(
      'Restart Container',
      `Are you sure you want to restart container "${containerName}"?`,
      async () => {
        try {
          await restartContainer(containerId);
          showAlert('success', `Container "${containerName}" restarted`);
          fetchContainers();
        } catch (error) {
          showAlert('danger', 'Failed to restart container');
        }
      }
    );
  };

  const handleUnquarantine = async (containerId, containerName) => {
    showConfirm(
      'Remove from Quarantine',
      `Are you sure you want to remove "${containerName}" from quarantine?`,
      async () => {
        try {
          await unquarantineContainer(containerId);
          showAlert('success', `Container "${containerName}" removed from quarantine`);
          fetchContainers();
        } catch (error) {
          showAlert('danger', 'Failed to unquarantine container');
        }
      }
    );
  };

  const showContainerDetails = async (containerId) => {
    try {
      const response = await getContainerDetails(containerId);
      setModalContainer(response.data);
      setShowModal(true);
    } catch (error) {
      showAlert('danger', 'Failed to load container details');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      running: 'success',
      exited: 'danger',
      paused: 'warning',
      restarting: 'info'
    };
    return <Badge bg={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const getHealthBadge = (health) => {
    if (!health) return <span className="text-muted">N/A</span>;

    const variants = {
      healthy: 'success',
      unhealthy: 'danger',
      starting: 'warning'
    };
    return <Badge bg={variants[health.status] || 'secondary'}>{health.status}</Badge>;
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <div className="mt-2">Loading containers...</div>
      </div>
    );
  }

  return (
    <>
      {alert && (
        <Alert variant={alert.variant} dismissible onClose={() => setAlert(null)}>
          {alert.message}
        </Alert>
      )}

      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            <i className="bi bi-box me-2"></i>
            Containers
          </h5>
          <div>
            <Button variant="primary" size="sm" onClick={fetchContainers} className="me-2">
              <i className="bi bi-arrow-clockwise me-1"></i>
              Refresh
            </Button>
            <Button
              variant="success"
              size="sm"
              onClick={handleEnableAutoheal}
              disabled={selectedContainers.size === 0}
              className="me-2"
            >
              <i className="bi bi-check-circle me-1"></i>
              Enable Auto-Heal
            </Button>
            <Button
              variant="warning"
              size="sm"
              onClick={handleDisableAutoheal}
              disabled={selectedContainers.size === 0}
            >
              <i className="bi bi-x-circle me-1"></i>
              Disable Auto-Heal
            </Button>
          </div>
        </Card.Header>

        <Card.Body className="p-0">
          <Table responsive hover className="mb-0">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <Form.Check
                    type="checkbox"
                    checked={selectedContainers.size === containers.length && containers.length > 0}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th>Name</th>
                <th>ID</th>
                <th>Image</th>
                <th>Status</th>
                <th>Health</th>
                <th>Monitored</th>
                <th>Restarts</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {containers.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-4 text-muted">
                    No containers found
                  </td>
                </tr>
              ) : (
                containers.map((container) => (
                  <tr
                    key={container.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => showContainerDetails(container.id)}
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                      <Form.Check
                        type="checkbox"
                        checked={selectedContainers.has(container.id)}
                        onChange={() => toggleSelection(container.id)}
                      />
                    </td>
                    <td><strong>{container.name}</strong></td>
                    <td><code>{container.id}</code></td>
                    <td className="small">{container.image}</td>
                    <td>{getStatusBadge(container.status)}</td>
                    <td>{getHealthBadge(container.health)}</td>
                    <td>
                      {container.monitored && (
                        <Badge bg="info">Yes</Badge>
                      )}
                      {container.quarantined && (
                        <Badge bg="warning" className="ms-1">Quarantined</Badge>
                      )}
                    </td>
                    <td>{container.restart_count}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleRestart(container.id, container.name)}
                        className="me-1"
                        title="Restart"
                      >
                        <i className="bi bi-arrow-clockwise"></i>
                      </Button>
                      {container.quarantined && (
                        <Button
                          variant="success"
                          size="sm"
                          onClick={() => handleUnquarantine(container.id, container.name)}
                          title="Unquarantine"
                        >
                          <i className="bi bi-unlock"></i>
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Container Details Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Container Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {modalContainer && (
            <div>
              <h6>Basic Information</h6>
              <Table size="sm" bordered>
                <tbody>
                  <tr><th>ID:</th><td><code>{modalContainer.full_id}</code></td></tr>
                  <tr><th>Name:</th><td>{modalContainer.name}</td></tr>
                  <tr><th>Image:</th><td>{modalContainer.image}</td></tr>
                  <tr><th>Status:</th><td>{getStatusBadge(modalContainer.status)}</td></tr>
                  <tr><th>Exit Code:</th><td>{modalContainer.exit_code || 'N/A'}</td></tr>
                  <tr><th>Restart Count:</th><td>{modalContainer.restart_count}</td></tr>
                  <tr><th>Recent Restarts:</th><td>{modalContainer.recent_restart_count}</td></tr>
                </tbody>
              </Table>

              <h6 className="mt-3">Monitoring</h6>
              <Table size="sm" bordered>
                <tbody>
                  <tr><th>Monitored:</th><td>{modalContainer.monitored ? 'Yes' : 'No'}</td></tr>
                  <tr><th>Quarantined:</th><td>{modalContainer.quarantined ? 'Yes' : 'No'}</td></tr>
                </tbody>
              </Table>

              {modalContainer.health && (
                <>
                  <h6 className="mt-3">Health Status</h6>
                  <pre className="bg-light p-3 rounded">
                    {JSON.stringify(modalContainer.health, null, 2)}
                  </pre>
                </>
              )}

              <h6 className="mt-3">Labels</h6>
              <pre className="bg-light p-3 rounded">
                {JSON.stringify(modalContainer.labels, null, 2)}
              </pre>
            </div>
          )}
        </Modal.Body>
      </Modal>

      {/* Confirmation Modal */}
      <Modal show={confirmModal.show} onHide={handleCancelConfirm} centered>
        <Modal.Header closeButton>
          <Modal.Title>{confirmModal.title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {confirmModal.message}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCancelConfirm}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleConfirm}>
            Confirm
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default ContainersPage;

