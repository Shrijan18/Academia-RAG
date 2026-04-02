import os
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import database
import engine
import watcher
from config import DEVICE

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Explicitly allow all origins for local dev

# Use robust absolute pathing
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(SCRIPT_DIR) 
DATA_DIR = os.path.join(ROOT_DIR, "Data") 

def startup_logic():
    """Initializes the database and starts the file watcher."""
    print(f"Targeting Data Directory: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    print("Initializing Vector Databases...")
    database.init_dbs(data_dir=DATA_DIR)
    
    # Start watcher in background
    watcher_thread = threading.Thread(
        target=watcher.start_file_watcher, 
        args=(DATA_DIR,), 
        daemon=True
    )
    watcher_thread.start()
    print(f"Background File Watcher Started on: {DATA_DIR}")

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_query = data.get("query")
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    try:
        result = engine.chatbot(user_query)
        return jsonify({"response": result.get("answer"), "sources": result.get("sources", [])})
    except Exception as e:
        print(f"🔥 CHATBOT CRASHED: {e}") # Add this line!
        import traceback
        traceback.print_exc() # This will show exactly which line failed
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    indexed_files = database.processed_files
    disk_files = []
    if os.path.exists(DATA_DIR):
        disk_files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    
    print(f"Status Request: Found {len(disk_files)} files on disk.")
    inventory = []
    for filename in disk_files:
        full_path = os.path.join(DATA_DIR, filename)
        is_indexed = full_path in indexed_files
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        category = 'txt'
        if ext == 'pdf': category = 'pdf'
        elif ext == 'csv': category = 'csv'
        elif ext in ['mp3', 'wav', 'm4a']: category = 'audio'

        inventory.append({
            "id": filename,
            "name": filename,
            "full_path": full_path,
            "type": category,
            "status": "indexed" if is_indexed else "pending",
            "vectors": len(indexed_files[full_path]["ids"]) if is_indexed else 0,
            "size": f"{round(os.path.getsize(full_path) / 1024, 1)} KB"
        })

    return jsonify({
        "status": "online",
        "total_vectors": database.text_db.index.ntotal if database.text_db else 0,
        "device": str(DEVICE),
        "inventory": inventory
    })

@app.route('/delete', methods=['DELETE'])
def delete_file():
    data = request.json
    file_path = data.get("file_path")
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
    try:
        database.remove_file_from_db(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"message": f"File {os.path.basename(file_path)} purged successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle both single 'file' and multiple 'files' keys
    uploaded_files = []
    if 'file' in request.files:
        uploaded_files.append(request.files['file'])
    if 'files' in request.files:
        uploaded_files.extend(request.files.getlist('files'))
    
    if not uploaded_files:
        return jsonify({"error": "No files provided"}), 400
    
    count = 0
    for file in uploaded_files:
        if file.filename == '':
            continue
        file_path = os.path.join(DATA_DIR, file.filename)
        file.save(file_path)
        count += 1
    
    return jsonify({"message": f"Successfully uploaded {count} files for indexing."}), 201

if __name__ == '__main__':
    startup_logic()
    app.run(host='0.0.0.0', port=8000, debug=False)
