# main.py
import pygame
import sys  # <--- NEU: Für Start-Argumente (load)
from constants import WIDTH, HEIGHT, CELL_SIZE, GRID_SIZE, COLORS, STAMINA
from game import Game
from menu import Menu
from storage import load_saved_maps
import random
from q_agent import QAgent
from stats_logger import StatsLogger

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
    pygame.display.set_caption("RL Adventure Game - Final")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    game = Game()
    menu = Menu(game)
    agent = QAgent()
    
    # --- NEU: Start-Argumente prüfen ---
    # Wenn wir 'python main.py load' eingeben, wird das Gehirn direkt geladen
    if len(sys.argv) > 1 and sys.argv[1] == "load":
        print("--> Start-Argument 'load' erkannt! Lade Gehirn...")
        agent.load_model("q_brain.csv")
    else:
        print("--> Start-Argument 'load' NICHT erkannt! Starte mit neuem Gehirn.")

    logger = StatsLogger("training_log.csv")
    episode_count = 1
    current_steps = 0  # Schritte in der aktuellen Runde zählen

    ai_mode = False

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

                    elif event.key == pygame.K_a:
                        ai_mode = not ai_mode
                        print(f"AI Mode: {ai_mode}")

                    elif event.key == pygame.K_s:
                        agent.save_model("q_brain.csv")
                    
                    # NEU: Taste 'L' (Load) - Nur wenn DU es willst!
                    elif event.key == pygame.K_l:
                        agent.load_model("q_brain.csv")
                        
                    # Manuelle Steuerung nur wenn AI aus ist
                    elif not ai_mode:
                        moved = False # Hilfsvariable
                        if event.key == pygame.K_UP: 
                            game.move_player(0, -1)
                            moved = True
                        elif event.key == pygame.K_DOWN: 
                            game.move_player(0, 1)
                            moved = True
                        elif event.key == pygame.K_LEFT: 
                            game.move_player(-1, 0)
                            moved = True
                        elif event.key == pygame.K_RIGHT: 
                            game.move_player(1, 0)
                            moved = True
                        
                        # NEU: Prüfen ob wir im Ziel sind (für den manuellen Spieler)
                        if moved:
                            px, py = game.player_pos
                            if game.grid[py][px] == "goal":
                                print("Ziel erreicht! (Manuell)")
                                game.reset_game(use_saved=(game.current_saved_map_id is not None))
                                
                        # Speichern nur manuell erlaubt
                        elif event.key == pygame.K_m:
                            game.save_current_map_to_disk()
                            game.saved_maps = load_saved_maps()

        # --- AI Logik (Läuft jeden Frame, wenn an) ---
        if ai_mode and not menu.active:
            # 1. Aktuellen Zustand holen
            state = game.get_state()
            
            # 2. Agent entscheidet
            action = agent.get_action(state)
            
            # 3. Spiel führt aus (über unsere neue step-Methode)
            next_state, reward, done = game.step(action)
            current_steps += 1
            
            # 4. Agent lernt
            agent.update_q_table(state, action, reward, next_state, done)
            agent.decay_epsilon()

            # Wenn Runde vorbei, automatisch Neustart für Training
            if done:

                px, py = game.player_pos
                is_at_goal = (game.grid[py][px] == "goal")

                success = True if is_at_goal else False
                outcome_text = "Goal" if success else "Dead"
                
                # 2. Prüfen, ob wir im "Test-Modus" sind
                # Definition: Wir testen, wenn wir quasi keinen Zufall mehr nutzen
                is_testing = True if agent.epsilon < 0.05 else False

                # 3. Statistik schreiben (Smartcab-Style)
                logger.log_episode(
                    trial=episode_count,
                    testing=is_testing,   # <--- NEUE SPALTE
                    steps=current_steps,
                    stamina=game.stamina,
                    epsilon=agent.epsilon,
                    alpha=agent.lr,
                    success=success,      # <--- NEUE SPALTE
                    outcome=outcome_text
                )
                
                print(f"Episode {episode_count}: {outcome_text} (Stamina: {game.stamina}) | Test: {is_testing}")
                
                print(f"Runde {episode_count} beendet. Log gespeichert.")
                
                episode_count += 1
                current_steps = 0 # Reset für nächste Runde

                
                
                if success:
                    # 1. ZIEL ERREICHT: Belohnung! Wir generieren eine NEUE, andere Map.
                    # Wir setzen auch die gespeicherte ID zurück, damit er nicht immer wieder die gleiche lädt, 
                    # falls du vorher eine aus dem Menü gewählt hattest.
                    game.current_saved_map_id = None 
                    game.reset_game(use_saved=False)
                    print("--> Sieg! Neue Map generiert.")
                    
                else:
                    # 2. GESTORBEN: Strafe! Er muss die GLEICHE Map nochmal üben.
                    # Das ist wichtig fürs Lernen: Er muss herausfinden, wie er DIESE Situation löst.
                    game.load_map_data(
                        game.start_map_data["grid"],
                        game.start_map_data["goal_pos"],
                        game.start_map_data.get("player_pos")
                    )
                    print("--> Tot. Map wird neu gestartet (Retry).")
        
        # drawing
        screen.fill((10,10,10))
        draw_game(screen, game, font)
        
        # NEU: Info anzeigen, ob AI läuft
        if ai_mode:
            ai_text = font.render(f"AI ACTIVE | Eps: {agent.epsilon:.2f}", True, (255, 0, 0))
            screen.blit(ai_text, (WIDTH - 150, HEIGHT - 30))

        if menu.active:
            menu.draw(screen, font)

        pygame.display.flip()

        if ai_mode:
            clock.tick(5) # DEINE GESCHWINDIGKEIT BLEIBT BEI 5!
        else:
            clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()