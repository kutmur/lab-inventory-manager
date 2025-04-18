# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()

def init_app(app):
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
