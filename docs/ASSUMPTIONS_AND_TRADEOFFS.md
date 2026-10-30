# Assumptions and Trade-offs

1. **POC over production:** The implementation prioritizes an explainable graph workflow, permission checks, evidence-grounded responses, and controlled failure modes within the assessment scope. It is not a complete production platform.

2. **Synthetic corpus:** Four synthetic internal payment/engineering documents are included. They contain no real customer or employee data.

3. **Model provider:** The current assessment configuration uses live OpenRouter calls (`MOCK_MODE=false`) with the configured chat model. Mock mode remains available for intentional offline testing. Live provider failures are surfaced as controlled errors rather than silently replaced with mock answers.

4. **Retrieval:** The application supports local lexical/term-overlap retrieval and Pinecone dense+sparse hybrid retrieval. The current `.env` enables Pinecone (`USE_PINECONE=true`) and configures OpenRouter embeddings. Cloud retrieval depends on valid credentials, a ready index with a matching 1536-dimensional configuration, and successful ingestion. Local fallback is not dense vector retrieval.

5. **Document ingestion:** Sample documents can be ingested through `python -m app.ingest`. The UI also supports administrator-demo uploads with department, document-type, and access-level metadata. In Pinecone mode, uploaded chunks are embedded and upserted to the configured namespace. In local fallback mode, uploaded content is held in backend process memory and is lost on restart. Scanned PDFs require OCR before upload.

6. **RLM:** The research workflow implements bounded planning, retrieval, batching, sub-analysis, and aggregation. It does not execute arbitrary LLM-generated Python in the main process. Running generated code would require a properly isolated sandbox.

7. **Authentication and authorization:** Demo user IDs are mapped to roles on the server, and requests with unknown demo users or mismatched submitted roles are rejected. However, the `user_id` is still supplied by the client, so this is not real authentication. Production must use verified OIDC/JWT claims or an equivalent authenticated session and enforce least-privilege authorization server-side.

8. **Document access controls:** Retrieval filters documents by access level: viewers and analysts can retrieve public/internal content, while administrators can retrieve public/internal/confidential content. Department metadata is stored and the retrieval function accepts an optional department filter, but the current chat graph does not propagate a user's department into retrieval. Department-level isolation is therefore not fully enforced end-to-end.

9. **Memory:** Session state is in-process, session-scoped, bounded, and volatile. A backend restart loses it. There is no durable cross-user memory. Production should use a shared store such as Redis/Postgres with appropriate tenant/user/session scoping, TTLs, retention controls, and deletion support.

10. **MCP and enterprise tools:** The application uses a permissioned local tool registry and mock enterprise tools. The included JSON-RPC stdio server is a lightweight demonstration, not a production MCP deployment. Production should use the official MCP SDK, authenticated transport, and per-tool authorization.

11. **LangSmith:** Tracing is optional and depends on valid credentials and tracing settings. Do not claim traces were inspected unless they were verified in the live LangSmith project. Avoid sending secrets or sensitive document content to traces.

12. **Rate limiting:** The in-memory token bucket supports a single-process assessment demo. Multi-worker or multi-instance production deployments require a shared implementation such as Redis or an API gateway.

13. **Streaming:** The UI displays graph activity after each request; it does not provide true token-by-token SSE/WebSocket streaming. This limitation should be stated during the demo.

14. **No arbitrary tool execution:** Tools are selected from an allow-listed registry, use defined parameters, and are subject to backend permission checks. The model is not given unrestricted shell or Python execution.
