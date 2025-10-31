import { useState, useEffect } from 'react';
import { Card, Button, Spinner, Badge, Alert, Modal } from 'react-bootstrap';
import { getEvents, clearEvents } from '../services/api';
import { format } from 'date-fns';

function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const fetchEvents = async () => {
    try {
      const response = await getEvents(50);
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to load events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearEventsClick = () => {
    setShowConfirmModal(true);
  };

  const handleCancelClear = () => {
    setShowConfirmModal(false);
  };

  const handleConfirmClear = async () => {
    setShowConfirmModal(false);

    try {
      await clearEvents();
      setEvents([]);
      setAlert({ type: 'success', message: 'All events cleared successfully!' });
      setTimeout(() => setAlert(null), 3000);
    } catch (error) {
      console.error('Failed to clear events:', error);
      setAlert({ type: 'danger', message: 'Failed to clear events. Please try again.' });
      setTimeout(() => setAlert(null), 5000);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, []);

  const getEventVariant = (status) => {
    const variants = {
      success: 'success',
      failure: 'danger',
      quarantined: 'warning'
    };
    return variants[status] || 'secondary';
  };

  const getEventIcon = (eventType) => {
    const icons = {
      restart: 'bi-arrow-clockwise',
      quarantine: 'bi-lock',
      health_check_failed: 'bi-exclamation-triangle'
    };
    return icons[eventType] || 'bi-info-circle';
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <div className="mt-2">Loading events...</div>
      </div>
    );
  }

  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">
          <i className="bi bi-clock-history me-2"></i>
          Event Log
        </h5>
        <div>
          <Button variant="primary" size="sm" onClick={fetchEvents} className="me-2">
            <i className="bi bi-arrow-clockwise me-1"></i>
            Refresh
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleClearEventsClick}
            disabled={events.length === 0}
          >
            <i className="bi bi-trash me-1"></i>
            Clear All
          </Button>
        </div>
      </Card.Header>

      <Card.Body style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {alert && (
          <Alert variant={alert.type} dismissible onClose={() => setAlert(null)} className="mb-3">
            {alert.message}
          </Alert>
        )}
        {events.length === 0 ? (
          <div className="text-center py-4 text-muted">
            No events recorded yet
          </div>
        ) : (
          <div className="event-list">
            {[...events].reverse().map((event, index) => (
              <div
                key={index}
                className={`event-item border-start border-${getEventVariant(event.status)} border-4 p-3 mb-3 bg-light rounded`}
              >
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <h6 className="mb-1">
                      <i className={`bi ${getEventIcon(event.event_type)} me-2`}></i>
                      {event.container_name}
                    </h6>
                    <small className="text-muted">
                      {format(new Date(event.timestamp), 'PPpp')}
                    </small>
                  </div>
                  <div className="text-end">
                    <Badge bg="secondary" className="me-1">{event.event_type}</Badge>
                    <Badge bg={getEventVariant(event.status)}>{event.status}</Badge>
                    <div className="mt-1">
                      <Badge bg="primary">Restarts: {event.restart_count}</Badge>
                    </div>
                  </div>
                </div>
                <div className="mt-2">
                  <strong>Message:</strong> {event.message}
                </div>
                <div className="mt-1 small text-muted">
                  <strong>Container ID:</strong> <code>{event.container_id}</code>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card.Body>

      {/* Confirmation Modal */}
      <Modal show={showConfirmModal} onHide={handleCancelClear} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="bi bi-exclamation-triangle text-warning me-2"></i>
            Confirm Clear Events
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="mb-0">
            Are you sure you want to clear all events? This action cannot be undone.
          </p>
          <p className="text-muted small mt-2 mb-0">
            <i className="bi bi-info-circle me-1"></i>
            {events.length} event{events.length !== 1 ? 's' : ''} will be permanently deleted.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCancelClear}>
            <i className="bi bi-x-circle me-1"></i>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleConfirmClear}>
            <i className="bi bi-trash me-1"></i>
            Clear All Events
          </Button>
        </Modal.Footer>
      </Modal>
    </Card>
  );
}

export default EventsPage;

