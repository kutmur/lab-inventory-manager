from datetime import datetime
from app.extensions import db

class TransferLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
    
    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    source_lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    destination_lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<TransferLog {self.id} - {self.timestamp}>' 