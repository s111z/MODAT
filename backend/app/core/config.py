import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
    # DeepSeek API配置
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "sk-c978cfc8da4c455287129de3bf1ba212")
    deepseek_api_base: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # 搜索引擎配置
    search_engine: str = os.getenv("SEARCH_ENGINE", "duckduckgo")
    search_max_results: int = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    
    # ChromaDB配置
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # 应用配置
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()