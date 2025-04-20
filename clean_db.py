#!/usr/bin/env python
from app import create_app, db
from app.models import Product, TransferLog, UserLog
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Clean test products and related logs from database while preserving users and labs"""
    try:
        app = create_app()
        with app.app_context():
            # Delete all transfer logs first (due to foreign key constraints)
            transfer_count = TransferLog.query.delete()
            logger.info(f"Deleted {transfer_count} transfer logs")

            # Delete all user logs related to products
            user_log_count = UserLog.query.filter(UserLog.product_id.isnot(None)).delete()
            logger.info(f"Deleted {user_log_count} product-related user logs")

            # Delete all products
            product_count = Product.query.delete()
            logger.info(f"Deleted {product_count} products")

            # Commit the changes
            db.session.commit()
            logger.info("Database cleaned successfully")
            return True

    except Exception as e:
        logger.error(f"Error cleaning database: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        return False

if __name__ == '__main__':
    success = clean_database()
    exit(0 if success else 1)