# game.py
import random
from datetime import datetime
from constants import GRID_SIZE, STAMINA
from storage import load_saved_maps, save_saved_maps, load_spawn_settings, save_spawn_settings

class Game:
    def __init__(self):
        # load persistent spawn settings (minimal)
        s = load_spawn_settings()
        self.keep_spawn = s.get("keep_spawn", False)
        self.saved_spawn_pos = s.get("spawn_pos", None)

        self.previous_scores = []            # history of stamina at goal
        self.saved_maps = load_saved_maps()  # persistent saved maps
        self.current_saved_map_id = None     # id of map currently loaded from saved maps (or None)
        self.reset_game(use_saved=False)

    # minimal helper to persist spawn state
    def save_spawn_state(self):
        save_spawn_settings({"keep_spawn": self.keep_spawn, "spawn_pos": self.saved_spawn_pos})

    def reset_game(self, use_saved=False):
        """Reset stamina and either load current_saved_map or generate new map."""
        self.stamina = 100
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

        # place bridges on straight positions
        candidates = []
        for (x, y) in self.river_coords:
            left = (x-1, y) if x-1 >= 0 else None
            right = (x+1, y) if x+1 < GRID_SIZE else None
            up = (x, y-1) if y-1 >= 0 else None
            down = (x, y+1) if y+1 < GRID_SIZE else None
            horizontal = left and right and self.grid[left[1]][left[0]] == "river" and self.grid[right[1]][right[0]] == "river"
            vertical = up and down and self.grid[up[1]][up[0]] == "river" and self.grid[down[1]][down[0]] == "river"
            if horizontal or vertical:
                if 0 < x < GRID_SIZE-1 and 0 < y < GRID_SIZE-1:
                    candidates.append((x, y))
        random.shuffle(candidates)
        bridge_count = max(1, len(candidates)//5)
        placed = 0
        for (bx, by) in candidates:
            adj_bridge = False
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = bx+dx, by+dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if self.grid[ny][nx] == "bridge":
                        adj_bridge = True
                        break
            if adj_bridge:
                continue
            self.grid[by][bx] = "bridge"
            self.field_values[by][bx] = STAMINA["bridge"]
            placed += 1
            if placed >= bridge_count:
                break

        # mountains
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

        # rewards & traps
        placed_rewards = 0
        for _ in range(random.randint(1, 3)):
            rx, ry = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[ry][rx] == "grass":
                self.grid[ry][rx] = "reward"
                self.field_values[ry][rx] = STAMINA["reward"]
                placed_rewards += 1
        if placed_rewards == 0:
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

        # place start and goal on grass
        self.place_start_and_goal(orientation)

        # ensure remaining grass has proper field value
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == "grass":
                    self.field_values[y][x] = STAMINA["grass"]

        self.last_pos = tuple(self.player_pos)

        self.start_map_data = self.export_current_map()

    # ---------- Place player and goal ----------
    def place_start_and_goal(self, orientation):
        def find_nearby_grass(x, y):
            if self.grid[y][x] == "grass":
                return x, y
            for radius in range(1, GRID_SIZE):
                for dy in range(-radius, radius+1):
                    for dx in range(-radius, radius+1):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            if self.grid[ny][nx] == "grass":
                                return nx, ny
            grass_cells = [(gx,gy) for gy in range(GRID_SIZE) for gx in range(GRID_SIZE) if self.grid[gy][gx] == "grass"]
            return random.choice(grass_cells) if grass_cells else (x,y)

        # Player spawn
        if getattr(self, "keep_spawn", False) and getattr(self, "saved_spawn_pos", None):
            sx, sy = self.saved_spawn_pos
            sx, sy = find_nearby_grass(sx, sy)
            self.player_pos = [sx, sy]

        if not hasattr(self, "player_pos") or not self.player_pos:
            if orientation == "horizontal":
                sy = random.randint(0, GRID_SIZE-1)
                sx, sy = find_nearby_grass(0, sy)
                self.player_pos = [sx, sy]
            else:
                sx = random.randint(0, GRID_SIZE-1)
                sx, sy = find_nearby_grass(sx, 0)
                self.player_pos = [sx, sy]

        if getattr(self, "keep_spawn", False):
            self.saved_spawn_pos = list(self.player_pos)
            self.save_spawn_state()

        # Goal placement
        if orientation == "horizontal":
            gx, gy = GRID_SIZE-1, random.randint(0, GRID_SIZE-1)
        else:
            gx, gy = random.randint(0, GRID_SIZE-1), GRID_SIZE-1

        gx, gy = find_nearby_grass(gx, gy)
        self.grid[gy][gx] = "goal"
        self.field_values[gy][gx] = STAMINA["goal"]
        self.goal_pos = [gx, gy]

    # ---------- Saving/Loading current map ----------
    def export_current_map(self):
        return {
            "id": datetime.utcnow().isoformat(timespec='seconds'),
            "grid": self.grid,
            "goal_pos": self.goal_pos,
            "player_pos": list(self.player_pos)
        }

    def save_current_map_to_disk(self):
        new_map = self.export_current_map()
        self.saved_maps.append(new_map)
        save_saved_maps(self.saved_maps)

    # Ersetze die ganze Methode load_map_data hiermit:

    def load_map_data(self, grid_data, goal_pos, player_pos=None): # <--- WICHTIG: player_pos=None muss hier stehen!
        self.stamina = 100  # <--- NEU: Tank auffüllen! WICHTIG!
        
        self.grid = [row[:] for row in grid_data]
        self.grid = [row[:] for row in grid_data]
        self.goal_pos = list(goal_pos)
        self.field_values = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Stamina-Werte wiederherstellen
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                t = self.grid[y][x]
                if t in STAMINA and STAMINA[t] is not None:
                    self.field_values[y][x] = STAMINA[t] if t != "grass" else STAMINA["grass"]
        
        # --- HIER WAR DER FEHLER (Doppelter Code) ---
        # Jetzt machen wir es richtig: Entweder gespeicherte Position ODER Zufall.
        if player_pos:
            self.player_pos = list(player_pos)
        else:
            # Fallback: Zufällig (nur wenn keine Position übergeben wurde)
            grass_cells = [(x,y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if self.grid[y][x] == "grass"]
            self.player_pos = list(random.choice(grass_cells)) if grass_cells else [0,0]
        
        self.last_pos = tuple(self.player_pos)

        # Start-Daten sichern (falls noch nicht geschehen)
        if not hasattr(self, "start_map_data") or self.start_map_data is None:
             self.start_map_data = self.export_current_map()


    # ---------- Movement ----------
    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        if not (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE):
            return
        cell_type = self.grid[new_y][new_x]
        if STAMINA[cell_type] is None:
            return
        prev_x, prev_y = self.player_pos
        prev_type = self.grid[prev_y][prev_x]
        self.player_pos = [new_x, new_y]
        self.stamina += self.field_values[new_y][new_x]
        if prev_type in ("trap", "reward"):
            self.grid[prev_y][prev_x] = "grass"
            self.field_values[prev_y][prev_x] = STAMINA["grass"]
        if cell_type == "goal":
            self.previous_scores.append(self.stamina)
            #self.reset_game(use_saved=(self.current_saved_map_id is not None))
            pass
    # ---------- Drawing ----------
        def draw(self, screen, font, COLORS):
            # draw grid
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    rect = __import__("pygame").Rect(x*__import__("constants").CELL_SIZE, y*__import__("constants").CELL_SIZE, __import__("constants").CELL_SIZE, __import__("constants").CELL_SIZE)
                    # but to avoid circular import issues when calling draw from main we will just use screen coordinates directly in main
        # NOTE: draw is implemented in main to avoid circular imports
# ... (der ganze restliche Code der Klasse Game bleibt gleich) ...

    # --- NEU FÜR DEN AGENTEN ---
    
    def get_state(self):
        """Gibt die aktuelle Position als Tuple zurück (für die Q-Table)"""
        return tuple(self.player_pos)

    def step(self, action):
        """
        Führt einen Schritt für den KI-Agenten aus.
        Action: 0=Up, 1=Down, 2=Left, 3=Right
        Return: (next_state, reward, done)
        """
        # 1. Aktion in Bewegung umwandeln
        dx, dy = 0, 0
        if action == 0: dy = -1   # Up
        elif action == 1: dy = 1  # Down
        elif action == 2: dx = -1 # Left
        elif action == 3: dx = 1  # Right
        
        # Alten Stamina-Wert merken, um Reward zu berechnen
        old_stamina = self.stamina
        
        # 2. Bewegung ausführen (nutzt die existierende Logik!)
        self.move_player(dx, dy)
        
        # 3. Reward berechnen (Differenz der Stamina)
        # Wenn wir in eine Falle laufen, sinkt Stamina stark -> negativer Reward
        # Wenn wir ein Reward-Feld finden, steigt sie -> positiver Reward
        reward = self.stamina - old_stamina
        
        # Wenn die Bewegung ungültig war (Wand), gab es keine Stamina-Änderung.
        # Wir wollen den Agenten aber bestrafen, wenn er gegen Wände läuft.
        if reward == 0:
            reward = -5  # Strafe für "Gegen die Wand laufen"

        # 4. Status prüfen
        done = False
        
        # Ziel erreicht? (Prüfung auf Feld-Typ)
        px, py = self.player_pos
        if self.grid[py][px] == "goal":
            done = True
            reward += 500 # Extra Bonus fürs Ziel
            
        # Tot? (Stamina leer)
        if self.stamina <= 0:
            done = True
            reward -= 100 # Strafe fürs Sterben

        next_state = self.get_state()
        return next_state, reward, done