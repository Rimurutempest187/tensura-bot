import os
from dotenv import load_dotenv

load_dotenv()

# ----------------------
# Bot settings
# ----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",") if uid]

# ----------------------
# Media folders
# ----------------------
MEDIA_PDFS = os.getenv("MEDIA_PDFS", "media/pdfs")
MEDIA_AUDIO = os.getenv("MEDIA_AUDIO", "media/audio")
MEDIA_IMAGES = os.getenv("MEDIA_IMAGES", "media/images")

# ----------------------
# Data files
# ----------------------
USERS_FILE = os.getenv("USERS_FILE", "data/users.json")
QUIZZES_FILE = os.getenv("QUIZZES_FILE", "data/quizzes.json")
EVENTS_FILE = os.getenv("EVENTS_FILE", "data/events.json")
VERSES_FILE = os.getenv("VERSES_FILE", "data/verses.json")
