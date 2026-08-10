from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    is_active = db.Column(db.Boolean, default=True)

    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('Company', backref='user', uselist=False, cascade='all, delete-orphan')

class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(50), nullable=False)
    website = db.Column(db.String(150))
    is_approved = db.Column(db.Boolean, default=False)
    
    # A company can have multiple placement drives
    drives = db.relationship('PlacementDrive', backref='company', cascade='all, delete-orphan')

class Student(db.Model):
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    cgpa = db.Column(db.Float, nullable=False) 
    skills = db.Column(db.String(255), nullable=True)
    education = db.Column(db.String(255), nullable=True)
    resume = db.Column(db.String(255), nullable=True)
    
    # A student can have multiple applications
    applications = db.relationship('JobApplication', backref='student', cascade='all, delete-orphan')

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Links to the Company that created the drive
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_branch = db.Column(db.String(100)) # e.g., 'CSE, ECE'
    eligibility_cgpa = db.Column(db.Float, default=0.0)
    application_deadline = db.Column(db.DateTime, nullable=False)
    
    # Admin must approve drives before students see them.
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Closed
    
    # Links to all applications submitted for this drive
    applications = db.relationship('JobApplication', backref='drive', cascade='all, delete-orphan')

class JobApplication(db.Model):
    __tablename__ = 'job_application'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Links to the Student who applied
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    # Links to the specific Placement Drive
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Company updates this status
    status = db.Column(db.String(20), default='Applied') # Applied, Shortlisted, Selected, Rejected
    feedback = db.Column(db.Text, nullable=True)
    interview_date = db.Column(db.String(50), nullable=True)