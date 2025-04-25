# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.engine.url import make_url

class CustomSQLAlchemy(SQLAlchemy):
    def get_engine(self, app=None, bind=None):
        """Override get_engine to apply database-specific options"""
        if app is None:
            app = self.get_app()
            
        if bind is None:
            uri = app.config['SQLALCHEMY_DATABASE_URI']
        else:
            uri = app.config['SQLALCHEMY_BINDS'][bind]
        
        url = make_url(uri)
        
        # Common options safe for all databases
        options = {
            'pool_pre_ping': True,
        }
        
        # Add additional options only for non-SQLite databases
        if not url.drivername.startswith('sqlite'):
            # These options are safe for PostgreSQL and MySQL
            options.update({
                'pool_size': app.config.get('SQLALCHEMY_POOL_SIZE', 10),
                'pool_recycle': app.config.get('SQLALCHEMY_POOL_RECYCLE', 300),
                'pool_timeout': app.config.get('SQLALCHEMY_POOL_TIMEOUT', 20),
                'max_overflow': app.config.get('SQLALCHEMY_MAX_OVERFLOW', 5),
            })
            
            # Database-specific connect_args
            if url.drivername.startswith('postgresql'):
                options['connect_args'] = {
                    'connect_timeout': app.config.get('SQLALCHEMY_CONNECT_TIMEOUT', 10),
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5
                }
            elif url.drivername.startswith('mysql'):
                options['connect_args'] = {
                    'connect_timeout': app.config.get('SQLALCHEMY_CONNECT_TIMEOUT', 10)
                }
        
        return self.create_engine(url, options)

# Initialize extensions
db = CustomSQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configure SocketIO with production-ready settings
socketio = SocketIO(
    cors_allowed_origins=[
        'https://*.onrender.com',  # Render domains
        'http://localhost:5000',   # Local development
        'http://127.0.0.1:5000'    # Local development
    ],
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=30,
    ping_interval=25,
    max_http_buffer_size=1000000
)

# Rate limiter with Redis support in production
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Will be overridden by RATELIMIT_STORAGE_URL in production
)

def init_app(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure SocketIO with app
    socketio.init_app(
        app,
        message_queue=app.config.get('REDIS_URL') if app.config.get('FLASK_ENV') == 'production' else None,
        async_mode='eventlet'
    )
    
    # Configure rate limiter
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
