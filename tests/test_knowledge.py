from app.knowledge import retrieve, DOCS

def test_sample_docs_loaded(): assert len(DOCS)>=4
def test_payment_query_retrieves_incident():
    docs=retrieve("payment gateway timeout certificate", "viewer")
    assert docs
    assert any("payment" in d["title"].lower() or "payment" in d["text"].lower() for d in docs)
def test_metadata_present():
    d=retrieve("retry spike database failover", "viewer")[0]
    assert all(k in d for k in ["id","department","document_type","access_level","created_date"])
