import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.json_utils import load_json, save_json
import config

USERS_FILE = f"{config.DATA_DIR}/users.json"
EVENTS_FILE = f"{config.DATA_DIR}/events.json"
VERSES_FILE = f"{config.DATA_DIR}/verses.json"

def add_user(uid: int, username: str = None, name: str = None):
    users = load_json(
