What We Built
  ┌────────────────────┬───────────────────────────────────────────────────────────────┐
  │     Component      │                          Description                          │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ FastAPI App        │ /chat endpoint accepts {"message": "..."}                     │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ Orchestrator       │ LLM-powered router selects tool + detects chart requests      │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ 3 Specialist Tools │ TFSATool, RRSPTool, FundFactsTool - each with own FAISS index │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ Local FAISS Search │ Vector similarity search on local embeddings                  │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ Chart Generation   │ Matplotlib charts from extracted data                         │
  ├────────────────────┼───────────────────────────────────────────────────────────────┤
  │ 40 Unit Tests      │ Full coverage of schemas, tools, orchestrator, API            │
  └────────────────────┴───────────────────────────────────────────────────────────────┘
  ---
  Configuration

  Environment Variables

  # Required
  ENVIRONMENT=dev                          # dev | workstation | prod
  GCP_PROJECT_ID=your-project-id
  GCP_REGION=us-central1

  # Auth (dev only)
  GOOGLE_API_KEY=your-api-key              # Required for ENVIRONMENT=dev

  # Gemini
  GEMINI_MODEL=gemini-2.5-flash

  # FAISS Indexes (paths to folders containing index.faiss + index.pkl)
  FAISS_INDEX_FUNDFACTS=./src/faiss_index_fundfacts
  FAISS_INDEX_RRSP=./src/faiss_index_rrsp
  FAISS_INDEX_TFSA=./src/faiss_index_tfsa

  # Optional
  PDF_BASE_URL=https://yoursite.com/funds  # For source links
  ALLOW_GENERAL_KNOWLEDGE_FALLBACK=true    # Use Gemini knowledge if no docs

  Authentication Modes
  ┌─────────────┬───────────────────────┬──────────────────────────┐
  │ Environment │      Auth Method      │      Required Vars       │
  ├─────────────┼───────────────────────┼──────────────────────────┤
  │ dev         │ Google API Key        │ GOOGLE_API_KEY           │
  ├─────────────┼───────────────────────┼──────────────────────────┤
  │ workstation │ Service Account (ADC) │ None (uses attached SA)  │
  ├─────────────┼───────────────────────┼──────────────────────────┤
  │ prod        │ Service Account (ADC) │ None (uses Cloud Run SA) │
  └─────────────┴───────────────────────┴──────────────────────────┘
  ---
  Running Locally

  # Setup
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

  # Configure
  cp .env.example .env
  # Edit .env with your GOOGLE_API_KEY and GCP_PROJECT_ID

  # Run
  uvicorn src.main:app --reload --port 8080

  # Test
  pytest tests/ -v

  ---
  Docker Deployment

  Dockerfile sets these env vars:
  ENV ENVIRONMENT=workstation \
      FAISS_INDEX_FUNDFACTS=./src/faiss_index_fundfacts \
      FAISS_INDEX_RRSP=./src/faiss_index_rrsp \
      FAISS_INDEX_TFSA=./src/faiss_index_tfsa

  Build & Run:
  docker build -t fund-rag-agent .
  docker run -p 8080:8080 \
    -e GCP_PROJECT_ID=your-project \
    -e GOOGLE_API_KEY=your-key \
    -e ENVIRONMENT=dev \
    fund-rag-agent

  For Cloud Run (uses service account):
  docker run -p 8080:8080 \
    -e GCP_PROJECT_ID=your-project \
    -e ENVIRONMENT=workstation \
    fund-rag-agent

  ---
  FAISS Index Structure

  Each index folder must contain:
  src/faiss_index_fundfacts/
  ├── index.faiss    # Vector index
  └── index.pkl      # Document metadata/docstore

  src/faiss_index_rrsp/
  ├── index.faiss
  └── index.pkl

  src/faiss_index_tfsa/
  ├── index.faiss
  └── index.pkl

  These need to be pre-built with your PDF documents using LangChain's FAISS vectorstore.