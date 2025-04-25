import os
import tempfile
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Lab, Product

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'ADMIN_USERNAME': 'admin',
        'ADMIN_PASSWORD': 'admin',
        'ADMIN_EMAIL': 'admin@test.com'
    })

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        init_test_data()

    yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """A test client that is authenticated as admin."""
    with client:
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin'
        })
        yield client

def init_test_data():
    """Initialize test data."""
    # Create test admin user
    admin = User(
        username='admin',
        email='admin@test.com',
        role='admin'
    )
    admin.set_password('admin')
    db.session.add(admin)

    # Create test editor user
    editor = User(
        username='editor',
        email='editor@test.com',
        role='editor'
    )
    editor.set_password('editor')
    db.session.add(editor)

    # Create test lab
    lab = Lab(
        code='TEST-LAB',
        name='Test Laboratory',
        description='Test Lab Description',
        location='Test Location'
    )
    db.session.add(lab)

    # Create test product
    product = Product(
        name='Test Product',
        registry_number='TEST001',
        quantity=10,
        unit='Adet',
        minimum_quantity=5,
        location_type='workspace',
        lab_id=1
    )
    db.session.add(product)

    db.session.commit()