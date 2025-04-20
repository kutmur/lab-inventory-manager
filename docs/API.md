# Lab Inventory Manager API Documentation

## WebSocket Events

### Connection Events

- `connect`: Triggered when a client connects. Requires authentication.
- `disconnect`: Triggered when a client disconnects.
- `status`: Emitted with connection status messages.

### Inventory Update Events

- Event: `inventory_update`
- Payload:
```json
{
    "product_id": "integer",
    "action": "string (add|edit|delete|transfer)",
    "data": {
        "name": "string",
        "quantity": "integer",
        "source_lab": "integer (optional)",
        "destination_lab": "integer (optional)"
    },
    "user": "string"
}
```

### Stock Alert Events

- Event: `stock_alert`
- Payload:
```json
{
    "product_id": "integer",
    "product_name": "string",
    "lab_code": "string",
    "level": "string (low|out)",
    "quantity": "integer",
    "minimum": "integer"
}
```

## Export Endpoints

### Export Lab Inventory

- **URL**: `/export/<lab_code>/<format>`
- **Method**: GET
- **Auth Required**: Yes
- **Parameters**:
  - `lab_code`: Lab code to export (e.g., 'LAB-001')
  - `format`: Export format ('xlsx', 'pdf', 'docx')
- **Response**: File download with appropriate mimetype

### Export All Labs

- **URL**: `/export/all/<format>`
- **Method**: GET
- **Auth Required**: Yes
- **Parameters**:
  - `format`: Export format ('xlsx', 'pdf', 'docx')
- **Response**: File download with appropriate mimetype

### File Format Details

#### Excel (xlsx)
- Workbook with single sheet "Lab Inventory"
- Formatted headers with background color
- Auto-sized columns
- Data includes: Name, Registry Number, Quantity, Unit, Min Quantity, Location, Notes
- For full export: Additional Lab column

#### PDF
- Title with lab code (or "Full Inventory")
- Generation timestamp in Europe/Istanbul timezone
- Formatted table with headers
- Data includes same fields as Excel
- Professional styling with grid lines

#### Word (docx)
- Title with lab code (or "Full Inventory")
- Generation timestamp in Europe/Istanbul timezone
- Table format with headers
- Data includes same fields as Excel