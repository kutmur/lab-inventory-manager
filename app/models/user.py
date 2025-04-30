from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User model representing application users.
    
    Inherits from:
        UserMixin: Provides default implementations for Flask-Login interface
        db.Model: SQLAlchemy model base class
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(
        db.String(20),
        nullable=False,
        default='user'
    )  # admin, editor, user
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Kullanıcı logları: UserLog modeline backref 'log_owner' eklendi
    logs = db.relationship('UserLog', backref=db.backref('log_owner', lazy='joined'), lazy='dynamic')

    def set_password(self, password):
        """Set user's password hash from plain text password.
        
        Args:
            password: Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if plain text password matches hash.
        
        Args:
            password: Plain text password to verify
        
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role.
        
        Returns:
            bool: True if user is admin, False otherwise
        """
        return self.role == 'admin'

    def is_editor(self):
        """Check if user has editor role.
        
        Returns:
            bool: True if user is editor or admin, False otherwise
        """
        return self.role in ['editor', 'admin']

    def update_last_login(self):
        """Update user's last login timestamp to current time."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        """Get string representation of User.
        
        Returns:
            str: User representation with username
        """
        return f'<User {self.username}>'