import csv
import os

class StatsLogger:
    def __init__(self, filename="training_log.csv"):
        self.filename = filename
        
        # Wenn die Datei neu ist, erstellen wir sie mit den Smartcab-Spalten
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                # NEU: 'testing' und 'success' hinzugefügt
                writer.writerow(["trial", "testing", "steps", "stamina_left", "epsilon", "alpha", "success", "outcome"])

    def log_episode(self, trial, testing, steps, stamina, epsilon, alpha, success, outcome):
        """Schreibt eine Zeile mit allen Details"""
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                trial, 
                testing,      # True/False
                steps, 
                stamina, 
                round(epsilon, 4), 
                alpha,
                success,      # True/False (oder 1/0)
                outcome       # "Goal"/"Dead" (für Lesbarkeit)
            ])