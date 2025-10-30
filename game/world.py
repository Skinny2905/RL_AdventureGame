from dataclasses import dataclass, field
import numpy as np
from typing import Dict, Tuple, Literal, List, Deque
from collections import deque
from .config import GRID_SIZE

Tile = Literal["tree", "water", "bridge", "log"]

@dataclass
class World:
    n: int = GRID_SIZE
    rng_seed: int | None = None
    objects: Dict[Tuple[int, int], Tile] = field(default_factory=dict)
    point_grid: np.ndarray = field(init=False)

    def __post_init__(self):
        if self.rng_seed is not None:
            np.random.seed(self.rng_seed)
        self.point_grid = self._make_point_grid(self.n)
        self._generate_layout()
        self._ensure_connectivity()  # Pfad von Start zu Ziel sichern

    # 🟩 Punkte-Grid erzeugen
    def _make_point_grid(self, n: int) -> np.ndarray:
        pg = np.zeros((n, n), dtype=int)
        for y in range(1, n - 1):
            for x in range(1, n - 1):
                pg[y, x] = np.random.randint(-5, 6)
        pg[1, 1] = 0               # Startfeld
        pg[n - 2, n - 2] = 0       # Zielfeld
        return pg

    # 🌳 Umgebung generieren
    def _generate_layout(self):
        water_cells = {(2, 2), (2, 3)}
        for c in water_cells:
            self.objects[c] = "water"
        self.objects[(2, 1)] = "bridge"

        for c in [(1, 3), (3, 1), (4, 2)]:
            self.objects[c] = "tree"

        for c in [(3, 3), (1, 4), (4, 4)]:
            self.objects[c] = "log"

        for c in [(1, 1), (self.n - 2, self.n - 2)]:
            self.objects.pop(c, None)

    # 🚧 Blocklogik
    def is_blocking(self, cell: Tuple[int, int]) -> bool:
        return self.objects.get(cell) in {"tree", "water"}

    def _passable(self, cell: Tuple[int, int]) -> bool:
        x, y = cell
        # Nur Innenraum ist begehbar (MiniGrid hat feste Außenwände!)
        if not (1 <= x < self.n - 1 and 1 <= y < self.n - 1):
            return False
        return not self.is_blocking(cell)


    def _neighbors(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = cell
        nb = [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]
        return [c for c in nb if 0 <= c[0] < self.n and 0 <= c[1] < self.n]

    def _has_path(self, start: Tuple[int,int], goal: Tuple[int,int]) -> bool:
        """BFS über passierbare Zellen (Brücke/Log gelten als passierbar)."""
        q: Deque[Tuple[int,int]] = deque([start])
        seen = {start}
        while q:
            c = q.popleft()
            if c == goal:
                return True
            for n in self._neighbors(c):
                if n not in seen and self._passable(n):
                    seen.add(n)
                    q.append(n)
        return False

    # 🛣️ Pfad erzwingen
    def _ensure_connectivity(self):
        start = (1, 1)
        goal  = (self.n - 2, self.n - 2)

        if self._has_path(start, goal):
            return  # alles gut

        # Kein Pfad: einfachen Korridor freischnitzen
        x, y = start
        gx, gy = goal

        while x != gx:
            x += 1 if gx > x else -1
            self.objects.pop((x, y), None)

        while y != gy:
            y += 1 if gy > y else -1
            self.objects.pop((x, y), None)

    # 🔁 Nächste Zelle berechnen
    def next_cell(self, x, y, dir_):
        dxdy = [(1,0),(0,1),(-1,0),(0,-1)][dir_]
        return (x + dxdy[0], y + dxdy[1])

    # 💰 Punkte aufnehmen
    def take_points(self, x: int, y: int) -> int:
        if 0 <= x < self.n and 0 <= y < self.n:
            val = int(self.point_grid[y, x])
            self.point_grid[y, x] = 0
            return val
        return 0
