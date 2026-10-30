# Orysys Enterprise AI Assistant — Technical Assessment POC

A runnable Python proof of concept for an enterprise knowledge assistant. It demonstrates a LangGraph multi-node workflow, retrieval-augmented generation (RAG), bounded RLM-style research, permissioned tool calling, role-based access control (RBAC), session memory, token-bucket rate limiting, citation validation, document ingestion, and OpenRouter integration.

> **Scope:** This is an assessment prototype, not a production-ready identity or security platform. It uses synthetic enterprise documents. The current configuration enables live OpenRouter calls and Pinecone retrieval. Pinecone and OpenRouter require valid credentials and a configured index. LangSmith tracing is optional and requires its own API key. The UI displays graph activity after each request; it does not stream tokens over SSE.

## Features

- LangGraph orchestration with specialized supervisor, retrieval, research, tool, and response nodes.
- Retrieval over synthetic payment, incident, runbook, and architecture documents.
- Pinecone Documents API ingestion and hybrid retrieval, with local lexical retrieval as a fallback.
- OpenRouter chat and embedding model integration.
- Upload support for PDF, DOCX, TXT, and Markdown files.
- Upload metadata: department, document type, and access level (`public`, `internal`, or `confidential`).
- Role-aware access checks for viewer, analyst, and administrator demo identities.
- Permissioned mock enterprise tools and bounded numeric analysis.
- Citation validation against retrieved document IDs.
- Session-scoped bounded memory and token-bucket rate limiting.
- Optional LangSmith tracing and Docker Compose configuration.

## Technology stack

Python, FastAPI, Streamlit, LangGraph, Pinecone, OpenRouter, LangSmith (optional), Pydantic, Docker, and Pytest.

## Project structure

```text
orysys_ai_assistant/
├── app/
│   ├── api.py              FastAPI endpoints, demo identity checks, sessions
│   ├── config.py           Environment configuration
│   ├── graph.py            LangGraph workflow and agent nodes
│   ├── ingest.py           Sample-document ingestion
│   ├── knowledge.py        Knowledge retrieval and Pinecone integration
│   ├── mcp_server.py       Minimal JSON-RPC stdio demonstration
│   ├── models.py           Pydantic API contracts
│   ├── security.py         Input validation, RBAC helpers, token bucket
│   ├── tools.py            Permissioned mock enterprise tools
│   ├── ui.py               Streamlit interface
│   └── uploads.py          Uploaded-document extraction, chunking, ingestion
├── data/                   Synthetic enterprise knowledge documents
├── docs/                   Architecture, setup, demo, and assessment notes
├── tests/                  API, graph, retrieval, security, and upload tests
├── .env                    Local environment variables (do not commit)
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Requirements

- Windows, macOS, or Linux
- Python compatible with the dependencies in `pyproject.toml`
- OpenRouter API key for live model and embedding calls
- Pinecone API key and configured index when `USE_PINECONE=true`
- Optional LangSmith API key for tracing
- Docker Desktop if using Docker Compose

## Windows setup

Open Command Prompt in the project directory:

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

Create or update `.env` in the project root. Do not overwrite an existing working `.env` file.

## Environment configuration

The current assessment configuration uses these settings. Keep secret values in your local `.env` file. Never include real keys in documentation, screenshots, source control, or assessment submissions.

```env
APP_ENV=local
MOCK_MODE=false
APP_NAME=Orysys Enterprise AI Assistant
API_HOST=0.0.0.0
API_PORT=8000

OPENROUTER_API_KEY=<your-openrouter-api-key>
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_URL=http://localhost:8501
OPENROUTER_APP_NAME=Orysys Enterprise AI Assistant

USE_PINECONE=true
PINECONE_API_KEY=<your-pinecone-api-key>
PINECONE_INDEX=orysys-enterprise-knowledge-v2
PINECONE_NAMESPACE=internal
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_DIMENSION=1536
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-langsmith-api-key>
LANGCHAIN_PROJECT=orysys-enterprise-assistant

TOKEN_BUCKET_CAPACITY=20
TOKEN_BUCKET_REFILL_PER_MINUTE=10
MAX_REQUEST_CHARS=4000
```

Notes:
- `MOCK_MODE=false` enables live model calls. Set it to `true` only when intentionally using the offline/mock path.
- `USE_PINECONE=true` enables Pinecone retrieval and ingestion. Set it to `false` to use the local lexical fallback.
- The configured embedding model uses 1536 dimensions; the Pinecone index dimension must match.
- `LANGCHAIN_TRACING_V2=true` enables tracing when a valid LangSmith key is configured. Set it to `false` to disable tracing.
- Restart FastAPI after changing environment variables.
- Confirm `.env` is covered by `.gitignore` before publishing the repository.

## Run the application

Start the API in the first Command Prompt window:

```cmd
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Start Streamlit in a second Command Prompt window:

```cmd
.venv\Scripts\activate
streamlit run app/ui.py
```

Open:
- Streamlit UI: http://localhost:8501
- FastAPI API: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

## Pinecone ingestion and retrieval

Sample documents are stored in `data/`. With `USE_PINECONE=true`, configure `PINECONE_API_KEY`, `OPENROUTER_API_KEY`, and the index settings in `.env`.

Run sample-document ingestion:

```cmd
python -m app.ingest
```

The configured index is `orysys-enterprise-knowledge-v2`, in the `internal` namespace, with a 1536-dimensional dense vector field. If the index needs to be created, allow it to become ready before retrying ingestion.

The local fallback uses lexical/term-overlap ranking. Pinecone mode uses the configured OpenRouter embedding model and Pinecone Documents API search/ingestion.

## Demo identities and RBAC

The assessment API maps these user IDs to server-side demo roles:

| Demo user ID | Assigned role | Intended access |
|---|---|---|
| `viewer_demo` | `viewer` | Knowledge chat/search with permitted public and internal content |
| `analyst_demo` | `analyst` | Knowledge search, analytics, and permitted mock enterprise tools |
| `admin_demo` | `administrator` | Administrative demo capabilities, confidential content, and document upload |

The API checks the submitted role against the role assigned to the supplied demo user ID and rejects mismatches. Retrieval applies these access-level rules:

- Viewer: `public`, `internal`
- Analyst: `public`, `internal`
- Administrator: `public`, `internal`, `confidential`

Document upload is restricted to the administrator demo identity. Uploaded documents can be assigned department, document type, and access-level metadata.

**Security limitation:** these are assessment demo identities, not real authentication. The `user_id` is still supplied by the client. Do not use this mechanism to protect real enterprise data. Production deployment requires verified OIDC/JWT authentication (or an equivalent authenticated session) and authorization based on trusted server-side identity claims.

**Department-filter limitation:** department metadata is stored with uploaded documents and retrieval supports a department filter. The current chat graph does not propagate a user's department as a retrieval filter, so department-level isolation is not fully enforced in the chat workflow.

## Upload knowledge documents

The Streamlit sidebar exposes **Knowledge document management** for the administrator demo identity.

Supported file types: PDF, DOCX, TXT, and Markdown.

The upload workflow extracts text, chunks the content, attaches metadata, and indexes the chunks. The UI allows the administrator to choose department, document type, and access level.

- With `USE_PINECONE=true`, chunks are embedded with the configured OpenRouter embedding model and upserted into the configured Pinecone namespace.
- With `USE_PINECONE=false`, uploaded content is held in the running backend process using local lexical retrieval and is lost when the backend restarts.
- Scanned PDFs require OCR before upload.
- The configured upload limit is 15 MB.

Upload dependencies are installed by `pip install -e .`, including `python-multipart`, `pypdf`, and `python-docx`.

## API example

Example chat request using the analyst demo identity:

```cmd
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"analyst_demo\",\"role\":\"analyst\",\"session_id\":\"demo-1\",\"message\":\"Summarize the payment incidents and identify recurring root causes\"}"
```

The API also exposes document upload and document listing endpoints. See http://localhost:8000/docs for request schemas.

## OpenRouter and LangSmith

The OpenRouter-compatible endpoint is `https://openrouter.ai/api/v1`. The configured chat model is `openai/gpt-4o-mini`; the embedding model is `openai/text-embedding-3-small`.

For live model use, set `OPENROUTER_API_KEY`, keep `MOCK_MODE=false`, confirm that the model is available to your account, and restart FastAPI.

For LangSmith tracing, set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT`, then restart FastAPI.

Live model calls do not silently replace failed calls with mock answers. Missing credentials, unavailable models, or provider errors can result in a controlled service error.

## Docker Compose

With Docker Desktop running and `.env` configured:

```cmd
docker compose up --build
```

UI: http://localhost:8501  
API: http://localhost:8000

Stop the services:

```cmd
docker compose down
```

## Tests

Run from the project root with the virtual environment activated:

```cmd
pytest -q
```

## Design highlights

- Specialized LangGraph nodes with explicit routing.
- Bounded research planning, batch analysis, and aggregation.
- Backend tool authorization rather than relying only on model instructions.
- Citation validation against retrieved document IDs.
- Role-aware retrieval access levels.
- Per-user token bucket, request validation, and controlled API errors.
- Session-scoped bounded memory.
- Pinecone-backed document ingestion and retrieval.
- Optional LangSmith tracing.
- Synthetic bank/payment documents; no real sensitive data.

## Known limitations and production roadmap

1. Replace assessment demo identities with verified OIDC/JWT authentication and trusted server-side authorization claims.
2. Complete and validate department-level authorization propagation through the chat graph.
3. Validate retrieval quality and access-control behavior against a larger evaluation corpus.
4. Replace the minimal JSON-RPC stdio demonstration with the official MCP SDK and authenticated transport.
5. Add SSE/WebSocket token streaming and stream LangGraph activity to the UI.
6. Move sessions and rate limits to Redis/Postgres for multi-instance deployment.
7. Add durable source-document storage, document versioning, ACL synchronization, and deletion workflows.
8. Add reranking, offline retrieval/answer evaluation, feedback capture, audit metrics, and human approval for consequential actions.
9. Add integration tests against provisioned Pinecone, OpenRouter, and LangSmith services.

## Additional documentation

See the `docs/` directory:
- `ARCHITECTURE.md` — system architecture and component responsibilities.
- `ASSUMPTIONS_AND_TRADEOFFS.md` — assumptions and design trade-offs.
- `DEMO_SCRIPT.md` — assessment demonstration flow.
- `OPENROUTER_SETUP_WINDOWS.md` — Windows-specific OpenRouter setup.
- `REQUIREMENTS_MATRIX.md` — assessment requirements mapping.
- `UPGRADE_FROM_PREVIOUS_PACKAGE.md` — package upgrade notes.
