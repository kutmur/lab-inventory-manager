# app/__init__.py

from flask import Flask, jsonify
from config import Config, ProductionConfig
from app.extensions import db, login_manager, socketio, migrate, limiter
from app.models import User, Product
from flask_migrate import upgrade
import os
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Force production config if FLASK_ENV is production
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
        
        # Production logging setup
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/lab_inventory.log',
                                             maxBytes=10240000,
                                             backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Lab Inventory Manager startup')

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    
    # Initialize SocketIO with proper message queue in production
    socketio.init_app(
        app,
        message_queue=app.config.get('REDIS_URL') if app.config.get('FLASK_ENV') == 'production' else None,
        async_mode='eventlet'
    )
    
    # Initialize rate limiter with proper storage
    limiter.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'

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

    # Register CLI commands
    from app.cli import init_cli
    init_cli(app)

    with app.app_context():
        if app.config.get('FLASK_ENV') == 'production':
            # Run migrations in production
            upgrade()
        else:
            # Just create tables in development
            db.create_all()
            
        # Ensure admin user exists
        if not User.query.filter_by(username=app.config['ADMIN_USERNAME']).first():
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                email=app.config['ADMIN_EMAIL'],
                role='admin'
            )
            if app.config['ADMIN_PASSWORD']:
                admin.set_password(app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        app.logger.error(f'Database error occurred: {str(error)}')
        if isinstance(error, OperationalError):
            return jsonify({'error': 'Database connection error. Please try again later.'}), 503
        elif isinstance(error, DisconnectionError):
            db.session.remove()  # Clean up the session
            return jsonify({'error': 'Lost connection to database. Please refresh the page.'}), 500
        return jsonify({'error': 'An unexpected database error occurred.'}), 500

    @app.teardown_appcontext
    def cleanup(resp_or_exc):
        """Ensure proper cleanup of database sessions"""
        db.session.remove()

    return app
