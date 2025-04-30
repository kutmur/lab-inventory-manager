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
    """Initialize admin user using environment variables.
    
    Creates admin user with credentials from environment variables if not exists.
    Required env vars:
    - ADMIN_USERNAME
    - ADMIN_PASSWORD
    - ADMIN_EMAIL
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    app = create_app()
    
    with app.app_context():
        try:
            admin = User.query.filter_by(
                username=current_app.config['ADMIN_USERNAME']
            ).first()
            
            if not admin:
                admin = User(
                    username=current_app.config['ADMIN_USERNAME'],
                    email=current_app.config['ADMIN_EMAIL'],
                    role='admin'
                )
                admin.set_password(current_app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()
                logger.info('Admin user created successfully')
            else:
                logger.info('Admin user already exists')
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error initializing admin user: {str(e)}')
            return False


if __name__ == '__main__':
    success = init_admin_user()
    exit(0 if success else 1)