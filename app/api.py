"""FastAPI service. Async route; synchronous LangGraph work is offloaded to a thread."""
import logging, uuid, asyncio
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.config import settings
from app.models import ChatRequest, ChatResponse, Source
from app.security import TokenBucketLimiter, validate_message
from app.graph import run_assistant
from app.uploads import ingest_uploaded_document, SUPPORTED_EXTENSIONS, MAX_UPLOAD_BYTES

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger=logging.getLogger("orysys.api")
app=FastAPI(title=settings.app_name,version="0.1.0",description="Enterprise AI Assistant assessment POC")
limiter=TokenBucketLimiter(settings.token_bucket_capacity,settings.token_bucket_refill_per_minute)
# Session history is in-memory for the demo; replace with Redis/Postgres for multi-instance production.
SESSIONS={}
DEMO_USER_ROLES = {
    "viewer_demo": "viewer",
    "analyst_demo": "analyst",
    "admin_demo": "administrator",
}
@app.middleware("http")
async def request_logging(request:Request,call_next):
    request_id=request.headers.get("x-request-id",str(uuid.uuid4()))
    try:
        response=await call_next(request); response.headers["x-request-id"]=request_id; return response
    except Exception:
        logger.exception("Unhandled request failure request_id=%s",request_id)
        return JSONResponse(status_code=500,content={"detail":"Internal error; request safely failed.","request_id":request_id})
@app.get("/health")
def health(): return {"status":"ok","mock_mode":settings.mock_mode,"provider":"mock" if settings.mock_mode else "openrouter","openrouter_configured":bool(settings.openrouter_api_key),"model":settings.openrouter_model if not settings.mock_mode else None,"retrieval_mode":"pinecone_hybrid" if settings.use_pinecone else "local_lexical_fallback","documents_loaded":len(__import__("app.knowledge",fromlist=["DOCS"]).DOCS)}
@app.get("/demo-users")
def demo_users(): return {"warning":"Assessment demo only; production must use OIDC/JWT and server-side identity, never trust a client-supplied role.","users":[{"user_id":"viewer_demo","role":"viewer"},{"user_id":"analyst_demo","role":"analyst"},{"user_id":"admin_demo","role":"administrator"}]}

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    role: str = Form(...),
    department: str = Form("general"),
    document_type: str = Form("policy"),
    access_level: str = Form("internal"),
):
    """Upload and index a knowledge document. Assessment demo RBAC: administrators only."""
    trusted_role = DEMO_USER_ROLES.get(user_id)

    if trusted_role is None:
        raise HTTPException(status_code=401, detail="Unknown demo user.")

    if trusted_role != "administrator" or role != trusted_role:
        raise HTTPException(
            status_code=403,
            detail="Only authenticated administrators can upload knowledge documents.",
        )
    if not user_id or len(user_id) > 80:
        raise HTTPException(status_code=422, detail="Invalid user_id.")
    filename=file.filename or ""
    from pathlib import Path
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, DOCX, TXT, MD.")
    raw=await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 15 MB upload limit.")
    if department not in {"general","payments","engineering","security","operations","finance","hr"}:
        raise HTTPException(status_code=422, detail="Unsupported department metadata value.")
    if document_type not in {"policy","architecture","runbook","incident","product_spec","meeting_notes","other"}:
        raise HTTPException(status_code=422, detail="Unsupported document_type metadata value.")
    if access_level not in {"public","internal","confidential"}:
        raise HTTPException(status_code=422, detail="Unsupported access_level metadata value.")
    try:
        return await asyncio.to_thread(ingest_uploaded_document, filename, raw, department, document_type, access_level)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document ingestion failed filename=%s", filename)
        raise HTTPException(status_code=503, detail=f"Document ingestion failed ({type(exc).__name__}). Check server logs and provider configuration.") from exc


@app.get("/documents")
async def list_documents(user_id: str, role: str):
    """List only documents the demo user is permitted to see."""
    trusted_role = DEMO_USER_ROLES.get(user_id)

    if trusted_role is None:
        raise HTTPException(status_code=401, detail="Unknown demo user.")

    if role != trusted_role:
        raise HTTPException(
            status_code=403,
            detail="Submitted role does not match the assigned role.",
        )

    from app.knowledge import DOCS

    allowed_levels = {
        "viewer": {"public", "internal"},
        "analyst": {"public", "internal"},
        "administrator": {"public", "internal", "confidential"},
    }[trusted_role]

    documents = [
        {
            "doc_id": d.get("id"),
            "title": d.get("title"),
            "department": d.get("department"),
            "document_type": d.get("document_type"),
            "access_level": d.get("access_level"),
            "filename": d.get("filename", d.get("id")),
        }
        for d in DOCS
        if d.get("access_level", "internal") in allowed_levels
    ]

    return {"documents": documents}



@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Resolve permissions from the server-side demo mapping.
    trusted_role = DEMO_USER_ROLES.get(req.user_id)

    if trusted_role is None:
        raise HTTPException(status_code=401, detail="Unknown demo user.")

    # Reject attempts to claim a different role.
    if req.role != trusted_role:
        raise HTTPException(
            status_code=403,
            detail="Submitted role does not match the assigned role.",
        )

    message = validate_message(req.message, settings.max_request_chars)

    if not limiter.consume(req.user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait and retry.",
        )

    key = f"{req.user_id}:{req.session_id}"
    history = SESSIONS.get(key, [])

    try:
        result = await asyncio.to_thread(
            run_assistant,
            req.user_id,
            trusted_role,
            req.session_id,
            message,
            history[-8:],
        )
    except Exception as exc:
        logger.exception("Assistant execution failed")
        if isinstance(exc, RuntimeError) and "OPENROUTER_API_KEY" in str(exc):
            raise HTTPException(
                status_code=503,
                detail="Live LLM is not configured. Set OPENROUTER_API_KEY in .env and restart FastAPI.",
            )
        raise HTTPException(
            status_code=503,
            detail=f"Assistant temporarily unavailable ({type(exc).__name__}). Check the API terminal logs for details.",
        )

    history.append({
        "question": message,
        "answer": result.get("answer", "")[:1500],
    })
    SESSIONS[key] = history[-10:]

    sources = [
        Source(
            doc_id=d["id"],
            title=d["title"],
            snippet=d.get("snippet", "")[:420],
            department=d.get("department", "general"),
            document_type=d.get("document_type", "unknown"),
            created_date=d.get("created_date", "unknown"),
        )
        for d in result.get("evidence", [])
    ]

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=sources,
        activities=result.get("activities", []),
        validation=result.get("validation", {}),
        session_id=req.session_id,
        request_id=result.get("request_id", "unknown"),
    )
