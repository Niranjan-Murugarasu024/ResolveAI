import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ResolveAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Database
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./resolveai.db"
    
    # LLM Settings & Multi-Provider Architecture
    LLM_PROVIDER: str = "openrouter" # openrouter, nvidia, groq, gemini, mock
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    NVIDIA_API_KEY: Optional[str] = os.getenv("NVIDIA_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    DEFAULT_MODEL: str = "openai/gpt-4o-mini"
    NVIDIA_MODEL: str = "moonshotai/kimi-k3"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    FALLBACK_MODEL: str = "google/gemini-2.5-flash"
    
    # Decision Engine Thresholds
    RESOLVE_THRESHOLD: float = 0.90
    REVIEW_THRESHOLD: float = 0.70
    
    # Agent Guardrails & Stop Conditions
    MAX_AGENT_ITERATIONS: int = 5
    MAX_TOOL_CALLS: int = 6
    MAX_EXECUTION_SECONDS: float = 30.0
    MAX_COST_PER_TICKET_USD: float = 0.05
    
    # Knowledge Directory
    KNOWLEDGE_DIR: str = "knowledge"
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
