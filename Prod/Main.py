import tkinter as tk
from tkinter import filedialog
import os
import shutil
import threading
from pathlib import Path
import time
import logging
from typing import Union
import configparser

# Configure logging to file and console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

file_handler = logging.FileHandler('backup_log.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Create and configure config parser
config = configparser.ConfigParser()
config_file = 'config.ini'

def load_config():
    """Load configuration from config.ini"""
    if not Path(config_file).exists():
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    config.read(config_file)
    global source_path_var, backup_path_var, history_path_var
    source_path_var.set(config.get('Paths', 'source_folder', fallback=''))
    backup_path_var.set(config.get('Paths', 'backup_folder', fallback=''))
    history_path_var.set(config.get('Paths', 'history_folder', fallback=''))

def save_config():
    """Save configuration to config.ini"""
    if not config.has_section('Paths'):
        config.add_section('Paths')
    config.set('Paths', 'source_folder', source_path_var.get())
    config.set('Paths', 'backup_folder', backup_path_var.get())
    config.set('Paths', 'history_folder', history_path_var.get())
    with open(config_file, 'w') as configfile:
        config.write(configfile)

# Utility functions
def ensure_directory(path: Union[Path, str]):
    """Ensures that the directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

def copy_file_with_history(src_file: Path, dst_file: Path, hist_file: Path):
    """Handles the file copying with version history."""
    try:
        if dst_file.exists() and src_file.stat().st_mtime > dst_file.stat().st_mtime:
            shutil.move(dst_file, hist_file)
            logger.info(f"Moved updated file to history: {hist_file}")

        if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
            shutil.copy2(src_file, dst_file)
            logger.info(f"Copied file to backup: {dst_file}")
    except PermissionError as e:
        logger.error(f"Permission denied for {src_file}: {e}")
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
                logger.warning(f"Retry for {src_file} after permission error.")
                time.sleep(5)  # Wait for 5 seconds and retry
                try:
                    copy_file_with_history(src_file, dst_file, hist_file)
                except PermissionError as e:
                    logger.error(f"Failed second attempt for {src_file}: {e}")

def backup_thread(source_folder: str, backup_folder: str, history_folder: str):
    """Run the backup process in a separate thread, for UI responsiveness."""
    try:
        incremental_backup_with_history_and_retry(source_folder, backup_folder, history_folder)
        logger.info("Backup process finished successfully.")
    except Exception as e:
        logger.error(f"Backup failed: {e}")

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

    # Validate the input paths
    if not source_folder or not Path(source_folder).is_dir():
        logger.error("Invalid source folder.")
        return
    if not backup_folder or not Path(backup_folder).is_dir():
        logger.error("Invalid backup folder.")
        return
    if not history_folder or not Path(history_folder).is_dir():
        logger.error("Invalid history folder.")
        return

    logger.info("Starting backup...")
    save_config()  # Save the current configuration before starting backup
    backup_thread_instance = threading.Thread(target=backup_thread, args=(source_folder, backup_folder, history_folder))
    backup_thread_instance.daemon = True
    backup_thread_instance.start()

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

# Load the configuration when the GUI initializes
load_config()

root.mainloop()