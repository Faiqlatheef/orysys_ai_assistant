"""Small mock knowledge corpus + hybrid lexical retrieval and optional Pinecone adapter."""
from pathlib import Path
import re, math
from collections import Counter, defaultdict
import hashlib
from app.config import settings

DATA_DIR=Path(__file__).resolve().parent.parent / "data"
def load_documents():
    docs=[]
    for path in sorted(DATA_DIR.glob("*.md")):
        text=path.read_text(encoding="utf-8")
        title=next((x.lstrip("# ").strip() for x in text.splitlines() if x.startswith("# ")),path.stem)
        meta={"department":"general","document_type":"runbook","access_level":"internal","created_date":"2026-01-01"}
        for line in text.splitlines()[:8]:
            if line.startswith("<!--") and "department=" in line:
                for pair in line.strip("<!-> ").split(";"):
                    if "=" in pair:
                        k,v=pair.split("=",1); meta[k.strip()]=v.strip()
        body="\n".join(x for x in text.splitlines() if not x.startswith("<!--"))
        docs.append({"id":path.stem,"title":title,"text":body,**meta})
    return docs
DOCS=load_documents()
TOKEN_RE=re.compile(r"[a-z0-9]+",re.I)
def tokens(s): return TOKEN_RE.findall(s.lower())
def bm25_like(query, docs):
    q=set(tokens(query)); scored=[]
    for d in docs:
        dt=tokens(d["text"]); c=Counter(dt)
        score=sum((1+math.log(1+n)) for term in q if (n:=c[term])>0) / (1+math.log(1+len(dt)))
        scored.append((score,d))
    return scored

def _sparse_vector(text: str, corpus: list[dict]):
    """Build a deterministic BM25-style sparse vector using hashed token IDs."""
    terms=tokens(text)
    if not terms:
        return {"indices": [], "values": []}
    docs_tokens=[tokens(d.get("text", "")) for d in corpus]
    n_docs=max(1,len(docs_tokens)); avg_len=sum(map(len,docs_tokens))/n_docs or 1
    df=Counter(term for doc in docs_tokens for term in set(doc))
    tf=Counter(terms); doc_len=len(terms); weights={}
    for term,count in tf.items():
        idf=math.log(1+(n_docs-df.get(term,0)+0.5)/(df.get(term,0)+0.5))
        denom=count+1.2*(1-0.75+0.75*doc_len/avg_len)
        weight=idf*(count*(1.2+1)/denom)
        idx=int.from_bytes(hashlib.blake2b(term.encode("utf-8"),digest_size=4).digest(),"big") % 2147483647
        weights[idx]=weights.get(idx,0.0)+weight
    ordered=sorted(weights.items())
    return {"indices":[i for i,_ in ordered],"values":[float(v) for _,v in ordered]}

def _embed_texts(texts: list[str]) -> list[list[float]]:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for Pinecone embedding generation.")
    from openai import OpenAI
    client=OpenAI(base_url=settings.openrouter_base_url,api_key=settings.openrouter_api_key,timeout=90.0,max_retries=2)
    result=client.embeddings.create(model=settings.openrouter_embedding_model,input=texts)
    vectors=[None]*len(result.data)
    for item in result.data:
        vectors[item.index]=item.embedding
    if any(v is None for v in vectors):
        raise RuntimeError("Embedding provider returned an incomplete batch.")
    return vectors

def _pinecone_index():
    if not settings.pinecone_api_key:
        raise RuntimeError("USE_PINECONE=true requires PINECONE_API_KEY in .env.")
    from pinecone import Pinecone
    return Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index)


def _retrieve_pinecone(
    query: str,
    role: str,
    top_k: int = 5,
    department: str | None = None,
):
    """Retrieve document chunks using Pinecone's Documents API."""
    from pinecone import DenseVectorQuery

    allowed_levels = {
        "viewer": ["public", "internal"],
        "analyst": ["public", "internal"],
        "administrator": ["public", "internal", "confidential"],
    }.get(role, ["public"])

    metadata_filter = {
        "access_level": {"$in": allowed_levels}
    }
    if department:
        metadata_filter["department"] = {"$eq": department}

    qvec = _embed_texts([query])[0]

    response = _pinecone_index().documents.search(
        namespace=settings.pinecone_namespace,
        score_by=[
            DenseVectorQuery(
                field="embedding",
                values=qvec,
            )
        ],
        top_k=top_k,
        include_fields=[
            "chunk_text",
            "title",
            "doc_id",
            "department",
            "document_type",
            "access_level",
            "created_date",
            "chunk_number",
        ],
        filter=metadata_filter,
    )

    results = []
    for match in response.matches:
        meta = match.to_dict() if hasattr(match, "to_dict") else vars(match)

        doc_id = meta.get("doc_id") or meta.get("_id", "").split("::", 1)[0]
        text_value = meta.get("chunk_text", "")

        results.append({
            "id": doc_id,
            "title": meta.get("title", doc_id),
            "text": text_value,
            "snippet": text_value[:420],
            "department": meta.get("department", "general"),
            "document_type": meta.get("document_type", "unknown"),
            "access_level": meta.get("access_level", "internal"),
            "created_date": meta.get("created_date", "unknown"),
            "score": round(float(meta.get("_score", 0) or 0), 4),
            "retrieval_mode": "pinecone_dense",
        })

    dedup = {}
    for result in results:
        if result["id"] not in dedup:
            dedup[result["id"]] = result

    return list(dedup.values())[:top_k]


def retrieve(query: str, role: str, top_k: int=5, department: str|None=None):
    """Use Pinecone dense+sparse hybrid retrieval when enabled; otherwise use local lexical fallback."""
    if settings.use_pinecone:
        return _retrieve_pinecone(query, role, top_k=top_k, department=department)
    docs=[d for d in DOCS if (not department or d.get("department")==department)]
    allowed_levels={"viewer":{"public","internal"},"analyst":{"public","internal"},"administrator":{"public","internal","confidential"}}.get(role,{"public"})
    docs=[d for d in docs if d.get("access_level","internal") in allowed_levels]
    lexical=bm25_like(query,docs); q=set(tokens(query)); scored=[]
    for lex,d in lexical:
        dt=set(tokens(d["text"])); overlap=len(q & dt)/max(1,len(q)); title_boost=0.15 if q & set(tokens(d["title"])) else 0
        dense_proxy=overlap
        score=0.65*(lex/(lex+1) if lex else 0)+0.25*dense_proxy+title_boost
        if score>0: scored.append((score,d))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{**d,"score":round(s,4),"snippet":d["text"][:420]} for s,d in scored[:top_k]]
