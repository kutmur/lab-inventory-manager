# app/__init__.py

from flask import Flask, jsonify
from config import Config, ProductionConfig
from app.extensions import (
    db, login_manager, socketio, migrate, limiter
)
from app.models import User, Product
from flask_migrate import upgrade
import os
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import (
    SQLAlchemyError,
    OperationalError,
    DisconnectionError
)


def create_app(config_class=Config):
    """Create and configure a Flask application instance.
    
    Args:
        config_class: Configuration class to use (default: Config)
    
    Returns:
        Flask: The configured Flask application instance
    """
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
            file_handler = RotatingFileHandler(
                'logs/lab_inventory.log',
                maxBytes=10240000,
                backupCount=10
            )
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
        message_queue=(
            app.config.get('REDIS_URL')
            if app.config.get('FLASK_ENV') == 'production'
            else None
        ),
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
        """Load a user instance from the database.
        
        Args:
            user_id: User ID to load
        
        Returns:
            User: The user instance or None if not found
        """
        return User.query.get(int(user_id))

    # Register blueprints
    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.context_processor
    def inject_models():
        """Make models available in templates."""
        return dict(Product=Product)

    # Register CLI commands
    from app.cli import init_cli
    init_cli(app)

    # Initialize database based on environment
    with app.app_context():
        if app.config.get('FLASK_ENV') == 'production':
            # Run migrations in production
            upgrade()
        else:
            # Just create tables in development
            db.create_all()
            
        # Ensure admin user exists
        if not User.query.filter_by(
            username=app.config['ADMIN_USERNAME']
        ).first():
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
        """Handle database-related errors.
        
        Args:
            error: The caught SQLAlchemy error
        
        Returns:
            tuple: JSON response and HTTP status code
        """
        app.logger.error(f'Database error occurred: {str(error)}')
        if isinstance(error, OperationalError):
            return jsonify({
                'error': 'Database connection error. Please try again later.'
            }), 503
        elif isinstance(error, DisconnectionError):
            db.session.remove()  # Clean up the session
            return jsonify({
                'error': 'Lost connection to database. Please refresh the page.'
            }), 500
        return jsonify({
            'error': 'An unexpected database error occurred.'
        }), 500

    @app.teardown_appcontext
    def cleanup(resp_or_exc):
        """Ensure proper cleanup of database sessions."""
        db.session.remove()

    return app
