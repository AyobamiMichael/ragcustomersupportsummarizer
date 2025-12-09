# backend/test_config.py
"""
Debug script to test if configuration is loading correctly
Run this from the backend folder: python test_config.py
"""

import os
from pathlib import Path

print("=" * 60)
print("CONFIGURATION DEBUG SCRIPT")
print("=" * 60)

# Check current directory
print(f"\n1. Current Directory: {os.getcwd()}")

# Check if .env exists in parent directory
env_path = Path("../.env")
if env_path.exists():
    print(f"✅ .env file found at: {env_path.absolute()}")
else:
    print(f"❌ .env file NOT found at: {env_path.absolute()}")
    print(f"   Looking for .env in these locations:")
    for location in [".env", "../.env", "../../.env"]:
        path = Path(location)
        print(f"   - {path.absolute()}: {'✅ EXISTS' if path.exists() else '❌ NOT FOUND'}")

# Try to read GROQ_API_KEY directly from os.environ
print(f"\n2. Reading from os.environ:")
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    print(f"✅ GROQ_API_KEY found: {groq_key[:10]}...{groq_key[-5:] if len(groq_key) > 15 else ''}")
else:
    print(f"❌ GROQ_API_KEY not found in environment")

# Try loading with python-dotenv
print(f"\n3. Loading with python-dotenv:")
try:
    from dotenv import load_dotenv
    
    # Try loading from parent directory
    loaded = load_dotenv("../.env")
    print(f"   load_dotenv('../.env'): {'✅ Success' if loaded else '❌ Failed'}")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"   ✅ GROQ_API_KEY now found: {groq_key[:10]}...{groq_key[-5:] if len(groq_key) > 15 else ''}")
    else:
        print(f"   ❌ GROQ_API_KEY still not found")
        
except ImportError:
    print("   ❌ python-dotenv not installed")

# Try loading Settings with Pydantic
print(f"\n4. Loading with Pydantic Settings:")
try:
    from src.config import get_settings
    
    settings = get_settings()
    print(f"   Settings loaded successfully")
    print(f"   GROQ_API_KEY: {'✅ Set (' + settings.GROQ_API_KEY[:10] + '...' + settings.GROQ_API_KEY[-5:] + ')' if settings.GROQ_API_KEY else '❌ Not set (None)'}")
    print(f"   LLM_MODEL: {settings.LLM_MODEL}")
    print(f"   API_PORT: {settings.API_PORT}")
    
except Exception as e:
    print(f"   ❌ Error loading settings: {e}")

# Check .env file content
print(f"\n5. Checking .env file content:")
try:
    with open("../.env", "r") as f:
        lines = f.readlines()
        groq_lines = [line for line in lines if "GROQ_API_KEY" in line and not line.strip().startswith("#")]
        if groq_lines:
            print(f"   ✅ Found GROQ_API_KEY line in .env:")
            for line in groq_lines:
                # Hide the actual key
                if "=" in line:
                    key_name, key_value = line.split("=", 1)
                    key_value = key_value.strip()
                    if key_value and key_value != "your_key_here":
                        print(f"      {key_name}={key_value[:10]}...{key_value[-5:]}")
                    else:
                        print(f"      {key_name}={key_value} ⚠️  (placeholder value)")
        else:
            print(f"   ❌ GROQ_API_KEY not found in .env file")
            print(f"   First 5 lines of .env:")
            for i, line in enumerate(lines[:5]):
                print(f"      {line.rstrip()}")
                
except FileNotFoundError:
    print(f"   ❌ .env file not found")
except Exception as e:
    print(f"   ❌ Error reading .env: {e}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)


# ========================================
# CORRECTED config.py
# ========================================

# backend/src/config.py
"""
Configuration management for RAG Summarizer with Groq API
CORRECTED VERSION - Proper Pydantic Settings usage
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import re


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
    
    # ============================================
    # Groq LLM Configuration (FREE)
    # ✅ CORRECTED: Let Pydantic handle environment variables
    # ============================================
    GROQ_API_KEY: Optional[str] = None  # Pydantic will read from .env automatically
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
    
    class Config:
        # ✅ CRITICAL: This tells Pydantic where to find .env
        # It looks in the current directory and parent directories
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Optional: search parent directories for .env
        env_file_path = "../.env"  # Add this if .env is in parent folder


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