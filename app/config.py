from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Make .env visible to LangGraph/LangSmith instrumentation as well as Pydantic settings.
load_dotenv(override=False)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Orysys Enterprise AI Assistant"
    app_env: str = "local"
    mock_mode: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_app_url: str = "http://localhost:8501"
    openrouter_app_name: str = "Orysys Enterprise AI Assistant"
    use_pinecone: bool = False
    pinecone_api_key: str = ""
    pinecone_index: str = "orysys-enterprise-knowledge"
    pinecone_namespace: str = "internal"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    pinecone_dimension: int = 1536
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "orysys-enterprise-assistant"
    token_bucket_capacity: int = 20
    token_bucket_refill_per_minute: int = 10
    max_request_chars: int = 4000

settings = Settings()
