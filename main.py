import pygame
import random
from game.q_agent import QAgent  # Achte darauf, dass dein QAgent korrekt importiert wird

# --- Spielfeldkonfiguration ---
GRID_SIZE = 10
CELL_SIZE = 50
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 120  # Platz für Punktestand & Historie

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

        # Brücken
        bridge_candidates = [pos for pos in self.river_coords if (pos[0] + pos[1]) % 2 == 0]
        bridge_count = max(1, len(bridge_candidates) // 5)
        random.shuffle(bridge_candidates)
        for bx, by in bridge_candidates[:bridge_count]:
            self.grid[by][bx] = "bridge"
            self.field_scores[by][bx] = SCORES["bridge"]

        # Berge
        for _ in range(random.randint(3, 6)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "mountain"
                self.field_scores[y][x] = 0

        # Schweres Terrain
        for _ in range(random.randint(8, 12)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "heavy"
                self.field_scores[y][x] = SCORES["heavy"]

        # Belohnungen & Fallen
        for _ in range(random.randint(1, 3)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "reward"
                self.field_scores[y][x] = SCORES["reward"]

        for _ in range(random.randint(1, 3)):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x] == "grass":
                self.grid[y][x] = "trap"
                self.field_scores[y][x] = SCORES["trap"]

        self.place_start_and_goal(orientation)

    def place_start_and_goal(self, orientation):
        if orientation == "horizontal":
            sy, gy = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.player_pos = [0, sy]
            self.grid[sy][0] = "grass"
            self.grid[gy][-1] = "goal"
            self.goal_pos = [GRID_SIZE - 1, gy]
        else:
            sx, gx = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.player_pos = [sx, 0]
            self.grid[0][sx] = "grass"
            self.grid[-1][gx] = "goal"
            self.goal_pos = [gx, GRID_SIZE - 1]

    def step(self, action):
        if action == 0:
            dx, dy = 0, -1
        elif action == 1:
            dx, dy = 0, 1
        elif action == 2:
            dx, dy = -1, 0
        elif action == 3:
            dx, dy = 1, 0
        else:
            return tuple(self.player_pos), -100, True

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if not (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE):
            return tuple(self.player_pos), -10, False

        cell_type = self.grid[new_y][new_x]
        if SCORES[cell_type] is None:
            return tuple(self.player_pos), -10, False

        reward = self.field_scores[new_y][new_x]
        self.field_scores[new_y][new_x] = 0
        self.score += reward
        self.player_pos = [new_x, new_y]

        if cell_type in ("reward", "trap"):
            self.grid[new_y][new_x] = "grass"

        done = cell_type == "goal"
        if done:
            self.previous_scores.append(self.score)

        return tuple(self.player_pos), reward, done

    def draw(self, screen, font):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = COLORS[self.grid[y][x]]
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

                val = self.field_scores[y][x]
                if SCORES.get(self.grid[y][x]) is not None:
                    text = font.render(str(val), True, (255, 255, 255))
                    text_rect = text.get_rect(center=rect.center)
                    screen.blit(text, text_rect)

        px, py = self.player_pos
        prect = pygame.Rect(px * CELL_SIZE + 8, py * CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
        pygame.draw.rect(screen, COLORS["player"], prect)

        score_text = font.render(f"Aktuelle Punkte: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (10, HEIGHT - 100))

        hist_text = "Letzte Runden: " + ", ".join(map(str, self.previous_scores[-5:])) if self.previous_scores else "Noch keine Ziele erreicht."
        hist_surface = font.render(hist_text, True, (200, 200, 200))
        screen.blit(hist_surface, (10, HEIGHT - 60))


# --- Training + Live-Visualisierung ---
def train_with_visual(episodes=2000):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Q-Agent live beim Lernen")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    game = Game()
    agent = QAgent(learning_rate=0.1, discount_factor=0.9, epsilon_decay=0.99995)

    for episode in range(episodes):
        game.reset_game()
        state = tuple(game.player_pos)
        done = False
        step_count = 0
        max_steps = 100

        while not done and step_count < max_steps:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return agent

            action = agent.get_action(state)
            next_state, reward, done = game.step(action)
            agent.update_q_table(state, action, reward, next_state, done)
            state = next_state
            step_count += 1

            # --- Fenster zeichnen ---
            screen.fill((0, 0, 0))
            game.draw(screen, font)
            pygame.display.flip()
            clock.tick(5)  # FPS

        agent.decay_epsilon()

        if (episode + 1) % 100 == 0:
            avg_score = sum(game.previous_scores[-100:]) / min(len(game.previous_scores), 100)
            print(f"Episode {episode+1}/{episodes} | Avg Score (letzte 100): {avg_score:.2f} | Epsilon: {agent.epsilon:.3f}")

    pygame.quit()
    return agent


if __name__ == "__main__":
    trained_agent = train_with_visual(episodes=2000)
    print("\nQ-Tabelle (Ausschnitt):")
    for i, (k, v) in enumerate(trained_agent.q_table.items()):
        if i > 10:
            break
        print(f"{k}: {v}")
