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

# Configuration parser for config-related operations
config = configparser.ConfigParser()
config_file = r'config.ini'

# Logging configuration: we're modularizing this in case future log paths need to be injectable.
def setup_logging(log_file_path: Union[Path, str] = 'backup_log.log'):
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Load and save config from the ini file
def load_config() -> None:
    """Load the configuration from the ini file and set global variables for paths."""
    if not Path(config_file).exists():
        # Initialize config with default paths if not exists
        with open(config_file, 'w') as configfile:
            config.write(configfile)

    config.read(config_file)
    source_path_var.set(config.get('Paths', 'source_folder', fallback=''))
    backup_path_var.set(config.get('Paths', 'backup_folder', fallback=''))
    history_path_var.set(config.get('Paths', 'history_folder', fallback=''))


def save_config() -> None:
    """Save the folder paths to the configuration ini file."""
    if not config.has_section('Paths'):
        config.add_section('Paths')
    config.set('Paths', 'source_folder', source_path_var.get())
    config.set('Paths', 'backup_folder', backup_path_var.get())
    config.set('Paths', 'history_folder', history_path_var.get())
    
    with open(config_file, 'w') as configfile:
        config.write(configfile)

# Utility Function for file handling
def copy_file_with_history(src_file: Path, dst_file: Path, hist_file: Path, retries: int = 5, delay: int = 1) -> None:
    """Handles file copy with retries and version history."""
    try_count = 0
    while try_count < retries:
        try:
            # Move existing file to history if it's older than source
            if dst_file.exists() and src_file.stat().st_mtime > dst_file.stat().st_mtime:
                shutil.move(dst_file, hist_file)
                logger.info(f"Moved to history: {hist_file}")
            
            # Copy the file to the backup if not exists or newer
            if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                shutil.copy2(src_file, dst_file)
                logger.info(f"Copied to backup: {dst_file}")
            break  # Success, break the loop

        except PermissionError as e:
            logger.error(f"Permission denied for {src_file}: {e}")
            try_count += 1
            if try_count < retries:
                logger.warning(f"Retrying {src_file} in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed after {retries} attempts: {e}")
                break
        except Exception as e:
            logger.error(f"Unexpected error: {src_file}, {e}")
            break

# Backup function with incremental logic
def incremental_backup(source_folder: str, backup_folder: str, history_folder: str) -> None:
    """Perform the incremental backup."""
    source = Path(source_folder)
    backup = Path(backup_folder)
    history = Path(history_folder)

    # Ensure backup directories exist
    ensure_directory(backup)
    ensure_directory(history)

    # Walk through the source directory
    for src_dir, _, files in os.walk(source):
        dst_dir = backup / Path(src_dir).relative_to(source)
        hist_dir = history / Path(src_dir).relative_to(source)
        ensure_directory(dst_dir)
        ensure_directory(hist_dir)

        # Copy files with history
        for file_ in files:
            src_file = Path(src_dir) / file_
            dst_file = dst_dir / file_
            hist_file = hist_dir / (file_ + "_alt")
            copy_file_with_history(src_file, dst_file, hist_file)

# Utility to ensure directories exist
def ensure_directory(path: Union[Path, str]) -> None:
    """Ensure that a directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

# Function to run backups in a new thread
def backup_thread(source_folder: str, backup_folder: str, history_folder: str) -> None:
    """Run the backup process inside a separate thread."""
    try:
        incremental_backup(source_folder, backup_folder, history_folder)
        logger.info("Backup process completed.")
    except Exception as e:
        logger.error(f"Backup failure: {e}")

# GUI utility for folder selection and backup starter
def select_folder(path_var: tk.StringVar) -> None:
    """Allow user to select and set the folder path for backup or history."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_var.set(folder_selected)

def start_backup() -> None:
    """Main backup trigger function."""
    source_folder = source_path_var.get()
    backup_folder = backup_path_var.get()
    history_folder = history_path_var.get()

    # Input validation
    if not Path(source_folder).is_dir():
        logger.error("Invalid source folder.")
        return
    if not Path(backup_folder).is_dir():
        logger.error("Invalid backup folder.")
        return
    if not Path(history_folder).is_dir():
        logger.error("Invalid history folder.")
        return
    
    # Save configuration before starting
    save_config()  
    logger.info("Starting backup...")
    
    # Start backup in a separate thread
    backup_worker = threading.Thread(target=backup_thread, args=(source_folder, backup_folder, history_folder))
    backup_worker.daemon = True
    backup_worker.start()

# GUI Setup (Tkinter Window)
root = tk.Tk()
root.title("Incremental Backup System")

source_path_var = tk.StringVar()
backup_path_var = tk.StringVar()
history_path_var = tk.StringVar()

# GUI Layout: Source Folder Selection
tk.Label(root, text="Source Folder:").grid(row=0, column=0, sticky="w")
tk.Entry(root, textvariable=source_path_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(source_path_var)).grid(row=0, column=2)

# GUI Layout: Backup Folder Selection
tk.Label(root, text="Backup Folder:").grid(row=1, column=0, sticky="w")
tk.Entry(root, textvariable=backup_path_var, width=50).grid(row=1, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(backup_path_var)).grid(row=1, column=2)

# GUI Layout: History Folder Selection
tk.Label(root, text="History Folder:").grid(row=2, column=0, sticky="w")
tk.Entry(root, textvariable=history_path_var, width=50).grid(row=2, column=1)
tk.Button(root, text="Select", command=lambda: select_folder(history_path_var)).grid(row=2, column=2)

# Start Backup Button
tk.Button(root, text="Start Backup", command=start_backup).grid(row=3, column=0, columnspan=3)

# Initialize Configuration on startup
load_config()

root.mainloop()