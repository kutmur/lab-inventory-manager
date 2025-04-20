#!/usr/bin/env python
import os
from flask import current_app
from app import create_app, db
from app.models import User
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_admin_user():
    """Initialize admin user using environment variables"""
    try:
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Check required environment variables
            required_vars = ['ADMIN_USERNAME', 'ADMIN_EMAIL', 'ADMIN_PASSWORD']
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
                return False

            username = os.environ['ADMIN_USERNAME']
            email = os.environ['ADMIN_EMAIL']
            password = os.environ['ADMIN_PASSWORD']

            # Check if admin user already exists
            existing_admin = User.query.filter_by(username=username).first()
            if existing_admin:
                logger.info(f"Admin user '{username}' already exists")
                return True

            # Create new admin user
            admin = User(
                username=username,
                email=email,
                role='admin'
            )
            admin.set_password(password)

            try:
                db.session.add(admin)
                db.session.commit()
                logger.info(f"Admin user '{username}' created successfully")
                return True
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating admin user: {str(e)}")
                return False

    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        return False

if __name__ == '__main__':
    success = init_admin_user()
    exit(0 if success else 1)