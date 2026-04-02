# Talos RAG: Enterprise Multi-Modal Intelligence

Talos is a high-performance, production-grade Retrieval-Augmented Generation (RAG) system designed to provide deep intelligence across diverse enterprise data formats. It seamlessly integrates text, structured data, and audio into a unified reasoning engine with a high-end, responsive user interface.

## 🚀 Key Features

- **Multi-Modal Ingestion**: Native support for **PDFs**, **CSVs**, **Plain Text**, and **Audio** (MP3/WAV).
- **Conversational Intelligence (STM)**: 
    - Implements a **Source-Stripped Sliding Window** memory.
    - Automates "Sticky Note" summarization to keep context alive while minimizing token usage.
- **Advanced Knowledge Base**:
    - **Folder-Based Navigation**: Data is categorized into smart folders (PDF, CSV, Audio, Text).
    - **Real-Time Reconciliation**: Live sync between your physical root `Data` folder and the AI's memory.
    - **Global Search**: Instant file filtering within the management UI.
    - **Surgical Deletion**: Remove specific files and their mathematical vectors instantly.
- **High-End UI/UX**:
    - **Drive-Style Upload Panel**: Floating bottom-right dashboard to monitor background indexing progress.
    - **Rich Text Support**: Full Markdown rendering with syntax-highlighted code blocks.
    - **Compact Form Factor**: Redesigned, professional modals with high-fidelity glassmorphism.
- **Acoustic Intelligence**: Dual-layer audio processing using **OpenAI Whisper** for transcription and **Wav2Vec2** for semantic acoustic feature extraction.

---

## 🏗️ Architecture

### **Reasoning Stack**
1.  **Retrieval**: FAISS-powered similarity search using `all-MiniLM-L6-v2` embeddings.
2.  **Reranking**: CPU-optimized reranking via **FlashRank** (TinyBERT) for maximum precision.
3.  **Generation**: Powered by **Gemini 2.0 Flash** for state-of-the-art response generation.

### **Backend (Python)**
- **`api.py`**: The RESTful gateway (Port 8000) managing chat, status, and multi-file uploads.
- **`engine.py`**: Orchestrates the RAG pipeline and manages Short-Term Memory state.
- **`database.py`**: Manages FAISS vector stores with incremental SHA-256 hashing.
- **`watcher.py`**: Background service for real-time root `Data` directory monitoring.

### **Frontend (React + TypeScript)**
- **Vite**: Ultra-fast build tool and development server.
- **Framer Motion**: High-fidelity animations and transitions.
- **Lenis**: Smooth inertial scrolling engine.

---

## 🚦 Getting Started

### **1. Prerequisites**
- Python 3.10+
- Node.js 18+
- A Google Gemini API Key

### **2. Backend Setup**
1. Navigate to the `backend` folder: `cd backend`
2. Activate your virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your `GOOGLE_API_KEY` in the `backend/.env` file.
4. Launch the API: `python api.py`

### **3. Frontend Setup**
1. Navigate to the `Frontend` folder: `cd Frontend`
2. Install dependencies: `npm install`
3. Start the UI: `npm run dev`

---

## 📂 Knowledge Management
- **The Data Root**: The system is connected to the **`D:\Coding\Talos_RAG\Data`** directory.
- **Auto-Sync**: Any file dropped into this folder is automatically detected and indexed by the `watcher.py` service.
- **Management**: Use the **Knowledge Base** button in the UI to search, filter, and purge files from the system.

---

## 📜 License
Internal Enterprise Use. (C) 2024 Talos Intelligence Systems.
