import pygame
import sys 
from constants import WIDTH, HEIGHT, CELL_SIZE, GRID_SIZE, COLORS, STAMINA
from game import Game
from menu import Menu
from storage import load_saved_maps
import random
from q_agent import QAgent
from stats_logger import StatsLogger

def draw_game(screen, game, font):
    # 1. Grid zeichnen
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

    # 2. Player zeichnen
    px, py = game.player_pos
    prect = pygame.Rect(px*CELL_SIZE + 6, py*CELL_SIZE + 6, CELL_SIZE-12, CELL_SIZE-12)
    pygame.draw.rect(screen, COLORS["player"], prect)

    # 3. UI Bereich am Boden
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
    pygame.display.set_caption("RL Adventure Game - Final")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    game = Game()
    menu = Menu(game)
    agent = QAgent()
    
    # Start-Argumente prüfen
    if len(sys.argv) > 1 and sys.argv[1] == "load":
        print("--> Start-Argument 'load' erkannt! Lade Gehirn...")
        agent.load_model("q_brain.csv")
    else:
        print("--> Start-Argument 'load' NICHT erkannt! Starte mit neuem Gehirn.")

    logger = StatsLogger("training_log.csv")
    episode_count = 1
    current_steps = 0 

    ai_mode = False
    waiting_for_choice = False # Status für die Abfrage nach Erfolg

    running = True
    while running:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # FALL 1: Menü ist offen
            elif menu.active:
                res = menu.handle_event(event)
                if res == "quit":
                    running = False

            # FALL 2: Ziel erreicht -> Auswahl N oder C
            elif waiting_for_choice:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n: # NEUE MAP
                        game.current_saved_map_id = None 
                        game.reset_game(use_saved=False)
                        waiting_for_choice = False
                        print("--> Neue Map generiert.")
                    elif event.key == pygame.K_c: # WEITERLERNEN (Gleiche Map)
                        game.reset_game(use_saved=(game.current_saved_map_id is not None))
                        waiting_for_choice = False
                        print("--> Lerne auf aktueller Map weiter.")

            # FALL 3: Normales Gameplay (Keys reagieren nur, wenn Fall 1 & 2 aus sind)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu.toggle()
                elif event.key == pygame.K_a:
                    ai_mode = not ai_mode
                    print(f"AI Mode: {ai_mode}")
                elif event.key == pygame.K_s:
                    agent.save_model("q_brain.csv")
                elif event.key == pygame.K_l:
                    agent.load_model("q_brain.csv")
                elif event.key == pygame.K_m:
                    game.save_current_map_to_disk()
                    game.saved_maps = load_saved_maps()
                
                # Manuelle Steuerung (nur wenn AI aus)
                elif not ai_mode:
                    moved = False
                    if event.key == pygame.K_UP: game.move_player(0, -1); moved = True
                    elif event.key == pygame.K_DOWN: game.move_player(0, 1); moved = True
                    elif event.key == pygame.K_LEFT: game.move_player(-1, 0); moved = True
                    elif event.key == pygame.K_RIGHT: game.move_player(1, 0); moved = True
                    
                    if moved:
                        px, py = game.player_pos
                        if game.grid[py][px] == "goal":
                            game.reset_game(use_saved=(game.current_saved_map_id is not None))

        # --- AI LOGIK ---
        if ai_mode and not menu.active and not waiting_for_choice:
            state = game.get_state()
            action = agent.get_action(state)
            next_state, reward, done = game.step(action)
            current_steps += 1
            
            agent.update_q_table(state, action, reward, next_state, done)
            agent.decay_epsilon()

            if done:
                px, py = game.player_pos
                success = (game.grid[py][px] == "goal")
                outcome_text = "Goal" if success else "Dead"
                is_testing = (agent.epsilon < 0.05)

                logger.log_episode(
                    trial=episode_count, testing=is_testing, steps=current_steps,
                    stamina=game.stamina, epsilon=agent.epsilon, alpha=agent.lr,
                    success=success, outcome=outcome_text
                )
                
                print(f"Episode {episode_count}: {outcome_text} | Stamina: {game.stamina}")
                episode_count += 1
                current_steps = 0 
                
                if success:
                    waiting_for_choice = True # Stoppt die AI für die Abfrage
                else:
                    game.reset_game(use_saved=(game.current_saved_map_id is not None))

        # --- DRAWING (Reihenfolge korrigiert!) ---
        screen.fill((10,10,10))  # 1. Hintergrund löschen
        draw_game(screen, game, font) # 2. Spielwelt zeichnen
        
        # 3. Info Overlays
        if ai_mode:
            ai_text = font.render(f"AI ACTIVE | Eps: {agent.epsilon:.2f}", True, (255, 0, 0))
            screen.blit(ai_text, (WIDTH - 150, HEIGHT - 30))

        if waiting_for_choice:
            # Hintergrund-Box für Text
            pygame.draw.rect(screen, (0,0,0), (WIDTH//2-170, HEIGHT//2-20, 340, 50))
            pygame.draw.rect(screen, (255,255,0), (WIDTH//2-170, HEIGHT//2-20, 340, 50), 2)
            choice_txt = font.render("ZIEL ERREICHT! [N] Neue Map | [C] Weiterlernen", True, (255, 255, 0))
            screen.blit(choice_txt, (WIDTH // 2 - 150, HEIGHT // 2))

        if menu.active:
            menu.draw(screen, font)

        pygame.display.flip()
        clock.tick(5 if ai_mode else 30)

    pygame.quit()

if __name__ == "__main__":
    main()