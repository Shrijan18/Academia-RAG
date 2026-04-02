# Talos RAG Backend: Technical Deep-Dive

This document provides a comprehensive analysis of the logic, architectural patterns, and technologies fueling the Talos RAG (Retrieval-Augmented Generation) backend.

---

## 1. Multi-Modal Ingestion Pipeline (`processors.py`)

Talos doesn't just read text; it understands structure and acoustics across diverse formats.

### **A. PDF Processing (PyMuPDF)**
- **Logic**: Uses `PyMuPDFLoader` for high-fidelity text extraction.
- **Chunking**: Employs `RecursiveCharacterTextSplitter` with a `chunk_size` of 1000 and `overlap` of 150.
- **Sanitization**: Implements a custom `clean_text` regex layer to remove redundant whitespace, control characters, and "junk" artifacts that often degrade embedding quality in enterprise documents.

### **B. CSV & Structured Data (Pandas)**
- **Semantic Mapping**: Instead of raw text dumping, each row is transformed into a key-value semantic string: `Column1: Value | Column2: Value`.
- **Row-Level Tracking**: Metadata includes the specific row index, allowing the AI to point users to the exact record in a spreadsheet.

### **C. Dual-Layer Audio Intelligence (Whisper + Wav2Vec2)**
This is a unique feature of Talos. Audio is processed through two distinct AI models:
1.  **Transcription (OpenAI Whisper)**: Generates high-accuracy text with word-level timestamps. The text is chunked into timestamped "documents" (e.g., `[02:15] Discussing the Q3 roadmap`).
2.  **Acoustic Features (Facebook Wav2Vec2)**: Extracted via `librosa` and `torch`. It creates a global "acoustic signature" of the file. This allows for future semantic searches based on tone or "vibe" rather than just words.
- **Memory Safety**: Long audio files are automatically sampled from the center (representative 30s slice) to prevent Out-Of-Memory (OOM) errors while maintaining feature extraction quality.

### **D. Web Scraping (Trafilatura)**
- **Logic**: Uses `trafilatura` for "Main Content Extraction." Unlike basic HTML scrapers, this library intelligently ignores navigation bars, ads, and footers, sending only the relevant article text to the AI.

---

## 2. The Intelligence Layer (`engine.py`)

Talos uses a **Reasoning Stack** designed for both precision and speed.

### **Step 1: Vector Retrieval (FAISS)**
- **Embeddings**: `all-MiniLM-L6-v2` (HuggingFace). Chosen for its excellent balance of speed and performance on CPU.
- **Broad Search**: Performs an initial `similarity_search` with $k=25$ to ensure a wide net is cast across the knowledge base.

### **Step 2: High-Speed Reranking (FlashRank)**
- **The Tech**: Uses `ms-marco-TinyBERT-L-2-v2` via the ONNX runtime.
- **The Logic**: Retrieval-only systems often suffer from "Contextual Noise." FlashRank scores the 25 candidates against the user query using a Cross-Encoder. Only the **Top 7** most relevant results are passed to the LLM. 
- **Benefit**: This significantly increases accuracy and reduces the risk of the LLM hallucinating from irrelevant data.

### **Step 3: Reasoning (Gemini 2.0 Flash)**
- **Implementation**: Orchestrated via `LangChain`.
- **Prompt Engineering**: Uses a sophisticated "System Anchor" that instructs the model to prioritize Document Context but fallback to Conversational Memory when needed.

---

## 3. Short-Term Memory (STM) Architecture

To keep turn-by-turn costs low and responses fast, Talos implements a **Source-Stripped Memory** system.

### **A. Source-Stripping Logic**
InTurn 1, the AI might use 3,000 tokens of PDF text. 
- **Traditional Approach**: Passing the entire Turn 1 into Turn 2. Result: Paying for 3,000 tokens twice.
- **Talos Approach**: Only the User's **Question** and the AI's **Answer** are saved. The raw PDF text is discarded after the response is generated. The AI's answer already contains the distilled knowledge, making the raw source redundant for Turn 2.

### **B. Automated "Sticky Note" Recap (Summarization)**
- **Trigger**: Once history exceeds 6 exchanges.
- **Action**: A background process distills the oldest 4 messages into a concise 2-sentence summary.
- **State**: The summary is pinned to the prompt header, and the detailed history is cleared, keeping only the 2 most recent detailed exchanges.

---

## 4. Storage & Persistence (`database.py`)

### **A. Incremental Indexing**
- **Hashing**: Every file is hashed using **SHA-256**.
- **The Logic**: On startup, Talos compares file hashes. If a file hasn't changed, it **skips ingestion** entirely, drastically speeding up boot times.
- **Surgical Updates**: If a file is modified, the system uses unique IDs (`file_path_index`) to delete only that file's vectors and replace them with new ones.

### **B. File-System Watching (`watcher.py`)**
- Uses the `watchdog` library to monitor the `./data` directory in real-time.
- **Hot-Loading**: Dropping a file into the folder triggers an immediate background ingestion thread. The AI's knowledge base updates while the server is running.

---

## 5. Intelligent Bulk Ingestion

Talos features a high-performance pipeline for bulk document uploads.

### **A. Multi-File Parallelism**
- The `/upload` endpoint can receive multiple files simultaneously via `multipart/form-data`.
- Each file is validated against the **SUPPORTED_EXTENSIONS** list (`.pdf`, `.csv`, `.mp3`, `.wav`, `.txt`, `.m4a`).
- Files are saved directly to the permanent `Data` directory, triggering the real-time `watchdog` service for instant vectorization.

---

## 6. API Gateway (`api.py`)

- **Framework**: Flask with `flask-cors`.
- **Port**: 8000 (standardized for the Talos Frontend).
- **Endpoint Design**:
    - `POST /chat`: The main RAG gateway. Handles stateful memory and retrieval.
    - `GET /status`: Provides a health check and summary of the knowledge base size.
    - `POST /upload`: Secure file ingestion gateway.

---

## 🛠️ Summary of Tech Stack

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Vector DB** | FAISS | Industry-standard speed for CPU search. |
| **Reranker** | FlashRank | Cross-encoding at 10x the speed of standard BERT. |
| **Reasoning** | Gemini 2.0 Flash | State-of-the-art long context and reasoning speed. |
| **Embeddings** | all-MiniLM-L6-v2 | Optimized for low-latency retrieval. |
| **Audio** | Whisper + Wav2Vec2 | Dual-layer transcription and acoustic feature extraction. |
| **Watchdog** | watchdog | Reliable, event-driven knowledge base updates. |
