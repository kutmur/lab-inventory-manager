from datetime import datetime
from app.extensions import db
from sqlalchemy import event
from sqlalchemy.orm import validates

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registry_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False)
    minimum_quantity = db.Column(db.Float, default=0)
    cabinet_number = db.Column(db.String(20), nullable=False)  # Format: "number-position" (e.g., "1-upper")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    
    # Relationships with unique backref names
    transfer_logs = db.relationship('TransferLog', backref='transferred_product')

    @validates('quantity')
    def validate_quantity(self, key, value):
        if value < 0:
            raise ValueError("Quantity cannot be negative")
        return value

    @validates('cabinet_number')
    def validate_cabinet_number(self, key, value):
        if not value or '-' not in value:
            raise ValueError("Invalid cabinet number format")
        number, position = value.split('-')
        if position not in ['upper', 'lower']:
            raise ValueError("Invalid cabinet position")
        try:
            int(number)
        except ValueError:
            raise ValueError("Cabinet number must be a number")
        return value

    def update_quantity(self, new_quantity):
        """Update quantity with optimistic locking"""
        current_version = self.version_id
        self.quantity = new_quantity
        self.version_id += 1
        try:
            db.session.commit()
        except:
            db.session.rollback()
            # Refresh the product from database
            db.session.refresh(self)
            if self.version_id != current_version:
                raise ConcurrencyError("Product was modified by another user")
            raise

    def __repr__(self):
        return f'<Product {self.registry_number}>' 

class ConcurrencyError(Exception):
    pass 