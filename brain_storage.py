import csv
import os
import numpy as np
from collections import defaultdict

class BrainStorage:
    def save(self, q_table, epsilon, filename="q_brain.csv"):
        """Nimmt Daten entgegen und schreibt sie in CSV"""
        print(f"--> Speichere Gehirn nach {filename}...")
        
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["X", "Y", "Q_UP", "Q_DOWN", "Q_LEFT", "Q_RIGHT", "EPSILON"])
            
            for state, q_values in q_table.items():
                x, y = state
                row = [x, y, q_values[0], q_values[1], q_values[2], q_values[3], epsilon]
                writer.writerow(row)
        
        print("--> Speichern abgeschlossen.")

    def load(self, filename="q_brain.csv"):
        """Liest CSV und gibt Q-Table und Epsilon zurück"""
        if not os.path.exists(filename):
            print(f"--> Keine Datei '{filename}' gefunden.")
            return None, None

        print(f"--> Lade Gehirn aus {filename}...")
        
        # Neue leere Tabelle erstellen
        q_table = defaultdict(lambda: np.zeros(4))
        epsilon = 1.0
        
        count = 0
        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Header überspringen
            
            for row in reader:
                if not row: continue
                
                x, y = int(row[0]), int(row[1])
                q_vals = [float(row[2]), float(row[3]), float(row[4]), float(row[5])]
                
                q_table[(x, y)] = np.array(q_vals)
                epsilon = float(row[6]) # Epsilon aus der letzten gelesenen Zeile nehmen
                count += 1
                
        print(f"--> Gehirn geladen! ({count} Zustände)")
        return q_table, epsilon