import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.llm import DeepSeekClient


class TestDeepSeekClient:
    """测试DeepSeekClient类"""

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        client = DeepSeekClient(
            api_key="test_key",
            api_base="https://test.com",
            model="test-model"
        )

        assert client.api_key == "test_key"
        assert client.api_base == "https://test.com"
        assert client.model == "test-model"

    @patch("app.core.llm.settings")
    def test_init_with_settings(self, mock_settings):
        """测试使用settings配置初始化"""
        mock_settings.deepseek_api_key = "settings_key"
        mock_settings.deepseek_api_base = "https://settings.com"
        mock_settings.deepseek_model = "settings-model"

        client = DeepSeekClient()

        assert client.api_key == "settings_key"
        assert client.api_base == "https://settings.com"
        assert client.model == "settings-model"

    @patch("app.core.llm.settings")
    def test_init_without_api_key_raises_error(self, mock_settings):
        """测试没有API密钥时抛出异常"""
        mock_settings.deepseek_api_key = ""

        with pytest.raises(ValueError, match="DeepSeek API密钥未配置"):
            DeepSeekClient()

    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """测试成功调用聊天补全API"""
        client = DeepSeekClient(api_key="test_key")

        # Mock响应数据
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "这是测试回复"
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()

            mock_post = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            messages = [{"role": "user", "content": "测试消息"}]
            result = await client.chat_completion(messages)

            assert result == mock_response
            mock_post.assert_called_once()

            # 验证调用参数
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == client.model
            assert call_args[1]["json"]["messages"] == messages
            assert call_args[1]["json"]["temperature"] == 0.7
            assert call_args[1]["json"]["max_tokens"] == 2000
            assert call_args[1]["json"]["stream"] is False

    @pytest.mark.asyncio
    async def test_chat_completion_with_custom_params(self):
        """测试使用自定义参数调用API"""
        client = DeepSeekClient(api_key="test_key")

        mock_response = {"choices": [{"message": {"content": "回复"}}]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()

            mock_post = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            messages = [{"role": "user", "content": "测试"}]
            await client.chat_completion(
                messages,
                temperature=0.5,
                max_tokens=1000,
                stream=True
            )

            call_args = mock_post.call_args
            assert call_args[1]["json"]["temperature"] == 0.5
            assert call_args[1]["json"]["max_tokens"] == 1000
            assert call_args[1]["json"]["stream"] is True

    @pytest.mark.asyncio
    async def test_chat_completion_http_error(self):
        """测试HTTP错误处理"""
        client = DeepSeekClient(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.raise_for_status.side_effect = Exception("HTTP错误")

            mock_post = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with pytest.raises(Exception, match="HTTP错误"):
                await client.chat_completion([{"role": "user", "content": "测试"}])

    def test_generate_response_with_system_message(self):
        """测试生成回复（带系统消息）"""
        client = DeepSeekClient(api_key="test_key")

        mock_result = {
            "choices": [
                {
                    "message": {
                        "content": "生成的回复"
                    }
                }
            ]
        }

        with patch.object(client, "chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_result

            result = client.generate_response(
                prompt="用户问题",
                system_message="你是一个助手"
            )

            assert result == "生成的回复"

            # 验证传递的消息
            call_args = mock_chat.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0]["role"] == "system"
            assert call_args[0]["content"] == "你是一个助手"
            assert call_args[1]["role"] == "user"
            assert call_args[1]["content"] == "用户问题"

    def test_generate_response_with_context(self):
        """测试生成回复（带上下文）"""
        client = DeepSeekClient(api_key="test_key")

        mock_result = {
            "choices": [
                {
                    "message": {
                        "content": "带上下文的回复"
                    }
                }
            ]
        }

        with patch.object(client, "chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_result

            result = client.generate_response(
                prompt="问题",
                context="上下文信息"
            )

            assert result == "带上下文的回复"

            # 验证消息格式
            call_args = mock_chat.call_args[0][0]
            assert len(call_args) == 1
            assert call_args[0]["role"] == "user"
            assert "上下文信息" in call_args[0]["content"]
            assert "问题" in call_args[0]["content"]

    def test_generate_response_simple(self):
        """测试简单生成回复"""
        client = DeepSeekClient(api_key="test_key")

        mock_result = {
            "choices": [
                {
                    "message": {
                        "content": "简单回复"
                    }
                }
            ]
        }

        with patch.object(client, "chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_result

            result = client.generate_response(prompt="简单问题")

            assert result == "简单回复"

    def test_generate_response_no_choices(self):
        """测试API返回无choices时的处理"""
        client = DeepSeekClient(api_key="test_key")

        with patch.object(client, "chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {}

            result = client.generate_response(prompt="问题")

            assert result == "抱歉,无法生成回复"

    def test_generate_response_empty_choices(self):
        """测试API返回空choices时的处理"""
        client = DeepSeekClient(api_key="test_key")

        with patch.object(client, "chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {"choices": []}

            result = client.generate_response(prompt="问题")

            assert result == "抱歉,无法生成回复"

    @patch("app.core.llm.settings")
    @patch("app.core.llm.DeepSeekClient")
    def test_global_deepseek_client(self, mock_client_class, mock_settings):
        """测试全局deepseek_client实例创建"""
        mock_settings.deepseek_api_key = "global_key"

        # 由于模块加载时已经创建了实例，这里只测试类型
        from app.core.llm import deepseek_client
        assert deepseek_client is not None
