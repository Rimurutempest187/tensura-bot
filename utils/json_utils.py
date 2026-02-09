# utils/json_utils.py
import json
import os
import asyncio
from pathlib import Path
from typing import Any

from datetime import datetime
import logging

logger = logging.getLogger("ChurchBot.json")

DEFAULT_FILES = {
    "users.json": {},
    "quizzes.json": [],
    "events.json": [],
    "verses.json": [],
    "admins.json": [],
    "groups.json": []
}

def init_data_files(data_dir: str):
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    for name, default in DEFAULT_FILES.items():
        path = os.path.join(data_dir, name)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)

async def load_json(path: str, default: Any):
    try:
        def _read():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return await asyncio.to_thread(_read)
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return default

async def save_json(path: str, data: Any):
    try:
        def _write():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        await asyncio.to_thread(_write)
    except Exception as e:
        logger.error("Failed to save %s: %s", path, e)
        raise
