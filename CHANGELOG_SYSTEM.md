# Changelog: Talos RAG Integration & Optimization

This log details the specific technical changes made to bridge the Talos RAG Backend (Python) with its High-End React Frontend.

## [2024-03-03] - System Integration & API Alignment

### 🚀 Major Enhancements
- **Connected Frontend to Backend**: Synchronized the Python Flask API with the React `api.ts` service.
- **Port Remapping**: Switched Backend from port `5000` to port `8000` to match the frontend's hardcoded expectations.
- **Endpoint Redesign**: Renamed `/query` to `/chat` and updated payload handling to support structured responses.
- **CORS Integration**: Added `flask-cors` to enable secure Cross-Origin Resource Sharing between the Vite frontend and Flask backend.

### 🧠 RAG Engine Improvements (`backend/engine.py`)
- **Structured Source Return**: Refactored the `chatbot` function to return a dictionary including both the AI's answer and an array of `sources` (content, scores, and metadata). This enables the frontend to display citations.
- **Model Version Bump**: Standardized on `gemini-2.0-flash` for the primary LLM to ensure optimal performance and long-context handling.
- **Score Formatting**: Ensured reranking scores are returned as native floats for JSON serialization.

### 🌐 API Updates (`backend/api.py`)
- **JSON Serialization**: Improved the `/chat` route to handle various result types and ensure consistent JSON responses.
- **Status API Overhaul**: Updated `/status` to include the number of indexed files and total vector counts, providing a clearer view of the Knowledge Base state.

### 📄 Documentation Updates
- **Backend README & DOCUMENTATION.md**: Reflected the new API structure, port, and response formats.
- **System Flow Diagramming**: Added a detailed breakdown of the 5-step RAG pipeline to the internal docs.

## [2024-03-03] - Enhanced Chat UI (Rich Text & Markdown)

### ✨ UI/UX Enhancements
- **Markdown Rendering**: Integrated `react-markdown` and `remark-gfm` to support bold, italics, tables, and lists.
- **Syntax Highlighting**: Added `react-syntax-highlighter` (Prism) with `vscDarkPlus` theme for beautiful code blocks.
- **Code Copy Feature**: Implemented a "Copy code" button for all code blocks with visual feedback.
- **Inline Code Styling**: Styled inline code snippets with a subtle bronze background to match the "Talos" aesthetic.
- **Responsive Tables**: Added a scrollable wrapper and custom styling for Markdown tables in chat bubbles.
- **Light/Dark Mode Code Support**: Synced code block themes with the global application theme.

---
**Status**: The system is now fully integrated. The Chat feature is operational with real-time source citation.
