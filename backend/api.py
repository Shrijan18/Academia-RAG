import os
import threading
from flask import send_file
from flask import send_from_directory
from flask import Flask, request, jsonify
from flask_cors import CORS
import database
import engine
import watcher
from config import DEVICE
from flask import send_from_directory, abort
from urllib.parse import unquote
import sqlite3
from flask import request, jsonify
from werkzeug.security import check_password_hash
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Explicitly allow all origins for local dev

# Use robust absolute pathing
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(SCRIPT_DIR) 
DATA_DIR = os.path.join(ROOT_DIR, "Data") 

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 1. Connect to the real database file
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 2. Search for the user
    cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    # 3. Verify the hashed password
    if user and check_password_hash(user[0], password):
        return jsonify({
            "success": True, 
            "role": user[1] 
        })
    
    return jsonify({"success": False, "message": "Invalid Credentials"}), 401

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


@app.route('/download/<path:filename>')
def download_file(filename):
    # 1. Decode the URL (turns %20 back into spaces)
    decoded_name = unquote(filename)
    
    # 2. Your EXACT Data directory
    data_dir = r"C:\Users\shrij\Desktop\desktop\minor 6th sem\talos\Talos_RAG\Data"
    
    # 3. Check if file actually exists before sending
    file_path = os.path.join(data_dir, decoded_name)
    print(f"DEBUG: Attempting to serve: {file_path}") # Check your terminal for this!

    if os.path.exists(file_path):
        return send_from_directory(data_dir, decoded_name, as_attachment=True)
    else:
        print(f"DEBUG: File not found at {file_path}")
        return f"File '{decoded_name}' not found on BIT Server.", 404

if __name__ == '__main__':
    startup_logic()
    app.run(host='0.0.0.0', port=8000, debug=False)
