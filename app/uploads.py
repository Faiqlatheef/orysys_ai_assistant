"""Document upload, text extraction, chunking, and indexing for the assessment POC."""
from __future__ import annotations
import hashlib
from hmac import digest
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid
from docx import text
from app.config import settings
from app import knowledge

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_EXTRACTED_CHARS = 2_000_000


def extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Upload PDF, DOCX, TXT, or MD files.")
    if not content:
        raise ValueError("The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 15 MB upload limit.")
    try:
        if ext in {".txt", ".md"}:
            text = content.decode("utf-8-sig")
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise ValueError("Password-protected PDFs are not supported.") from exc
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            from docx import Document
            document = Document(io.BytesIO(content))
            parts = [p.text for p in document.paragraphs if p.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            text = "\n".join(parts)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not read this {ext} file. Check that it is valid and not corrupted.") from exc
    text = re.sub(r"\x00", "", text).strip()

    if not text:
        if ext in {".txt", ".md"}:
            raise ValueError("The uploaded file is empty or contains only whitespace.")
        raise ValueError(
            "No extractable text was found. Scanned PDFs need OCR before upload."
        )
    if len(text) > MAX_EXTRACTED_CHARS:
        raise ValueError("Extracted text exceeds the 2-million-character safety limit.")
    return text


def split_chunks(text: str, chunk_chars: int = 1000, overlap: int = 150) -> list[str]:
    chunks=[]; start=0
    while start < len(text):
        end=min(len(text), start+chunk_chars)
        if end < len(text):
            boundary=text.rfind("\n", start, end)
            if boundary > start + chunk_chars//2: end=boundary
        part=text[start:end].strip()
        if part: chunks.append(part)
        if end >= len(text): break
        start=max(start+1, end-overlap)
    return chunks



def _upsert_pinecone(doc: dict[str, Any], chunks: list[str]) -> None:
    """Index document chunks using Pinecone's Documents API."""
    from app.knowledge import _embed_texts, _sparse_vector
    from pinecone import Pinecone

    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing.")
    if not settings.openrouter_api_key:
        raise RuntimeError("OpenRouter embedding credentials are required.")

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index)

    corpus = [{"text": chunk} for chunk in chunks]
    batch_size = 16

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        dense_vectors = _embed_texts(batch)
        documents = []

        for offset, (chunk, dense) in enumerate(
            zip(batch, dense_vectors), start=start
        ):
            sparse = _sparse_vector(chunk, corpus)

            documents.append({
                "_id": f"{doc['id']}::chunk-{offset}",
                "embedding": dense,
                "sparse_embedding": sparse,
                "chunk_text": chunk,
                "title": doc["title"],
                "doc_id": doc["id"],
                "department": doc["department"],
                "document_type": doc["document_type"],
                "access_level": doc["access_level"],
                "created_date": doc["created_date"],
                "chunk_number": offset,
            })

        index.documents.upsert(
            namespace=settings.pinecone_namespace,
            documents=documents,
        )



def ingest_uploaded_document(filename: str, content: bytes, department: str, document_type: str,
                             access_level: str, created_date: str | None = None) -> dict[str, Any]:
    text=extract_text(filename, content)
    safe_name=Path(filename).name
    digest = hashlib.sha256(content).hexdigest()[:16]
    doc_id = f"upload-{digest}-{uuid.uuid4().hex[:8]}"
    title=Path(safe_name).stem.replace("_", " ").replace("-", " ").strip() or safe_name
    created_date=created_date or datetime.now(timezone.utc).date().isoformat()
    doc={"id":doc_id,"title":title,"text":text,"department":department,
         "document_type":document_type,"access_level":access_level,"created_date":created_date,
         "filename":safe_name,"uploaded_at":datetime.now(timezone.utc).isoformat()}
    chunks=split_chunks(text)
    if settings.use_pinecone:
        _upsert_pinecone(doc,chunks)
    # Keep an in-process copy for local fallback and document listing; live Pinecone retrieval
    # uses the same doc ID and indexed chunk metadata. Avoid duplicate entries on re-upload.
    knowledge.DOCS[:]=[d for d in knowledge.DOCS if d.get("id") != doc_id]
    knowledge.DOCS.append(doc)
    return {"doc_id":doc_id,"title":title,"filename":safe_name,"characters":len(text),
            "chunks":len(chunks),"department":department,"document_type":document_type,
            "access_level":access_level,"index_mode":"pinecone_hybrid" if settings.use_pinecone else "local_lexical_fallback"}
