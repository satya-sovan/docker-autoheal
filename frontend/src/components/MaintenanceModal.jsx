import { useEffect, useState } from 'react';
import { Modal, Button } from 'react-bootstrap';

function MaintenanceModal({ show, startTime, onDismiss }) {
  const [elapsedTime, setElapsedTime] = useState('00:00:00');

  useEffect(() => {
    if (!show || !startTime) return;

    const updateTimer = () => {
      const start = new Date(startTime);
      const now = new Date();
      const diff = Math.floor((now - start) / 1000);

      const hours = Math.floor(diff / 3600);
      const minutes = Math.floor((diff % 3600) / 60);
      const seconds = diff % 60;

      setElapsedTime(
        `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      );
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [show, startTime]);

  return (
    <Modal
      show={show}
      onHide={() => {}} // Prevent closing by clicking backdrop
      backdrop="static"
      keyboard={false}
      centered
      className="maintenance-modal"
    >
      <Modal.Header className="bg-warning text-dark border-0">
        <Modal.Title className="w-100 text-center">
          <i className="bi bi-tools me-2"></i>
          Maintenance Mode Active
        </Modal.Title>
      </Modal.Header>
      <Modal.Body className="text-center py-5">
        <div className="mb-4">
          <i className="bi bi-exclamation-triangle-fill text-warning" style={{ fontSize: '4rem' }}></i>
        </div>
        <h4 className="mb-3">Auto-Healing Suspended</h4>
        <p className="text-muted mb-4">
          All automatic container restarts are currently paused.
          <br />
          Manual operations are still available.
        </p>
        <div className="rounded p-4 mb-4" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <div className="text-muted small mb-2">TIME IN MAINTENANCE</div>
          <div className="display-4 fw-bold text-warning font-monospace">
            {elapsedTime}
          </div>
        </div>
      </Modal.Body>
      <Modal.Footer className="border-0 justify-content-center">
        <Button
          variant="success"
          size="lg"
          onClick={onDismiss}
          className="px-5"
        >
          <i className="bi bi-check-circle me-2"></i>
          Exit Maintenance Mode
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default MaintenanceModal;

