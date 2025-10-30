import pygame
from .config import COLORS, GRID_SIZE


def draw_grid_lines(screen, scaled_size):
    """Zeichnet Gitternetzlinien über das Spielfeld."""
    w, h = scaled_size
    cw, ch = w / GRID_SIZE, h / GRID_SIZE
    for i in range(1, GRID_SIZE):
        pygame.draw.line(screen, (60, 60, 60), (i * cw, 0), (i * cw, h), 1)
        pygame.draw.line(screen, (60, 60, 60), (0, i * ch), (w, i * ch), 1)


def draw_points(screen, scaled_size, point_grid, small_font):
    """Zeigt die Punktewerte (Rewards) im Spielfeld an."""
    cw = scaled_size[0] / GRID_SIZE
    ch = scaled_size[1] / GRID_SIZE
    for j in range(GRID_SIZE):
        for i in range(GRID_SIZE):
            val = int(point_grid[j, i])
            if val != 0:
                text = small_font.render(str(val), True, COLORS["point_pos"])
                tx = int(i * cw + cw / 2 - text.get_width() / 2)
                ty = int(j * ch + ch / 2 - text.get_height() / 2)
                screen.blit(text, (tx, ty))


def draw_objects(screen, scaled_size, objects):
    """Zeichnet Hindernisse und Objekte (Bäume, Wasser, Brücke, Holzstämme)."""
    cw = scaled_size[0] / GRID_SIZE
    ch = scaled_size[1] / GRID_SIZE
    color_map = {
        "tree": COLORS["tree"],
        "water": COLORS["water"],
        "bridge": COLORS["bridge"],
        "log": COLORS["log"],
    }
    for (x, y), obj_type in objects.items():
        color = color_map.get(obj_type, (255, 255, 255))
        rect = pygame.Rect(int(x * cw), int(y * ch), int(cw), int(ch))
        pygame.draw.rect(screen, color, rect)


def draw_score(screen, font, score):
    """Zeigt den aktuellen Punktestand an."""
    text = font.render(f"Punkte: {score}", True, COLORS["score_text"])
    screen.blit(text, (10, 10))


def draw_legend(screen, font):
    """Zeigt eine kleine Legende unten rechts an (Objektfarben und Bedeutung)."""
    items = [
        ("tree", "Baum (blockiert)"),
        ("water", "Wasser (blockiert)"),
        ("bridge", "Brücke (ok)"),
        ("log", "Stamm (ok)"),
    ]

    padding, box_w = 8, 240
    x = screen.get_width() - box_w - padding
    y = screen.get_height() - (len(items) * 24 + 2 * padding)

    # Hintergrundbox
    pygame.draw.rect(screen, (20, 20, 20), (x, y, box_w, len(items) * 24 + 2 * padding))
    pygame.draw.rect(screen, (80, 80, 80), (x, y, box_w, len(items) * 24 + 2 * padding), 1)

    ty = y + padding
    for key, label in items:
        color = COLORS[key]
        pygame.draw.rect(screen, color, (x + 8, ty + 4, 20, 16))
        text = font.render(label, True, (230, 230, 230))
        screen.blit(text, (x + 36, ty + 2))
        ty += 24

def draw_goal(screen, scaled_size, goal_cell, border_color=(255, 215, 0)):
    """Goldener Rahmen um die Zielzelle (skalierte Stärke)."""
    cw = scaled_size[0] / GRID_SIZE
    ch = scaled_size[1] / GRID_SIZE
    gx, gy = goal_cell
    rect = pygame.Rect(int(gx * cw), int(gy * ch), int(cw), int(ch))
    thickness = max(2, int(min(cw, ch) * 0.08))
    pygame.draw.rect(screen, border_color, rect, thickness)

