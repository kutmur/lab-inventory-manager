import pytest
from app.models import Product, Lab, User
from app.extensions import db

def test_index_page(client):
    """Test the index page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Lab Inventory Manager' in response.data

def test_login_required(client):
    """Test that protected pages require login."""
    protected_routes = [
        '/dashboard',
        '/product/add',
        '/logs',
        '/transfer'
    ]
    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302  # Redirect to login
        assert '/auth/login' in response.location

def test_admin_required(auth_client, client):
    """Test that admin-only routes are protected."""
    # First try without admin rights
    response = client.post('/product/1/delete')
    assert response.status_code == 302
    assert '/auth/login' in response.location

    # Then try with admin rights
    response = auth_client.post('/product/1/delete')
    assert response.status_code == 302
    assert 'dashboard' in response.location

def test_add_product(auth_client, app):
    """Test adding a new product."""
    with app.app_context():
        lab = Lab.query.first()
        data = {
            'name': 'New Test Product',
            'registry_number': 'TEST123',
            'quantity': '10',
            'unit': 'Adet',
            'minimum_quantity': '5',
            'location_number': 'workspace',
            'lab_id': str(lab.id),
            'notes': 'Test notes'
        }
        response = auth_client.post('/product/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'successfully added' in response.data

        # Verify product was added to database
        product = Product.query.filter_by(registry_number='TEST123').first()
        assert product is not None
        assert product.name == 'New Test Product'
        assert product.quantity == 10

def test_edit_product(auth_client, app):
    """Test editing an existing product."""
    with app.app_context():
        product = Product.query.first()
        data = {
            'name': product.name,
            'registry_number': product.registry_number,
            'quantity': '15',  # Changed quantity
            'unit': product.unit,
            'minimum_quantity': str(product.minimum_quantity),
            'location_number': 'workspace',
            'lab_id': str(product.lab_id),
            'notes': 'Updated notes'
        }
        response = auth_client.post(f'/product/{product.id}/edit', 
                                  data=data, 
                                  follow_redirects=True)
        assert response.status_code == 200
        assert b'updated successfully' in response.data

        # Verify changes in database
        updated = Product.query.get(product.id)
        assert updated.quantity == 15
        assert updated.notes == 'Updated notes'

def test_transfer_product(auth_client, app):
    """Test transferring product between labs."""
    with app.app_context():
        # Create second lab for transfer
        lab2 = Lab(
            code='TEST-LAB2',
            name='Test Laboratory 2',
            description='Second Test Lab'
        )
        db.session.add(lab2)
        db.session.commit()

        product = Product.query.first()
        original_quantity = product.quantity
        transfer_quantity = 2

        data = {
            'destination_lab_id': str(lab2.id),
            'quantity': str(transfer_quantity),
            'notes': 'Test transfer'
        }
        response = auth_client.post(f'/product/{product.id}/transfer',
                                  data=data,
                                  follow_redirects=True)
        assert response.status_code == 200
        assert b'transferred successfully' in response.data

        # Verify source product quantity decreased
        source_product = Product.query.get(product.id)
        assert source_product.quantity == original_quantity - transfer_quantity

        # Verify destination product was created
        dest_product = Product.query.filter_by(
            registry_number=product.registry_number,
            lab_id=lab2.id
        ).first()
        assert dest_product is not None
        assert dest_product.quantity == transfer_quantity

def test_export_lab(auth_client, app):
    """Test exporting lab inventory."""
    formats = ['xlsx', 'pdf', 'docx']
    with app.app_context():
        lab = Lab.query.first()
        for format in formats:
            response = auth_client.get(f'/export/{lab.code}/{format}')
            assert response.status_code == 200
            assert 'attachment' in response.headers['Content-Disposition']
            assert format in response.headers['Content-Type']

def test_search_products(auth_client, app):
    """Test product search functionality."""
    with app.app_context():
        # Search by name
        response = auth_client.get('/search?q=Test')
        assert response.status_code == 200
        assert b'Test Product' in response.data

        # Search by registry number
        response = auth_client.get('/search?q=TEST001')
        assert response.status_code == 200
        assert b'TEST001' in response.data

        # Search with lab filter
        lab = Lab.query.first()
        response = auth_client.get(f'/search?q=Test&lab={lab.code}')
        assert response.status_code == 200
        assert lab.code.encode() in response.data