import pygame
import gymnasium as gym
import minigrid  # noqa: F401
from minigrid.core.actions import Actions

# Mapping MiniGrid-Richtungen: 0=→, 1=↓, 2=←, 3=↑
KEY_TO_DIR = {
    pygame.K_RIGHT: 0,
    pygame.K_DOWN:  1,
    pygame.K_LEFT:  2,
    pygame.K_UP:    3,
}

def main():
    env = gym.make("MiniGrid-Empty-5x5-v0", render_mode="rgb_array")
    obs, info = env.reset(seed=42)

    pygame.init()
    pygame.display.set_caption("MiniGrid – Nur A dreht, Pfeile bewegen")
    clock = pygame.time.Clock()

    # erste Frame holen, um Fenstergröße zu bestimmen
    frame = env.render()
    h, w = frame.shape[:2]

    # 💡 hier skalieren wir auf 512x512 (klassische Minigrid-Größe)
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
                        obs, info = env.reset()
                    continue

                # Pfeiltasten: nur bewegen, wenn Pfeilrichtung == Blickrichtung
                if event.key in KEY_TO_DIR:
                    agent_dir = env.unwrapped.agent_dir
                    desired_dir = KEY_TO_DIR[event.key]
                    if desired_dir == agent_dir:
                        obs, reward, terminated, truncated, info = env.step(Actions.forward)
                        if terminated or truncated:
                            obs, info = env.reset()

        # Rendering + Skalierung
        frame = env.render()
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surf = pygame.transform.scale(surf, scaled_size)
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    env.close()
    pygame.quit()

if __name__ == "__main__":
    main()
