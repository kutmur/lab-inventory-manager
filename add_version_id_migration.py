"""
Manual migration script to add version_id column to the product table
"""
from app import create_app, db
from sqlalchemy import Column, Integer, text

def upgrade():
    """Add version_id column to product table"""
    app = create_app()
    with app.app_context():
        print("Adding version_id column to product table...")
        # Check if column already exists
        result = db.session.execute(text("PRAGMA table_info(product)")).fetchall()
        column_names = [row[1] for row in result]
        
        if 'version_id' not in column_names:
            # Add the column if it doesn't exist
            db.session.execute(text("ALTER TABLE product ADD COLUMN version_id INTEGER NOT NULL DEFAULT 1"))
            db.session.commit()
            print("Column added successfully")
        else:
            print("version_id column already exists")

def downgrade():
    """Remove version_id column from product table"""
    app = create_app()
    with app.app_context():
        print("Removing version_id column from product table...")
        # This is just for documentation - SQLite doesn't support dropping columns easily
        print("Note: SQLite doesn't directly support dropping columns")
        print("To properly downgrade, you would need to recreate the table without the column")

if __name__ == '__main__':
    upgrade()
