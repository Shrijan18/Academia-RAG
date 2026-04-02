# Talos RAG Backend

Refactored backend for the Talos RAG project. This application provides a unified RAG system for PDFs, CSVs, and Audio files, with real-time file watching and high-quality reranking.

## Project Structure

- **`main.py`**: Entry point. Manages background threads and the user interaction loop.
- **`config.py`**: Configuration, API keys, and model singleton initialization.
- **`processors.py`**: Data extraction logic for PDF, CSV, Audio, and Web Scraping.
- **`database.py`**: FAISS vector store management and incremental updates.
- **`engine.py`**: RAG logic, reranking (BGE), and chatbot integration (Gemini).
- **`watcher.py`**: Real-time file system monitoring using `watchdog`.

## Setup & Execution

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Open `config.py` and add your **Google Gemini API Key** and any other required keys.

3.  **Data Folder**:
    The system watches the `./data` directory for changes. Place your `.pdf`, `.csv`, `.mp3`, or `.wav` files there.

4.  **Run the Backend**:
    ```bash
    python main.py
    ```

## Tech Stack
- **RAG Orchestration**: LangChain
- **Models**: OpenAI Whisper, Wav2Vec2, HuggingFace Embeddings, Gemini 2.0 Flash
- **Vector DB**: FAISS
- **Reranker**: CrossEncoder (ms-marco-MiniLM-L-6-v2)
