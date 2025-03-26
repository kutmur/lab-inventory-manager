from datetime import datetime
from app.extensions import db

class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)  # add, edit, delete, transfer
    quantity = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)

    # Relationships with unique backref names
    user = db.relationship('User', backref='activity_logs')
    product = db.relationship('Product', backref='activity_logs')
    lab = db.relationship('Lab', backref='activity_logs')

    def __repr__(self):
        return f'<UserLog {self.action_type} - {self.timestamp}>' 