"""
Configuration management for RAG Summarizer with Groq API
"""


from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import re
import os 
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "RAG Customer Support Summarizer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080", "*"]

    # Redis Cache (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = False
    
    # Model Paths
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    MODEL_CACHE_DIR: str = "./models"
    
    # Pipeline Configuration
    MAX_INPUT_LENGTH: int = 10000
    MIN_SENTENCE_LENGTH: int = 10
    MAX_SENTENCE_LENGTH: int = 50
    
    # TextRank
    TEXTRANK_TOP_K: int = 10
    TEXTRANK_WINDOW_SIZE: int = 2
    TEXTRANK_DAMPING: float = 0.85
    
    # Semantic Re-ranking
    SEMANTIC_TOP_K: int = 5
    SEMANTIC_THRESHOLD: float = 0.5
    
    # Groq LLM Configuration (FREE)
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT: int = 30
    
    # Performance
    BATCH_SIZE: int = 32
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 60
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    
    # Latency SLOs (milliseconds)
    SLO_EXTRACTIVE_P95: int = 300
    SLO_SEMANTIC_P95: int = 500
    SLO_ABSTRACTIVE_P95: int = 1500


     # ============================================
    # FIXED: Pydantic v2 Configuration for Windows
    # ============================================
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),  # Points to root .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )

    #class Config:
     #   env_file = ".env"
      #  env_file_encoding = "utf-8"
       # case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Precompiled regex patterns
REGEX_PATTERNS = {
    'html_tags': re.compile(r'<[^>]+>'),
    'whitespace': re.compile(r'\s+'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
    'section_header': re.compile(r'^[A-Z][A-Za-z\s]{1,30}:\s'),
    'ticket_id': re.compile(r'#\d+|TICKET-\d+|INC\d+', re.IGNORECASE),
}



# Keywords for heuristic scoring
PRIORITY_KEYWORDS = {
    'issue': 2.0,
    'error': 2.0,
    'problem': 2.0,
    'bug': 2.0,
    'resolved': 2.5,
    'solution': 2.5,
    'fixed': 2.0,
    'workaround': 1.5,
    'steps': 1.5,
    'reproduce': 1.5,
    'expected': 1.0,
    'actual': 1.0,
    'customer': 1.0,
    'user': 1.0,
}


# Section identifiers
KNOWN_SECTIONS = [
    'summary',
    'description',
    'steps to reproduce',
    'expected result',
    'actual result',
    'resolution',
    'workaround',
    'root cause',
    'impact',
    'priority',
]


