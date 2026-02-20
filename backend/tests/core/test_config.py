import os
import pytest
from unittest.mock import patch
from app.core.config import Settings, settings


class TestSettings:
    """测试Settings配置类"""

    def test_settings_default_values(self):
        """测试默认配置值"""
        test_settings = Settings()

        # 测试DeepSeek默认配置
        assert test_settings.deepseek_api_base == "https://api.deepseek.com/v1"
        assert test_settings.deepseek_model == "deepseek-chat"

        # 测试搜索引擎默认配置
        assert test_settings.search_engine == "duckduckgo"
        assert test_settings.search_max_results == 5

        # 测试ChromaDB默认配置
        assert test_settings.chroma_db_path == "./chroma_db"

        # 测试应用默认配置
        assert test_settings.app_env == "development"
        assert test_settings.debug is True

    @patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test_key_123",
        "DEEPSEEK_API_BASE": "https://custom.api.com/v1",
        "DEEPSEEK_MODEL": "custom-model",
        "SEARCH_ENGINE": "google",
        "SEARCH_MAX_RESULTS": "10",
        "CHROMA_DB_PATH": "/custom/path",
        "APP_ENV": "production",
        "DEBUG": "false"
    })
    def test_settings_from_env(self):
        """测试从环境变量读取配置"""
        test_settings = Settings()

        assert test_settings.deepseek_api_key == "test_key_123"
        assert test_settings.deepseek_api_base == "https://custom.api.com/v1"
        assert test_settings.deepseek_model == "custom-model"
        assert test_settings.search_engine == "google"
        assert test_settings.search_max_results == 10
        assert test_settings.chroma_db_path == "/custom/path"
        assert test_settings.app_env == "production"
        assert test_settings.debug is False

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""})
    def test_empty_api_key(self):
        """测试空API密钥"""
        test_settings = Settings()
        assert test_settings.deepseek_api_key == ""

    @patch.dict(os.environ, {"DEBUG": "True"})
    def test_debug_true_variations(self):
        """测试DEBUG的各种true值"""
        test_settings = Settings()
        assert test_settings.debug is True

    @patch.dict(os.environ, {"DEBUG": "FALSE"})
    def test_debug_false_case_insensitive(self):
        """测试DEBUG不区分大小写"""
        test_settings = Settings()
        assert test_settings.debug is False

    def test_global_settings_instance(self):
        """测试全局settings实例"""
        assert settings is not None
        assert isinstance(settings, Settings)
