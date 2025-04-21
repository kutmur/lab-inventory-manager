# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.engine.url import make_url


class CustomSQLAlchemy(SQLAlchemy):
    def get_engine(self, app=None, bind=None):
        """Override get_engine to apply database-specific options.
        
        Args:
            app: Flask application instance
            bind: Bind key from config
        """
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
                'pool_size': app.config.get(
                    'SQLALCHEMY_POOL_SIZE',
                    10
                ),
                'pool_recycle': app.config.get(
                    'SQLALCHEMY_POOL_RECYCLE',
                    300
                ),
                'pool_timeout': app.config.get(
                    'SQLALCHEMY_POOL_TIMEOUT',
                    20
                ),
                'max_overflow': app.config.get(
                    'SQLALCHEMY_MAX_OVERFLOW',
                    5
                ),
            })
            
            # Database-specific connect_args
            if url.drivername.startswith('postgresql'):
                options['connect_args'] = {
                    'connect_timeout': app.config.get(
                        'SQLALCHEMY_CONNECT_TIMEOUT',
                        10
                    ),
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5
                }
            elif url.drivername.startswith('mysql'):
                options['connect_args'] = {
                    'connect_timeout': app.config.get(
                        'SQLALCHEMY_CONNECT_TIMEOUT',
                        10
                    )
                }
        
        return self.create_engine(url, options)


# Initialize Flask extensions
db = CustomSQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"  # Will be overridden in production
)


def init_app(app):
    """Initialize Flask extensions.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
