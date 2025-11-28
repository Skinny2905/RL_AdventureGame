# storage.py
import json
import os
from typing import List, Dict
from constants import SAVE_FILE, SPAWN_FILE

def load_saved_maps() -> List[Dict]:
    """Return list of saved map dicts or [] if none."""
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_saved_maps(list_of_maps):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(list_of_maps, f, ensure_ascii=False, indent=2)

def load_spawn_settings():
    if not os.path.exists(SPAWN_FILE):
        return {"keep_spawn": False, "spawn_pos": None}
    try:
        with open(SPAWN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"keep_spawn": False, "spawn_pos": None}

def save_spawn_settings(data):
    with open(SPAWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
