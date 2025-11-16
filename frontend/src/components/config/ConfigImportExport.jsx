import { Card, Form, Button } from 'react-bootstrap';

/**
 * ConfigImportExport Component
 * Handles configuration export and import functionality
 *
 * @param {Object} props - Component props
 * @param {Function} props.onExport - Callback when export is triggered
 * @param {Function} props.onImport - Callback when import file is selected
 */
function ConfigImportExport({ onExport, onImport }) {
  return (
    <Card>
      <Card.Header>
        <h5 className="mb-0">
          <i className="bi bi-file-earmark-code me-2"></i>
          Configuration Export/Import
        </h5>
      </Card.Header>
      <Card.Body>
        <div className="mb-3">
          <Button
            variant="success"
            className="w-100 mb-2"
            onClick={onExport}
          >
            <i className="bi bi-download me-1"></i>
            Export Configuration
          </Button>
          <Form.Text className="d-block">
            Download current configuration as JSON file (includes Uptime Kuma settings)
          </Form.Text>
        </div>

        <div className="mb-3">
          <Form.Control
            type="file"
            accept=".json"
            onChange={onImport}
            id="importFile"
          />
          <Form.Text className="d-block mt-2">
            Upload configuration JSON file to restore all settings
          </Form.Text>
        </div>
      </Card.Body>
    </Card>
  );
}

export default ConfigImportExport;

