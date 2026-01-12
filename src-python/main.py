"""FastAPI application for the Fund RAG Agent."""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import ConfigurationError, get_settings, get_validated_settings
from src.orchestrator import Orchestrator
from src.startup import sync_pdfs_on_startup
from src.tools.schemas import ChatRequest, ChatResponse
from src.utils.responses import format_error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print("Starting Fund RAG Agent...")

    # Validate configuration early with helpful error messages
    try:
        get_validated_settings()
    except ConfigurationError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    await sync_pdfs_on_startup()
    print("Fund RAG Agent ready.")
    yield
    # Shutdown
    print("Shutting down Fund RAG Agent...")


app = FastAPI(
    title="Fund RAG Agent",
    description="RAG-powered assistant for Fund Facts, TFSA, and RRSP information",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator (lazy initialization to avoid import issues)
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return a response.

    The orchestrator will:
    1. Route the query to the appropriate tool (TFSA, RRSP, or Fund Facts)
    2. Optionally generate a chart if requested
    3. Return the response with sources

    Request body:
    - message: The user's question

    Response:
    - reply: The text answer
    - chart_type: Type of chart if generated (bar, line, pie, scatter, histogram)
    - image_base64: Base64-encoded PNG image if chart generated
    - sources: List of source documents used
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        orchestrator = get_orchestrator()
        response = orchestrator.process(request.message)
        return response
    except Exception as e:
        # Log the error in production
        settings = get_settings()
        if settings.is_dev():
            print(f"Error processing chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        else:
            return format_error_response("An unexpected error occurred")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Fund RAG Agent",
        "version": "0.1.0",
        "endpoints": {
            "/chat": "POST - Send a message and get a response",
            "/health": "GET - Health check",
            "/docs": "GET - OpenAPI documentation",
        },
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.is_dev(),
    )
