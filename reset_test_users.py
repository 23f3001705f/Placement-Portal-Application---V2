from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    users = User.query.all()
    print("--- REGISTERED ACCOUNTS ---")
    for u in users:
        if u.role == 'admin':
            print(f"ADMIN  | Email: {u.email} | (Password unchanged)")
        else:
            # Overwrite the hashed password for students and companies
            u.password = generate_password_hash('pass123')
            print(f"{u.role.upper():<6} | Email: {u.email} | Password reset to: pass123")
    
    db.session.commit()
    print("---------------------------")
    print("Database updated successfully.")