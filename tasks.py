import csv
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import celery
from datetime import datetime, timedelta
from models import db, JobApplication, PlacementDrive, Company, User

# --- MAILTRAP SMTP CONFIGURATION ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "testing98260@gmail.com"  # <--- Replace this
SMTP_PASS = "bvlkbyusothyufni"  # <--- Replace this

def send_email(to_email, subject, body_html):
    """Helper function to send emails via Mailtrap"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "testing98260@gmail.com"
    msg['To'] = to_email

    part = MIMEText(body_html, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            # 2. Secure the connection
            server.starttls() 
            # 3. Login with App Password
            server.login(SMTP_USER, SMTP_PASS)
            # 4. Send the email
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        print(f"✅ Real email successfully sent to: {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

@celery.task
def send_daily_reminders():
    """
    Triggered daily by Celery Beat.
    Queries the database for active drives and sends a summary reminder.
    """
    print("\n🚀 CELERY BEAT: Running Daily Reminder Task...")
    
    # Query all active placement drives
    active_drives = PlacementDrive.query.filter_by(status='Active').all()
    
    # Build a real HTML email using the database results
    html_content = """
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #d9534f;">Daily Reminder: Active Placement Drives</h2>
        <p>Don't miss out! Here are the currently active placement drives you can apply for:</p>
        <ul>
    """
    
    for drive in active_drives:
        # Format the deadline nicely
        deadline_str = drive.application_deadline.strftime('%Y-%m-%d')
        html_content += f"<li><strong>{drive.job_title}</strong> - Deadline: {deadline_str}</li>"
        
    html_content += """
        </ul>
        <p>Log in to your Student Dashboard to apply today.</p>
    </div>
    """
    
    # Sending to your test email to avoid bounce errors during the viva
    send_email("testing98260@gmail.com", "Action Required: Upcoming Placement Deadlines", html_content)
    
    print("✅ Daily reminders sent successfully.\n")
    return "Daily reminders task completed."


@celery.task
def monthly_activity_report():
    """
    Triggered monthly by Celery Beat.
    Calculates total drives, applications, and selections for the Admin.
    """
    print("\n🚀 CELERY BEAT: Running Monthly Activity Report...")
    
    # Real SQLAlchemy Aggregate Queries!
    total_drives = PlacementDrive.query.count()
    total_applications = JobApplication.query.count()
    total_selected = JobApplication.query.filter_by(status='Selected').count()
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2 style="color: #0275d8;">Monthly Placement Activity Report</h2>
        <p>Here is the automated summary of the institute's placement cell activities:</p>
        <hr>
        <ul style="font-size: 16px;">
            <li><b>Total Placement Drives Conducted:</b> {total_drives}</li>
            <li><b>Total Student Applications Processed:</b> {total_applications}</li>
            <li><b>Total Students Successfully Selected:</b> {total_selected}</li>
        </ul>
        <hr>
        <p>This report was generated automatically by the Celery Beat Scheduler.</p>
    </div>
    """
    
    # Sending to your test email for the live demo
    send_email("testing98260@gmail.com", "Monthly Placement Portal Activity Report", html_content)
    
    print("✅ Monthly activity report generated and sent.\n")
    return "Monthly report task completed."
import csv
import os

# ... (Keep your existing email tasks above this) ...

@celery.task
def export_student_applications_csv(student_id, file_path):
    """
    Triggered asynchronously by the user.
    Generates a CSV of a student's applications and saves it to the static folder.
    """
    print(f"\n🚀 CELERY WORKER: Generating CSV for Student ID: {student_id}")
    
    # Ensure the static/exports directory exists before writing to it
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Query all applications for this student
    applications = JobApplication.query.filter_by(student_id=student_id).all()
    
    # Create and write to the CSV file
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(['Application ID', 'Company Name', 'Job Title', 'Status', 'Interview Date', 'Feedback'])
        
        # Write the data rows
        for app in applications:
            drive = PlacementDrive.query.get(app.drive_id)
            company = Company.query.get(drive.company_id) if drive else None
            
            writer.writerow([
                app.id,
                company.name if company else 'Unknown',
                drive.job_title if drive else 'Unknown',
                app.status,
                app.interview_date if app.interview_date else 'Pending',
                app.feedback if app.feedback else 'None'
            ])
            
    print(f"✅ CSV successfully saved to {file_path}\n")
    return file_path
@celery.task
def export_company_applications_csv(company_id, file_path):
    import os
    import csv
    # Import the app and models directly inside the task to prevent background crashes
    from app import app
    from models import Company, PlacementDrive, JobApplication, Student

    print(f"\n🚀 CELERY WORKER: Generating CSV for Company ID: {company_id}...")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Wrap the database query in the app context
    with app.app_context():
        drives = PlacementDrive.query.filter_by(company_id=company_id).all()
        if not drives:
            drive_ids = []
        else:
            drive_ids = [d.id for d in drives]
        
        if drive_ids:
            apps = JobApplication.query.filter(JobApplication.drive_id.in_(drive_ids)).all()
        else:
            apps = []
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Student Name', 'Job Title', 'Status', 'Interview Date', 'Feedback'])
            
            for application in apps:
                student = Student.query.get(application.student_id)
                student_name = student.name if student else "Unknown"
                
                drive = PlacementDrive.query.get(application.drive_id)
                job_title = drive.job_title if drive else "Unknown"
                
                writer.writerow([
                    student_name,
                    job_title,
                    application.status,
                    application.interview_date or "N/A",
                    application.feedback or "N/A"
                ])
                
    print(f"✅ CSV successfully saved to {file_path}\n")
    return file_path