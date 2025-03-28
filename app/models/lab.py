from app.extensions import db
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    max_cabinets = db.Column(db.Integer, nullable=False, default=8)  # Default to 8 cabinets
    
    # Relationships
    products = db.relationship('Product', backref='lab', lazy='dynamic')
    transfers_source = db.relationship('TransferLog', backref='source_lab',
                                     foreign_keys='TransferLog.source_lab_id', lazy='dynamic')
    transfers_destination = db.relationship('TransferLog', backref='destination_lab',
                                          foreign_keys='TransferLog.destination_lab_id', lazy='dynamic')

    # Predefined lab codes with their max cabinets
    PREDEFINED_LABS = [
        ('EEMLAB01-361', 'EEMLAB01-361', 'Laboratory 1', 8),
        ('EEMLAB02-363', 'EEMLAB02-363', 'Laboratory 2', 8),
        ('EEMLAB03-365', 'EEMLAB03-365', 'Laboratory 3', 8),
        ('EEMLAB04-367', 'EEMLAB04-367', 'Laboratory 4', 8),
        ('EEMLAB05-369', 'EEMLAB05-369', 'Laboratory 5', 8),
        ('EEMLAB06-371', 'EEMLAB06-371', 'Laboratory 6', 8),
        ('EEMLAB07-373', 'EEMLAB07-373', 'Laboratory 7', 8),
    ]

    @classmethod
    def get_predefined_labs(cls):
        """Get all predefined labs, creating them if they don't exist."""
        for code, name, description, max_cabinets in cls.PREDEFINED_LABS:
            lab = cls.query.filter_by(code=code).first()
            if not lab:
                lab = cls(code=code, name=name, description=description, max_cabinets=max_cabinets)
                db.session.add(lab)
        db.session.commit()
        return cls.query.filter(cls.code.in_([code for code, _, _, _ in cls.PREDEFINED_LABS])).all()

    def get_cabinet_choices(self):
        """Get all cabinet choices for this lab."""
        choices = []
        for cabinet_num in range(1, self.max_cabinets + 1):
            choices.extend([
                (f"{cabinet_num}-upper", f"Dolap No: {cabinet_num} - Üst"),
                (f"{cabinet_num}-lower", f"Dolap No: {cabinet_num} - Alt")
            ])
        return choices

    def __init__(self, **kwargs):
        if 'code' not in kwargs:
            raise ValueError("Lab code is required")
        super(Lab, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Lab {self.code} - {self.name}>'

# Add validation event listener
@event.listens_for(Lab, 'before_insert')
def validate_lab_code(mapper, connection, target):
    if not target.code:
        raise IntegrityError("Lab code cannot be empty", None, None) 