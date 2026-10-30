# Configure OpenRouter on Windows

## 1. Create an API key

Create a key in your OpenRouter account: https://openrouter.ai/keys. Do not paste it into source code or commit it to GitHub.

## 2. Configure `.env`

In the project root, copy `.env.example` to `.env` if `.env` does not exist. Edit `.env` and set:

```dotenv
MOCK_MODE=false
OPENROUTER_API_KEY=sk-or-v1-your-real-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_URL=http://localhost:8501
OPENROUTER_APP_NAME=Orysys Enterprise AI Assistant
```

Choose a model slug that is currently available in your OpenRouter account. The default is an example; model availability and pricing can change.

## 3. Install and restart

From CMD in the project root:

```cmd
.venv\Scripts\activate
python -m pip install -e .
uvicorn app.api:app --reload --port 8000
```

In a second CMD window:

```cmd
.venv\Scripts\activate
python -m streamlit run app/ui.py
```

Open http://localhost:8000/health. Confirm `provider` is `openrouter`, `mock_mode` is `false`, and `openrouter_configured` is `true`. This confirms configuration only; send a chat prompt to verify a live model request.

## 4. LangSmith tracing

In `.env`, set `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY` to your LangSmith API key, and `LANGCHAIN_PROJECT=orysys-enterprise-assistant`. Restart FastAPI and inspect the matching project in LangSmith. Do not include API keys in screenshots or the public repository.

## 5. Troubleshooting

- `401` / authentication error: confirm the OpenRouter key is correct and active.
- `402` / insufficient credits: review OpenRouter account credits and the selected model's pricing.
- `404` / model not found: choose a currently listed model slug.
- `429`: check provider/account rate limits and retry later.
- `OPENROUTER_API_KEY is missing`: `.env` must be in the directory from which you launch FastAPI; restart the server after editing it.

The app intentionally does not silently switch to a fake answer when live mode fails. That makes provider failures visible during the assessment demo.

## Optional: enable real Pinecone hybrid retrieval

Set these in `.env` after creating a Pinecone API key:

```dotenv
USE_PINECONE=true
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=orysys-enterprise-knowledge
PINECONE_NAMESPACE=internal
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_DIMENSION=1536
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
```

From the project root, run `python -m app.ingest`. The first run creates the index if absent; wait for Pinecone to report it ready, then rerun to chunk, embed, and upsert the sample documents. Restart FastAPI. `/health` should report `retrieval_mode: pinecone_hybrid`. If `USE_PINECONE=false`, the app intentionally uses the local lexical fallback.
