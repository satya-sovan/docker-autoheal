import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container, Toast, ToastContainer } from 'react-bootstrap';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import ContainersPage from './components/ContainersPage';
import EventsPage from './components/EventsPage';
import ConfigPage from './components/ConfigPage';
import NotificationsPage from './components/NotificationsPage';
import MaintenanceModal from './components/MaintenanceModal';
import {
  getSystemStatus,
  enableMaintenanceMode,
  disableMaintenanceMode
} from './services/api';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [errorToast, setErrorToast] = useState({ show: false, message: '' });

  const fetchSystemStatus = async () => {
    try {
      const response = await getSystemStatus();
      setSystemStatus(response.data);
      // Sync maintenance modal visibility with backend state
      setShowMaintenanceModal(response.data.maintenance_mode);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMaintenanceToggle = async () => {
    try {
      if (systemStatus?.maintenance_mode) {
        await disableMaintenanceMode();
        setShowMaintenanceModal(false);
      } else {
        await enableMaintenanceMode();
        setShowMaintenanceModal(true);
      }
      await fetchSystemStatus();
    } catch (error) {
      console.error('Failed to toggle maintenance mode:', error);
      setErrorToast({ show: true, message: 'Failed to toggle maintenance mode. Please try again.' });
    }
  };

  const handleDismissMaintenanceModal = async () => {
    await handleMaintenanceToggle();
  };

  useEffect(() => {
    fetchSystemStatus();

    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000);

    // Handle visibility change to refresh immediately when tab becomes visible
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchSystemStatus();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return (
    <div className="app">
      <Navigation systemStatus={systemStatus} />

      <Container
        fluid
        className="py-4"
        style={{
          opacity: systemStatus?.maintenance_mode ? 0.5 : 1,
          pointerEvents: systemStatus?.maintenance_mode ? 'none' : 'auto',
          transition: 'opacity 0.3s ease'
        }}
      >
        <Routes>
          <Route path="/" element={<Navigate to="/containers" replace />} />
          <Route
            path="/containers"
            element={
              <>
                {!loading && systemStatus && (
                  <Dashboard
                    systemStatus={systemStatus}
                    onRefresh={fetchSystemStatus}
                    onMaintenanceToggle={handleMaintenanceToggle}
                  />
                )}
                <ContainersPage />
              </>
            }
          />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </Container>

      <MaintenanceModal
        show={showMaintenanceModal}
        startTime={systemStatus?.maintenance_start_time}
        onDismiss={handleDismissMaintenanceModal}
      />

      {/* Error Toast Notification */}
      <ToastContainer position="top-end" className="p-3" style={{ zIndex: 9999 }}>
        <Toast
          show={errorToast.show}
          onClose={() => setErrorToast({ show: false, message: '' })}
          autohide
          delay={5000}
          bg="danger"
        >
          <Toast.Header>
            <strong className="me-auto">Error</strong>
          </Toast.Header>
          <Toast.Body className="text-white">{errorToast.message}</Toast.Body>
        </Toast>
      </ToastContainer>
    </div>
  );
}

export default App;

