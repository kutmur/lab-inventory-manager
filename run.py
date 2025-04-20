#!/usr/bin/env python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file, fallback to .env.development
env_path = Path('.env')
if not env_path.exists():
    env_path = Path('.env.development')
load_dotenv(env_path)

from app import create_app, db
from app.extensions import socketio
from app.models import User, Lab

app = create_app()

def init_database():
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        print("Database tables created fresh.")

        # Create admin user from environment variables
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin:
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                email=app.config['ADMIN_EMAIL'],
                role='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            print('Admin user created')

        # Create editor user from environment variables
        editor = User.query.filter_by(username=app.config['EDITOR_USERNAME']).first()
        if not editor:
            editor = User(
                username=app.config['EDITOR_USERNAME'],
                email=app.config['EDITOR_EMAIL'],
                role='editor'
            )
            editor.set_password(app.config['EDITOR_PASSWORD'])
            db.session.add(editor)
            print('Editor user created')

        # Create predefined labs
        Lab.get_predefined_labs()
        
        try:
            db.session.commit()
            print('Database initialized successfully')
        except Exception as e:
            db.session.rollback()
            print(f'Error initializing database: {str(e)}')
            raise

if __name__ == '__main__':
    # Check if this is development environment
    if os.environ.get('FLASK_ENV') == 'development':
        # Initialize database if it doesn't exist or is empty
        db_path = os.path.join(os.path.dirname(__file__), 'app.db')
        if not os.path.exists(db_path):
            print("Creating new database...")
            init_database()
        else:
            with app.app_context():
                # Check if users table is empty
                user_count = User.query.count()
                if user_count == 0:
                    print("Database exists but empty, reinitializing...")
                    init_database()
                else:
                    print('Using existing database with users.')

        socketio.run(app, debug=True)
    else:
        # Production mode - let gunicorn handle the serving
        socketio.run(app, debug=app.config['DEBUG'])
