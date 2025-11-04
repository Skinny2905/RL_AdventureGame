import pygame
import random

# --- Spielfeldkonfiguration ---
GRID_SIZE = 10
CELL_SIZE = 50
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 120  # Platz für Punktestand & Historie

# Farben
COLORS = {
    "grass": (34, 139, 34),       # Grün
    "heavy": (128, 128, 128),     # Grau
    "river": (0, 0, 139),         # Dunkelblau
    "bridge": (139, 69, 19),      # Braun
    "reward": (255, 215, 0),      # Gold
    "trap": (0, 0, 0),            # Schwarz
    "mountain": (255, 255, 255),  # Weiß
    "goal": (135, 206, 235),      # Hellblau
    "player": (255, 0, 0),        # Rot
}

# Punktwerte
SCORES = {
    "grass": 0,
    "heavy": -1,
    "river": -3,
    "bridge": 0,
    "reward": +5,
    "trap": -5,
    "mountain": None,  # unpassierbar
    "goal": 0,
}


class Game:
    def __init__(self):
        self.previous_scores = []
        self.reset_game()

    def reset_game(self):
        self.grid = [["grass" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.field_scores = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.generate_map()

    def generate_map(self):
        # --- Flussrichtung ---
        orientation = random.choice(["horizontal", "vertical"])

        if orientation == "horizontal":
            y = random.randint(2, GRID_SIZE - 3)
            for x in range(GRID_SIZE):
                self.grid[y][x] = "river"
                self.field_scores[y][x] = SCORES["river"]
            self.river_coords = [(x, y) for x in range(GRID_SIZE)]
        else:
            x = random.randint(2, GRID_SIZE - 3)
            for y in range(GRID_SIZE):
                self.grid[y][x] = "river"
                self.field_scores[y][x] = SCORES["river"]
            self.river_coords = [(x, y) for y in range(GRID_SIZE)]

        # --- Brücken auf sinnvollen Positionen ---
        bridge_candidates = [pos for pos in self.river_coords if (pos[0] + pos[1]) % 2 == 0]
        bridge_count = max(1, len(bridge_candidates)//5)
        random.shuffle(bridge_candidates)
        for bx, by in bridge_candidates[:bridge_count]:
            self.grid[by][bx] = "bridge"
            self.field_scores[by][bx] = SCORES["bridge"]

        # --- Berge (weiß) ---
        for _ in range(random.randint(3, 6)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "mountain"
                self.field_scores[y][x] = 0

        # --- Schweres Terrain (grau) ---
        for _ in range(random.randint(8, 12)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "heavy"
                self.field_scores[y][x] = SCORES["heavy"]

        # --- Belohnungen & Fallen ---
        reward_count = random.randint(1, 3)
        trap_count = random.randint(1, 3)
        for _ in range(reward_count):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "reward"
                self.field_scores[y][x] = SCORES["reward"]

        for _ in range(trap_count):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "trap"
                self.field_scores[y][x] = SCORES["trap"]

        # --- Start und Ziel ---
        self.place_start_and_goal(orientation)

    def place_start_and_goal(self, orientation):
        """Platziere Start- und Zielfeld an gegenüberliegenden Rändern"""
        if orientation == "horizontal":
            # Start links, Ziel rechts
            sy, gy = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            self.player_pos = [0, sy]
            self.grid[sy][0] = "grass"
            self.grid[gy][-1] = "goal"
            self.goal_pos = [GRID_SIZE-1, gy]
        else:
            # Start oben, Ziel unten
            sx, gx = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            self.player_pos = [sx, 0]
            self.grid[0][sx] = "grass"
            self.grid[-1][gx] = "goal"
            self.goal_pos = [gx, GRID_SIZE-1]

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        if not (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE):
            return
        cell_type = self.grid[new_y][new_x]
        if SCORES[cell_type] is None:
            return  # unpassierbar

        # Punkte verrechnen
        field_value = self.field_scores[new_y][new_x]
        self.score += field_value
        self.field_scores[new_y][new_x] = 0  # Punkte "verbraucht"

        # Falle oder Belohnung wird nach Betreten zu Gras
        if cell_type in ("reward", "trap"):
            self.grid[new_y][new_x] = "grass"

        # Spieler bewegen
        self.player_pos = [new_x, new_y]

        # Ziel erreicht?
        if cell_type == "goal":
            self.previous_scores.append(self.score)
            self.reset_game()

    def draw(self, screen, font):
        # Karte zeichnen
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = COLORS[self.grid[y][x]]
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

                # Punktewert anzeigen (falls sichtbar)
                val = self.field_scores[y][x]
                if SCORES.get(self.grid[y][x]) is not None:
                    text = font.render(str(val), True, (255, 255, 255))
                    text_rect = text.get_rect(center=rect.center)
                    screen.blit(text, text_rect)

        # Spieler zeichnen
        px, py = self.player_pos
        prect = pygame.Rect(px * CELL_SIZE + 8, py * CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
        pygame.draw.rect(screen, COLORS["player"], prect)

        # Aktuelle Punkte
        score_text = font.render(f"Aktuelle Punkte: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (10, HEIGHT - 100))

        # Punkt-Historie
        hist_text = "Letzte Runden: " + ", ".join(map(str, self.previous_scores[-5:])) if self.previous_scores else "Noch keine Ziele erreicht."
        hist_surface = font.render(hist_text, True, (200, 200, 200))
        screen.blit(hist_surface, (10, HEIGHT - 60))


# --- Hauptprogramm ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Grid-Abenteuer mit Ziel, Punkten & Historie")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    game.move_player(0, -1)
                elif event.key == pygame.K_DOWN:
                    game.move_player(0, 1)
                elif event.key == pygame.K_LEFT:
                    game.move_player(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move_player(1, 0)

        screen.fill((0, 0, 0))
        game.draw(screen, font)
        pygame.display.flip()
        clock.tick(10)

    pygame.quit()


if __name__ == "__main__":
    main()
