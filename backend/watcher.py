import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import database

class FileChangeHandler(FileSystemEventHandler):
    """
    Handles file system events to keep the FAISS index in sync with the data directory.
    """
    def on_modified(self, event):
        if event.is_directory:
            return
        print(f"File modified: {event.src_path}")
        database.add_file_to_db(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        print(f"File created: {event.src_path}")
        database.add_file_to_db(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f"File deleted: {event.src_path}")
        database.remove_file_from_db(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        print(f"File moved: from {event.src_path} to {event.dest_path}")
        database.remove_file_from_db(event.src_path)
        database.add_file_to_db(event.dest_path)

def start_file_watcher(directory):
    """
    Starts the watchdog observer in the background.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created watched directory: {directory}")
        
    observer = Observer()
    event_handler = FileChangeHandler()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"Watcher active on: {os.path.abspath(directory)}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        print(f"Watcher Error: {e}")
        observer.stop()

    observer.join()
