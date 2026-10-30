"""Chunk sample Markdown documents, embed them via OpenRouter, and upsert to Pinecone."""
from __future__ import annotations
import re
from app.config import settings
from app.knowledge import DOCS, _embed_texts, _sparse_vector

def chunks_for_document(doc: dict, chunk_chars: int=900, overlap: int=150) -> list[dict]:
    text=doc["text"]
    chunks=[]; start=0
    while start < len(text):
        end=min(len(text),start+chunk_chars)
        if end < len(text):
            boundary=text.rfind("\n",start,end)
            if boundary > start+chunk_chars//2: end=boundary
        body=text[start:end].strip()
        if body: chunks.append({**doc,"chunk_text":body,"chunk_number":len(chunks)})
        if end >= len(text): break
        start=max(start+1,end-overlap)
    return chunks

def main():
    if not settings.pinecone_api_key: raise SystemExit("Set PINECONE_API_KEY in .env first.")
    if not settings.openrouter_api_key: raise SystemExit("Set OPENROUTER_API_KEY in .env first.")
    from pinecone import Pinecone, ServerlessSpec
    pc=Pinecone(api_key=settings.pinecone_api_key)
    existing=set(pc.list_indexes().names())
    if settings.pinecone_index not in existing:
        pc.create_index(name=settings.pinecone_index,dimension=settings.pinecone_dimension,metric="dotproduct",spec=ServerlessSpec(cloud=settings.pinecone_cloud,region=settings.pinecone_region))
        print(f"Created Pinecone index {settings.pinecone_index}; wait for it to become ready and rerun this command.")
        return
    index=pc.Index(settings.pinecone_index)
    all_chunks=[]
    for doc in DOCS: all_chunks.extend(chunks_for_document(doc))
    batch_size=32; upserted=0
    for start in range(0,len(all_chunks),batch_size):
        batch=all_chunks[start:start+batch_size]
        dense=_embed_texts([x["chunk_text"] for x in batch])
        vectors=[]
        for item,vector in zip(batch,dense):
            meta={k:item.get(k,"unknown") for k in ["title","department","document_type","access_level","created_date"]}
            meta.update({"doc_id":item["id"],"chunk_number":item["chunk_number"],"text":item["chunk_text"]})
            sparse=_sparse_vector(item["chunk_text"],DOCS)
            vectors.append({"id":f"{item['id']}::chunk-{item['chunk_number']}","values":vector,"sparse_values":sparse,"metadata":meta})
        index.upsert(vectors=vectors,namespace=settings.pinecone_namespace)
        upserted+=len(vectors); print(f"Upserted {upserted}/{len(all_chunks)} chunks")
    print(f"Done. Namespace={settings.pinecone_namespace}; chunks={upserted}")

if __name__ == "__main__": main()
