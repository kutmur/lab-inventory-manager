import os
from dotenv import load_dotenv
import secrets
from urllib.parse import urlparse

basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file, fallback to .env.development
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '.env.development')
load_dotenv(env_path)


class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY must be set in production")
        SECRET_KEY = 'dev-secret-key'

    # Fix Render's DATABASE_URL if needed
    SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')
    if (SQLALCHEMY_DATABASE_URL and
            SQLALCHEMY_DATABASE_URL.startswith('postgres://')):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            'postgres://',
            'postgresql://',
            1
        )
    
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URL or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Secure cookie settings
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Redis configuration with timeouts
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_SOCKET_CONNECT_TIMEOUT = 5
    REDIS_RETRY_ON_TIMEOUT = True
    REDIS_MAX_CONNECTIONS = 20
    
    # Rate limiting defaults
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Redis configuration with fallback
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Admin user configuration
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    # Editor user configuration  
    EDITOR_USERNAME = os.environ.get('EDITOR_USERNAME', 'editor')
    EDITOR_PASSWORD = os.environ.get('EDITOR_PASSWORD')
    EDITOR_EMAIL = os.environ.get('EDITOR_EMAIL')
    
    # Rate limiting configuration
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = "200 per day"
    
    # Timezone settings
    TIMEZONE = 'Europe/Istanbul'
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']  # Replace with actual admin email
    
    # Security Configuration
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Fix Render's DATABASE_URL if needed
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    REDIS_URL = os.environ.get('REDIS_URL') or Config.REDIS_URL
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 7  # 7 days in production
    
    # Production logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    RATELIMIT_STORAGE_URL = 'memory://'  # Memory storage in development


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database
    WTF_CSRF_ENABLED = False  # Disable CSRF protection in tests
    RATELIMIT_ENABLED = False  # Disable rate limiting in tests


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration class based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
