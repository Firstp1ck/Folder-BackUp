import tkinter as tk
from tkinter import filedialog
import os
import shutil
from pathlib import Path
import time

def incremental_backup_with_history_and_retry(source_folder, backup_folder, history_folder):
    source_folder = Path(source_folder)
    backup_folder = Path(backup_folder)
    history_folder = Path(history_folder)

def incremental_backup_with_history_and_retry(source_folder, backup_folder, history_folder):
    source_folder = Path(source_folder)
    backup_folder = Path(backup_folder)
    history_folder = Path(history_folder)

    # Stellt sicher, dass das Backup- und das History-Verzeichnis existieren
    backup_folder.mkdir(parents=True, exist_ok=True)
    history_folder.mkdir(parents=True, exist_ok=True)

    for src_dir, dirs, files in os.walk(source_folder):
        dst_dir = backup_folder / Path(src_dir).relative_to(source_folder)
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        hist_dir = history_folder / Path(src_dir).relative_to(source_folder)
        hist_dir.mkdir(parents=True, exist_ok=True)

        for file_ in files:
            src_file = Path(src_dir) / file_
            dst_file = dst_dir / file_
            hist_file = hist_dir / (file_ + "_alt")

            # Versucht, die Operation durchzuführen
            try:
                # Wenn eine Datei im Backup existiert und aktualisiert wurde
                if dst_file.exists() and src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    # Verschiebt die alte Datei ins History-Verzeichnis und kennzeichnet sie mit "_alt"
                    shutil.move(dst_file, hist_file)
                
                # Kopiert die Datei, wenn sie im Backup-Verzeichnis nicht existiert
                # oder nach dem Verschieben der alten Version
                if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(src_file, dst_file)
            except PermissionError:
                print(f"Zugriff auf {src_file} nicht möglich, warte kurz.")
                time.sleep(5)  # Wartet 5 Sekunden
                try:
                    shutil.copy2(src_file, dst_file)
                except PermissionError as e:
                    print(f"Erneuter Zugriffsversuch auf {src_file} fehlgeschlagen, überspringe. Fehler: {e}")

    print(f"Inkrementelles Backup mit History und Wiederholungsversuchen wurde erfolgreich erstellt in: {backup_folder}")
    print(f"Alte Versionen wurden gespeichert in: {history_folder}")

def select_source_folder():
    folder_selected = filedialog.askdirectory()
    source_path_var.set(folder_selected)

def select_backup_folder():
    folder_selected = filedialog.askdirectory()
    backup_path_var.set(folder_selected)

def select_history_folder():
    folder_selected = filedialog.askdirectory()
    history_path_var.set(folder_selected)

def start_backup():
    source_folder = source_path_var.get()
    backup_folder = backup_path_var.get()
    history_folder = history_path_var.get()
    incremental_backup_with_history_and_retry(source_folder, backup_folder, history_folder)

# Tkinter GUI setup
root = tk.Tk()
root.title("Incremental Backup GUI")

source_path_var = tk.StringVar()
backup_path_var = tk.StringVar()
history_path_var = tk.StringVar()

tk.Label(root, text="Source Folder:").grid(row=0, column=0, sticky="w")
source_entry = tk.Entry(root, textvariable=source_path_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Select", command=select_source_folder).grid(row=0, column=2)

tk.Label(root, text="Backup Folder:").grid(row=1, column=0, sticky="w")
backup_entry = tk.Entry(root, textvariable=backup_path_var, width=50).grid(row=1, column=1)
tk.Button(root, text="Select", command=select_backup_folder).grid(row=1, column=2)

tk.Label(root, text="History Folder:").grid(row=2, column=0, sticky="w")
history_entry = tk.Entry(root, textvariable=history_path_var, width=50).grid(row=2, column=1)
tk.Button(root, text="Select", command=select_history_folder).grid(row=2, column=2)

tk.Button(root, text="Start Backup", command=start_backup).grid(row=3, column=0, columnspan=3)

root.mainloop()
