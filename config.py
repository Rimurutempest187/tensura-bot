import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

_admins = os.getenv("ADMIN_IDS", "")
if _admins.strip():
    try:
        ADMIN_IDS = [int(x) for x in _admins.split(",") if x.strip()]
    except Exception:
        ADMIN_IDS = []
else:
    ADMIN_IDS = []

# Media folders
MEDIA_PDFS = "media/pdfs"
MEDIA_AUDIO = "media/audio"
MEDIA_IMAGES = "media/images"

# Data files
USERS_FILE = "data/users.json"
QUIZZES_FILE = "data/quizzes.json"
EVENTS_FILE = "data/events.json"
VERSES_FILE = "data/verses.json"
