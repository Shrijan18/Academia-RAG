
# 🎓 Academia RAG: Precision Academic Intelligence
**Academia RAG** is a high-fidelity, production-grade **Retrieval-Augmented Generation (RAG)** platform engineered specifically for the **Bhilai Institute of Technology**. It transforms static institutional data into a dynamic, role-aware reasoning engine, providing students and faculty with instant, cited academic clarity.

---

### 🚀 Core Capabilities
* **Context-Aware Reasoning (CAR):** Beyond simple search—the system identifies your **Regulation Batch (R23, R24)** and filters the entire knowledge base to provide batch-specific syllabus and timetable data.
* **Role-Based Access Control (RBAC):** * **Student/Teacher:** High-speed conversational interface for rapid information retrieval.
    * **Admin:** A full-scale **Command Center** for knowledge management and vector maintenance.
* **Multi-Modal Ingestion:** Native processing of academic **PDFs** (Syllabus/Schemes), **CSVs** (Result data), **Plain Text**, and **Audio** resources.
* **Institutional Memory:** Implements a sliding-window context buffer that maintains conversation flow without losing the "thread" of complex academic queries.



[Image of a RAG retrieval-augmented generation process]


---

### 🏗️ The Architecture
#### **The Reasoning Stack**
* **Retrieval:** **FAISS-powered** similarity search utilizing `all-MiniLM-L6-v2` embeddings for semantic mapping.
* **Reranking:** CPU-optimized **FlashRank (TinyBERT)** layer to ensure the most relevant academic chunk always hits the top.
* **Generation:** Orchestrated by the **Gemini 2.5 API** for state-of-the-art natural language synthesis.

#### **Backend (Python)**
* `api.py`: The RESTful gateway (Port 8000) managing secure chat sessions and file uploads.
* `database.py`: The "Librarian"—manages FAISS vector stores with incremental **SHA-256 hashing** to prevent redundant indexing.
* `engine.py`: The brain that orchestrates the RAG pipeline and manages batch-specific metadata filtering.

#### **Frontend (React + TypeScript)**
* **Vite:** For ultra-fast, modern development and deployment.
* **Framer Motion:** Powering high-fidelity UI transitions and "Glassmorphism" effects.
* **Lucide React:** A comprehensive iconography set for a professional enterprise feel.

---

### 🚦 Getting Started
#### **1. Prerequisites**
* Python 3.10+ & Node.js 18+
* A valid **Google Gemini API Key**

#### **2. Backend Ignition**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python api.py
```

#### **3. Frontend Launch**
```bash
cd frontend
npm install
npm run dev
```

---

### 📂 Knowledge Management
* **The Data Root:** Connected directly to the `C:\...\Talos_RAG\Data` directory.
* **Regulation Partitioning:** Smart-folders categorized by **Regulation Year** (2023, 2024, 2025) to ensure zero cross-contamination of academic data.
* **Surgical Purge:** Admins can instantly search, filter, and delete specific document vectors via the **Management UI** to keep the intelligence fresh.

---

### 📜 Institutional Notice
**Developed for the 6th Semester Minor Project Milestone.** © 2026 Academia RAG Systems • Bhilai Institute of Technology (BIT).

---
