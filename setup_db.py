from app import create_app
from models import db, User, Company, Student, PlacementDrive, JobApplication
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # This command creates any tables that are missing in the SQLite file
    db.create_all()
    print("Database tables synchronized successfully.")
    
    # Ensure the admin user still exists
    admin = User.query.filter_by(email='admin@institute.edu').first()
    if not admin:
        hashed_pw = generate_password_hash('admin123')
        new_admin = User(email='admin@institute.edu', password=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")