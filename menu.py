# menu.py
import pygame
from storage import load_saved_maps
from constants import WIDTH, HEIGHT, COLORS

class Menu:
    def __init__(self, game):
        self.game = game
        self.active = False
        # added "Keep Spawn" option minimally
        self.options = ["Resume", "Smooth", "Load Random Map", "Saved Maps", "Keep Spawn", "Quit"]
        self.sel = 0
        self.submode = None  # None / "saved_list"
        self.saved_sel = 0

    def toggle(self):
        self.active = not self.active
        self.submode = None
        self.sel = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if self.submode == "saved_list":
            if event.key == pygame.K_UP:
                self.saved_sel = max(0, self.saved_sel - 1)
            elif event.key == pygame.K_DOWN:
                self.saved_sel = min(len(self.game.saved_maps) - 1, self.saved_sel + 1)
            elif event.key == pygame.K_RETURN:
                if 0 <= self.saved_sel < len(self.game.saved_maps):
                    chosen = self.game.saved_maps[self.saved_sel]
                    # set as current saved map and load it immediately
                    self.game.current_saved_map_id = chosen["id"]
                    self.game.reset_game(use_saved=True)
                    self.active = False
                    self.submode = None
            elif event.key == pygame.K_ESCAPE:
                self.submode = None
            return None

        # main menu navigation
        if event.key == pygame.K_UP:
            self.sel = max(0, self.sel - 1)
        elif event.key == pygame.K_DOWN:
            self.sel = min(len(self.options)-1, self.sel + 1)
        elif event.key == pygame.K_RETURN:
            choice = self.options[self.sel]
            if choice == "Resume":
                self.active = False
            elif choice == "Smooth":
                self.game.smooth = not self.game.smooth
            elif choice == "Load Random Map":
                self.game.current_saved_map_id = None
                self.game.reset_game(use_saved=False)
                self.active = False
            elif choice == "Saved Maps":
                # open sublist
                if self.game.saved_maps:
                    self.submode = "saved_list"
                    self.saved_sel = 0
            elif choice == "Keep Spawn":
                # Toggle & persist immediately (minimal)
                self.game.keep_spawn = not self.game.keep_spawn
                if self.game.keep_spawn:
                    # store current player_pos as saved spawn
                    if hasattr(self.game, "player_pos") and self.game.player_pos:
                        self.game.saved_spawn_pos = list(self.game.player_pos)
                else:
                    # clear saved spawn
                    self.game.saved_spawn_pos = None
                # save to disk
                if hasattr(self.game, "save_spawn_state"):
                    self.game.save_spawn_state()
            elif choice == "Quit":
                return "quit"
        elif event.key == pygame.K_ESCAPE:
            self.active = False
        return None

    def draw(self, screen, font):
        # overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        screen.blit(overlay, (0,0))
        # menu box
        box_w, box_h = 420, 500
        bx = (WIDTH - box_w)//2
        by = (HEIGHT - box_h)//2
        pygame.draw.rect(screen, (40,40,40), (bx,by,box_w,box_h))
        pygame.draw.rect(screen, (200,200,200), (bx,by,box_w,box_h), 2)
        title = font.render("PAUSED - Menu", True, COLORS["text"])
        screen.blit(title, (bx+16, by+12))
        if self.submode == "saved_list":
            subtitle = font.render("Saved Maps (select):", True, COLORS["text"])
            screen.blit(subtitle, (bx+16, by+48))
            # list saved maps
            for i, m in enumerate(self.game.saved_maps):
                y = by + 80 + i*28
                text = font.render(f"{i+1}. {m['id']}", True, COLORS["text"])
                rect = pygame.Rect(bx+16, y-4, box_w-32, 26)
                if i == self.saved_sel:
                    pygame.draw.rect(screen, COLORS["ui_sel"], rect)
                screen.blit(text, (bx+22, y))
            note = font.render("Enter to load, Esc to back", True, (180,180,180))
            screen.blit(note, (bx+16, by+box_h-36))
        else:
            for i, opt in enumerate(self.options):
                y = by + 70 + i*48
                rect = pygame.Rect(bx+16, y-18, box_w-32, 36)
                if i == self.sel:
                    pygame.draw.rect(screen, COLORS["ui_sel"], rect)
                label = opt
                if opt == "Keep Spawn":
                    label = f"{opt}: {'ON' if getattr(self.game, 'keep_spawn', False) else 'OFF'}"
                txt = font.render(label, True, COLORS["text"])
                if opt == "Smooth":
                    label = f"{opt}: {'ON' if getattr(self.game, 'smooth', False) else 'OFF'}"
                txt = font.render(label, True, COLORS["text"])
                screen.blit(txt, (bx+28, y))
            hint = font.render("Up/Down to navigate - Enter to choose - Esc to resume", True, (180,180,180))
            screen.blit(hint, (bx+16, by+box_h-36))
