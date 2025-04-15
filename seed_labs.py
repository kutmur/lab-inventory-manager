# lab_seed.py

from app import create_app, db
from app.models import Lab

# Mevcut “labs” verisi
labs_data = [
    {"code": "EEMLAB01-361", "name": "Elektrik Makineler Laboratuvarı", 
     "description": "Elektrik Makineler Laboratuvarı", "location": "Room 361"},
    {"code": "EEMLAB02-363", "name": "Güç Elektroniği Laboratuvarı", 
     "description": "Güç Elektroniği Laboratuvarı", "location": "Room 363"},
    {"code": "EEMLAB03-365", "name": "Otomatik Kontrol Laboratuvarı", 
     "description": "Otomatik Kontrol Laboratuvarı", "location": "Room 365"},
    # ... buraya tüm lab verilerini ekle ...
]

def seed_labs():
    app = create_app()
    with app.app_context():
        # 1) Default Lab'i güncelle
        default_lab = Lab.query.filter_by(name='Default Lab').first()
        if default_lab and not default_lab.code:
            default_lab.code = 'LAB-DEFAULT'
            print(f"Updated Default Lab with code: {default_lab.code}")
        
        # 2) labs_data'daki laboratuvarları ekle veya varsa geç
        for lab_info in labs_data:
            existing_lab = Lab.query.filter_by(code=lab_info["code"]).first()
            if not existing_lab:
                new_lab = Lab(
                    code=lab_info["code"],
                    name=lab_info["name"],
                    description=lab_info["description"],
                    location=lab_info["location"]
                )
                db.session.add(new_lab)
                print(f"Added new lab: {lab_info['code']} - {lab_info['name']}")
        
        db.session.commit()
        print("Labs have been seeded/updated successfully!")

if __name__ == "__main__":
    seed_labs()
