#!/usr/bin/python3
import os
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

# Rclone configuration
RCLONE_REMOTE = "your_remote_name"  # Replace with your Rclone remote name
RCLONE_DEST = "your_remote_path"   # Replace with your Rclone destination path

# Directories to monitor
DIRECTORIES_TO_MONITOR = [
    "/shared-data/fresh-data",
    "/shared-data/used-data"]

# Sync interval in seconds
SYNC_INTERVAL = 300  # Sync every 5 minutes


def check_directories(directories):
    for directory in directories:
        if os.path.isdir(directory):
            print(f"Rclone: The directory '{directory}' exists.")
        else:
            print(f"Rclone: The directory '{directory}' does not exist.")


class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:  # Only handle files
            print(f"New file detected: {event.src_path}")
            # No need for immediate exfiltration as sync will handle it

def sync_directories():
    while True:
        for directory in DIRECTORIES_TO_MONITOR:
            print(f"Syncing directory {directory} to {RCLONE_REMOTE}:{RCLONE_DEST}")
            try:
                result = subprocess.run(
                    ["rclone", "sync", directory, f"{RCLONE_REMOTE}:{RCLONE_DEST}"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"Directory {directory} successfully synced.")
                else:
                    print(f"Error syncing directory {directory}: {result.stderr}")
            except Exception as e:
                print(f"Exception during sync: {e}")
        time.sleep(SYNC_INTERVAL)


def monitor_directories():
    event_handler = NewFileHandler()
    observer = Observer()
    for directory in DIRECTORIES_TO_MONITOR:
        print(f"Starting monitor on {directory}")
        observer.schedule(event_handler, directory, recursive=False)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    check_directories(DIRECTORIES_TO_MONITOR)
    
    # Start the sync functionality in a separate thread
    sync_thread = Thread(target=sync_directories, daemon=True)
    sync_thread.start()
    
    # Start monitoring for file changes (optional)
    monitor_directories()
