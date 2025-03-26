from app.extensions import db

class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    
    # Relationships
    products = db.relationship('Product', backref='lab', lazy='dynamic')
    transfers_source = db.relationship('TransferLog', backref='source_lab',
                                     foreign_keys='TransferLog.source_lab_id', lazy='dynamic')
    transfers_destination = db.relationship('TransferLog', backref='destination_lab',
                                          foreign_keys='TransferLog.destination_lab_id', lazy='dynamic')

    def __repr__(self):
        return f'<Lab {self.name}>' 