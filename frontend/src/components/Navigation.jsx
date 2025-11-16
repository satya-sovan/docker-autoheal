import { Navbar, Nav, Container, Badge } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';

function Navigation({ systemStatus }) {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <Navbar bg="primary" variant="dark" expand="lg" className="shadow-sm">
      <Container fluid>
        <Navbar.Brand>
          <i className="bi bi-shield-check me-2"></i>
          Docker Auto-Heal Service
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="basic-navbar-nav" />

        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link
              as={Link}
              to="/containers"
              className={isActive('/containers') ? 'active' : ''}
            >
              <i className="bi bi-box me-1"></i>
              Containers
            </Nav.Link>

            <Nav.Link
              as={Link}
              to="/events"
              className={isActive('/events') ? 'active' : ''}
            >
              <i className="bi bi-clock-history me-1"></i>
              Events
            </Nav.Link>


            <Nav.Link
              as={Link}
              to="/config"
              className={isActive('/config') ? 'active' : ''}
            >
              <i className="bi bi-gear me-1"></i>
              Configuration
            </Nav.Link>

            <Nav.Link href="/docs" target="_blank">
              <i className="bi bi-book me-1"></i>
              API Docs
            </Nav.Link>
          </Nav>

          <Nav>
            {systemStatus && (
              <Nav.Item className="d-flex align-items-center text-light">
                <Badge
                  bg={systemStatus.monitoring_active && systemStatus.docker_connected ? 'success' : 'danger'}
                  className="me-2"
                >
                  <i className={`bi ${systemStatus.monitoring_active ? 'bi-check-circle' : 'bi-x-circle'} me-1`}></i>
                  {systemStatus.monitoring_active ? 'Active' : 'Inactive'}
                </Badge>
                <span className="small">
                  {systemStatus.monitored_containers}/{systemStatus.total_containers} monitored
                </span>
              </Nav.Item>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Navigation;

