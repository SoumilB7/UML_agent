from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from api import diagram, rl
import os


app = FastAPI(
    title="Mermaid Diagram Generator API",
    description="API to generate Mermaid UML diagrams from prompts",
    version="0.0.8"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
