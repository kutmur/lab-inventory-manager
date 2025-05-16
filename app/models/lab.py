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

    # Hard-coded labs as specified in requirements
    PREDEFINED_LABS = [
        ("1", "Elektrik Makineler", "Elektrik Makineler Laboratuvarı", 8),
        ("2", "Güç Elektroniği", "Güç Elektroniği Laboratuvarı", 8),
        ("3", "Otomatik Kontrol", "Otomatik Kontrol Laboratuvarı", 8),
        ("4", "Yapay Zeka ve İleri Sinyal", "Yapay Zeka ve İleri Sinyal Laboratuvarı", 8),
        ("5", "Mikroişlemci", "Mikroişlemci Laboratuvarı", 8),
        ("6", "Haberleşme ve Mikrodalga", "Haberleşme ve Mikrodalga Laboratuvarı", 8),
        ("7", "Temel Elektrik-Elektronik", "Temel Elektrik-Elektronik Laboratuvarı", 8),
    ]

    @classmethod
    def get_predefined_labs(cls):
        """Create predefined labs if they don't exist."""
        for code, name, desc, maxc in cls.PREDEFINED_LABS:
            lab = cls.query.filter_by(code=code).first()
            if not lab:
                lab = cls(
                    code=code,
                    name=name,
                    description=desc,
                    location=f"Room {code}",
                    max_cabinets=maxc
                )
                db.session.add(lab)
        db.session.commit()
        return cls.query.filter(
            cls.code.in_([c for c, _, _, _ in cls.PREDEFINED_LABS])
        ).all()

    def __repr__(self):
        return f'<Lab {self.code}>'


@event.listens_for(Lab, 'before_insert')
def validate_lab_code(mapper, connection, target):
    """Ensure lab code is unique before insert."""
    if not target.code:
        raise IntegrityError("Lab code cannot be empty", None, None)
    
    # Check for duplicate code
    if Lab.query.filter_by(code=target.code).first():
        raise IntegrityError(
            f"Lab with code {target.code} already exists",
            None,
            None
        )
