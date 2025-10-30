# game/env_manager.py
import gymnasium as gym
import minigrid  # noqa: F401


class EnvManager:
    """
    Verwaltet die MiniGrid-Umgebung:
    - Erstellen, Zurücksetzen, Step-Ausführung
    - Zugriff auf Beobachtungen, Rewards, etc.
    """

    def __init__(self, env_name: str = "MiniGrid-Empty-5x5-v0", render_mode: str = "rgb_array"):
        self.env = gym.make(env_name, render_mode=render_mode)
        self.obs = None
        self.info = None

    def reset(self):
        """Setzt die Umgebung zurück und gibt Beobachtung + Info zurück."""
        self.obs, self.info = self.env.reset()
        return self.obs, self.info

    def step(self, action):
        """Führt eine Aktion aus und gibt (obs, reward, terminated, truncated, info) zurück."""
        return self.env.step(action)

    def render(self):
        """Gibt das aktuelle Frame der Umgebung zurück."""
        return self.env.render()

    def close(self):
        """Schließt die Umgebung."""
        self.env.close()
