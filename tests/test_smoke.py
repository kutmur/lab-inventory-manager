import pytest
from app.models import User, Product, Lab, UserLog
from app.extensions import db
from flask import url_for

def test_login_smoke(client):
    """Test basic login functionality."""
    response = client.get('/login')
    assert response.status_code == 200
    
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin',
        'remember_me': False
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_add_product_smoke(auth_client, app):
    """Smoke test for adding a product."""
    with app.app_context():
        # Get a lab
        lab = Lab.query.first()
        
        # Create product data
        data = {
            'name': 'Smoke Test Product',
            'registry_number': 'SMOKE001',
            'quantity': '10', 
            'unit': 'Adet',
            'minimum_quantity': '2',
            'location': 'workspace',
            'lab_id': str(lab.id),
            'notes': 'Smoke test notes'
        }
        
        # Initial log count
        initial_log_count = UserLog.query.count()
        
        # Add the product
        response = auth_client.post(
            url_for('main.add_product', lab=lab.code), 
            data=data, 
            follow_redirects=True
        )
        
        # Verify success
        assert response.status_code == 200
        assert b'Product added successfully' in response.data
        
        # Verify product was added
        product = Product.query.filter_by(registry_number='SMOKE001').first()
        assert product is not None
        assert product.name == 'Smoke Test Product'
        assert product.quantity == 10
        
        # Verify log was created
        assert UserLog.query.count() == initial_log_count + 1
        log = UserLog.query.order_by(UserLog.id.desc()).first()
        assert log.action_type == 'add'
        assert log.product_id == product.id
        assert log.lab_id == lab.id

def test_transfer_product_smoke(auth_client, app):
    """Smoke test for transferring a product between labs."""
    with app.app_context():
        # Get source lab and create a product
        source_lab = Lab.query.first()
        dest_lab = Lab.query.filter(Lab.id != source_lab.id).first()
        
        # Make sure we have at least two labs
        if not dest_lab:
            # Create a second lab if none exists
            dest_lab = Lab(
                code='TEST-LAB2',
                name='Test Lab 2',
                description='Test Description'
            )
            db.session.add(dest_lab)
            db.session.commit()
            
        # Create a product for transfer
        product = Product(
            name='Transfer Test Product',
            registry_number='TRANSFER001',
            quantity=20,
            unit='Adet',
            minimum_quantity=5,
            location_type='workspace',
            lab_id=source_lab.id
        )
        db.session.add(product)
        db.session.commit()
        
        # Initial log count
        initial_log_count = UserLog.query.count()
        
        # Transfer data
        transfer_data = {
            'destination_lab_id': str(dest_lab.id),
            'quantity': '5',
            'notes': 'Transfer smoke test'
        }
        
        # Perform the transfer
        response = auth_client.post(
            url_for('main.transfer_product', product_id=product.id),
            data=transfer_data,
            follow_redirects=True
        )
        
        # Verify success
        assert response.status_code == 200
        assert b'Product transferred successfully' in response.data
        
        # Verify source product updated
        source_product = Product.query.get(product.id)
        assert source_product.quantity == 15
        
        # Verify destination product created or updated
        dest_product = Product.query.filter_by(
            registry_number='TRANSFER001',
            lab_id=dest_lab.id
        ).first()
        assert dest_product is not None
        assert dest_product.quantity == 5
        
        # Verify logs were created (one for source, one for destination)
        assert UserLog.query.count() >= initial_log_count + 2
        source_log = UserLog.query.filter_by(
            action_type='transfer',
            product_id=source_product.id,
            lab_id=source_lab.id
        ).order_by(UserLog.id.desc()).first()
        assert source_log is not None
        assert source_log.quantity == -5