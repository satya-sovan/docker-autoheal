import { Modal, Button } from 'react-bootstrap';

/**
 * DeleteMappingModal Component
 * Confirmation modal for deleting a container-monitor mapping
 *
 * @param {Object} props - Component props
 * @param {boolean} props.show - Whether to show the modal
 * @param {string} props.containerName - Name of the container
 * @param {Function} props.onHide - Callback to hide modal
 * @param {Function} props.onConfirm - Callback when confirmed
 */
function DeleteMappingModal({ show, containerName, onHide, onConfirm }) {
  return (
    <Modal
      show={show}
      onHide={onHide}
      centered
      backdrop="static"
      keyboard={true}
    >
      <Modal.Header closeButton className="bg-danger text-white">
        <Modal.Title>
          <i className="bi bi-trash-fill me-2"></i>
          Delete Mapping?
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="mb-3">
          Are you sure you want to delete this container-monitor mapping?
        </p>
        <div className="alert alert-light border">
          <strong>Container:</strong> {containerName}
        </div>
        <p className="text-muted small mb-0">
          <i className="bi bi-info-circle me-1"></i>
          The container will no longer be automatically restarted based on the Uptime-Kuma monitor status.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          <i className="bi bi-x-circle me-1"></i>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm}>
          <i className="bi bi-trash me-1"></i>
          Delete Mapping
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default DeleteMappingModal;

