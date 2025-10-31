import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// System Status
export const getSystemStatus = () => api.get('/status');
export const getHealth = () => axios.get('/health');

// Containers
export const getContainers = (includeStopped = false) =>
  api.get('/containers', { params: { include_stopped: includeStopped } });

export const getContainerDetails = (containerId) =>
  api.get(`/containers/${containerId}`);

export const updateContainerSelection = (containerIds, enabled) =>
  api.post('/containers/select', { container_ids: containerIds, enabled });

export const restartContainer = (containerId) =>
  api.post(`/containers/${containerId}/restart`);

export const unquarantineContainer = (containerId) =>
  api.post(`/containers/${containerId}/unquarantine`);

// Configuration
export const getConfig = () => api.get('/config');
export const updateConfig = (config) => api.put('/config', config);
export const updateMonitorConfig = (config) => api.put('/config/monitor', config);
export const updateRestartConfig = (config) => api.put('/config/restart', config);
export const exportConfig = () => api.get('/config/export');
export const importConfig = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/config/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Observability
export const updateObservabilityConfig = (observabilityConfig) => api.put('/config/observability', observabilityConfig);

// Health Checks
export const getHealthChecks = () => api.get('/healthchecks');
export const getHealthCheck = (containerId) => api.get(`/healthchecks/${containerId}`);
export const addHealthCheck = (healthCheck) => api.post('/healthchecks', healthCheck);
export const deleteHealthCheck = (containerId) => api.delete(`/healthchecks/${containerId}`);

// Events
export const getEvents = (limit = 50) => api.get('/events', { params: { limit } });
export const clearEvents = () => api.delete('/events');

// Maintenance Mode
export const enableMaintenanceMode = () => api.post('/maintenance/enable');
export const disableMaintenanceMode = () => api.post('/maintenance/disable');
export const getMaintenanceStatus = () => api.get('/maintenance/status');

export default api;

