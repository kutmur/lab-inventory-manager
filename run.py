# run.py

from app import create_app, db
from app.extensions import socketio, migrate
from dotenv import load_dotenv
from app.models import User, Lab
import uuid

load_dotenv()

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # DEVELOPMENT'da tabloyu sıfırlamak istersen aç:
        # db.drop_all()
        # db.create_all()

        # Admin veya editor kullanıcı eklemek istersen:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created => admin / admin123')

        editor = User.query.filter_by(username='editor').first()
        if not editor:
            editor = User(username='editor', email='editor@example.com', role='editor')
            editor.set_password('editor123')
            db.session.add(editor)
            db.session.commit()
            print('Editor user created => editor / editor123')

        # Predefined labs
        Lab.get_predefined_labs()
        db.session.commit()
        print('Database set up with labs, admin, editor users if needed.')

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
