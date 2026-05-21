import os
from pydantic_settings import BaseSettings

# .env 文件的绝对路径（相对于本文件向上两级到 backend/），
# 无论从哪个目录启动后端都能正确找到
_ENV_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

class Settings(BaseSettings):
    """应用配置"""

    # DeepSeek API配置
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout: float = 180.0

    # 搜索引擎配置
    search_engine: str = "duckduckgo"
    search_max_results: int = 5
    web_search_enabled: bool = True   # 改 .env: WEB_SEARCH_ENABLED=false 可关闭网络检索

    # ChromaDB配置
    chroma_db_path: str = "./chroma_db"
    chroma_collection_name: str = "mota_knowledge"

    # Embedding模型配置
    embedding_model_type: str = "vllm"
    model_base_dir: str = "/root/modelparams"
    embedding_model_name: str = "Qwen3-Embedding-0.6B"
    embedding_device: str = "cuda"
    vllm_gpu_memory_utilization: float = 0.70
    vllm_max_model_len: int = 8192

    # 应用配置
    app_env: str = "development"
    debug: bool = True

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
