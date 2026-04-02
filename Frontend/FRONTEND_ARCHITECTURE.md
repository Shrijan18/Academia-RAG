# Talos RAG Frontend Architecture

This document provides an in-depth technical overview of the Talos Enterprise Document AI frontend, a high-performance React application designed for multi-modal RAG (Retrieval-Augmented Generation).

---

## 1. Tech Stack Overview

The application is built with a focus on professional aesthetics, smooth interactions, and type safety.

*   **Framework:** [React 18](https://react.dev/) with [TypeScript](https://www.typescriptlang.org/)
*   **Build Tool:** [Vite](https://vitejs.dev/)
*   **Styling:** Vanilla CSS with a centralized Design System (CSS Variables)
*   **Animations:** [Framer Motion](https://www.framer.com/motion/)
*   **Smooth Scrolling:** [Lenis](https://lenis.darkroom.engineering/)
*   **Icons:** [Lucide React](https://lucide.dev/)
*   **API Client:** Native `fetch` API wrapped in a TypeScript service

---

## 2. Project Structure

```text
Frontend/
├── src/
│   ├── services/
│   │   └── api.ts      # Backend communication logic
│   ├── App.tsx         # Main application component & state management
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles, theming, and layout
├── index.html          # HTML entry point
├── tsconfig.json       # TypeScript configuration
└── package.json        # Dependencies and scripts
```

---

## 3. Design System: "Talos Bronze"

The application uses a sophisticated design system defined in `index.css`.

### Color Palette
The primary brand color is **Bronze**, defined across a 10-step scale (`--bronze-50` to `--bronze-950`).
*   **Primary Accent:** `#c5a059` (Light) / `#d4af37` (Dark)
*   **Accent Gradient:** A 135-degree linear gradient from light bronze to deep bronze.

### Theming
The frontend supports a native **Light/Dark mode** using the `data-theme` attribute on the root element.
*   **Dark Mode:** Default setting. Uses deep blacks (`#0f0d0a`) and muted bronze tones for high-end enterprise feel.
*   **Glassmorphism:** Components like the sidebar and headers use `backdrop-filter: blur(30px)` and semi-transparent backgrounds to create depth.

### Visual Effects
*   **Decorative Blobs:** Two large, blurred radial gradients (`decorative-blob-1` and `decorative-blob-2`) rotate in the background to provide a modern, dynamic atmosphere.

---

## 4. Core Logic & Features (`App.tsx`)

### State Management
The application uses React's `useState` and `useEffect` hooks to manage:
*   `messages`: An array of `Message` objects (User/Bot).
*   `theme`: Current active theme (stored in state and synced to DOM).
*   `isSidebarOpen`: Controls the responsive sidebar layout.
*   `isLoading`: Tracks active RAG queries or file uploads.

### Chat Functionality
*   **Auto-expanding Textarea:** Dynamically adjusts height as the user types, up to 200px.
*   **Markdown-ready Bubbles:** Messages are rendered in distinct bubbles with role-specific styling.
*   **Metadata Display:** Bot responses can include source citations (PDF, CSV, Audio) with confidence scores.

### Multi-modal Support
The interface includes a hidden file input triggered by a paperclip icon, supporting:
*   `.pdf` (Textual analysis)
*   `.csv` (Data analysis)
*   `.wav` / `.mp3` (Audio transcription and query)

---

## 5. Animations & UX

### Framer Motion
Used for high-quality transitions:
*   **Sidebar:** Spring-based sliding animation (`initial: {x: -300}`).
*   **Messages:** Staggered entry from the bottom (`y: 15` to `0`) using `AnimatePresence`.
*   **Theme Toggle:** Rotation of the Sun/Moon icons.

### Lenis Smooth Scroll
A custom `useLayoutEffect` hook initializes Lenis on the chat scroll area. This provides:
*   Inertial scrolling.
*   Controlled scroll duration for a "premium" feel.
*   Programmatic scrolling to the bottom when new messages arrive.

---

## 6. API Integration (`services/api.ts`)

The frontend communicates with a FastAPI backend at `http://localhost:8000`.

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/chat` | `POST` | Sends a user query and returns bot response + sources. |
| `/upload` | `POST` | Uploads a file for FAISS indexing. |
| `/status` | `GET` | Health check for the RAG engine. |

---

## 7. Development Commands

*   `npm run dev`: Starts the Vite development server.
*   `npm run build`: Compiles TypeScript and builds the production bundle.
*   `npm run lint`: Runs ESLint for code quality checks.
