from pydantic import BaseModel, Field
from typing import Literal, Any

Role = Literal["viewer", "analyst", "administrator"]
class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    role: Role = "viewer"
    session_id: str = Field(default="default", min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
class Source(BaseModel):
    doc_id: str
    title: str
    snippet: str
    department: str
    document_type: str
    created_date: str
class Activity(BaseModel):
    state: str
    node: str
    detail: str
class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = []
    activities: list[Activity] = []
    validation: dict[str, Any] = {}
    session_id: str
    request_id: str
