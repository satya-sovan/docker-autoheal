import { useState, useEffect } from 'react';
import { Row, Col, Alert, Spinner } from 'react-bootstrap';
import {
  getConfig,
  updateMonitorConfig,
  updateRestartConfig,
  updateObservabilityConfig,
  exportConfig,
  importConfig
} from '../services/api';
import api from '../services/api';
import { useAlert } from '../hooks/useAlert';
import { useConfigValidation } from '../hooks/useConfigValidation';

// Component imports
import MonitorSettings from './config/MonitorSettings';
import RestartPolicySettings from './config/RestartPolicySettings';
import ObservabilitySettings from './config/ObservabilitySettings';
import ConfigImportExport from './config/ConfigImportExport';
import UptimeKumaIntegration from './config/UptimeKumaIntegration';
import ValidationModal from './config/ValidationModal';
import DisableUptimeKumaModal from './config/DisableUptimeKumaModal';
import DeleteMappingModal from './config/DeleteMappingModal';

/**
 * ConfigPage Component
 * Main configuration page that orchestrates all configuration sections
 * Following SOLID principles:
 * - Single Responsibility: Each component handles one specific configuration area
 * - Open/Closed: Components can be extended without modifying existing code
 * - Liskov Substitution: Components can be replaced with compatible implementations
 * - Interface Segregation: Each component has minimal, focused props interface
 * - Dependency Inversion: Components depend on abstractions (callbacks) not implementations
 */
function ConfigPage() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInfoAlert, setShowInfoAlert] = useState(true);
  const [validationModal, setValidationModal] = useState({
    show: false,
    title: '',
    message: '',
    errors: [],
    suggestions: []
  });
  const [showDisableConfirmModal, setShowDisableConfirmModal] = useState(false);
  const [deleteMappingModal, setDeleteMappingModal] = useState({
    show: false,
    containerId: null,
    containerName: ''
  });

  // Uptime Kuma states
  const [monitors, setMonitors] = useState([]);
  const [containers, setContainers] = useState([]);
  const [mappings, setMappings] = useState([]);

  // Custom hooks
  const { alert, showAlert, clearAlert } = useAlert();
  const { validateTimingConfiguration } = useConfigValidation(config || {});

  // Fetch configuration on mount
  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await getConfig();
      setConfig(response.data);

      // Load Uptime Kuma data if enabled
      if (response.data.uptime_kuma?.enabled) {
        loadUptimeKumaData();
      }
    } catch (error) {
      showAlert('danger', 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const loadUptimeKumaData = async () => {
    try {
      const [monitorsRes, mappingsRes, containersRes] = await Promise.all([
        api.get('/uptime-kuma/monitors'),
        api.get('/uptime-kuma/mappings'),
        api.get('/containers')
      ]);

      setMonitors(monitorsRes.data.monitors || []);
      setMappings(mappingsRes.data.mappings || []);
      setContainers(containersRes.data || []);
    } catch (error) {
      console.error('Failed to load Uptime Kuma data:', error);
    }
  };

  // Monitor Settings Handlers
  const handleMonitorConfigChange = (newMonitorConfig) => {
    setConfig({ ...config, monitor: newMonitorConfig });
  };

  const handleMonitorConfigSubmit = async () => {
    const validation = validateTimingConfiguration();
    if (!validation.isValid) {
      setValidationModal({
        show: true,
        title: 'Invalid Monitor Settings Configuration',
        message: 'The monitoring interval conflicts with your restart policy settings:',
        errors: validation.errors,
        suggestions: validation.suggestions
      });
      return;
    }

    try {
      await updateMonitorConfig(config.monitor);
      showAlert('success', 'Monitor configuration updated');
      fetchConfig();
    } catch (error) {
      showAlert('danger', 'Failed to update monitor configuration');
    }
  };

  // Restart Policy Handlers
  const handleRestartConfigChange = (newRestartConfig) => {
    setConfig({ ...config, restart: newRestartConfig });
  };

  const handleRestartConfigSubmit = async () => {
    const validation = validateTimingConfiguration();
    if (!validation.isValid) {
      setValidationModal({
        show: true,
        title: 'Invalid Restart Policy Configuration',
        message: 'The restart policy settings conflict with your monitoring configuration:',
        errors: validation.errors,
        suggestions: validation.suggestions
      });
      return;
    }

    try {
      await updateRestartConfig(config.restart);
      showAlert('success', 'Restart policy updated');
      fetchConfig();
    } catch (error) {
      showAlert('danger', 'Failed to update restart policy');
    }
  };

  // Observability Handlers
  const handleObservabilityConfigChange = (newObservabilityConfig) => {
    setConfig({ ...config, observability: newObservabilityConfig });
  };

  const handleObservabilityConfigSubmit = async () => {
    try {
      await updateObservabilityConfig(config.observability);
      showAlert('success', `Settings Saved Successfully! Log level changed to ${config.observability.log_level}. Changes are now active.`);
      fetchConfig();
    } catch (error) {
      showAlert('danger', 'Failed to update observability settings. Please try again.');
    }
  };

  // Import/Export Handlers
  const handleExportConfig = async () => {
    try {
      const response = await exportConfig();
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autoheal-config-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showAlert('success', 'Configuration exported successfully');
    } catch (error) {
      showAlert('danger', 'Failed to export configuration');
    }
  };

  const handleImportConfig = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      await importConfig(file);
      showAlert('success', 'Configuration imported successfully');
      fetchConfig();
      e.target.value = '';
    } catch (error) {
      showAlert('danger', 'Failed to import configuration');
    }
  };

  // Uptime Kuma Handlers
  const handleUptimeKumaConfigChange = (newUptimeKumaConfig) => {
    setConfig({ ...config, uptime_kuma: newUptimeKumaConfig });
  };

  const handleTestUptimeKumaConnection = async () => {
    try {
      const response = await api.post('/uptime-kuma/test-connection', {
        server_url: config.uptime_kuma.server_url,
        api_token: config.uptime_kuma.api_token,
        username: config.uptime_kuma.username || ''
      });

      if (response.data.success) {
        showAlert('success', `Connection successful! Found ${response.data.monitor_count} monitors.`);
        return true;
      } else {
        showAlert('danger', `${response.data.message}`);
        return false;
      }
    } catch (error) {
      showAlert('danger', `Connection failed: ${error.message}`);
      return false;
    }
  };

  const handleEnableUptimeKuma = async () => {
    try {
      const response = await api.post('/uptime-kuma/enable', {
        server_url: config.uptime_kuma.server_url,
        api_token: config.uptime_kuma.api_token,
        username: config.uptime_kuma.username || '',
        auto_restart_on_down: config.uptime_kuma.auto_restart_on_down
      });

      if (response.data.success) {
        setMonitors(response.data.monitors);
        setMappings(response.data.auto_mappings);
        showAlert('success', `Integration enabled! ${response.data.auto_mappings.length} auto-mappings created.`);
        fetchConfig();
      } else {
        showAlert('danger', `${response.data.message}`);
      }
    } catch (error) {
      showAlert('danger', `Failed to enable integration: ${error.message}`);
    }
  };

  const handleDisableUptimeKuma = () => {
    setShowDisableConfirmModal(true);
  };

  const confirmDisableUptimeKuma = async () => {
    setShowDisableConfirmModal(false);

    try {
      await api.post('/uptime-kuma/disable');
      setMonitors([]);
      setMappings([]);
      showAlert('success', 'Integration disabled successfully');
      fetchConfig();
    } catch (error) {
      showAlert('danger', `Failed to disable integration: ${error.message}`);
    }
  };

  const handleAddMapping = async (mapping) => {
    if (!mapping.container_id || !mapping.monitor_friendly_name) {
      showAlert('danger', 'Please select both container and monitor');
      return;
    }

    try {
      await api.post('/uptime-kuma/mappings', mapping);
      loadUptimeKumaData();
      showAlert('success', 'Mapping added successfully!');
    } catch (error) {
      showAlert('danger', `Failed to add mapping: ${error.message}`);
    }
  };

  const handleDeleteMapping = (containerId) => {
    const container = containers.find(c => c.id === containerId || c.id.startsWith(containerId));
    const containerName = container ? container.name : containerId;
    setDeleteMappingModal({ show: true, containerId, containerName });
  };

  const confirmDeleteMapping = async () => {
    const { containerId } = deleteMappingModal;
    setDeleteMappingModal({ show: false, containerId: null, containerName: '' });

    try {
      await api.delete(`/uptime-kuma/mappings/${containerId}`);
      loadUptimeKumaData();
      showAlert('success', 'Mapping deleted!');
    } catch (error) {
      showAlert('danger', `Failed to delete mapping: ${error.message}`);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <div className="mt-2">Loading configuration...</div>
      </div>
    );
  }

  // Error state
  if (!config) {
    return <Alert variant="danger">Failed to load configuration</Alert>;
  }

  return (
    <>
      {/* Info Banner */}
      {showInfoAlert && (
        <div
          className="d-flex align-items-center justify-content-between px-3 py-2 text-white mb-4"
          style={{
            backgroundColor: '#dc3545',
            fontSize: '0.875rem',
            borderRadius: '0.375rem'
          }}
        >
          <div className="d-flex align-items-center">
            <i className="bi bi-info-circle-fill me-2"></i>
            <span><strong>Note:</strong> Configuration is stored in memory. Export regularly to backup your settings.</span>
          </div>
          <button
            type="button"
            onClick={() => setShowInfoAlert(false)}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '0 0.5rem',
              lineHeight: '1'
            }}
            aria-label="Close"
          >
            ×
          </button>
        </div>
      )}

      {/* Alert */}
      {alert && (
        <Alert
          variant={alert.variant}
          dismissible
          onClose={clearAlert}
          className="mb-4 d-flex align-items-center"
          style={{ fontSize: '1.1rem', fontWeight: '500' }}
        >
          {alert.variant === 'success' && <i className="bi bi-check-circle-fill me-2 fs-4"></i>}
          {alert.variant === 'danger' && <i className="bi bi-exclamation-circle-fill me-2 fs-4"></i>}
          <span>{alert.message}</span>
        </Alert>
      )}

      {/* Configuration Cards */}
      <Row className="g-4 align-items-start">
        {/* Monitor Settings */}
        <Col md={6}>
          <MonitorSettings
            config={config.monitor}
            onConfigChange={handleMonitorConfigChange}
            onSubmit={handleMonitorConfigSubmit}
          />
        </Col>

        {/* Restart Policy */}
        <Col md={6}>
          <RestartPolicySettings
            config={config.restart}
            onConfigChange={handleRestartConfigChange}
            onSubmit={handleRestartConfigSubmit}
          />
        </Col>

        {/* Observability Settings */}
        <Col md={6}>
          <ObservabilitySettings
            config={config.observability}
            onConfigChange={handleObservabilityConfigChange}
            onSubmit={handleObservabilityConfigSubmit}
          />
        </Col>

        {/* Export/Import */}
        <Col md={6}>
          <ConfigImportExport
            onExport={handleExportConfig}
            onImport={handleImportConfig}
          />
        </Col>

        {/* Uptime Kuma Integration */}
        <Col md={6}>
          <UptimeKumaIntegration
            config={config.uptime_kuma}
            monitors={monitors}
            containers={containers}
            mappings={mappings}
            onConfigChange={handleUptimeKumaConfigChange}
            onTestConnection={handleTestUptimeKumaConnection}
            onEnableIntegration={handleEnableUptimeKuma}
            onDisableIntegration={handleDisableUptimeKuma}
            onAddMapping={handleAddMapping}
            onDeleteMapping={handleDeleteMapping}
            onShowDisableModal={handleDisableUptimeKuma}
          />
        </Col>
      </Row>

      {/* Modals */}
      <ValidationModal
        show={validationModal.show}
        title={validationModal.title}
        message={validationModal.message}
        errors={validationModal.errors}
        suggestions={validationModal.suggestions}
        config={config}
        onHide={() => setValidationModal({ show: false, title: '', message: '', errors: [], suggestions: [] })}
      />

      <DisableUptimeKumaModal
        show={showDisableConfirmModal}
        onHide={() => setShowDisableConfirmModal(false)}
        onConfirm={confirmDisableUptimeKuma}
      />

      <DeleteMappingModal
        show={deleteMappingModal.show}
        containerName={deleteMappingModal.containerName}
        onHide={() => setDeleteMappingModal({ show: false, containerId: null, containerName: '' })}
        onConfirm={confirmDeleteMapping}
      />
    </>
  );
}

export default ConfigPage;

