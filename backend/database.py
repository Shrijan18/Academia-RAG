import os
import faiss
import pickle
import hashlib
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import embeddings
from processors import load_pdf, load_csv, load_audio, load_txt

# Configuration
DB_PATH = "faiss_index"
METADATA_PATH = "faiss_metadata.pkl"

# Global Storage
# text_db: Combined store for PDF, CSV, TXT, and Web
# audio_index: Raw Wav2Vec2 audio feature vectors
text_db = None
audio_index = None
audio_index_map = [] # To track which audio file belongs to which index in audio_index

# Track processed files: { "file_path": { "hash": "...", "ids": [...] } }
processed_files = {}

def get_file_hash(file_path):
    """Generates SHA-256 hash of a file to detect changes."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def save_db():
    """Persists the database and tracking metadata to disk."""
    if text_db:
        text_db.save_local(DB_PATH)
    
    metadata = {
        "processed_files": processed_files,
        "audio_index_map": audio_index_map
    }
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)
    
    if audio_index:
        faiss.write_index(audio_index, "audio_features.index")
    print("Database and metadata saved locally.")

def load_db():
    """Loads the database and tracking metadata from disk."""
    global text_db, processed_files, audio_index, audio_index_map
    
    if os.path.exists(DB_PATH):
        text_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        print("Loaded existing Text Vector Store.")
    
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
            processed_files = metadata.get("processed_files", {})
            audio_index_map = metadata.get("audio_index_map", [])
        print("Loaded Ingestion Metadata.")

    if os.path.exists("audio_features.index"):
        audio_index = faiss.read_index("audio_features.index")
        print("Loaded Audio Feature Index.")
    else:
        audio_index = faiss.IndexFlatL2(768)

def add_file_to_db(file_path):
    """
    Processes a file and adds it to the DB if it's new or changed.
    Supports PDF, CSV, TXT, MP3, WAV.
    """
    global text_db, audio_index
    
    current_hash = get_file_hash(file_path)
    file_ext = os.path.splitext(file_path)[-1].lower()
    
    # Check if file is already processed and unchanged
    if file_path in processed_files and processed_files[file_path]["hash"] == current_hash:
        print(f"Skipping {os.path.basename(file_path)} (Unchanged)")
        return False

    # Remove old version if it exists
    if file_path in processed_files:
        remove_file_from_db(file_path)

    print(f"Ingesting: {os.path.basename(file_path)}")
    
    new_docs = []
    if file_ext == ".pdf":
        new_docs = load_pdf(file_path)
    elif file_ext == ".csv":
        new_docs = load_csv(file_path)
    elif file_ext == ".txt":
        new_docs = load_txt(file_path)
    elif file_ext in [".mp3", ".wav"]:
        audio_docs, audio_embedding = load_audio(file_path)
        new_docs = audio_docs
        if audio_embedding is not None:
            audio_index.add(np.array([audio_embedding]))
            audio_index_map.append(file_path)

    if new_docs:
        # Generate unique IDs for these documents to allow future deletion
        ids = [f"{file_path}_{i}" for i in range(len(new_docs))]
        
        if text_db is None:
            # Initialize with an empty index if needed, but here we can just use the first batch
            # We must pass the ids specifically to maintain tracking consistency
            text_db = FAISS.from_documents(new_docs, embeddings, ids=ids)
        else:
            text_db.add_documents(new_docs, ids=ids)
        
        processed_files[file_path] = {"hash": current_hash, "ids": ids}
        save_db()
        return True
    
    return False

def remove_file_from_db(file_path):
    """Removes a file's documents from the FAISS index."""
    global text_db
    if file_path in processed_files:
        print(f"Removing old index entries for: {file_path}")
        ids_to_remove = processed_files[file_path]["ids"]
        try:
            text_db.delete(ids_to_remove)
        except Exception as e:
            print(f"Warning during deletion: {e}")
        
        del processed_files[file_path]
        
        # Audio feature cleanup (simplified: just reset if file found)
        if file_path in audio_index_map:
            audio_index_map.remove(file_path)
            # Note: faiss.IndexFlatL2 doesn't support easy deletion by ID, 
            # usually requires rebuilding the index for small collections.
        
        save_db()

# Use robust absolute pathing for Data directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # D:\Coding\Talos_RAG\backend
ROOT_DIR = os.path.dirname(SCRIPT_DIR) # D:\Coding\Talos_RAG
DEFAULT_DATA_DIR = os.path.join(ROOT_DIR, "Data") # D:\Coding\Talos_RAG\Data\doc_train

# def init_dbs(data_dir=None):
#     """Scans the data directory and initializes everything."""
#     if data_dir is None:
#         data_dir = DEFAULT_DATA_DIR
        
#     load_db()
    
#     if not os.path.exists(data_dir):
#         os.makedirs(data_dir)
#         print(f"Created data directory: {data_dir}")
        
#     print(f"Initializing Knowledge Base from: {data_dir}")
#     for root, _, files in os.walk(data_dir):
#         for file in files:
#             file_path = os.path.join(root, file)
#             add_file_to_db(file_path)
    
#     # Initialize an empty DB if nothing was found to prevent crashes
#     global text_db
#     if text_db is None:
#         text_db = FAISS.from_texts(["Initial system prompt: System initialized."], embeddings)

def init_dbs(data_dir=None):
    """Scans the data directory and initializes everything without crashing."""
    global text_db
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
        
    # FIX: Only call load_db if the FAISS folder actually exists
    # Replace DB_PATH with the folder name (usually 'faiss_index')
    if os.path.exists(DB_PATH):
        try:
            load_db()
        except Exception as e:
            print(f"⚠️ Could not load existing DB: {e}. Starting fresh ingestion.")
    else:
        print("🚀 No existing database found. Initializing new Knowledge Base...")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")
        
    print(f"Initializing Knowledge Base from: {data_dir}")
    for root, _, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # This handles the 'Ingestion' phase of your RAG pipeline
            add_file_to_db(file_path) 
    
    # Final safety check to prevent frontend crashes
    if text_db is None:
        text_db = FAISS.from_texts(["System initialized: Knowledge Base is empty."], embeddings)
        print("✅ Empty Vector Store created.")