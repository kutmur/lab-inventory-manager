# app/models/product.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates, joinedload
from sqlalchemy import event, text

class ConcurrencyError(Exception):
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Replace manual version_id with SQLAlchemy's version_id_col
    __mapper_args__ = {
        'version_id_col': db.Column('version_id', db.Integer, nullable=False, default=0)
    }
    
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('registry_number', 'lab_id', name='unique_registry_per_lab'),
    )

    @validates('registry_number')
    def validate_registry_number(self, key, value):
        if not value:
            raise ValueError("Registry number cannot be empty")
        # Strip any whitespace to ensure clean values
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
        if value not in ['workspace','cabinet']:
            raise ValueError("Invalid location type")
        return value

    @validates('location_position')
    def validate_location_position(self, key, value):
        if self.location_type=='cabinet' and value not in ['upper','lower', None]:
            raise ValueError("Cabinet position must be 'upper' or 'lower'")
        if self.location_type=='workspace' and value is not None:
            raise ValueError("Workspace items should not have a location_position")
        return value

    def update_record(self, data: dict):
        """
        Update product fields from a dict (like form data),
        then commit. Uses SQLAlchemy's version_id_col for concurrency.
        """
        try:
            with db.session.begin_nested():
                self.name = data.get('name', self.name)
                self.registry_number = data.get('registry_number', self.registry_number)
                self.quantity = int(data.get('quantity', self.quantity))
                self.unit = data.get('unit', self.unit)
                self.minimum_quantity = int(data.get('minimum_quantity', self.minimum_quantity))
                
                loc_value = data.get('location_number', 'workspace').split('-')
                if loc_value[0] == 'workspace':
                    self.location_type = 'workspace'
                    self.location_number = None
                    self.location_position = None
                else:
                    self.location_type = 'cabinet'
                    self.location_number = loc_value[1]
                    self.location_position = loc_value[2]
                    
                self.notes = data.get('notes', self.notes)
                db.session.flush()
        except db.exc.StaleDataError:
            raise ConcurrencyError("Product was modified by another user.")

    def get_location_display(self):
        if self.location_type=='workspace':
            return "Çalışma Alanı"
        pos_text='Üst' if self.location_position=='upper' else 'Alt'
        return f"Dolap No: {self.location_number} - {pos_text}"

    def check_stock_level(self):
        """
        Stok seviyesini kontrol eder.
        Returns: 
            - 'low' if quantity <= minimum_quantity
            - 'out' if quantity == 0
            - 'ok' otherwise
        """
        if self.quantity == 0:
            return 'out'
        elif self.quantity <= self.minimum_quantity:
            return 'low'
        return 'ok'

    @classmethod
    def search(cls, query, lab_id=None, page=1, per_page=20):
        """
        Ürün adı veya sicil numarasına göre arama yapar
        Now with pagination support
        """
        search = f"%{query}%"
        base_query = cls.query\
            .options(joinedload(cls.lab))\
            .filter(
                db.or_(
                    cls.name.ilike(search),
                    cls.registry_number.ilike(search)
                )
            )
        
        if lab_id:
            base_query = base_query.filter(cls.lab_id == lab_id)
            
        return base_query.order_by(cls.name).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def get_category_from_name(name):
        """Determine product category based on keywords in name"""
        name = name.lower()
        categories = {
            'resistor': ['resistor', 'direnc', 'resistance'],
            'capacitor': ['capacitor', 'kondansator', 'capacitance'],
            'transistor': ['transistor', 'bjt', 'mosfet', 'fet'],
            'ic': ['ic', 'integrated circuit', 'chip', 'mcu', 'microcontroller'],
            'sensor': ['sensor', 'detector', 'transducer'],
            'connector': ['connector', 'socket', 'header', 'terminal'],
            'passive': ['inductor', 'crystal', 'oscillator', 'transformer'],
            'power': ['power supply', 'battery', 'voltage regulator', 'converter'],
            'display': ['lcd', 'led', 'display', 'indicator'],
            'mechanical': ['switch', 'button', 'relay', 'enclosure', 'case', 'heatsink']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name for keyword in keywords):
                return category
        return 'other'

    @classmethod
    def get_sorted_products(cls, lab_id):
        """Get products sorted by location, category, and name using optimized SQL"""
        # Use a single query with joins to get all data
        products = cls.query.filter_by(lab_id=lab_id)\
            .options(joinedload(cls.lab))\
            .order_by(
                text("CASE WHEN location_type = 'workspace' THEN 0 ELSE 1 END"),
                cls.location_number.nullslast(),
                cls.location_position.nullslast(),
                cls.name
            ).all()
        
        # Group in memory since it's complex business logic
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
        
        # Sort locations: workspace first, then cabinets by number and position
        sorted_locations = sorted(location_groups.keys(), key=lambda x: (
            0 if x[0] == 'workspace' else 1,
            x[1],
            x[2]
        ))
        
        # Process categories within each location
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
