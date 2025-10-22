import pygame
import gymnasium as gym
import minigrid  # noqa: F401
from minigrid.core.actions import Actions
import numpy as np

# Mapping MiniGrid-Richtungen: 0=→, 1=↓, 2=←, 3=↑
KEY_TO_DIR = {
    pygame.K_RIGHT: 0,
    pygame.K_DOWN:  1,
    pygame.K_LEFT:  2,
    pygame.K_UP:    3,
}

def main():
    env = gym.make("MiniGrid-Empty-5x5-v0", render_mode="rgb_array")

    grid_size = 5

    # 🧩 Hilfsfunktion für kompletten Reset (Umgebung + Punkte + Score)
    def reset_game():
        obs, info = env.reset()
        # Punktgrid mit Nullen erstellen
        pg = np.zeros((grid_size, grid_size), dtype=int)
        # Zufällige Punkte nur innerhalb des Rands
        for y in range(1, grid_size - 1):
            for x in range(1, grid_size - 1):
                pg[y, x] = np.random.randint(-5, 6)
        # Start- und Zielposition auf 0
        pg[1, 1] = 0
        pg[grid_size - 2, grid_size - 2] = 0
        # Score zurücksetzen
        return obs, info, pg, 0

    # Initiales Setup
    obs, info, point_grid, score = reset_game()

    pygame.init()
    pygame.display.set_caption("MiniGrid – Punkte sammeln!")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)

    frame = env.render()
    h, w = frame.shape[:2]
    SCALE = 512 // max(h, w)
    scaled_size = (w * SCALE, h * SCALE)
    screen = pygame.display.set_mode(scaled_size)

    running = True
    while running:
        # Eingaben abfragen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                    break

                # Nur A darf drehen (90° rechts)
                if event.key == pygame.K_a:
                    obs, reward, terminated, truncated, info = env.step(Actions.right)
                    if terminated or truncated:
                        obs, info, point_grid, score = reset_game()
                    continue

                # Pfeiltasten: nur bewegen, wenn Pfeilrichtung == Blickrichtung
                if event.key in KEY_TO_DIR:
                    agent_dir = env.unwrapped.agent_dir
                    desired_dir = KEY_TO_DIR[event.key]
                    if desired_dir == agent_dir:
                        obs, reward, terminated, truncated, info = env.step(Actions.forward)

                        # Neue Position holen
                        new_pos = env.unwrapped.agent_pos
                        x, y = int(new_pos[0]), int(new_pos[1])

                        # Punkte hinzufügen/abziehen, wenn vorhanden
                        if 0 <= x < grid_size and 0 <= y < grid_size:
                            score += point_grid[y, x]
                            point_grid[y, x] = 0  # Feld geleert

                        # Wenn Spiel endet -> alles zurücksetzen
                        if terminated or truncated:
                            obs, info, point_grid, score = reset_game()

        # Rendering + Skalierung
        frame = env.render()
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surf = pygame.transform.scale(surf, scaled_size)
        screen.blit(surf, (0, 0))

        # Punkte auf Grid zeichnen
        cell_size = scaled_size[0] / grid_size
        for j in range(grid_size):
            for i in range(grid_size):
                val = point_grid[j, i]
                if val != 0:
                    text = small_font.render(str(val), True, (255, 255, 255))
                    tx = int(i * cell_size + cell_size / 2 - text.get_width() / 2)
                    ty = int(j * cell_size + cell_size / 2 - text.get_height() / 2)
                    screen.blit(text, (tx, ty))

        # Score anzeigen
        score_text = font.render(f"Punkte: {score}", True, (255, 255, 0))
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(30)

    env.close()
    pygame.quit()

if __name__ == "__main__":
    main()

