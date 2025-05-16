# Lab Inventory Manager

A Flask-based inventory management system designed for laboratories.

## Features

- Multi-laboratory inventory tracking with predefined laboratory locations
- Product transfers between labs with complete audit logging
- Real-time notifications via WebSocket
- Export reports in Excel, PDF, and Word formats
- Role-based access control (Admin/Editor)
- Stock level monitoring and alerts
- Comprehensive activity logging

## Laboratories

The system includes the following predefined laboratories:

| Code | Name | Description |
|------|------|-------------|
| 1 | Elektrik Makineler | Elektrik Makineler Laboratuvarı |
| 2 | Güç Elektroniği | Güç Elektroniği Laboratuvarı |
| 3 | Otomatik Kontrol | Otomatik Kontrol Laboratuvarı |
| 4 | Yapay Zeka ve İleri Sinyal | Yapay Zeka ve İleri Sinyal Laboratuvarı |
| 5 | Mikroişlemci | Mikroişlemci Laboratuvarı |
| 6 | Haberleşme ve Mikrodalga | Haberleşme ve Mikrodalga Laboratuvarı |
| 7 | Temel Elektrik-Elektronik | Temel Elektrik-Elektronik Laboratuvarı |

## Setup

### Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lab-inventory-manager.git
cd lab-inventory-manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional in development):
```bash
# Required in production, defaults provided in development
export SECRET_KEY=your-secret-key
export WTF_CSRF_SECRET_KEY=your-csrf-key

# Database URL (defaults to SQLite in development)
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis for rate limiting (optional)
export REDIS_URL=redis://localhost:6379

# Admin credentials (defaults provided in development)
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=password
export ADMIN_EMAIL=admin@example.com

# Editor credentials (optional)
export EDITOR_USERNAME=editor
export EDITOR_PASSWORD=password
export EDITOR_EMAIL=editor@example.com
```

5. Initialize the database:
```bash
flask init-db
```

6. Seed the predefined laboratories:
```bash
flask seed-labs
```

7. Run the development server:
```bash
flask run
```

### Production Deployment

1. Set all required environment variables (see above)
2. Ensure PostgreSQL or MySQL database is configured
3. Install production requirements:
```bash
pip install gunicorn eventlet
```

4. Run with gunicorn:
```bash
gunicorn --worker-class eventlet -w 1 manage:app
```

## CLI Commands

The application provides several management commands:

- `flask init-db`: Initialize fresh database tables
- `flask seed-labs`: Seed predefined laboratory data
- `flask create-admin`: Create an admin user
- `flask convert-quantities`: Convert existing float quantities to integers
- `flask update-lab-codes`: Update missing lab codes

Examples:
```bash
# Create an admin user with custom credentials
flask create-admin --username=admin --password=secure123 --email=admin@lab.com

# Initialize fresh database
flask init-db

# Seed initial lab data
flask seed-labs
```

## Testing

1. Install test dependencies:
```bash
pip install pytest pytest-cov flake8 mypy
```

2. Run tests:
```bash
# Run all tests
pytest

# Run smoke tests only
pytest tests/test_smoke.py

# Run with coverage report
pytest --cov=app tests/

# Run style checks
flake8 app tests
mypy app
```

## Documentation

- [API Documentation](docs/API.md): Socket events and export endpoints
- User documentation: Coming soon

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests to ensure no regressions
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.