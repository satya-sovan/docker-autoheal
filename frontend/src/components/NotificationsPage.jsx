import { useState, useEffect } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Form,
  Table,
  Modal,
  Alert,
  Badge,
  Spinner
} from 'react-bootstrap';
import {
  getNotificationsConfig,
  updateNotificationsConfig,
  addNotificationService,
  updateNotificationService,
  deleteNotificationService,
  testNotificationService
} from '../services/api';

function NotificationsPage() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [alert, setAlert] = useState({ show: false, message: '', variant: 'success' });
  const [testingService, setTestingService] = useState(null);

  const serviceTypes = [
    { value: 'webhook', label: 'Generic Webhook' },
    { value: 'discord', label: 'Discord' },
    { value: 'slack', label: 'Slack' },
    { value: 'telegram', label: 'Telegram' },
    { value: 'ntfy', label: 'Ntfy' },
    { value: 'gotify', label: 'Gotify' },
    { value: 'pushover', label: 'Pushover' }
  ];

  const eventTypes = [
    { value: 'restart', label: 'Container Restart' },
    { value: 'quarantine', label: 'Container Quarantine' },
    { value: 'health_check_failed', label: 'Health Check Failed' },
    { value: 'auto_monitor', label: 'Auto Monitor' },
    { value: 'unquarantine', label: 'Unquarantine' }
  ];

  const [formData, setFormData] = useState({
    name: '',
    type: 'webhook',
    enabled: true,
    url: '',
    headers: {},
    username: '',
    password: '',
    bot_token: '',
    chat_id: '',
    topic: '',
    server_url: '',
    app_token: '',
    user_key: '',
    api_token: ''
  });

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await getNotificationsConfig();
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch notifications config:', error);
      showAlert('Failed to load notifications configuration', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const showAlert = (message, variant = 'success') => {
    setAlert({ show: true, message, variant });
    setTimeout(() => setAlert({ show: false, message: '', variant: 'success' }), 5000);
  };

  const handleToggleNotifications = async (enabled) => {
    try {
      setSaving(true);
      await updateNotificationsConfig({ enabled });
      setConfig({ ...config, enabled });
      showAlert(`Notifications ${enabled ? 'enabled' : 'disabled'}`, 'success');
    } catch (error) {
      console.error('Failed to toggle notifications:', error);
      showAlert('Failed to update notifications', 'danger');
    } finally {
      setSaving(false);
    }
  };

  const handleEventFiltersChange = async (selectedEvents) => {
    try {
      setSaving(true);
      await updateNotificationsConfig({ event_filters: selectedEvents });
      setConfig({ ...config, event_filters: selectedEvents });
      showAlert('Event filters updated', 'success');
    } catch (error) {
      console.error('Failed to update event filters:', error);
      showAlert('Failed to update event filters', 'danger');
    } finally {
      setSaving(false);
    }
  };

  const handleEventFilterToggle = (eventType) => {
    const current = config.event_filters || [];
    const updated = current.includes(eventType)
      ? current.filter(e => e !== eventType)
      : [...current, eventType];
    handleEventFiltersChange(updated);
  };

  const handleOpenModal = (service = null) => {
    if (service) {
      setEditingService(service);
      setFormData({ ...service });
    } else {
      setEditingService(null);
      setFormData({
        name: '',
        type: 'webhook',
        enabled: true,
        url: '',
        headers: {},
        username: '',
        password: '',
        bot_token: '',
        chat_id: '',
        topic: '',
        server_url: '',
        app_token: '',
        user_key: '',
        api_token: ''
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingService(null);
  };

  const handleSaveService = async () => {
    try {
      setSaving(true);

      // Clean up the form data - only send relevant fields for the service type
      const cleanedData = {
        name: formData.name,
        type: formData.type,
        enabled: formData.enabled
      };

      // Add type-specific fields
      if (['webhook', 'discord', 'slack'].includes(formData.type) && formData.url) {
        cleanedData.url = formData.url;
      }
      if (formData.type === 'webhook' && formData.headers && Object.keys(formData.headers).length > 0) {
        cleanedData.headers = formData.headers;
      }
      if (formData.type === 'discord' && formData.username) {
        cleanedData.username = formData.username;
      }
      if (formData.type === 'telegram') {
        if (formData.bot_token) cleanedData.bot_token = formData.bot_token;
        if (formData.chat_id) cleanedData.chat_id = formData.chat_id;
      }
      if (formData.type === 'ntfy') {
        if (formData.topic) cleanedData.topic = formData.topic;
        if (formData.server_url) cleanedData.server_url = formData.server_url;
        if (formData.username) cleanedData.username = formData.username;
        if (formData.password) cleanedData.password = formData.password;
      }
      if (formData.type === 'gotify') {
        if (formData.server_url) cleanedData.server_url = formData.server_url;
        if (formData.app_token) cleanedData.app_token = formData.app_token;
      }
      if (formData.type === 'pushover') {
        if (formData.user_key) cleanedData.user_key = formData.user_key;
        if (formData.api_token) cleanedData.api_token = formData.api_token;
      }

      if (editingService) {
        await updateNotificationService(editingService.name, cleanedData);
        showAlert('Notification service updated successfully', 'success');
      } else {
        await addNotificationService(cleanedData);
        showAlert('Notification service added successfully', 'success');
      }

      await fetchConfig();
      handleCloseModal();
    } catch (error) {
      console.error('Failed to save service:', error);
      showAlert(error.response?.data?.detail || 'Failed to save notification service', 'danger');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteService = async (serviceName) => {
    if (!window.confirm(`Are you sure you want to delete the service "${serviceName}"?`)) {
      return;
    }

    try {
      setSaving(true);
      await deleteNotificationService(serviceName);
      showAlert('Notification service deleted successfully', 'success');
      await fetchConfig();
    } catch (error) {
      console.error('Failed to delete service:', error);
      showAlert('Failed to delete notification service', 'danger');
    } finally {
      setSaving(false);
    }
  };

  const handleTestService = async (serviceName) => {
    try {
      setTestingService(serviceName);
      await testNotificationService(serviceName);
      showAlert(`Test notification sent to "${serviceName}"`, 'success');
    } catch (error) {
      console.error('Failed to test service:', error);
      showAlert(error.response?.data?.detail || 'Failed to send test notification', 'danger');
    } finally {
      setTestingService(null);
    }
  };

  const renderServiceFields = () => {
    switch (formData.type) {
      case 'webhook':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Webhook URL *</Form.Label>
              <Form.Control
                type="url"
                value={formData.url || ''}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://example.com/webhook"
                required
              />
            </Form.Group>
          </>
        );

      case 'discord':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Discord Webhook URL *</Form.Label>
              <Form.Control
                type="url"
                value={formData.url || ''}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://discord.com/api/webhooks/..."
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Username (optional)</Form.Label>
              <Form.Control
                type="text"
                value={formData.username || ''}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="Docker Auto-Heal"
              />
            </Form.Group>
          </>
        );

      case 'slack':
        return (
          <Form.Group className="mb-3">
            <Form.Label>Slack Webhook URL *</Form.Label>
            <Form.Control
              type="url"
              value={formData.url || ''}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              placeholder="https://hooks.slack.com/services/..."
              required
            />
          </Form.Group>
        );

      case 'telegram':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Bot Token *</Form.Label>
              <Form.Control
                type="text"
                value={formData.bot_token || ''}
                onChange={(e) => setFormData({ ...formData, bot_token: e.target.value })}
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Chat ID *</Form.Label>
              <Form.Control
                type="text"
                value={formData.chat_id || ''}
                onChange={(e) => setFormData({ ...formData, chat_id: e.target.value })}
                placeholder="-1001234567890"
                required
              />
            </Form.Group>
          </>
        );

      case 'ntfy':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Topic *</Form.Label>
              <Form.Control
                type="text"
                value={formData.topic || ''}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                placeholder="docker-autoheal"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Server URL (optional)</Form.Label>
              <Form.Control
                type="url"
                value={formData.server_url || ''}
                onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
                placeholder="https://ntfy.sh (default)"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Username (optional)</Form.Label>
              <Form.Control
                type="text"
                value={formData.username || ''}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Password (optional)</Form.Label>
              <Form.Control
                type="password"
                value={formData.password || ''}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </Form.Group>
          </>
        );

      case 'gotify':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Server URL *</Form.Label>
              <Form.Control
                type="url"
                value={formData.server_url || ''}
                onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
                placeholder="https://gotify.example.com"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>App Token *</Form.Label>
              <Form.Control
                type="text"
                value={formData.app_token || ''}
                onChange={(e) => setFormData({ ...formData, app_token: e.target.value })}
                placeholder="AaBbCcDdEeFf"
                required
              />
            </Form.Group>
          </>
        );

      case 'pushover':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label>User Key *</Form.Label>
              <Form.Control
                type="text"
                value={formData.user_key || ''}
                onChange={(e) => setFormData({ ...formData, user_key: e.target.value })}
                placeholder="uQiRzpo4DXghDmr9QzzfQu27cmVRsG"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>API Token *</Form.Label>
              <Form.Control
                type="text"
                value={formData.api_token || ''}
                onChange={(e) => setFormData({ ...formData, api_token: e.target.value })}
                placeholder="azGDORePK8gMaC0QOYAMyEEuzJnyUi"
                required
              />
            </Form.Group>
          </>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" />
        <p className="mt-3">Loading notifications configuration...</p>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <Row className="mb-4">
        <Col>
          <h2>Notifications</h2>
          <p className="text-muted">
            Configure notification services to receive alerts for container events
          </p>
        </Col>
      </Row>

      {alert.show && (
        <Alert variant={alert.variant} dismissible onClose={() => setAlert({ ...alert, show: false })}>
          {alert.message}
        </Alert>
      )}

      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5>Notification System</h5>
                  <p className="text-muted mb-0">
                    {config?.enabled ? 'Notifications are enabled' : 'Notifications are disabled'}
                  </p>
                </div>
                <Form.Check
                  type="switch"
                  checked={config?.enabled || false}
                  onChange={(e) => handleToggleNotifications(e.target.checked)}
                  disabled={saving}
                  label={config?.enabled ? 'Enabled' : 'Disabled'}
                />
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Event Filters</h5>
            </Card.Header>
            <Card.Body>
              <p className="text-muted">Select which event types should trigger notifications</p>
              <div className="d-flex flex-wrap gap-2">
                {eventTypes.map((eventType) => (
                  <Badge
                    key={eventType.value}
                    bg={config?.event_filters?.includes(eventType.value) ? 'primary' : 'secondary'}
                    style={{ cursor: 'pointer', fontSize: '0.9rem', padding: '0.5rem 1rem' }}
                    onClick={() => handleEventFilterToggle(eventType.value)}
                  >
                    {eventType.label}
                    {config?.event_filters?.includes(eventType.value) && ' ✓'}
                  </Badge>
                ))}
              </div>
              {(!config?.event_filters || config.event_filters.length === 0) && (
                <Alert variant="info" className="mt-3 mb-0">
                  No filters selected - all events will trigger notifications
                </Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Notification Services</h5>
              <Button variant="primary" size="sm" onClick={() => handleOpenModal()}>
                + Add Service
              </Button>
            </Card.Header>
            <Card.Body>
              {config?.services?.length === 0 ? (
                <Alert variant="info" className="mb-0">
                  No notification services configured. Click "Add Service" to get started.
                </Alert>
              ) : (
                <Table responsive striped hover>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {config?.services?.map((service) => (
                      <tr key={service.name}>
                        <td>{service.name}</td>
                        <td>
                          <Badge bg="info">
                            {serviceTypes.find(t => t.value === service.type)?.label || service.type}
                          </Badge>
                        </td>
                        <td>
                          <Badge bg={service.enabled ? 'success' : 'secondary'}>
                            {service.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </td>
                        <td>
                          <Button
                            variant="outline-primary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleTestService(service.name)}
                            disabled={testingService === service.name || !service.enabled}
                          >
                            {testingService === service.name ? (
                              <>
                                <Spinner animation="border" size="sm" className="me-1" />
                                Testing...
                              </>
                            ) : (
                              'Test'
                            )}
                          </Button>
                          <Button
                            variant="outline-secondary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleOpenModal(service)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => handleDeleteService(service.name)}
                            disabled={saving}
                          >
                            Delete
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Modal show={showModal} onHide={handleCloseModal} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {editingService ? 'Edit Notification Service' : 'Add Notification Service'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Service Name *</Form.Label>
              <Form.Control
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Discord Server"
                required
                disabled={!!editingService}
              />
              <Form.Text className="text-muted">
                A unique name to identify this service
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Service Type *</Form.Label>
              <Form.Select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                disabled={!!editingService}
              >
                {serviceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Check
                type="switch"
                label="Enabled"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
              />
            </Form.Group>

            <hr />

            {renderServiceFields()}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSaveService}
            disabled={saving || !formData.name}
          >
            {saving ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Saving...
              </>
            ) : (
              editingService ? 'Update Service' : 'Add Service'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default NotificationsPage;

