from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0',
        include=['tasks']
    )
    
    celery.conf.update(app.config)

    # NEW: The Celery Beat Schedule
    # The Celery Beat Schedule
    celery.conf.beat_schedule = {
        'run-daily-reminder': {
            'task': 'tasks.send_daily_reminders', 
            'schedule': crontab(hour=10, minute=0), # Runs every day at 10:00 AM
        },
        'run-monthly-activity-report': {
            'task': 'tasks.monthly_activity_report', 
            'schedule': crontab(day_of_month='1', hour=8, minute=0), # Runs 1st day of every month at 8:00 AM
        }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery