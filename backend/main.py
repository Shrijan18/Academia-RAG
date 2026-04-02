import threading
import os
import sys
import time
import database
import engine
import watcher
from config import DEVICE

def print_banner():
    print("\n" + "="*50)
    print("TALOS RAG BACKEND - ACTIVE")
    print(f"Hardware: {DEVICE}")
    print(f"Watcher: ./data")
    print("Type your question or 'exit' to quit.")
    print("Type 'status' to see indexed files.")
    print("="*50 + "\n")

def show_status():
    """Displays the current state of the vector database."""
    files = database.processed_files
    if not files:
        print("\nDatabase is currently empty.")
    else:
        print(f"\nIndexed Files ({len(files)}):")
        for path, info in files.items():
            print(f"  - {os.path.basename(path)} [{info['hash'][:8]}...]")
    
    if database.text_db:
        print(f"Total Text Vectors: {database.text_db.index.ntotal}")
    if database.audio_index:
        print(f"Total Audio Vectors: {database.audio_index.ntotal}")
    print("")

def main():
    # 1. Ensure Data Directory exists
    data_dir = "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 2. Initialize and Load Database
    print("Initializing Vector Databases...")
    database.init_dbs(data_dir=data_dir)

    # 3. Start File Watcher in a background daemon thread
    watcher_thread = threading.Thread(
        target=watcher.start_file_watcher, 
        args=(data_dir,), 
        daemon=True
    )
    watcher_thread.start()

    print_banner()

    # 4. Interactive Command Loop
    while True:
        try:
            query = input("User >> ").strip()
            
            if not query:
                continue
            
            cmd = query.lower()
            if cmd in ["exit", "quit", "q"]:
                print("Shutting down Talos RAG...")
                database.save_db()
                break
            
            if cmd == "status":
                show_status()
                continue

            # Run full RAG pipeline
            engine.chatbot(query)
            
        except KeyboardInterrupt:
            print("\nForced shutdown. Saving state...")
            database.save_db()
            sys.exit(0)
        except Exception as e:
            print(f"Application Error: {e}")

if __name__ == "__main__":
    main()
