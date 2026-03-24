"""DesensitizeAgent单元测试"""

import pytest
from agents.desensitize_agent import DesensitizeAgent


@pytest.mark.unit
class TestDesensitizeAgent:

    def setup_method(self):
        self.agent = DesensitizeAgent()

    # --- 脱敏测试 ---

    def test_phone_desensitize(self):
        text, mapping = self.agent.desensitize("联系电话13812345678")
        assert "13812345678" not in text
        assert "[PHONE_" in text
        assert "13812345678" in mapping.values()

    def test_id_card_desensitize(self):
        text, mapping = self.agent.desensitize("身份证110101199001011234")
        assert "110101199001011234" not in text
        assert "[ID_CARD_" in text

    def test_email_desensitize(self):
        text, mapping = self.agent.desensitize("邮箱test@example.com")
        assert "test@example.com" not in text
        assert "[EMAIL_" in text

    def test_bank_card_desensitize(self):
        text, mapping = self.agent.desensitize("卡号6222021234567890123")
        assert "6222021234567890123" not in text
        assert "[BANK_CARD_" in text

    def test_multi_pii(self):
        text = "张三 手机13912345678 邮箱zhang@test.com 身份证110101199001011234"
        result, mapping = self.agent.desensitize(text)
        assert len(mapping) == 3
        assert "13912345678" not in result
        assert "zhang@test.com" not in result
        assert "110101199001011234" not in result

    def test_no_pii(self):
        text = "今天天气不错，适合写代码"
        result, mapping = self.agent.desensitize(text)
        assert result == text
        assert mapping == {}

    def test_duplicate_pii(self):
        text = "号码13812345678，再次确认13812345678"
        result, mapping = self.agent.desensitize(text)
        # 同一号码只有一条mapping
        phone_values = [v for v in mapping.values() if v == "13812345678"]
        assert len(phone_values) == 1
        # 两处都被替换
        assert "13812345678" not in result

    # --- 还原测试 ---

    def test_restore(self):
        original = "联系电话13812345678，邮箱test@example.com"
        desensitized, mapping = self.agent.desensitize(original)
        restored = DesensitizeAgent.restore(desensitized, mapping)
        assert restored == original

    def test_restore_empty_mapping(self):
        text = "无敏感信息"
        restored = DesensitizeAgent.restore(text, {})
        assert restored == text
