from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    DATABASE_URL: str = 'postgresql+psycopg2://cherrat:cherrat_pwd@localhost:5432/cherrat_stock'
    SECRET_KEY: str = 'change-me'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    QDRANT_URL: str = 'http://localhost:6333'
    QDRANT_COLLECTION: str = 'stock_medicaments'
    OLLAMA_URL: str = 'http://localhost:11434'
    LLM_MODEL: str = 'llama3.1:8b'
    EMBED_MODEL: str = 'nomic-embed-text'
    UPLOAD_DIR: str = 'uploads'
    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''
    ALERT_EMAILS: str = ''
    # Clé partagée avec n8n (en-tête X-API-Key). Vide = automatisation désactivée.
    AUTOMATION_API_KEY: str = ''


settings = Settings()
