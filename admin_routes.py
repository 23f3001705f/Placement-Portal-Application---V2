from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, User, Student, Company, PlacementDrive, JobApplication

admin_bp = Blueprint('admin', __name__)

def is_admin():
    """Helper function to strictly verify the user is the Admin"""
    claims = get_jwt()
    return claims.get('role') == 'admin'

# ==========================================
# GET ROUTES (Dashboards & Search)
# ==========================================

@admin_bp.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_stats():
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403

    stats = {
        "total_students": Student.query.count(),
        "total_companies": Company.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": JobApplication.query.count()
    }
    return jsonify(stats), 200

@admin_bp.route('/api/admin/companies', methods=['GET'])
@jwt_required()
def get_companies():
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
    
    search = request.args.get('search', '').lower()

    # --- INJECT REDIS CACHE HERE ---
    from app import cache
    cache_key = f"admin_comp_search_{search}"
    cached_data = cache.get(cache_key)
    if cached_data:
        print("🚀 SUCCESS: Serving Admin Companies from REDIS CACHE!")
        return jsonify(cached_data), 200
    # -------------------------------

    if search:
        companies = Company.query.filter(Company.name.ilike(f"%{search}%")).all()
    else:
        companies = Company.query.all()
        
    company_list = []
    for c in companies:
        user = User.query.get(c.user_id)
        company_list.append({
            "id": c.id,
            "name": c.name,
            "hr_contact": c.hr_contact,
            "website": c.website,
            "is_approved": c.is_approved,
            "user_id": c.user_id,
            "is_active": user.is_active if user else False
        })

    # --- SAVE TO REDIS CACHE BEFORE RETURNING ---
    cache.set(cache_key, company_list, timeout=60)
    print("⚠️ Cache miss. Queried from SQLite.")
    # --------------------------------------------

    return jsonify(company_list), 200

@admin_bp.route('/api/admin/students', methods=['GET'])
@jwt_required()
def get_students():
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
        
    search = request.args.get('search', '').lower()

    # --- INJECT REDIS CACHE HERE ---
    from app import cache
    cache_key = f"admin_stud_search_{search}"
    cached_data = cache.get(cache_key)
    if cached_data:
        print("🚀 SUCCESS: Serving Admin Students from REDIS CACHE!")
        return jsonify(cached_data), 200
    # -------------------------------

    if search:
        students = Student.query.filter(
            (Student.name.ilike(f"%{search}%")) | 
            (Student.roll_number.ilike(f"%{search}%"))
        ).all()
    else:
        students = Student.query.all()
        
    student_list = []
    for s in students:
        user = User.query.get(s.user_id)
        student_list.append({
            "id": s.id,
            "name": s.name,
            "roll_number": s.roll_number,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "user_id": s.user_id,
            "is_active": user.is_active if user else False
        })

    # --- SAVE TO REDIS CACHE BEFORE RETURNING ---
    cache.set(cache_key, student_list, timeout=60)
    print("⚠️ Cache miss. Queried from SQLite.")
    # --------------------------------------------

    return jsonify(student_list), 200

# ==========================================
# POST ROUTES (Approvals & Blacklisting)
# ==========================================

@admin_bp.route('/api/admin/company/<int:company_id>/status', methods=['POST'])
@jwt_required()
def update_company_status(company_id):
    """Admin can Approve or Reject a company profile"""
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
        
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404
        
    data = request.get_json()
    action = data.get('action') # Expecting 'Approve' or 'Reject' from frontend
    
    if action == 'Approve':
        company.is_approved = True
        message = f"Company {company.name} approved."
    else:
        company.is_approved = False
        message = f"Company {company.name} rejected."
        
    db.session.commit()
    return jsonify({"message": message}), 200

@admin_bp.route('/api/admin/drive/<int:drive_id>/status', methods=['POST'])
@jwt_required()
def update_drive_status(drive_id):
    """Admin can Approve or Reject a placement drive created by a company"""
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
    
    drive = PlacementDrive.query.get(drive_id)
    if not drive: 
        return jsonify({"message": "Drive not found"}), 404
    
    data = request.get_json()
    new_status = data.get('status') # Expecting 'Active', 'Rejected', etc. from frontend
    
    drive.status = new_status
    db.session.commit()
    return jsonify({"message": f"Drive status updated to {new_status}."}), 200

@admin_bp.route('/api/admin/user/<int:user_id>/toggle_active', methods=['POST'])
@jwt_required()
def toggle_user_active(user_id):
    """Admin can blacklist (deactivate) or reactivate a student or company user account"""
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    if user.role == 'admin':
        return jsonify({"message": "Cannot deactivate admin account"}), 400
        
    # Flip the boolean status
    user.is_active = not user.is_active
    db.session.commit()
    
    status_msg = "activated" if user.is_active else "deactivated (blacklisted)"
    return jsonify({"message": f"Account {status_msg} successfully", "is_active": user.is_active}), 200
@admin_bp.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def get_all_applications():
    """Admin can view all job applications across the platform"""
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
        
    apps = JobApplication.query.all()
    app_list = []
    
    for app in apps:
        student = Student.query.get(app.student_id)
        drive = PlacementDrive.query.get(app.drive_id)
        company = Company.query.get(drive.company_id) if drive else None
        
        app_list.append({
            "id": app.id,
            "student_name": student.name if student else "Unknown",
            "company_name": company.name if company else "Unknown",
            "job_title": drive.job_title if drive else "Unknown",
            "status": app.status
        })
        
    return jsonify(app_list), 200
@admin_bp.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def get_platform_applications():
    """Admin can view all job applications across the platform"""
    if not is_admin():
        return jsonify({"message": "Unauthorized access"}), 403
        
    apps = JobApplication.query.all()
    app_list = []
    
    for app in apps:
        student = Student.query.get(app.student_id)
        drive = PlacementDrive.query.get(app.drive_id)
        company = Company.query.get(drive.company_id) if drive else None
        
        app_list.append({
            "id": app.id,
            "student_name": student.name if student else "Unknown",
            "company_name": company.name if company else "Unknown",
            "job_title": drive.job_title if drive else "Unknown",
            "status": app.status
        })
        
    return jsonify(app_list), 200