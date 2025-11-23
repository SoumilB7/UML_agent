# 🎨 UML Diagram Generator

An intelligent, AI-powered monorepo for generating and editing UML diagrams from natural language prompts. Transform your ideas into beautiful Mermaid diagrams with a modern web interface, powered by OpenAI and featuring reinforcement learning capabilities.

---

## ✨ Features

### 🚀 Core Capabilities

- **AI-Powered Generation**: Generate UML diagrams from natural language descriptions using OpenAI GPT models
- **Multiple Variations**: Generate up to 3 variations of a diagram to choose from
- **Interactive Editing**: Edit existing diagrams with natural language instructions
- **Real-Time Rendering**: Live preview of diagrams using Mermaid.js
- **Zoom & Pan**: Interactive diagram exploration with zoom and pan controls
- **Export Options**: Copy Mermaid code or download diagrams as SVG
- **Feedback System**: Rate and provide feedback on generated diagrams
- **RL Tracking**: Comprehensive user action tracking for reinforcement learning

### 📊 Supported Diagram Types

- **Class Diagrams**: Object-oriented class structures with relationships
- **Sequence Diagrams**: Interaction flows between components
- **State Diagrams**: State machines and transitions
- **Activity Diagrams**: Process flows and workflows
- **Use Case Diagrams**: System requirements and actors
- **Component Diagrams**: System architecture and components
- **Deployment Diagrams**: Infrastructure and deployment topology
- **Package Diagrams**: Namespace and package organization
- **Timing/Gantt Charts**: Timeline-based visualizations

---

## 🏗️ Architecture

This is a **monorepo** containing both frontend and backend components:

```
UML_agent/
├── Backend/          # FastAPI Python backend
│   ├── api/         # API routes (diagram, RL tracking)
│   ├── utils/       # Core utilities (diagram generation, editing, logging)
│   ├── models.py    # Pydantic data models
│   ├── constants.py # System prompts and configuration
│   └── app.py       # FastAPI application entry point
│
└── Frontend/        # Next.js React frontend
    ├── components/  # React components
    │   ├── DiagramDisplay.tsx    # Diagram rendering & interaction
    │   ├── DiagramGenerator.tsx   # Main orchestrator
    │   ├── PromptInput.tsx       # User input interface
    │   └── FeedbackPanel.tsx     # Rating & feedback
    ├── utils/       # Frontend utilities
    │   └── rlTracking.ts          # RL action tracking
    └── app/         # Next.js app directory
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **OpenAI API**: GPT models for diagram generation
- **Pydantic**: Data validation and settings
- **Python-dotenv**: Environment configuration
- **Uvicorn**: ASGI server

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Mermaid.js**: Diagram rendering engine
- **Tailwind CSS**: Utility-first styling
- **React Hooks**: State management

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd Backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file (like `.env.example`):**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the server:**
   ```bash
   uvicorn app:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure API URL** (required):
   Create `.env` in the `Frontend` directory (like `.env.example`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
   
   **Important Notes:**
   - The `NEXT_PUBLIC_` prefix is required for Next.js to expose the variable to the browser
   - Change the URL if your backend runs on a different port or domain
   - For production, set this to your deployed backend URL
   - **Restart the Next.js dev server** after creating/modifying `.env.local`
   - You can copy `.env.example` to `.env.local` as a starting point

4. **Run development server:**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

---

## 🔍 Development

### Running Tests

Currently, the project focuses on functional testing through the UI. Future test suite additions are planned.

### Logging

- **LLM Calls**: All OpenAI API calls are logged to `log.txt` with full request/response details
- **Mermaid Code**: Generated and edited Mermaid code is tracked separately
- **RL Actions**: User actions are logged to `rl_actions.json`

### Code Quality

- **Backend**: Python type hints with Pydantic validation
- **Frontend**: TypeScript for type safety
- **Error Handling**: Comprehensive error handling with user-friendly messages

---

## 🤝 Contributing

This is a monorepo project. When contributing:

1. **Backend changes**: Test API endpoints with the frontend
2. **Frontend changes**: Ensure compatibility with backend API
3. **New features**: Update both frontend and backend as needed
4. **RL tracking**: Ensure new actions are properly tracked

---

## 📝 License

[Add your license here]

---

## 🙏 Acknowledgments

- **Mermaid.js** for excellent diagram rendering
- **OpenAI** for powerful language models
- **FastAPI** and **Next.js** communities for great frameworks

---

## 🐛 Troubleshooting

### Common Issues

1. **Diagrams not rendering**: Check browser console for Mermaid errors
2. **API connection errors**: Verify backend is running and `NEXT_PUBLIC_API_URL` is correct
3. **OpenAI errors**: Check `.env` file has valid `OPENAI_API_KEY`
4. **CORS errors**: Backend CORS is configured for all origins; check if backend is running

---

## 🚧 Future Enhancements

- [ ] Diagram templates library
- [ ] Collaborative editing
- [ ] Diagram version history
- [ ] Export to PNG/PDF
- [ ] Custom diagram themes
- [ ] Batch diagram generation
- [ ] Integration with version control systems

---

**Built with ❤️ for developers who love beautiful diagrams**
