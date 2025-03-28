from app import create_app, db
from app.models import Lab

labs = [
    {"code": "EEMLAB01-361", "name": "Elektrik Makineler Laboratuvarı", "description": "Elektrik Makineler Laboratuvarı", "location": "Room 361"},
    {"code": "EEMLAB02-363", "name": "Güç Elektroniği Laboratuvarı", "description": "Güç Elektroniği Laboratuvarı", "location": "Room 363"},
    {"code": "EEMLAB03-365", "name": "Otomatik Kontrol Laboratuvarı", "description": "Otomatik Kontrol Laboratuvarı", "location": "Room 365"},
    {"code": "EEMLAB04-367", "name": "Yapay Zeka ve İleri Sinyal İşleme Araştırma Laboratuvarı", "description": "Yapay Zeka ve İleri Sinyal İşleme Araştırma Laboratuvarı", "location": "Room 367"},
    {"code": "EEMLAB05-369", "name": "Mikroişlemci Laboratuvarı", "description": "Mikroişlemci Laboratuvarı", "location": "Room 369"},
    {"code": "EEMLAB06-371", "name": "Haberleşme ve Mikrodalga Laboratuvarı", "description": "Haberleşme ve Mikrodalga Laboratuvarı", "location": "Room 371"},
    {"code": "EEMLAB07-373", "name": "Temel Elektrik Elektronik Devre Laboratuvarı", "description": "Temel Elektrik Elektronik Devre Laboratuvarı", "location": "Room 373"},
]

def seed_labs():
    app = create_app()
    with app.app_context():
        # First, handle Default Lab if it exists
        default_lab = Lab.query.filter_by(name='Default Lab').first()
        if default_lab and not default_lab.code:
            default_lab.code = 'LAB-DEFAULT'
            print(f"Updated Default Lab with code: {default_lab.code}")
        
        # Then add new labs
        for lab in labs:
            existing_lab = Lab.query.filter_by(code=lab["code"]).first()
            if not existing_lab:
                new_lab = Lab(
                    code=lab["code"],
                    name=lab["name"],
                    description=lab["description"],
                    location=lab["location"]
                )
                db.session.add(new_lab)
                print(f"Added new lab: {lab['code']} - {lab['name']}")
        
        db.session.commit()
        print("Labs have been seeded successfully!")

if __name__ == "__main__":
    seed_labs() 