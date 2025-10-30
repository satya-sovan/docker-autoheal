import { Row, Col, Card, Button } from 'react-bootstrap';

function Dashboard({ systemStatus, onRefresh, onMaintenanceToggle }) {
  const MetricCard = ({ icon, value, label, variant = 'primary' }) => (
    <Card className="text-center h-100 shadow-sm">
      <Card.Body>
        <div className={`display-4 text-${variant} mb-2`}>
          <i className={`bi ${icon}`}></i>
        </div>
        <div className="display-6 fw-bold">{value}</div>
        <div className="text-muted text-uppercase small">{label}</div>
      </Card.Body>
    </Card>
  );

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">Dashboard</h2>
        <Button
          variant={systemStatus.maintenance_mode ? "success" : "warning"}
          onClick={onMaintenanceToggle}
          className="d-flex align-items-center"
        >
          <i className={`bi ${systemStatus.maintenance_mode ? 'bi-play-circle' : 'bi-tools'} me-2`}></i>
          {systemStatus.maintenance_mode ? 'Exit Maintenance' : 'Enter Maintenance Mode'}
        </Button>
      </div>

      <Row className="g-4 mb-4">
            <Col md={3}>
            <MetricCard
              icon="bi-box"
              value={systemStatus.total_containers}
              label="Total Containers"
              variant="primary"
            />
          </Col>

          <Col md={3}>
            <MetricCard
              icon="bi-eye"
              value={systemStatus.monitored_containers}
              label="Monitored"
              variant="info"
            />
          </Col>

          <Col md={3}>
            <MetricCard
              icon="bi-exclamation-triangle"
              value={systemStatus.quarantined_containers}
              label="Quarantined"
              variant="warning"
            />
          </Col>

          <Col md={3}>
            <Card className="text-center h-100 shadow-sm">
              <Card.Body>
                <div className={`display-4 mb-2 ${systemStatus.monitoring_active ? 'text-success' : 'text-danger'}`}>
                  <i className={`bi ${systemStatus.monitoring_active ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}`}></i>
                </div>
                <div className="h5 fw-bold">
                  {systemStatus.monitoring_active ? 'Active' : 'Inactive'}
                </div>
                <div className="text-muted text-uppercase small">Service Status</div>
                <button className="btn btn-sm btn-outline-primary mt-2" onClick={onRefresh}>
                  <i className="bi bi-arrow-clockwise me-1"></i>
                  Refresh
                </button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
    </>
  );
}

export default Dashboard;

