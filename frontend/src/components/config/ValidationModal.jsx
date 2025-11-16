import { Modal, Button } from 'react-bootstrap';

/**
 * ValidationModal Component
 * Displays validation errors and suggestions for configuration timing issues
 *
 * @param {Object} props - Component props
 * @param {boolean} props.show - Whether to show the modal
 * @param {string} props.title - Modal title
 * @param {string} props.message - Modal message
 * @param {Array} props.errors - List of validation errors
 * @param {Array} props.suggestions - List of suggestions to fix errors
 * @param {Object} props.config - Current configuration object
 * @param {Function} props.onHide - Callback to close modal
 */
function ValidationModal({ show, title, message, errors, suggestions, config, onHide }) {
  return (
    <Modal
      show={show}
      onHide={onHide}
      size="lg"
      centered
      backdrop="static"
      keyboard={true}
    >
      <Modal.Header closeButton className="bg-warning text-dark">
        <Modal.Title>
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {title}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <div className="mb-3">
          <p className="fw-bold mb-2">{message}</p>
          {errors && errors.length > 0 && (
            <div className="alert alert-danger mb-3">
              <strong>Issues Found:</strong>
              <ul className="mb-0 mt-2">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {suggestions && suggestions.length > 0 && (
          <div className="alert alert-info">
            <strong><i className="bi bi-lightbulb-fill me-2"></i>Recommended Solutions:</strong>
            <ul className="mb-0 mt-2">
              {suggestions.map((suggestion, index) => (
                <li key={index} className="mb-1">{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="alert alert-light border mt-3">
          <strong><i className="bi bi-info-circle me-2"></i>Current Configuration:</strong>
          <div className="mt-2 small">
            <div><strong>Monitoring Interval:</strong> {config?.monitor?.interval_seconds} seconds</div>
            <div><strong>Cooldown:</strong> {config?.restart?.cooldown_seconds} seconds</div>
            <div><strong>Max Restarts:</strong> {config?.restart?.max_restarts}</div>
            <div><strong>Max Restarts Window:</strong> {config?.restart?.max_restarts_window_seconds} seconds</div>
          </div>
        </div>

        <div className="alert alert-success border mt-3">
          <strong><i className="bi bi-check-circle me-2"></i>How These Settings Work Together:</strong>
          <ul className="mb-0 mt-2 small">
            <li><strong>Monitoring Interval:</strong> How often the system checks container health</li>
            <li><strong>Cooldown:</strong> Wait time between restart attempts</li>
            <li><strong>Max Restarts:</strong> Maximum restart attempts before quarantine</li>
            <li><strong>Max Restarts Window:</strong> Time window for counting restarts (must fit all restart attempts)</li>
          </ul>
          <div className="mt-2 small text-muted">
            <em>Formula: Max Restarts Window ≥ MAX(Max Restarts × Cooldown, Max Restarts × Monitoring Interval)</em>
          </div>
        </div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          <i className="bi bi-x-circle me-1"></i>
          Close and Adjust Settings
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default ValidationModal;

