#!/usr/bin/env python
from app import create_app, db
from app.models import Product, TransferLog, UserLog
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Clean test products and related logs from database.
    
    This function preserves users and labs while removing:
    - All products
    - All transfer logs
    - All user activity logs
    
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Delete in correct order to maintain referential integrity
            UserLog.query.delete()
            TransferLog.query.delete()
            Product.query.delete()
            
            db.session.commit()
            logger.info('Database cleaned successfully')
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error cleaning database: {str(e)}')
            return False

if __name__ == '__main__':
    success = clean_database()
    exit(0 if success else 1)