import streamlit as st
import httpx, os, json
API_URL=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="Orysys AI Assistant",page_icon="🔎",layout="wide")
st.title("Orysys Enterprise AI Assistant")
st.caption("Assessment proof of concept · Grounded knowledge · Visible agent activity")
with st.sidebar:
    st.subheader("Demo identity")
    user=st.selectbox("User",["viewer_demo","analyst_demo","admin_demo"])
    role={"viewer_demo":"viewer","analyst_demo":"analyst","admin_demo":"administrator"}[user]
    st.write(f"Role: **{role}**")
    session=st.text_input("Session ID","demo-session")
    st.warning("Demo identity selector only. Production identity must come from verified OIDC/JWT claims.")
    try:
        health = httpx.get(f"{API_URL}/health", timeout=2.0).json()
        if health.get("mock_mode"):
            st.error("LLM mode: MOCK (not suitable as a live AI demo)")
        elif health.get("provider") == "openrouter" and health.get("openrouter_configured"):
            st.success(f"LLM mode: OpenRouter · {health.get('model')}")
        else:
            st.warning("Live mode selected, but OPENROUTER_API_KEY is not configured.")
    except Exception:
        st.caption("Backend status unavailable; start FastAPI on port 8000.")
with st.sidebar:
    st.divider()
    st.subheader("Knowledge document management")
    if role == "administrator":
        uploaded = st.file_uploader(
            "Upload knowledge document",
            type=["pdf", "docx", "txt", "md"],
            help="Maximum 15 MB. Scanned PDFs without selectable text require OCR first.",
            key="knowledge_document_uploader",
        )

        with st.form("document_upload_form", clear_on_submit=False):
            department = st.selectbox(
                "Department",
                ["general", "payments", "engineering", "security",
                "operations", "finance", "hr"],
            )
            document_type = st.selectbox(
                "Document type",
                ["policy", "architecture", "runbook", "incident",
                "product_spec", "meeting_notes", "other"],
            )
            access_level = st.selectbox(
                "Access level",
                ["public", "internal", "confidential"],
                index=1,
            )

            submit_upload = st.form_submit_button(
                "Upload and index",
                type="primary",
                disabled=uploaded is None,
            )

        if submit_upload and uploaded is not None:
            try:
                with st.spinner(
                    "Validating, extracting, chunking and indexing document…"
                ):
                    response = httpx.post(
                        f"{API_URL}/documents/upload",
                        data={
                            "user_id": user,
                            "role": role,
                            "department": department,
                            "document_type": document_type,
                            "access_level": access_level,
                        },
                        files={
                            "file": (
                                uploaded.name,
                                uploaded.getvalue(),
                                uploaded.type or "application/octet-stream",
                            )
                        },
                        timeout=180.0,
                    )

                if response.status_code >= 400:
                    st.error(
                        f"Upload failed ({response.status_code}): {response.text}"
                    )
                else:
                    result = response.json()
                    st.success(
                        f"Indexed {result['title']} · "
                        f"{result['chunks']} chunk(s)"
                    )
                    st.caption(f"Retrieval mode: {result['index_mode']}")

            except Exception as exc:
                st.error(f"Upload service unavailable: {exc}")
    else:
        st.caption("Document uploads are restricted to the Administrator role in this assessment demo.")
    try:
        listed = httpx.get(f"{API_URL}/documents", timeout=5.0).json().get("documents", [])
        with st.expander(f"Indexed documents ({len(listed)})"):
            for doc in listed:
                st.markdown(f"**{doc.get('title') or doc.get('filename')}**")
                st.caption(f"{doc.get('department')} · {doc.get('document_type')} · {doc.get('access_level')}")
    except Exception:
        st.caption("Document list unavailable until the backend starts.")

if "messages" not in st.session_state: st.session_state.messages=[]
left,right=st.columns([3,2])
with left:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    prompt=st.chat_input("Ask about incidents, runbooks, services, or policies…")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        try:
            with st.spinner("Running LangGraph workflow…"):
                r=httpx.post(f"{API_URL}/chat",json={"user_id":user,"role":role,"session_id":session,"message":prompt},timeout=30)
            if r.status_code>=400: st.error(f"Request failed ({r.status_code}): {r.text}"); st.stop()
            data=r.json(); st.session_state.messages.append({"role":"assistant","content":data["answer"]})
            with st.chat_message("assistant"): st.markdown(data["answer"])
            st.session_state.last_result=data
        except Exception as e: st.error(f"API unavailable: {e}. Start FastAPI first.")
with right:
    st.subheader("Agent activity")
    data=st.session_state.get("last_result")
    if data:
        for a in data.get("activities",[]):
            st.markdown(f"**{a['node']}** · {a['state']}\n\n{a['detail']}")
            st.divider()
        st.subheader("Retrieved evidence")
        for s in data.get("sources",[]):
            with st.expander(f"{s['title']} · {s['doc_id']}"):
                st.caption(f"{s['department']} · {s['document_type']} · {s['created_date']}")
                st.write(s["snippet"])
        st.subheader("Validation")
        st.json(data.get("validation",{}))
    else: st.info("Agent state, retrieval evidence, and validation results appear here after a question.")
