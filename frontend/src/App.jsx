import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import ContainersPage from './components/ContainersPage';
import EventsPage from './components/EventsPage';
import ConfigPage from './components/ConfigPage';
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
      alert('Failed to toggle maintenance mode. Please try again.');
    }
  };

  const handleDismissMaintenanceModal = async () => {
    await handleMaintenanceToggle();
  };

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000); // Refresh every 5s
    return () => clearInterval(interval);
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
        {!loading && systemStatus && (
          <Dashboard
            systemStatus={systemStatus}
            onRefresh={fetchSystemStatus}
            onMaintenanceToggle={handleMaintenanceToggle}
          />
        )}

        <Routes>
          <Route path="/" element={<Navigate to="/containers" replace />} />
          <Route path="/containers" element={<ContainersPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </Container>

      <MaintenanceModal
        show={showMaintenanceModal}
        startTime={systemStatus?.maintenance_start_time}
        onDismiss={handleDismissMaintenanceModal}
      />
    </div>
  );
}

export default App;

