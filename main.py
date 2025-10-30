import pygame
from minigrid.core.actions import Actions
from game.env_manager import EnvManager
from game.world import World
from game.renderer import (
    draw_points,
    draw_objects,
    draw_grid_lines,
    draw_score,
    draw_legend,
    draw_goal,
)
from game.config import GRID_SIZE, WINDOW_BASE, FPS


# Richtungstasten-Mapping
KEY_TO_DIR = {
    pygame.K_RIGHT: 0,
    pygame.K_DOWN: 1,
    pygame.K_LEFT: 2,
    pygame.K_UP: 3,
}


def init_pygame(frame_shape):
    """Initialisiert das Fenster und Fonts basierend auf der Framegröße."""
    pygame.init()
    pygame.display.set_caption("MiniGrid – Adventure (Phase 2)")
    h, w = frame_shape[:2]
    scale = max(1, WINDOW_BASE // max(h, w))
    scaled_size = (w * scale, h * scale)
    screen = pygame.display.set_mode(scaled_size)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)
    return screen, scaled_size, clock, font, small_font


def main():
    # Umgebung und Welt initialisieren
    envm = EnvManager("MiniGrid-Empty-5x5-v0", render_mode="rgb_array")
    obs, info = envm.reset()
    world = World(GRID_SIZE, rng_seed=42)  # deterministisch für Tests
    goal_cell = (GRID_SIZE - 2, GRID_SIZE - 2)  # Ziel unten rechts

    # Fenster initialisieren
    first = envm.render()
    screen, scaled_size, clock, font, small_font = init_pygame(first.shape)
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Spiel beenden
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                # 🔁 Welt neu würfeln (R-Taste)
                elif event.key == pygame.K_r:
                    world = World(GRID_SIZE, rng_seed=None)
                    score = 0
                    goal_cell = (GRID_SIZE - 2, GRID_SIZE - 2)

                # 🔄 Drehung (A-Taste)
                elif event.key == pygame.K_a:
                    _, _, term, trunc, _ = envm.step(Actions.right)
                    if term or trunc:
                        obs, info = envm.reset()
                        world = World(GRID_SIZE)
                        goal_cell = (GRID_SIZE - 2, GRID_SIZE - 2)
                        score = 0

                # 🚶‍♂️ Vorwärtsbewegung (Pfeiltasten)
                elif event.key in KEY_TO_DIR:
                    desired_dir = KEY_TO_DIR[event.key]

                    # Nur bewegen, wenn Blickrichtung passt
                    if desired_dir == envm.env.unwrapped.agent_dir:
                        pos = envm.env.unwrapped.agent_pos
                        x, y = int(pos[0]), int(pos[1])
                        nx, ny = world.next_cell(x, y, desired_dir)

                        # 🚫 Blocklogik: Baum oder Wasser = unpassierbar
                        if (
                            0 <= nx < GRID_SIZE
                            and 0 <= ny < GRID_SIZE
                            and world.is_blocking((nx, ny))
                        ):
                            continue  # keine Bewegung

                        # Schritt ausführen
                        obs, reward, term, trunc, _ = envm.step(Actions.forward)

                        # Punkte sammeln
                        pos = envm.env.unwrapped.agent_pos
                        px, py = int(pos[0]), int(pos[1])
                        score += world.take_points(px, py)

                        # ✅ Ziel erreicht → Reset
                        if (px, py) == goal_cell:
                            obs, info = envm.reset()
                            world = World(GRID_SIZE)
                            goal_cell = (GRID_SIZE - 2, GRID_SIZE - 2)
                            score = 0
                            continue

                        # Falls Episode vorzeitig endet
                        if term or trunc:
                            obs, info = envm.reset()
                            world = World(GRID_SIZE)
                            goal_cell = (GRID_SIZE - 2, GRID_SIZE - 2)
                            score = 0

        # 🖼️ Frame rendern
        frame = envm.render()
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surf = pygame.transform.scale(surf, scaled_size)
        screen.blit(surf, (0, 0))

        # 🔳 Overlays zeichnen
        draw_objects(screen, scaled_size, world.objects)
        draw_points(screen, scaled_size, world.point_grid, small_font)
        draw_grid_lines(screen, scaled_size)
        draw_score(screen, font, score)
        draw_legend(screen, small_font)
        draw_goal(screen, scaled_size, goal_cell)  # 🎯 Zielmarkierung

        # 🕹️ Anzeige aktualisieren
        pygame.display.flip()
        clock.tick(FPS)

    envm.close()
    pygame.quit()


if __name__ == "__main__":
    main()
