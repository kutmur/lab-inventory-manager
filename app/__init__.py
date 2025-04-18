# app/__init__.py

from flask import Flask
from config import Config
from app.extensions import db, login_manager, socketio, migrate
from app.models import User, Product

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.context_processor
    def inject_models():
        return dict(Product=Product)

    return app
