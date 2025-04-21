# app/models/product.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates, joinedload
from sqlalchemy import event, text


class ConcurrencyError(Exception):
    """Raised when a concurrent update is detected."""
    pass


class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registry_number = db.Column(db.String(50), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False)
    minimum_quantity = db.Column(db.Integer, default=0)
    location_type = db.Column(db.String(20), nullable=False)
    location_number = db.Column(db.String(20))
    location_position = db.Column(db.String(10))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Replace manual version_id with SQLAlchemy's version_id_col
    __mapper_args__ = {
        'version_id_col': db.Column(
            'version_id',
            db.Integer,
            nullable=False,
            default=0
        )
    }

    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint(
            'registry_number',
            'lab_id',
            name='unique_registry_per_lab'
        ),
    )

    @validates('registry_number')
    def validate_registry_number(self, key, value):
        if not value:
            raise ValueError("Registry number cannot be empty")
        return value.strip()

    @validates('quantity')
    def validate_quantity(self, key, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Quantity must be a whole number")
        if value < 0:
            raise ValueError("Quantity cannot be negative")
        return value

    @validates('minimum_quantity')
    def validate_minimum_quantity(self, key, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Minimum quantity must be a whole number")
        if value < 0:
            raise ValueError("Minimum quantity cannot be negative")
        return value

    @validates('location_type')
    def validate_location_type(self, key, value):
        if value not in ['workspace', 'cabinet']:
            raise ValueError("Invalid location type")
        return value

    def update_record(self, data: dict):
        """Update product record with optimistic locking."""
        if (
            hasattr(self, 'version_id') and
            data.get('version_id') != self.version_id
        ):
            raise ConcurrencyError("Product was modified by another user.")
        
        for key, value in data.items():
            if hasattr(self, key) and key != 'version_id':
                setattr(self, key, value)

    def get_location_display(self):
        """Get human-readable location string."""
        if self.location_type == 'workspace':
            return "Workspace"
        
        if self.location_type == 'cabinet':
            location = f"Cabinet {self.location_number or ''}"
            if self.location_position:
                location += f", Position {self.location_position}"
            return location
        
        return "Unknown"

    def check_stock_level(self):
        """Check current stock level status."""
        if self.quantity <= 0:
            return 'out'
        if self.quantity <= self.minimum_quantity:
            return 'low'
        return 'ok'

    @classmethod
    def search(cls, query, lab_id=None, page=1, per_page=20):
        """Search products by name or registry number."""
        base_query = cls.query
        if lab_id:
            base_query = base_query.filter_by(lab_id=lab_id)

        search = f"%{query}%"
        return base_query.filter(
            db.or_(
                cls.name.ilike(search),
                cls.registry_number.ilike(search)
            )
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def get_category_from_name(name):
        """Extract category from product name."""
        if not name:
            return "Uncategorized"
        
        parts = name.split()
        if len(parts) > 1:
            return parts[0].title()
        return "Uncategorized"

    @classmethod
    def get_sorted_products(cls, lab_id):
        """Get products sorted by location, category, and name."""
        products = cls.query.filter_by(lab_id=lab_id)\
            .options(joinedload(cls.lab))\
            .order_by(
                text("CASE WHEN location_type = 'workspace' THEN 0 ELSE 1 END"),
                cls.location_number.nullslast(),
                cls.location_position.nullslast(),
                cls.name
            ).all()
        
        location_groups = {}
        for product in products:
            location_key = (
                product.location_type,
                product.location_number or '',
                product.location_position or ''
            )
            if location_key not in location_groups:
                location_groups[location_key] = []
            location_groups[location_key].append(product)
        
        sorted_locations = sorted(location_groups.keys(), key=lambda x: (
            0 if x[0] == 'workspace' else 1,
            x[1],
            x[2]
        ))
        
        result = []
        for location in sorted_locations:
            products = location_groups[location]
            category_groups = {}
            
            for product in products:
                category = cls.get_category_from_name(product.name)
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(product)
            
            # Sort products within categories
            for products in category_groups.values():
                products.sort(key=lambda x: x.name)
            
            result.append({
                'location': location,
                'location_display': products[0].get_location_display(),
                'categories': category_groups
            })
        
        return result

    def __repr__(self):
        return f'<Product {self.registry_number}>'
