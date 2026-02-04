import os
from dotenv import load_dotenv

# Load env first
load_dotenv()

# ------------------
# BOT TOKEN
# ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env")

# ------------------
# ADMINS
# ------------------
ADMIN_IDS = []

admins = os.getenv("ADMIN_IDS", "")

if admins:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admins.split(",")]
    except:
        ADMIN_IDS = []

# ------------------
# PATHS
# ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

MEDIA_DIR = os.path.join(BASE_DIR, "media")

MEDIA_PDFS = os.path.join(MEDIA_DIR, "pdfs")
MEDIA_AUDIO = os.path.join(MEDIA_DIR, "audio")
MEDIA_IMAGES = os.path.join(MEDIA_DIR, "images")

# ------------------
# FILES
# ------------------
USERS_FILE = os.path.join(DATA_DIR, "users.json")
QUIZZES_FILE = os.path.join(DATA_DIR, "quizzes.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
VERSES_FILE = os.path.join(DATA_DIR, "verses.json")
