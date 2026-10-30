import pytest
from app.uploads import extract_text, split_chunks

def test_extract_plain_text():
    assert extract_text("runbook.txt", b"Payment outage response\nRestart only after approval.") == "Payment outage response\nRestart only after approval."

def test_reject_unsupported_file():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("payload.exe", b"hello")

def test_reject_empty_text():
    with pytest.raises(ValueError, match="empty"):
        extract_text("empty.txt", b"   ")

def test_chunk_overlap_and_content():
    text = "line\n" * 600
    chunks = split_chunks(text, chunk_chars=300, overlap=50)
    assert len(chunks) > 1
    assert all(chunks)
