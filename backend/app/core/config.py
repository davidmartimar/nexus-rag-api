import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "NEXUS"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # Database
    # Default to /app/data/nexus.db for Docker/Production
    # This can be overridden by setting DB_PATH env var
    DB_PATH: str = os.getenv("DB_PATH", "/app/data/nexus.db")
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH}"
    
    # Limits
    LOG_RETENTION_HOURS: int = 24
    CHAT_RETENTION_HOURS: int = 2
    MAX_REQUESTS_LIMIT: int = 20

    def __init__(self):
        # Strict security validation for production
        if not self.SECRET_KEY:
            raise ValueError("CRITICAL: SECRET_KEY environment variable is not set. Application cannot start securely.")
        if not self.OPENAI_API_KEY:
             # Warning only? Or fail? User said "Si no existen las claves... el código debe fallar". 
             # OpenAI key is essential for NEXUS.
            raise ValueError("CRITICAL: OPENAI_API_KEY environment variable is not set.")

settings = Settings()
