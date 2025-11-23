import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from api import diagram, rl

load_dotenv()

app = FastAPI(
    title="Mermaid Diagram Generator API",
    description="API to generate Mermaid UML diagrams from prompts",
    version="0.0.8"
)

# CORS Configuration
environment = os.getenv("ENVIRONMENT", "development")
logger = logging.getLogger(__name__)

# Middleware to log the Origin header for debugging
@app.middleware("http")
async def log_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"Incoming request from Origin: {origin}")
    response = await call_next(request)
    return response

if environment == "production":
    # Production: Only allow the specific frontend URL
    origins = [
        "https://uml-agent.vercel.app",
        "https://uml-agent-back.vercel.app" # Allow self if needed
    ]
    logger.info("Running in PRODUCTION mode. CORS restricted to specific origins.")
else:
    # Development: Allow localhost and production (for testing)
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://uml-agent.vercel.app"
    ]
    logger.info("Running in DEVELOPMENT mode. CORS allows localhost.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from Frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve the frontend index.html at the root"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API is working. Frontend not found."}


app.include_router(diagram.router)
app.include_router(rl.router)
