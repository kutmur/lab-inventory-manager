from app import create_app, db
from app.models import Lab

def update_existing_labs():
    app = create_app()
    with app.app_context():
        # Get all labs that might have NULL codes
        labs = Lab.query.all()
        
        # Update Default Lab if it exists
        default_lab = Lab.query.filter_by(name='Default Lab').first()
        if default_lab:
            default_lab.code = 'LAB-DEFAULT'
            print(f"Updated Default Lab with code: {default_lab.code}")
        
        # Update any other labs that might not have codes
        for lab in labs:
            if not lab.code or lab.code == 'None':
                lab.code = f"LAB-{lab.id:03d}"
                print(f"Updated lab '{lab.name}' with code: {lab.code}")
        
        db.session.commit()
        print("Finished updating lab codes!")

if __name__ == "__main__":
    update_existing_labs() 