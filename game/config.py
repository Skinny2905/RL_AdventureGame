# Globale Einstellungen & Farben für Phase 2 (ohne RL)

GRID_SIZE = 5            # Spielfeldgröße (MiniGrid-Empty-5x5)
WINDOW_BASE = 512        # Basisgröße für Render-Scaling
FPS = 30                 # Ziel-FPS für Pygame-Loop

# Farben (RGB)
COLORS = {
    "score_text": (255, 255, 0),
    "point_pos":  (255, 255, 255),
    "overlay":    (0, 0, 0),

    # Objekte/Hindernisse (nur visuell in Phase 2)
    "tree":       (34, 139, 34),    # grün
    "water":      (30, 144, 255),   # blau
    "bridge":     (128, 128, 128),  # grau
    "log":        (139, 69, 19),    # braun
}
