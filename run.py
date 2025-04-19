# run.py

from app import create_app, db
from app.extensions import socketio, migrate
from dotenv import load_dotenv
from app.models import User, Lab
import os

load_dotenv()

app = create_app()

def init_database():
    """Initialize database with default data"""
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        print("Database tables created fresh.")

        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print('Default admin user created')

        # Create default editor user if not exists
        editor = User.query.filter_by(username='editor').first()
        if not editor:
            editor = User(username='editor', email='editor@example.com', role='editor')
            editor.set_password('editor123')
            db.session.add(editor)
            print('Default editor user created')

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

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
