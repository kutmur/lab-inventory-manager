# app/models/lab.py

from app.extensions import db
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    max_cabinets = db.Column(db.Integer, nullable=False, default=8)

    products = db.relationship('Product', backref='lab', lazy='dynamic')

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
        for code,name,desc,maxc in cls.PREDEFINED_LABS:
            lab = cls.query.filter_by(code=code).first()
            if not lab:
                lab = cls(code=code, name=name, description=desc, max_cabinets=maxc)
                db.session.add(lab)
        db.session.commit()
        return cls.query.filter(cls.code.in_([c for c,_,_,_ in cls.PREDEFINED_LABS])).all()

@event.listens_for(Lab, 'before_insert')
def validate_lab_code(mapper, connection, target):
    if not target.code:
        raise IntegrityError("Lab code cannot be empty", None, None)
