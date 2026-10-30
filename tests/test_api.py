from fastapi.testclient import TestClient
from app.api import app
client=TestClient(app)

def test_health(): assert client.get("/health").status_code==200
def test_chat_contract():
    r=client.post("/chat",json={"user_id":"viewer_demo","role":"viewer","session_id":"test","message":"What caused the payment gateway timeout?"})
    assert r.status_code==200
    data=r.json(); assert data["answer"] and data["activities"] and "sources" in data
def test_invalid_user_id():
    r=client.post("/chat",json={"user_id":"bad user","role":"viewer","session_id":"x","message":"hi"})
    assert r.status_code==422
