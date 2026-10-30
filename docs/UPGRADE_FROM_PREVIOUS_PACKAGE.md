# Upgrade from the earlier assessment package

1. Stop both Streamlit and FastAPI terminals with Ctrl+C.
2. Back up your existing project folder.
3. Extract the updated ZIP and copy its project files over the old folder. Preserve your existing `.env` file, or create one by copying `.env.example` to `.env`.
4. In `.env`, set `MOCK_MODE=false` and set a real `OPENROUTER_API_KEY`.
5. In the project root, run `python -m pip install -e .`.
6. Restart FastAPI and Streamlit.
7. Check `http://localhost:8000/health`: `provider` should be `openrouter`, `mock_mode` should be `false`, and `openrouter_configured` should be `true`.
8. Send a question in the UI. The response validation panel should identify `provider: openrouter`.

Never publish `.env` or include API keys in Git. The ZIP intentionally does not include a real `.env`.
