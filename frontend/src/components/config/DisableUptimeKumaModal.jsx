import { Modal, Button } from 'react-bootstrap';

/**
 * DisableUptimeKumaModal Component
 * Confirmation modal for disabling Uptime Kuma integration
 *
 * @param {Object} props - Component props
 * @param {boolean} props.show - Whether to show the modal
 * @param {Function} props.onHide - Callback to hide modal
 * @param {Function} props.onConfirm - Callback when confirmed
 */
function DisableUptimeKumaModal({ show, onHide, onConfirm }) {
  return (
    <Modal
      show={show}
      onHide={onHide}
      centered
      backdrop="static"
      keyboard={true}
    >
      <Modal.Header closeButton className="bg-warning text-dark">
        <Modal.Title>
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          Disable Uptime-Kuma Integration?
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="mb-3">
          Are you sure you want to disable the Uptime-Kuma integration?
        </p>
        <div className="alert alert-warning mb-0">
          <strong><i className="bi bi-info-circle me-2"></i>This will:</strong>
          <ul className="mb-0 mt-2">
            <li>Stop monitoring all Uptime-Kuma monitors</li>
            <li>Remove all container-monitor mappings</li>
            <li>Disable automatic container restarts based on monitor status</li>
          </ul>
        </div>
        <p className="text-muted small mt-3 mb-0">
          You can re-enable the integration at any time by configuring and enabling it again.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          <i className="bi bi-x-circle me-1"></i>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm}>
          <i className="bi bi-toggle-off me-1"></i>
          Disable Integration
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default DisableUptimeKumaModal;

