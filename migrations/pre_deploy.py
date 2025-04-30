#!/usr/bin/env python
import os
from flask_migrate import upgrade
from app import create_app, db
from app.models import User

def deploy():
    """Run deployment tasks"""
    app = create_app()
    app.app_context().push()

    # Migrate database to latest revision
    upgrade()

    # Ensure admin user exists
    if not User.query.filter_by(username=app.config['ADMIN_USERNAME']).first():
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['ADMIN_EMAIL'],
            role='admin'
        )
        if app.config['ADMIN_PASSWORD']:
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            try:
                db.session.commit()
                print('Admin user created successfully')
            except Exception as e:
                db.session.rollback()
                print(f'Error creating admin user: {str(e)}')
                raise

if __name__ == '__main__':
    deploy()