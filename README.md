# 🎨 Diagram AI

**Intelligent UML Diagram Generator**

An intelligent, AI-powered tool for generating, editing, and visualizing UML diagrams from natural language prompts. Built with a "Bring Your Own Key" (BYOK) architecture for security and styled with a sophisticated, warm "Claude-like" aesthetic.

![Diagram AI Screenshot](https://raw.githubusercontent.com/SoumilB7/UML_agent/main/frontend/public/favicon.svg) <!-- Replace with actual screenshot if available -->

---

## ✨ Features

### 🚀 Core Capabilities

-   **AI-Powered Generation**: Transform text into professional Mermaid.js diagrams using OpenAI models.
-   **Bring Your Own Key (BYOK)**: **Secure by design.** Your OpenAI API key is stored locally in your browser and never saved on our servers.
-   **Multiple Variations**: Generate multiple diagram options at once to explore different structural approaches.
-   **Interactive Editing**: Refine existing diagrams using natural language (e.g., "Add a User class", "Make the arrows dotted").
-   **Import & Export**:
    -   **Import**: Paste existing Mermaid code to visualize and edit it.
    -   **Export**: Download as SVG or copy code to clipboard.
-   **Reinforcement Learning (RL) Tracking**: User interactions (edits, ratings, feedback) are tracked in MongoDB to improve future model performance.
-   **"Claude" Aesthetic**: A premium, distraction-free UI with warm stone, cream, and charcoal tones.

### 📊 Supported Diagram Types

-   **Class Diagrams**: Object-oriented structures.
-   **Sequence Diagrams**: Component interactions.
-   **Flowcharts**: Process workflows.
-   **State Diagrams**: State machine transitions.
-   **Entity Relationship Diagrams (ERD)**: Database schemas.
-   **Gantt/Timeline**: Project schedules.

---

## 🏗️ Architecture

This project is a **monorepo** deployed on **Vercel** (Frontend & Backend).

```
UML_agent/
├── Backend/                 # FastAPI (Python)
│   ├── api/                 # Endpoints (generate, edit, feedback)
│   ├── utils/               # Logic for LLM interaction & MongoDB
│   ├── old_RL/              # Archived file-based logs
│   ├── app.py               # Main application entry
│   └── requirements.txt     # Python dependencies
│
└── frontend/                # Next.js 14 (TypeScript)
    ├── components/          # React components (DiagramDisplay, PromptInput)
    ├── public/              # Static assets (Favicon)
    ├── utils/               # Tracking & API clients
    └── tailwind.config.ts   # Custom "Claude" theme config
```

---

## 🛠️ Tech Stack

### Frontend
-   **Next.js 14**: App Router, SSR/CSR.
-   **TypeScript**: Robust type safety.
-   **Tailwind CSS**: Custom color palette (`claude-bg`, `claude-card`, etc.).
-   **Mermaid.js**: Client-side diagram rendering.

### Backend
-   **FastAPI**: High-performance Python ASGI framework.
-   **MongoDB (Atlas)**: Cloud database for storing user sessions and RL feedback.
-   **Motor**: Asynchronous MongoDB driver.
-   **OpenAI API**: LLM intelligence (passed via headers from frontend).

---

## 🚀 Quick Start

### Prerequisites
-   Python 3.9+
-   Node.js 18+
-   MongoDB Atlas Connection String

### 1. Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `Backend/`:
```env
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
ENVIRONMENT=development
```

Run the server:
```bash
uvicorn app:app --reload
# Runs on http://localhost:8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the dev server:
```bash
npm run dev
# Runs on http://localhost:3000
```

---

## 🔐 Security (BYOK)

We utilize a **Bring Your Own Key** system.
-   **No Server Storage**: Your OpenAI API Key is **never** stored in our database.
-   **Local Storage**: It is saved in your browser's `localStorage` for convenience.
-   **Transmission**: It is sent to the backend securely via the `X-OpenAI-Key` header for each request.

---

## ☁️ Deployment (Vercel)

### Backend
1.  Deploy `Backend` directory as a standalone Python project.
2.  Set Environment Variables in Vercel:
    -   `MONGODB_URL`: Your Atlas connection string.
    -   `ENVIRONMENT`: `production` (Enables strict CORS protocols).

### Frontend
1.  Deploy `frontend` directory as a Next.js project.
2.  Set Environment Variables in Vercel:
    -   `NEXT_PUBLIC_API_URL`: The URL of your deployed Backend (e.g., `https://your-backend.vercel.app`).

---

## 🤝 Contributing

1.  **Fork** the repository.
2.  **Clone** your fork.
3.  **Branch** for your feature (`git checkout -b feature/amazing-feature`).
4.  **Commit** changes (`git commit -m 'Add amazing feature'`).
5.  **Push** (`git push origin feature/amazing-feature`).
6.  **Open a PR**.

---

## 🙏 Acknowledgments

-   **Mermaid.js** for the incredible rendering engine.
-   **Anthropic's Claude** for the design inspiration.
-   **OpenAI** for the intelligence under the hood.

---

**Made with ♥️ by SoumilB7**
