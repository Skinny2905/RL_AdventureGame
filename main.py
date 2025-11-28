# main.py
import pygame
from constants import WIDTH, HEIGHT, CELL_SIZE, GRID_SIZE, COLORS, STAMINA
from game import Game
from menu import Menu
from storage import load_saved_maps
import random

def draw_game(screen, game, font):
    # draw grid (same visuals as before)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            t = game.grid[y][x]
            color = COLORS.get(t, COLORS["grass"])
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 1)
            if STAMINA.get(t) is not None:
                val = game.field_values[y][x]
                txt_col = (255,255,255) if val >= 0 else (255,200,200)
                txt = font.render(str(val), True, txt_col)
                txt_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, txt_rect)

    # draw player
    px, py = game.player_pos
    prect = pygame.Rect(px*CELL_SIZE + 6, py*CELL_SIZE + 6, CELL_SIZE-12, CELL_SIZE-12)
    pygame.draw.rect(screen, COLORS["player"], prect)

    # draw UI area
    ui_y = GRID_SIZE*CELL_SIZE + 6
    pygame.draw.rect(screen, COLORS["ui_bg"], (0, GRID_SIZE*CELL_SIZE, WIDTH, HEIGHT - GRID_SIZE*CELL_SIZE))
    stamina_txt = font.render(f"Stamina: {game.stamina}", True, COLORS["text"])
    screen.blit(stamina_txt, (8, ui_y))

    hist = game.previous_scores[-8:]
    hist_txt = "History (last): " + ", ".join(map(str, hist)) if hist else "No completed rounds yet"
    hist_surf = font.render(hist_txt, True, (200,200,200))
    screen.blit(hist_surf, (8, ui_y + 28))

    saved_count_txt = font.render(f"Saved maps: {len(game.saved_maps)}", True, (180,180,180))
    screen.blit(saved_count_txt, (8, ui_y + 56))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Grid-Stamina-Spiel")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    game = Game()
    menu = Menu(game)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif menu.active:
                res = menu.handle_event(event)
                if res == "quit":
                    running = False
            else:
                # gameplay keys
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        menu.toggle()
                    elif event.key == pygame.K_m:
                        # save current map
                        game.save_current_map_to_disk()
                        # reload saved maps from disk to reflect saved id
                        game.saved_maps = load_saved_maps()
                    elif event.key == pygame.K_UP:
                        game.move_player(0, -1)
                    elif event.key == pygame.K_DOWN:
                        game.move_player(0, 1)
                    elif event.key == pygame.K_LEFT:
                        game.move_player(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move_player(1, 0)

        # drawing
        screen.fill((10,10,10))
        draw_game(screen, game, font)
        if menu.active:
            menu.draw(screen, font)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
