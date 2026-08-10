import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, Student, PlacementDrive, JobApplication, Company
from datetime import datetime
from cache_config import cache
from werkzeug.utils import secure_filename
from flask import current_app


student_bp = Blueprint('student', __name__)

def get_student():
    user_id = get_jwt_identity()
    return Student.query.filter_by(user_id=user_id).first()

@student_bp.route('/api/student/profile', methods=['POST'])
@jwt_required()
def update_profile():
    student = get_student()
    if not student:
        return jsonify({"message": "Student not found"}), 404

    # 1. Update text fields (e.g., skills, education) if provided
    # Using request.form because we are expecting multipart/form-data for file uploads
    student.skills = request.form.get('skills', student.skills)
    student.education = request.form.get('education', student.education)
    
    # 2. Handle the Resume File Upload
    if 'resume' in request.files:
        file = request.files['resume']
        if file and file.filename != '':
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(f"{student.id}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file to the local directory
            file.save(filepath)
            
            # Update the database with the file path
            student.resume = filepath

    db.session.commit()
    return jsonify({
        "message": "Profile and resume updated successfully",
        "resume_url": f"/{student.resume}" if student.resume else None
    }), 200

@student_bp.route('/api/student/me', methods=['GET'])
@jwt_required()
def get_my_details():
    student = get_student()
    if not student:
        return jsonify({"message": "Not found"}), 404
    return jsonify({
        "name": student.name, 
        "skills": student.skills
    }), 200

@student_bp.route('/api/student/drives', methods=['GET'])
@jwt_required()
def get_drives():
    student = get_student()
    if not student:
        return jsonify({"message": "Student not found"}), 404

    # 1. Create a unique cache key for this specific student
    cache_key = f"drives_list_for_student_{student.id}"
    
    # 2. Check if the data is already in Redis
    cached_drives = cache.get(cache_key)
    if cached_drives:
        print(f"🚀 SUCCESS: Serving drives for Student {student.id} from REDIS CACHE!")
        return jsonify(cached_drives), 200

    print("⚠️ Cache miss. Querying the SQLite database...")

    # Only show Active drives
    current_date = datetime.now()
    drives = PlacementDrive.query.filter(
        PlacementDrive.status == 'Active',
        PlacementDrive.application_deadline >= current_date
    ).all()
    
    drive_list = []
    for d in drives:
        has_applied = JobApplication.query.filter_by(student_id=student.id, drive_id=d.id).first() is not None
        company = Company.query.get(d.company_id)
        drive_list.append({
            "id": d.id,
            "company_name": company.name if company else "Unknown",
            "job_title": d.job_title,
            "eligibility_branch": d.eligibility_branch,
            "eligibility_cgpa": d.eligibility_cgpa,
            "deadline": d.application_deadline.strftime('%Y-%m-%d'),
            "has_applied": has_applied
        })
        
    # FIX: Use drive_list instead of drives_data
    cache.set(cache_key, drive_list, timeout=60)
    
    return jsonify(drive_list), 200

@student_bp.route('/api/student/apply/<int:drive_id>', methods=['POST'])
@jwt_required()
def apply_for_drive(drive_id):
    student = get_student()
    drive = PlacementDrive.query.get(drive_id)
    if not drive: 
        return jsonify({"message": "Drive not found"}), 404
        
    # --- NEW: Eligibility Validation ---
    if student.cgpa < drive.eligibility_cgpa:
        return jsonify({"message": "You do not meet the minimum CGPA requirement."}), 403
        
    # Assuming branches are stored as comma-separated strings (e.g., "CSE,AI")
    if drive.eligibility_branch != "Any" and student.branch not in drive.eligibility_branch:
        return jsonify({"message": "Your branch is not eligible for this drive."}), 403
    # -----------------------------------
        
    existing_app = JobApplication.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing_app: 
        return jsonify({"message": "Already applied."}), 400
        
    new_app = JobApplication(student_id=student.id, drive_id=drive_id, status='Applied')
    db.session.add(new_app)
    db.session.commit()
    return jsonify({"message": f"Successfully applied for {drive.job_title}"}), 201

@student_bp.route('/api/student/applications', methods=['GET'])
@jwt_required()
def get_my_applications():
    student = get_student()
    apps = JobApplication.query.filter_by(student_id=student.id).all()
    
    app_list = []
    for app in apps:
        drive = PlacementDrive.query.get(app.drive_id)
        company = Company.query.get(drive.company_id)
        app_list.append({
            "id": app.id,
            "job_title": drive.job_title,
            "company_name": company.name if company else "Unknown",
            "status": app.status,
            "feedback": app.feedback,
            "interview_date": app.interview_date
        })
        
    return jsonify(app_list), 200
@student_bp.route('/api/student/export', methods=['POST'])
@jwt_required()
def trigger_export():
    student = get_student()
    if not student: return jsonify({"message": "Not found"}), 404

    # NEW: Import the task inside the route to prevent circular import crashes
    from tasks import export_student_applications_csv

    # Define where the CSV will be saved (inside the static folder so it can be downloaded)
    file_name = f"export_student_{student.id}.csv"
    file_path = os.path.join('static', 'exports', file_name)
    
    # TRIGGER THE CELERY TASK ASYNCHRONOUSLY USING .delay()
    export_student_applications_csv.delay(student.id, file_path)
    
    # Immediately return a 202 Accepted response to the frontend, do not wait for the CSV to finish!
    return jsonify({
        "message": "CSV Export started in the background. Please wait a few moments.", 
        "download_url": f"/static/exports/{file_name}"
    }), 202