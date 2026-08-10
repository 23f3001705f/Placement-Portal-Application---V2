from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, Company, PlacementDrive, JobApplication, Student
from datetime import datetime
import os

company_bp = Blueprint('company', __name__)

def get_approved_company():
    user_id = get_jwt_identity() 
    company = Company.query.filter_by(user_id=user_id).first()
    if not company or not company.is_approved:
        return None
    return company

@company_bp.route('/api/company/stats', methods=['GET'])
@jwt_required()
def company_stats():
    company = get_approved_company()
    if not company: return jsonify({"message": "Unapproved"}), 403
    total_drives = PlacementDrive.query.filter_by(company_id=company.id).count()
    total_apps = JobApplication.query.join(PlacementDrive).filter(PlacementDrive.company_id == company.id).count()
    return jsonify({"company_name": company.name, "total_drives": total_drives, "total_applications": total_apps}), 200

import os

@company_bp.route('/api/company/export', methods=['POST'])
@jwt_required()
def trigger_company_export():
    user_id = get_jwt_identity()
    company = Company.query.filter_by(user_id=user_id).first()
    
    if not company:
        return jsonify({"message": "Company not found"}), 404
        
    file_path = os.path.join('static', 'exports', f'export_company_{company.id}.csv')
    
    try:
        from tasks import export_company_applications_csv
        export_company_applications_csv.delay(company.id, file_path)
    except Exception as e:
        return jsonify({"message": "Error starting background task"}), 500
        
    download_url = f"/static/exports/export_company_{company.id}.csv"
    
    return jsonify({
        "message": "CSV Export started in the background. Please wait a few moments.", 
        "download_url": download_url
    }), 202

@company_bp.route('/api/company/application/<int:app_id>/status', methods=['POST'])
@jwt_required()
def update_application_status(app_id):
    # Identify the logged-in company
    user_id = get_jwt_identity()
    company = Company.query.filter_by(user_id=user_id).first()
    if not company: 
        return jsonify({"message": "Company profile not found"}), 404

    # Find the specific application
    application = JobApplication.query.get(app_id)
    if not application: 
        return jsonify({"message": "Application not found"}), 404

    # SECURITY CHECK: Ensure this company actually owns the drive the student applied to
    drive = PlacementDrive.query.get(application.drive_id)
    if drive.company_id != company.id:
        return jsonify({"message": "Unauthorized to modify this application"}), 403

    # Grab the incoming data from the frontend
    data = request.get_json()
    
    # Update the fields (if the frontend sent them, otherwise keep the old value)
    application.status = data.get('status', application.status)
    application.feedback = data.get('feedback', application.feedback)
    application.interview_date = data.get('interview_date', application.interview_date)

    db.session.commit()
    
    return jsonify({"message": f"Application updated to {application.status}"}), 200

@company_bp.route('/api/company/drives', methods=['GET', 'POST'])
@jwt_required()
def create_placement_drive():
    user_id = get_jwt_identity()
    company = Company.query.filter_by(user_id=user_id).first()
    if not company: 
      return jsonify({"message": "Company not found"}), 404
    
    if not company.is_approved:
        return jsonify({
            "message": "Access Denied. Your company profile must be approved by the Admin before you can post jobs."
        }), 403
    if request.method == 'POST':
        data = request.get_json()
        try:
            deadline_date = datetime.strptime(data.get('deadline'), '%Y-%m-%d')
        except ValueError:
            return jsonify({"message": "Invalid date format."}), 400

        new_drive = PlacementDrive(
            company_id=company.id,
            job_title=data.get('job_title'),
            job_description=data.get('job_description'),
            eligibility_branch=data.get('eligibility_branch', ''),
            eligibility_cgpa=float(data.get('eligibility_cgpa', 0)),
            application_deadline=deadline_date,
            status='Active' # Starts as Active so it can be closed later
        )
        db.session.add(new_drive)
        db.session.commit()
        return jsonify({"message": "Placement drive created successfully"}), 201

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drive_list = [{"id": d.id, "job_title": d.job_title, "deadline": d.application_deadline.strftime('%Y-%m-%d'), "status": d.status} for d in drives]
    return jsonify(drive_list), 200

# NEW: Toggle Drive Status (Active <-> Closed)
@company_bp.route('/api/company/drives/<int:drive_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_drive(drive_id):
    company = get_approved_company()
    if not company: return jsonify({"message": "Unapproved"}), 403
    
    drive = PlacementDrive.query.get(drive_id)
    if not drive or drive.company_id != company.id:
        return jsonify({"message": "Unauthorized"}), 403
        
    drive.status = 'Closed' if drive.status == 'Active' else 'Active'
    db.session.commit()
    return jsonify({"message": f"Drive marked as {drive.status}"}), 200

@company_bp.route('/api/company/applications', methods=['GET'])
@jwt_required()
def get_company_applications():
    user_id = get_jwt_identity()
    company = Company.query.filter_by(user_id=user_id).first()
    
    if not company:
        return jsonify({"message": "Company not found"}), 404
        
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drive_ids = [d.id for d in drives]
    
    # If the company has no drives, return empty list safely
    if not drive_ids:
        return jsonify([]), 200
        
    applications = JobApplication.query.filter(JobApplication.drive_id.in_(drive_ids)).all()
    
    app_list = []
    for app in applications:
        student = Student.query.get(app.student_id)
        drive = PlacementDrive.query.get(app.drive_id)
        
        # Safely extract resume and skills to prevent crashes
        student_skills = getattr(student, 'skills', "None listed")
        student_resume_raw = getattr(student, 'resume', None)

        if student_resume_raw:
            # Strip away any slashes or folder paths the DB accidentally saved
            clean_filename = student_resume_raw.replace('\\', '/').split('/')[-1]
            # Force the exact, correct path
            resume_url = f"/static/resumes/{clean_filename}"
        else:
            resume_url = None
            
        app_list.append({
            "id": app.id,
            "student_name": student.name if student else "Unknown",
            "student_cgpa": student.cgpa if student else "N/A",
            "student_branch": student.branch if student else "N/A",
            "student_skills": student_skills if student_skills else "None listed",
            "student_resume": resume_url, # Now properly using the fixed URL
            "job_title": drive.job_title if drive else "Unknown",
            "status": app.status,
            "interview_date": app.interview_date,
            "feedback": app.feedback
        })
        
    return jsonify(app_list), 200

@company_bp.route('/api/company/application/<int:app_id>/status', methods=['POST'])
@jwt_required()
def update_app_status(app_id):
    company = get_approved_company()
    if not company: return jsonify({"message": "Unapproved"}), 403

    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['Shortlisted', 'Selected', 'Rejected']:
        return jsonify({"message": "Invalid status."}), 400

    application = JobApplication.query.get(app_id)
    if not application: return jsonify({"message": "Application not found"}), 404
        
    drive = PlacementDrive.query.get(application.drive_id)
    if drive.company_id != company.id: return jsonify({"message": "Unauthorized"}), 403
        
    application.status = new_status
    application.feedback = data.get('feedback', '')
    application.interview_date = data.get('interview_date', '')
    
    db.session.commit()
    return jsonify({"message": f"Application updated to {new_status}"}), 200