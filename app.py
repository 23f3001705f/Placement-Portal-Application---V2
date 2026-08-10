from flask import Flask, render_template
from routes import auth_bp
from models import db, User
from admin_routes import admin_bp
from company_routes import company_bp
from student_routes import student_bp
from flask_jwt_extended import JWTManager
from celery_config import make_celery
from cache_config import cache
from werkzeug.security import generate_password_hash
import os


def create_app():
    # Flask automatically knows to look in the 'templates' folder for HTML
    app = Flask(__name__)
    
    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.sqlite3'
    app.config['JWT_SECRET_KEY'] = 'your-very-secret-key-for-jwt'

    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # Cache expires every 60 seconds
    
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'resumes')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.init_app(app)
    JWTManager(app)
    cache.init_app(app)

    # Register APIs
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(auth_bp)

    # Initialize Celery
    app.celery = make_celery(app)

    # The one and only root route pointing to templates/index.html
    @app.route('/')
    def serve_vue_app():
        return render_template('index.html')
    with app.app_context():
        db.create_all() # Creates tables if they don't exist
        
        # Check if an admin exists, if not, create one programmatically
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            # Note: In a real app, use werkzeug.security to hash this password
            hashed_password = generate_password_hash('admin123')
            admin = User(email='admin@institute.edu', password=hashed_password, role='admin')        
            db.session.add(admin)
            db.session.commit()
            print("✅ Default Admin created programmatically.")
    return app

# Create global instances for the server and Celery worker
app = create_app()
celery = app.celery

if __name__ == '__main__':
    app.run(debug=True)