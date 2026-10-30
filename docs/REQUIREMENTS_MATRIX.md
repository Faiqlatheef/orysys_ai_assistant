# Assessment Requirements Matrix

| Requirement | POC status | Evidence |
|---|---|---|
| Streamlit chat / multi-turn | Implemented; graph activity is displayed after each turn, but token-by-token streaming is not implemented | `app/ui.py`, `app/api.py` |
| FastAPI async endpoints | Implemented; synchronous graph execution is offloaded to a worker thread | `app/api.py` |
| LangGraph specialized agents | Implemented with supervisor, retrieval, research, tool, and response workflow nodes | `app/graph.py` |
| RLM concepts | Bounded planning, retrieval, batching, sub-analysis, and aggregation; no arbitrary generated-code execution | `research_agent` in `app/graph.py` |
| Hybrid retrieval | Local lexical/term-overlap fallback and Pinecone dense+sparse hybrid retrieval path | `app/knowledge.py` |
| Pinecone namespaces / metadata | Pinecone Documents API ingestion and search use the configured namespace and document metadata; requires valid credentials and a ready index | `app/knowledge.py`, `app/ingest.py`, `app/uploads.py` |
| Document upload | Administrator-demo upload for PDF, DOCX, TXT, and Markdown with department, document-type, and access-level metadata | `app/ui.py`, `app/api.py`, `app/uploads.py` |
| Session memory | Bounded, in-memory session history; volatile across backend restarts | `app/api.py`, `app/graph.py` |
| Knowledge / Python / MCP tools | Permissioned mock tool registry, bounded numeric analysis, and minimal JSON-RPC stdio demonstration; not a production MCP deployment | `app/tools.py`, `app/mcp_server.py`, `app/graph.py` |
| LangSmith | Tracing configured through environment variables; requires valid credentials and live verification | `.env`, `app/config.py`, `app/graph.py` |
| Prompt injection | Heuristic pre-check and untrusted-context policy; not a complete prompt-injection defense | `app/security.py`, `app/graph.py` |
| RBAC | Server-side demo-user-to-role mapping, submitted-role mismatch rejection, tool permission checks, access-level filtering, and administrator-only upload. Client-supplied `user_id` means this is not production authentication. Department filtering is not propagated through the chat graph. | `app/api.py`, `app/security.py`, `app/tools.py`, `app/knowledge.py`, `app/uploads.py` |
| Token bucket | Thread-safe, in-memory per-user limiter; intended for the single-process assessment demo | `app/security.py`, `app/api.py` |
| Graceful failures | Live provider failures surface as controlled API errors; deterministic mock behavior is used only when `MOCK_MODE=true` | `app/graph.py`, `app/api.py` |
| Architecture diagram | Architecture diagram image and Mermaid flow documented in the architecture documentation | `docs/Orysys Enterprise AI Assistant Architecture.png`, `docs/ARCHITECTURE.md` |
| Public repository / demo video / public traces | External submission deliverables; must be published or recorded by the candidate and must not be claimed as completed unless actually available | Candidate submission materials; `docs/DEMO_SCRIPT.md` |

## Assessment notes

- The current `.env` configuration enables live OpenRouter calls, Pinecone retrieval, and LangSmith tracing. These integrations still depend on valid credentials and successful service configuration.
- The demo identity mapping improves role validation but does not authenticate the person supplying the `user_id`. Production deployment requires verified identity (for example, OIDC/JWT) and trusted server-side claims.
- Department metadata is stored and the retrieval function supports an optional department filter, but the current chat graph does not pass a department filter through retrieval. Do not claim end-to-end department-level isolation.
- The architecture image present in the project directory is a PNG file, not an SVG.
- Public repository, recorded demo, and public trace links are submission tasks, not application features.
