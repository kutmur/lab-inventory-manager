import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User, Lab, Product, TransferLog, UserLog

def init_cli(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_labs_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(convert_quantities_command)
    app.cli.add_command(update_lab_codes_command)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize database tables"""
    db.drop_all()
    db.create_all()
    click.echo("Database tables created fresh.")

@click.command("seed-labs")
@with_appcontext
def seed_labs_command():
    """Seed predefined labs"""
    # Update Default Lab if exists
    default_lab = Lab.query.filter_by(name='Default Lab').first()
    if default_lab and not default_lab.code:
        default_lab.code = '0'
        click.echo(f"Updated Default Lab with code: {default_lab.code}")
    
    # Add labs from predefined data
    for code, name, desc, maxc in Lab.PREDEFINED_LABS:
        existing_lab = Lab.query.filter_by(code=code).first()
        if not existing_lab:
            new_lab = Lab(
                code=code,
                name=name,
                description=desc,
                location=f"Room {code}",
                max_cabinets=maxc
            )
            db.session.add(new_lab)
            click.echo(f"Added new lab: {code} - {name}")
    
    try:
        db.session.commit()
        click.echo("Labs have been seeded/updated successfully!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error seeding labs: {str(e)}", err=True)

@click.command("create-admin")
@click.option('--username', default='admin', help='Admin username')
@click.option('--password', default='admin123', help='Admin password')
@click.option('--email', default='admin@example.com', help='Admin email')
@with_appcontext
def create_admin_command(username, password, email):
    """Create an admin user"""
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        click.echo(f"Admin '{username}' already exists")
        return
    
    admin = User(
        username=username,
        email=email,
        role='admin'
    )
    admin.set_password(password)
    
    db.session.add(admin)
    try:
        db.session.commit()
        click.echo(f"Admin '{username}' has been created")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin: {str(e)}", err=True)

@click.command("convert-quantities")
@with_appcontext
def convert_quantities_command():
    """Convert all float quantities to integers"""
    products = Product.query.all()
    for product in products:
        product.quantity = round(float(product.quantity))
        product.minimum_quantity = round(float(product.minimum_quantity))
    
    transfer_logs = TransferLog.query.all()
    for log in transfer_logs:
        log.quantity = round(float(log.quantity))
    
    user_logs = UserLog.query.all()
    for log in user_logs:
        if log.quantity is not None:
            log.quantity = round(float(log.quantity))
    
    try:
        db.session.commit()
        click.echo("Successfully converted all quantities to integers")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error converting quantities: {str(e)}", err=True)

@click.command("update-lab-codes")
@with_appcontext
def update_lab_codes_command():
    """Update lab codes for labs without codes"""
    labs = Lab.query.all()
    
    default_lab = Lab.query.filter_by(name='Default Lab').first()
    if default_lab:
        default_lab.code = '0'
        click.echo(f"Updated Default Lab with code: {default_lab.code}")
    
    for lab in labs:
        if not lab.code or lab.code == 'None':
            lab.code = f"{lab.id}"
            click.echo(f"Updated lab '{lab.name}' with code: {lab.code}")
    
    try:
        db.session.commit()
        click.echo("Lab codes updated successfully!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error updating lab codes: {str(e)}", err=True)