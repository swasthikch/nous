"""Main FastAPI Application Entrypoint for NOUS."""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.sessions_api import router as sessions_router
from backend.app.api.routing_api import router as routing_router
from backend.app.api.memory_api import router as memory_router
from backend.app.api.voice_api import router as voice_router
from backend.app.api.routine_api import router as routine_router
from backend.app.api.email_api import router as email_router
from backend.app.api.projects_api import router as projects_router
from backend.app.api.market_api import router as market_router
from backend.app.api.research_api import router as research_router
from backend.app.api.automation_api import router as automation_router
from backend.app.api.security_api import router as security_router
from backend.app.api.diagnostics_api import router as diagnostics_router
from backend.app.api.public_apis_api import router as public_apis_router
from backend.app.core.ollama_client import ollama_client

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print("=" * 60)
    print(f"  {settings.PROJECT_NAME} v{settings.VERSION}")
    print("  Tagline: Your Intelligence. Your Memory. Your Assistant.")
    print("=" * 60)

    # Check Ollama status at startup
    status = await ollama_client.check_connection()
    if status.get("status") == "connected":
        models = status.get("available_models", [])
        print(f"[OLLAMA] Connected. Available models: {models}")
        print(f"[OLLAMA] Active default model: {settings.OLLAMA_MODEL}")
    else:
        print(f"[OLLAMA WARNING] {status.get('detail')}")

    yield

    print("[NOUS] Shutting down cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend orchestration engine for NOUS Personal AI Assistant.",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for seamless local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(routing_router)
app.include_router(memory_router)
app.include_router(voice_router)
app.include_router(routine_router)
app.include_router(email_router)
app.include_router(projects_router)
app.include_router(market_router)
app.include_router(research_router)
app.include_router(automation_router)
app.include_router(security_router)
app.include_router(diagnostics_router)
app.include_router(public_apis_router)

# Mount frontend static files if directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        return {"message": "Frontend index.html not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
