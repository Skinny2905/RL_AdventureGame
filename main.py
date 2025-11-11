import pygame
import random
import json
import os
from datetime import datetime

# --- Konfiguration ---
GRID_SIZE = 10
CELL_SIZE = 50
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 140

SAVE_FILE = "saved_maps.json"

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
    "ui_bg": (20, 20, 20),
    "ui_sel": (100, 100, 100),
    "text": (230, 230, 230),
}

# Stamina-Effekte
STAMINA = {
    "grass": -1,
    "heavy": -3,
    "river": -5,
    "bridge": -1,
    "reward": +20,
    "trap": -50,
    "mountain": None,
    "goal": 0,
}

# --- Utilities for saving/loading maps ---
def load_saved_maps():
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_saved_maps(list_of_maps):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(list_of_maps, f, ensure_ascii=False, indent=2)

# --- Game class ---
class Game:
    def __init__(self):
        self.keep_spawn = False 
        self.previous_scores = []            # history of stamina at goal
        self.saved_maps = load_saved_maps()  # persistent saved maps
        self.current_saved_map_id = None     # id of map currently loaded from saved maps (or None)
        self.reset_game(use_saved=False)

    def reset_game(self, use_saved=False):
        """Reset stamina and either load current_saved_map or generate new map."""
        self.stamina = 50
        if use_saved and self.current_saved_map_id is not None:
            # load that saved map
            found = next((m for m in self.saved_maps if m["id"] == self.current_saved_map_id), None)
            if found:
                self.load_map_data(found["grid"], found["goal_pos"])
                return
        # otherwise generate random map
        self.generate_map()

    # ---------- Map generation ----------
    def generate_map(self):
        # initialize
        self.grid = [["grass" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.field_values = [[STAMINA["grass"] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        # create river as linear path either horizontal or vertical
        orientation = random.choice(["horizontal", "vertical"])
        if orientation == "horizontal":
            # choose a row not too close to border for variety
            y = random.randint(2, GRID_SIZE - 3)
            for x in range(GRID_SIZE):
                self.grid[y][x] = "river"
                self.field_values[y][x] = STAMINA["river"]
            self.river_coords = [(x, y) for x in range(GRID_SIZE)]
        else:
            x = random.randint(2, GRID_SIZE - 3)
            for y in range(GRID_SIZE):
                self.grid[y][x] = "river"
                self.field_values[y][x] = STAMINA["river"]
            self.river_coords = [(x, y) for y in range(GRID_SIZE)]

        # place bridges on straight positions (not on corners) and ensure not many adjacent bridges
        candidates = []
        for (x, y) in self.river_coords:
            # straight positions: river neighbors opposite each other
            # check neighbors in 4 directions for river presence
            left = (x-1, y) if x-1 >= 0 else None
            right = (x+1, y) if x+1 < GRID_SIZE else None
            up = (x, y-1) if y-1 >= 0 else None
            down = (x, y+1) if y+1 < GRID_SIZE else None
            # horizontal straight (left & right are river)
            horizontal = left and right and self.grid[left[1]][left[0]] == "river" and self.grid[right[1]][right[0]] == "river"
            vertical = up and down and self.grid[up[1]][up[0]] == "river" and self.grid[down[1]][down[0]] == "river"
            if horizontal or vertical:
                # exclude edges
                if 0 < x < GRID_SIZE-1 and 0 < y < GRID_SIZE-1:
                    candidates.append((x, y))
        random.shuffle(candidates)
        bridge_count = max(1, len(candidates)//5)
        placed = 0
        for (bx, by) in candidates:
            # ensure no adjacent bridge
            adj_bridge = False
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = bx+dx, by+dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if self.grid[ny][nx] == "bridge":
                        adj_bridge = True
                        break
            if adj_bridge:
                continue
            # replace river with bridge
            self.grid[by][bx] = "bridge"
            self.field_values[by][bx] = STAMINA["bridge"]
            placed += 1
            if placed >= bridge_count:
                break

        # mountains (unpassierbar) - rare
        for _ in range(random.randint(3, 6)):
            rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "mountain"
                self.field_values[ry][rx] = 0

        # heavy terrain
        for _ in range(random.randint(8, 12)):
            rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "heavy"
                self.field_values[ry][rx] = STAMINA["heavy"]

        # rewards & traps (at least one each)
        placed_rewards = 0
        for _ in range(random.randint(1, 3)):
            rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "reward"
                self.field_values[ry][rx] = STAMINA["reward"]
                placed_rewards += 1
        if placed_rewards == 0:
            # force place one
            while True:
                rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                if self.grid[ry][rx] == "grass":
                    self.grid[ry][rx] = "reward"
                    self.field_values[ry][rx] = STAMINA["reward"]
                    break

        placed_traps = 0
        for _ in range(random.randint(1, 3)):
            rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "trap"
                self.field_values[ry][rx] = STAMINA["trap"]
                placed_traps += 1
        if placed_traps == 0:
            while True:
                rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                if self.grid[ry][rx] == "grass":
                    self.grid[ry][rx] = "trap"
                    self.field_values[ry][rx] = STAMINA["trap"]
                    break

        # place start and goal on opposite edges; player spawn must be on grass
        self.place_start_and_goal(orientation)

        # ensure any remaining grass tiles have field value -1
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == "grass":
                    self.field_values[y][x] = STAMINA["grass"]

        # done: reset last_visited for trap/reward conversion logic
        self.last_pos = tuple(self.player_pos)

    def place_start_and_goal(self, orientation):
        # player spawn must be on grass and after map creation
        if orientation == "horizontal":
            # start on left edge (x=0), goal on right edge (x=GRID_SIZE-1)
            # pick random y for start and goal independently but ensure start is grass
            # if chosen start position is not grass, pick another random grass cell anywhere
            sy = random.randint(0, GRID_SIZE-1)
            if self.grid[sy][0] == "grass":
                self.player_pos = [0, sy]
            else:
                # find a random grass cell
                grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
                if grass_cells:
                    self.player_pos = list(random.choice(grass_cells))
                else:
                    self.player_pos = [0, sy]  # fallback
            # place goal at right edge on a grass tile if possible
            gy = random.randint(0, GRID_SIZE-1)
            if self.grid[gy][GRID_SIZE-1] == "grass":
                self.grid[gy][GRID_SIZE-1] = "goal"
                self.field_values[gy][GRID_SIZE-1] = STAMINA["goal"]
                self.goal_pos = [GRID_SIZE-1, gy]
            else:
                # find random grass on border
                border_grass = [(x,y) for y in range(GRID_SIZE) for x in (0, GRID_SIZE-1) if self.grid[y][x] == "grass"]
                if border_grass:
                    gx, gy = random.choice(border_grass)
                    self.grid[gy][gx] = "goal"
                    self.field_values[gy][gx] = STAMINA["goal"]
                    self.goal_pos = [gx, gy]
                else:
                    # fallback to any grass
                    grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
                    if grass_cells:
                        gx, gy = random.choice(grass_cells)
                        self.grid[gy][gx] = "goal"
                        self.field_values[gy][gx] = STAMINA["goal"]
                        self.goal_pos = [gx, gy]
        else:
            # vertical: start top(y=0), goal bottom(y=GRID_SIZE-1)
            sx = random.randint(0, GRID_SIZE-1)
            if self.grid[0][sx] == "grass":
                self.player_pos = [sx, 0]
            else:
                grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
                if grass_cells:
                    self.player_pos = list(random.choice(grass_cells))
                else:
                    self.player_pos = [sx, 0]
            gx = random.randint(0, GRID_SIZE-1)
            if self.grid[GRID_SIZE-1][gx] == "grass":
                self.grid[GRID_SIZE-1][gx] = "goal"
                self.field_values[GRID_SIZE-1][gx] = STAMINA["goal"]
                self.goal_pos = [gx, GRID_SIZE-1]
            else:
                border_grass = [(x,y) for x in range(GRID_SIZE) for y in (0, GRID_SIZE-1) if self.grid[y][x] == "grass"]
                if border_grass:
                    gx, gy = random.choice(border_grass)
                    self.grid[gy][gx] = "goal"
                    self.field_values[gy][gx] = STAMINA["goal"]
                    self.goal_pos = [gx, gy]
                else:
                    grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
                    if grass_cells:
                        gx, gy = random.choice(grass_cells)
                        self.grid[gy][gx] = "goal"
                        self.field_values[gy][gx] = STAMINA["goal"]
                        self.goal_pos = [gx, gy]

    # ---------- Saving/Loading current map ----------
    def export_current_map(self):
        """Export current grid and goal pos to a dict for saving."""
        return {
            "id": datetime.utcnow().isoformat(timespec='seconds'),
            "grid": self.grid,
            "goal_pos": self.goal_pos
        }

    def save_current_map_to_disk(self):
        new_map = self.export_current_map()
        self.saved_maps.append(new_map)
        save_saved_maps(self.saved_maps)

    def load_map_data(self, grid_data, goal_pos):
        """Load grid data from saved map and recompute field_values accordingly."""
        self.grid = [row[:] for row in grid_data]
        self.goal_pos = list(goal_pos)
        # recompute field_values from types
        self.field_values = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                t = self.grid[y][x]
                if t in STAMINA and STAMINA[t] is not None:
                    if t == "grass":
                        self.field_values[y][x] = STAMINA["grass"]
                    else:
                        self.field_values[y][x] = STAMINA[t]
                else:
                    self.field_values[y][x] = 0
        # place player AFTER loading map - find a grass spawn
        grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
        if grass_cells:
            self.player_pos = list(random.choice(grass_cells))
        else:
            self.player_pos = [0, 0]

        self.last_pos = tuple(self.player_pos)

    # ---------- Movement ----------
    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        if not (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE):
            return
        cell_type = self.grid[new_y][new_x]
        if STAMINA[cell_type] is None:
            return  # mountain, unpassierbar

        prev_x, prev_y = self.player_pos
        prev_type = self.grid[prev_y][prev_x]

        # move player
        self.player_pos = [new_x, new_y]

        # apply stamina change from NEW cell
        delta = self.field_values[new_y][new_x]
        self.stamina += delta

        # After moving, if previous tile was trap or reward, convert it to grass with grass stamina (-1)
        if prev_type in ("trap", "reward"):
            self.grid[prev_y][prev_x] = "grass"
            self.field_values[prev_y][prev_x] = STAMINA["grass"]

        # If stepping onto trap/reward we DO NOT immediately convert; conversion happens on leaving (as above)

        # If reach goal -> record stamina and reset to either saved map or new map
        if cell_type == "goal":
            self.previous_scores.append(self.stamina)
            # On reset, stamina resets to 50; if a saved map is selected (current_saved_map_id) it will be used
            self.reset_game(use_saved=(self.current_saved_map_id is not None))

    # ---------- Drawing ----------
    def draw(self, screen, font):
        # draw grid
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                t = self.grid[y][x]
                color = COLORS.get(t, COLORS["grass"])
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0,0,0), rect, 1)
                # draw stamina value for tiles that have numeric effect
                if STAMINA.get(t) is not None:
                    # show current field value
                    val = self.field_values[y][x]
                    txt_col = (255,255,255) if val >= 0 else (255,200,200)
                    txt = font.render(str(val), True, txt_col)
                    txt_rect = txt.get_rect(center=rect.center)
                    screen.blit(txt, txt_rect)

        # draw player
        px, py = self.player_pos
        prect = pygame.Rect(px*CELL_SIZE + 6, py*CELL_SIZE + 6, CELL_SIZE-12, CELL_SIZE-12)
        pygame.draw.rect(screen, COLORS["player"], prect)

        # draw UI area
        ui_y = GRID_SIZE*CELL_SIZE + 6
        pygame.draw.rect(screen, COLORS["ui_bg"], (0, GRID_SIZE*CELL_SIZE, WIDTH, HEIGHT - GRID_SIZE*CELL_SIZE))
        stamina_txt = font.render(f"Stamina: {self.stamina}", True, COLORS["text"])
        screen.blit(stamina_txt, (8, ui_y))

        hist = self.previous_scores[-8:]
        hist_txt = "History (last): " + ", ".join(map(str, hist)) if hist else "No completed rounds yet"
        hist_surf = font.render(hist_txt, True, (200,200,200))
        screen.blit(hist_surf, (8, ui_y + 28))

        saved_count_txt = font.render(f"Saved maps: {len(self.saved_maps)}", True, (180,180,180))
        screen.blit(saved_count_txt, (8, ui_y + 56))


# ---------- Menu handling ----------
class Menu:
    def __init__(self, game):
        self.game = game
        self.active = False
        # <--- "Saved Maps" wieder hinzugefügt, "Keep Spawn" bleibt vorhanden
        self.options = ["Resume", "Load Random Map", "Saved Maps", "Keep Spawn", "Quit"]
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
            elif choice == "Load Random Map":
                self.game.current_saved_map_id = None
                self.game.reset_game(use_saved=False)
                self.active = False
            elif choice == "Saved Maps":
                # open sublist
                if self.game.saved_maps:
                    self.submode = "saved_list"
                    self.saved_sel = 0
                else:
                    # nothing saved -> do nothing
                    pass
            elif choice == "Keep Spawn":
                self.game.keep_spawn = not self.game.keep_spawn   # <--- Toggle Logik
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
        box_w, box_h = 420, 360
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
                # show Keep Spawn status inline
                label = opt
                if opt == "Keep Spawn":
                    label = f"{opt}: {'ON' if getattr(self.game, 'keep_spawn', False) else 'OFF'}"
                txt = font.render(label, True, COLORS["text"])
                screen.blit(txt, (bx+28, y))
            # <-- HINWEIS WIEDERHERGESTELLT -->
            hint = font.render("Up/Down to navigate - Enter to choose - Esc to resume", True, (180,180,180))
            screen.blit(hint, (bx+16, by+box_h-36))


# ---------- Main loop ----------
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
        game.draw(screen, font)
        if menu.active:
            menu.draw(screen, font)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
