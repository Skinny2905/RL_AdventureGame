# constants.py
from datetime import datetime

GRID_SIZE = 10
CELL_SIZE = 50
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 140

SAVE_FILE = "saved_maps.json"
SPAWN_FILE = "spawn_settings.json"

# Farben
COLORS = {
    "grass": (34, 139, 34),
    "heavy": (128, 128, 128),
    "river": (0, 0, 139),
    "bridge": (139, 69, 19),
    "reward": (255, 215, 0),
    "trap": (0, 0, 0),
    "mountain": (255, 255, 255),
    "goal": (135, 206, 235),
    "player": (255, 0, 0),
    "ui_bg": (20, 20, 20),
    "ui_sel": (100, 100, 100),
    "text": (230, 230, 230),
}

# Stamina-Effekte (used when stepping onto a tile)
STAMINA = {
    "grass": -1,
    "heavy": -3,
    "river": -5,
    "bridge": -1,
    "reward": +20,
    "trap": -50,
    "mountain": None,
    "goal": 0,
}
