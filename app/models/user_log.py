# File: app/models/user_log.py
from datetime import datetime
from app.extensions import db

class UserLog(db.Model):
    """Kullanıcı aksiyonlarının log tablosu"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # add, edit, delete, transfer
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'))
    quantity = db.Column(db.Float)  # Miktar değişimi (+/-)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notification_sent = db.Column(db.Boolean, default=False)  # Bildirim gönderildi mi?
    notification_type = db.Column(db.String(20))  # 'stock_low', 'stock_out', etc.

    # Relationships
    product = db.relationship('Product')
    lab = db.relationship('Lab')

    def __repr__(self):
        return f'<UserLog {self.action_type} by User {self.user_id}>'
