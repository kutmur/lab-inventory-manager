import pytest
from app.models import Product, Lab, User, TransferLog, UserLog
from app.extensions import db

def test_product_validation(app):
    with app.app_context():
        # Test quantity validation
        with pytest.raises(ValueError, match="Quantity must be a whole number"):
            Product(
                name="Test",
                registry_number="TEST002",
                quantity=1.5,  # Should be integer
                unit="Adet",
                minimum_quantity=1,
                location_type="workspace",
                lab_id=1
            )

        # Test negative quantity
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            Product(
                name="Test",
                registry_number="TEST002",
                quantity=-1,
                unit="Adet",
                minimum_quantity=1,
                location_type="workspace",
                lab_id=1
            )

        # Test location type validation
        with pytest.raises(ValueError, match="Invalid location type"):
            Product(
                name="Test",
                registry_number="TEST002",
                quantity=1,
                unit="Adet",
                minimum_quantity=1,
                location_type="invalid",
                lab_id=1
            )

def test_product_unique_registry(app):
    with app.app_context():
        # First product
        p1 = Product(
            name="Test 1",
            registry_number="UNIQUE001",
            quantity=1,
            unit="Adet",
            minimum_quantity=1,
            location_type="workspace",
            lab_id=1
        )
        db.session.add(p1)
        db.session.commit()

        # Second product with same registry in same lab should fail
        p2 = Product(
            name="Test 2",
            registry_number="UNIQUE001",  # Same registry number
            quantity=1,
            unit="Adet",
            minimum_quantity=1,
            location_type="workspace",
            lab_id=1  # Same lab
        )
        db.session.add(p2)
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()
        db.session.rollback()

def test_user_roles(app):
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        editor = User.query.filter_by(username='editor').first()

        assert admin.is_admin() is True
        assert admin.is_editor() is True
        assert editor.is_admin() is False
        assert editor.is_editor() is True

def test_lab_code_generation(app):
    with app.app_context():
        lab = Lab(
            name="New Lab",
            description="Test Description"
        )
        db.session.add(lab)
        db.session.commit()

        assert lab.code is not None
        assert len(lab.code) > 0

def test_product_stock_level(app):
    with app.app_context():
        product = Product.query.first()
        
        # Test normal stock
        product.quantity = 20
        product.minimum_quantity = 5
        assert product.check_stock_level() == 'ok'
        
        # Test low stock
        product.quantity = 5
        assert product.check_stock_level() == 'low'
        
        # Test out of stock
        product.quantity = 0
        assert product.check_stock_level() == 'out'

def test_product_location_display(app):
    with app.app_context():
        # Test workspace location
        workspace_product = Product(
            name="Workspace Item",
            registry_number="WS001",
            quantity=1,
            unit="Adet",
            minimum_quantity=1,
            location_type="workspace",
            lab_id=1
        )
        assert workspace_product.get_location_display() == "Çalışma Alanı"

        # Test cabinet location
        cabinet_product = Product(
            name="Cabinet Item",
            registry_number="CAB001",
            quantity=1,
            unit="Adet",
            minimum_quantity=1,
            location_type="cabinet",
            location_number="1",
            location_position="upper",
            lab_id=1
        )
        assert cabinet_product.get_location_display() == "Dolap No: 1 - Üst"