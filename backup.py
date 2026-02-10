# backup.py
import os, shutil, datetime

BACKUP_DIR = "backup"

def backup_files():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(target_dir, exist_ok=True)

    # Backup data folder
    if os.path.exists("data"):
        shutil.copytree("data", os.path.join(target_dir, "data"))

    # Backup logs folder
    if os.path.exists("logs"):
        shutil.copytree("logs", os.path.join(target_dir, "logs"))

    # Backup SQLite DB
    if os.path.exists("data/bot.db"):
        shutil.copy("data/bot.db", os.path.join(target_dir, "bot.db"))

    print(f"✅ Backup completed at {target_dir}")
