from app import create_app, db
from app.extensions import socketio
from dotenv import load_dotenv
from app.models import User, Lab
from flask import request, redirect, url_for, render_template

load_dotenv()

app = create_app()

# Create tables and admin user within application context
if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        
        # Create default lab
        default_lab = Lab(
            name='Default Lab',
            description='Default laboratory',
            location='Main Building'
        )
        
        db.session.add(admin)
        db.session.add(default_lab)
        db.session.commit()
        print('Database initialized with admin user and default lab')

    # Use socketio.run with explicit host and port
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

@app.route('/success/<name>')
def success(name):
    return 'welcome %s' % name

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # Use get() to avoid KeyError if 'nm' is missing
        user = request.form.get('nm', '')
        if user:  # Check if user name is not empty
            return redirect(url_for('success', name=user))
        else:
            return render_template('login.html', error="Please enter a name")
    
    # GET request - show login form
    return render_template('login.html')  # Note the quotes around template name 