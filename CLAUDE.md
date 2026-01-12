# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fund RAG Agent - A RAG-powered assistant for Fund Facts, TFSA, and RRSP information. Built with TypeScript, Express, LangChain.js, FAISS (local vector search), and Gemini.

## Development Commands

```bash
# Install dependencies
npm install

# Development (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test                    # Watch mode
npm run test:run            # Single run

# Linting and formatting
npm run lint                # Check for issues
npm run lint:fix            # Auto-fix issues
npm run format              # Format with Prettier
npm run typecheck           # TypeScript check
```

## Architecture

```
POST /chat → Orchestrator → Tool (TFSA/RRSP/Fund Facts) → Response
                  ↓               ↓
           Route + Chart?    FAISS Search + Gemini RAG
                                  ↓
                           Chart Generator (optional)
```

### Core Components

- **`src/index.ts`** - Entry point, starts Express server
- **`src/server.ts`** - Express app with `/chat`, `/health` endpoints
- **`src/config.ts`** - Zod-validated configuration from env vars
- **`src/orchestrator/router.ts`** - LangChain.js router that determines tool + chart parameters
- **`src/tools/`** - Specialist tools (TFSATool, RRSPTool, FundFactsTool) with local FAISS RAG
- **`src/tools/local-search.ts`** - FAISS vector search client for document retrieval
- **`src/charts/`** - Chart.js chart generation with Gemini structured output for data extraction
- **`src/types/schemas.ts`** - Zod schemas for request/response validation

### Request Flow

1. User sends message to `POST /chat`
2. Orchestrator routes query to appropriate tool (tfsa/rrsp/fund_facts) and detects chart requests
3. Tool queries local FAISS index with topic-specific filter
4. Tool generates RAG response via Gemini with retrieved context
5. If `generateChart=true`, extracts data via Gemini structured output and generates Chart.js chart
6. Returns response with reply, sources, and optional base64 chart image

## Key Patterns

### Adding a New Tool

1. Create `src/tools/new-tool.ts` extending `BaseTool`
2. Set `searchFilter` for FAISS metadata filtering (e.g., `"category:new_topic"`)
3. Set `systemPrompt` with domain-specific instructions
4. Register in `src/tools/index.ts` and `src/orchestrator/router.ts`

### Tool Base Class Pattern

```typescript
import { BaseTool } from './base.js';

export class MyTool extends BaseTool {
  readonly name = 'my_tool';
  readonly searchFilter = 'category:my_category';
  readonly systemPrompt = 'You are an expert in...';
}
```

### FAISS Index

The FAISS index should be pre-built and placed at `FAISS_INDEX_PATH`. The index must contain:
- `index.faiss` - The vector index file
- `index.pkl` - Metadata/docstore pickle file

Documents in the index should have metadata including: `title`, `source_url`, `category`, `page`.

## Configuration

### Environment Variables

```bash
ENVIRONMENT=dev                      # dev | workstation | prod
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
FAISS_INDEX_PATH=./src/faiss_index_fundfacts
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your-key              # Dev only
PDF_BASE_URL=https://yoursite.com/funds
PORT=8080
```

### Authentication

| Environment | Method | Usage |
|-------------|--------|-------|
| dev | API Key | Set `GOOGLE_API_KEY` env var |
| workstation | Service Account (ADC) | Uses workstation's attached service account |
| prod | Service Account (ADC) | Uses Cloud Run's service account |

Dev uses `@langchain/google-genai`, workstation/prod use `@langchain/google-vertexai`.

## Infrastructure (Terraform)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars  # Edit values
terraform init
terraform plan
terraform apply
```

Creates: Cloud Run service, IAM roles for Gemini access.

## Response Schema

```json
{
  "reply": "Answer text...",
  "chart_type": "bar",
  "image_base64": "data:image/png;base64,...",
  "sources": [
    {"pdf_name": "Fund A Facts", "pdf_url": "https://...", "page": 2}
  ]
}
```

## Chart Types

- `bar` - Comparisons (MER, fund performance)
- `line` - Time series, trends
- `pie` - Distributions, allocations
- `scatter` - Correlations (risk vs return)
- `histogram` - Frequency distributions

## Project Structure

```
fund-rag-agent/
├── package.json
├── tsconfig.json
├── tsup.config.ts
├── .env.example
├── src/
│   ├── index.ts                    # Entry point
│   ├── server.ts                   # Express HTTP server
│   ├── config.ts                   # Zod-validated config
│   ├── types/
│   │   └── schemas.ts              # Zod schemas
│   ├── orchestrator/
│   │   ├── router.ts               # LangChain routing
│   │   └── prompts.ts              # System prompts
│   ├── tools/
│   │   ├── base.ts                 # Abstract BaseTool
│   │   ├── local-search.ts         # FAISS client
│   │   ├── tfsa-tool.ts
│   │   ├── rrsp-tool.ts
│   │   └── fund-facts-tool.ts
│   ├── charts/
│   │   ├── generator.ts            # Chart.js rendering
│   │   └── data-extractor.ts       # Gemini structured output
│   └── utils/
│       ├── gemini.ts               # Gemini client
│       └── responses.ts
├── tests/
│   └── api.test.ts
└── src-python/                     # Old Python code (reference)
```
