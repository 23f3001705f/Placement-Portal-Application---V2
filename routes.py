from flask import Blueprint, request, jsonify
from models import db, User, Student, Company
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"message": "Account deactivated by Admin"}), 403

    # --- THE CRITICAL FIX IS HERE ---
    # identity MUST be a string (str). Extra data goes in additional_claims.
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role
    }), 200

@auth_bp.route('/api/register/student', methods=['POST'])
def register_student():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first() or Student.query.filter_by(roll_number=data.get('roll_number')).first():
        return jsonify({"message": "User already registered"}), 400

    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(email=data.get('email'), password=hashed_pw, role='student')
    db.session.add(new_user)
    db.session.flush() 
    
    new_student = Student(
        user_id=new_user.id, name=data.get('name'), roll_number=data.get('roll_number'),
        branch=data.get('branch'), cgpa=float(data.get('cgpa')), skills=data.get('skills', '')
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"message": "Student registered successfully"}), 201

@auth_bp.route('/api/register/company', methods=['POST'])
def register_company():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Email already registered"}), 400

    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(email=data.get('email'), password=hashed_pw, role='company')
    db.session.add(new_user)
    db.session.flush() 
    
    new_company = Company(
        user_id=new_user.id, name=data.get('name'), hr_contact=data.get('hr_contact'), website=data.get('website', '')
    )
    db.session.add(new_company)
    db.session.commit()
    return jsonify({"message": "Company registered successfully. Pending Admin approval."}), 201