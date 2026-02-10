# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from backup import backup_files

def start_scheduler():
    scheduler = BackgroundScheduler()
    # run backup daily at midnight
    scheduler.add_job(backup_files, "cron", hour=0, minute=0)
    scheduler.start()
    return scheduler
