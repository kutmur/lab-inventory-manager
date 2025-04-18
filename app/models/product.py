# app/models/product.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import validates

class ConcurrencyError(Exception):
    pass

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registry_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False)
    minimum_quantity = db.Column(db.Float, default=0)
    location_type = db.Column(db.String(20), nullable=False)
    location_number = db.Column(db.String(20))
    location_position = db.Column(db.String(10))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    version_id = db.Column(db.Integer, nullable=False, default=0)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)

    @validates('quantity')
    def validate_quantity(self, key, value):
        if value<0:
            raise ValueError("Quantity cannot be negative")
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
        then commit. Also increment version for concurrency check.
        """
        self.name = data.get('name', self.name)
        self.registry_number = data.get('registry_number', self.registry_number)
        self.quantity = float(data.get('quantity', self.quantity))
        self.unit = data.get('unit', self.unit)
        self.minimum_quantity = float(data.get('minimum_quantity', self.minimum_quantity))
        loc_value = data.get('location_number', 'workspace').split('-')
        if loc_value[0]=='workspace':
            self.location_type='workspace'
            self.location_number=None
            self.location_position=None
        else:
            self.location_type='cabinet'
            self.location_number=loc_value[1]
            self.location_position=loc_value[2]
        self.notes = data.get('notes', self.notes)
        # concurrency
        old_version = self.version_id
        self.version_id += 1
        try:
            db.session.commit()
        except:
            db.session.rollback()
            db.session.refresh(self)
            if self.version_id!=old_version+1:
                raise ConcurrencyError("Product was modified by another user.")
            raise

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
    def search(cls, query, lab_id=None):
        """
        Ürün adı veya sicil numarasına göre arama yapar
        """
        search = f"%{query}%"
        base_query = cls.query.filter(
            db.or_(
                cls.name.ilike(search),
                cls.registry_number.ilike(search)
            )
        )
        
        if lab_id:
            base_query = base_query.filter(cls.lab_id == lab_id)
            
        return base_query.order_by(cls.name).all()

    def __repr__(self):
        return f'<Product {self.registry_number}>'
