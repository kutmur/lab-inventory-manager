from app import create_app, db
from app.extensions import socketio
from dotenv import load_dotenv
from app.models import User, Lab, Product
from flask import request, redirect, url_for, render_template, send_file
from app.main.forms import ProductForm
import uuid

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
        
        # Create predefined labs
        Lab.get_predefined_labs()
        
        db.session.add(admin)
        db.session.commit()
        print('Database initialized with admin user and predefined labs')

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

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()  # Instantiate the form
    if request.method == 'POST':
        if form.validate_on_submit():
            # Assuming you have a Product model with a lab_id field
            selected_lab_id = form.lab_id.data
            new_product = Product(
                name=form.name.data,
                registry_number=form.registry_number.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                minimum_quantity=form.minimum_quantity.data,
                location_in_lab=form.location_in_lab.data,
                lab_id=selected_lab_id,
                notes=form.notes.data
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('success', name=new_product.name))
    return render_template('add_product.html', form=form)

@app.route('/export/<lab_code>/<format>')
def export_lab(lab_code, format):
    # Logic to generate and return the file for the specific lab
    # Example: return send_file('path/to/generated/file', as_attachment=True)
    pass

@app.route('/export/all/<format>')
def export_all_labs(format):
    # Logic to generate and return the combined file for all labs
    # Example: return send_file('path/to/generated/file', as_attachment=True)
    pass