import random
import numpy as np
from collections import defaultdict
from brain_storage import BrainStorage

class QAgent:
    def __init__(self, learning_rate=0.1, discount_factor=0.99, 
                 epsilon_start=1.0, epsilon_decay=0.9995, epsilon_min=0.01):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = defaultdict(lambda: np.zeros(4))

        self.storage = BrainStorage()

    def get_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, 3)
        else:
            return np.argmax(self.q_table[state])

    def update_q_table(self, state, action, reward, next_state, done):
        old_value = self.q_table[state][action]
        
        if done:
            next_max = 0
        else:
            next_max = np.max(self.q_table[next_state])
        
        # Bellman Equation
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[state][action] = new_value

    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, filename="q_brain.csv"):
        """Gibt die Daten an den Speicher-Helfer weiter"""
        self.storage.save(self.q_table, self.epsilon, filename)

    def load_model(self, filename="q_brain.csv"):
        """Fragt den Speicher-Helfer nach Daten"""
        loaded_q, loaded_eps = self.storage.load(filename)
        
        # Wenn Daten gefunden wurden, übernehmen wir sie
        if loaded_q is not None:
            self.q_table = loaded_q
            self.epsilon = loaded_eps
            print(f"--> Agent hat Wissen übernommen. (Epsilon: {self.epsilon:.4f})")        