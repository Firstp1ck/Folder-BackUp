import tkinter as tk
from tkinter import filedialog
import os
import shutil
from pathlib import Path
import time
import logging

# Configure logging
logging.basicConfig(filename='backup_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Utility functions
def ensure_directory(path: Path):
    """Ensures that the directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def copy_file_with_history(src_file: Path, dst_file: Path, hist_file: Path):
    """Handles the file copying with version history."""
    try:
        if dst_file.exists() and src_file.stat().st_mtime > dst_file.stat().st_mtime:
            shutil.move(dst_file, hist_file)
            logging.info(f"Moved updated file to history: {hist_file}")

        if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
            shutil.copy2(src_file, dst_file)
            logging.info(f"Copied file to backup: {dst_file}")
    except PermissionError as e:
        logging.error(f"Permission denied for {src_file}: {e}")
        raise

def incremental_backup_with_history_and_retry(source_folder: str, backup_folder: str, history_folder: str):
    """Performs incremental backup of files with retry logic."""
    source_folder = Path(source_folder)
    backup_folder = Path(backup_folder)
    history_folder = Path(history_folder)

    ensure_directory(backup_folder)
    ensure_directory(history_folder)

    for src_dir, _, files in os.walk(source_folder):
        dst_dir = backup_folder / Path(src_dir).relative_to(source_folder)
        ensure_directory(dst_dir)
        hist_dir = history_folder / Path(src_dir).relative_to(source_folder)
        ensure_directory(hist_dir)

        for file_ in files:
            src_file = Path(src_dir) / file_
            dst_file = dst_dir / file_
            hist_file = hist_dir / (file_ + "_alt")

            try:
                copy_file_with_history(src_file, dst_file, hist_file)
            except PermissionError:
                logging.warning(f"Retry for {src_file} after permission error.")
                time.sleep(5)  # Wait for 5 seconds and retry
                try:
                    copy_file_with_history(src_file, dst_file, hist_file)
                except PermissionError as e:
                    logging.error(f"Failed second attempt for {src_file}: {e}")

# GUI functions
def select_folder(path_var: tk.StringVar):
    """Opens a dialog to select a folder and updates the path variable."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_var.set(folder_selected)

def start_backup():
    """Starts the backup process."""
    source_folder = source_path_var.get()
    backup_folder = backup_path_var.get()
    history_folder = history_path_var.get()
    try:
        incremental_backup_with_history_and_retry(source_folder, backup_folder, history_folder)
        logging.info("Backup completed successfully.")
    except Exception as e:
        logging.error(f"Backup failed: {e}")

# Tkinter GUI setup
root = tk.Tk()
root.title("Incremental Backup GUI")

source_path_var = tk.StringVar()
backup_path_var = tk.StringVar()
history_path_var = tk.StringVar()

tk.Label(root, text="Source Folder:").grid(row=0, column=0, sticky="w")
tk.Entry(root, textvariable=source_path_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(source_path_var)).grid(row=0, column=2)

tk.Label(root, text="Backup Folder:").grid(row=1, column=0, sticky="w")
tk.Entry(root, textvariable=backup_path_var, width=50).grid(row=1, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(backup_path_var)).grid(row=1, column=2)

tk.Label(root, text="History Folder:").grid(row=2, column=0, sticky="w")
tk.Entry(root, textvariable=history_path_var, width=50).grid(row=2, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(history_path_var)).grid(row=2, column=2)

tk.Button(root, text="Start Backup", command=start_backup).grid(row=3, column=0, columnspan=3)

root.mainloop()