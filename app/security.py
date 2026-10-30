"""Request validation, role-based tool permissions, injection heuristic and token bucket."""
import re, time, threading
from collections import defaultdict
from fastapi import HTTPException

ROLE_PERMISSIONS = {
    "viewer": {"knowledge_search"},
    "analyst": {"knowledge_search", "python_analysis", "mcp_employee_lookup", "mcp_service_catalog", "mcp_incident_lookup"},
    "administrator": {"knowledge_search", "python_analysis", "mcp_employee_lookup", "mcp_service_catalog", "mcp_incident_lookup", "admin_stats"},
}
INJECTION_PATTERNS = [r"ignore (all )?(previous|prior) instructions", r"reveal (the )?(system prompt|secrets|api key)", r"exfiltrate", r"bypass (the )?(access|security|authorization)", r"act as (an? )?administrator"]

def validate_message(message: str, max_chars: int = 4000) -> str:
    value = message.strip()
    if not value or len(value) > max_chars:
        raise HTTPException(422, "Message must be non-empty and within configured length limit.")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise HTTPException(422, "Control characters are not permitted.")
    return value

def detect_injection(message: str) -> bool:
    return any(re.search(p, message, re.I) for p in INJECTION_PATTERNS)

def authorize(role: str, tool: str):
    if tool not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail=f"Role '{role}' is not authorized to use tool '{tool}'.")

class TokenBucketLimiter:
    """Thread-safe in-memory per-user token bucket. Use Redis for multi-worker production."""
    def __init__(self, capacity=20, refill_per_minute=10):
        self.capacity=float(capacity); self.refill=float(refill_per_minute)/60.0
        self.buckets=defaultdict(lambda: [self.capacity, time.monotonic()]); self.lock=threading.Lock()
    def consume(self, user_id: str, tokens: float=1.0) -> bool:
        with self.lock:
            available, last = self.buckets[user_id]
            now=time.monotonic(); available=min(self.capacity, available+(now-last)*self.refill)
            if available < tokens:
                self.buckets[user_id]=[available, now]; return False
            self.buckets[user_id]=[available-tokens, now]; return True
