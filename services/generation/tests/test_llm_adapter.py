"""LLM 适配器测试。"""

import json

import pytest

from app.core.llm_adapter import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponse,
    MockLLMAdapter,
    OpenAIAdapter,
    get_llm_adapter,
)


class TestMockLLMAdapter:
    """Mock LLM 适配器测试。"""

    def test_init(self):
        """测试初始化。"""
        adapter = MockLLMAdapter(model="test-model", max_tokens=512, temperature=0.5)
        assert adapter.model == "test-model"
        assert adapter.max_tokens == 512
        assert adapter.temperature == 0.5

    @pytest.mark.asyncio
    async def test_generate(self):
        """测试内容生成。"""
        adapter = MockLLMAdapter()
        response = await adapter.generate("请生成一个NPC角色")

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.model == "mock-model"
        assert response.finish_reason == "stop"
        assert "total_tokens" in response.usage

    @pytest.mark.asyncio
    async def test_generate_with_npc_prompt(self):
        """测试 NPC 提示生成。"""
        adapter = MockLLMAdapter()
        response = await adapter.generate("请生成一个NPC角色描述")

        content = response.content
        data = json.loads(content)
        assert "name" in data
        assert "role" in data
        assert "description" in data

    @pytest.mark.asyncio
    async def test_generate_with_quest_prompt(self):
        """测试任务提示生成。"""
        adapter = MockLLMAdapter()
        response = await adapter.generate("请设计一个quest任务")

        content = response.content
        data = json.loads(content)
        assert "title" in data
        assert "objectives" in data

    @pytest.mark.asyncio
    async def test_generate_json(self):
        """测试 JSON 生成。"""
        adapter = MockLLMAdapter()
        data = await adapter.generate_json("请生成一个NPC角色")

        assert isinstance(data, dict)
        assert "name" in data

    @pytest.mark.asyncio
    async def test_generate_json_with_system_prompt(self):
        """测试带系统提示的 JSON 生成。"""
        adapter = MockLLMAdapter()
        data = await adapter.generate_json(
            prompt="生成内容",
            system_prompt="你是游戏设计师",
        )

        assert isinstance(data, dict)


class TestOpenAIAdapter:
    """OpenAI 适配器测试（不实际调用 API）。"""

    def test_init(self):
        """测试初始化。"""
        adapter = OpenAIAdapter(
            api_key="test-key",
            model="gpt-4o-mini",
            max_tokens=1024,
            temperature=0.7,
            timeout=60,
        )
        assert adapter.api_key == "test-key"
        assert adapter.model == "gpt-4o-mini"
        assert adapter.max_tokens == 1024
        assert adapter.temperature == 0.7
        assert adapter.timeout == 60

    def test_init_with_base_url(self):
        """测试自定义 API URL。"""
        adapter = OpenAIAdapter(
            api_key="test-key",
            base_url="https://custom.api.com/v1",
        )
        assert adapter.base_url == "https://custom.api.com/v1"

    @pytest.mark.asyncio
    async def test_close_client(self):
        """测试关闭客户端。"""
        adapter = OpenAIAdapter(api_key="test-key")
        # 初始化客户端
        await adapter._get_client()
        assert adapter._client is not None

        # 关闭客户端
        await adapter.close()
        assert adapter._client is None


class TestGetLLMAdapter:
    """获取 LLM 适配器测试。"""

    def test_get_mock_adapter_by_default(self, monkeypatch):
        """测试默认返回 Mock 适配器。"""
        monkeypatch.setenv("GENERATION_LLM_PROVIDER", "mock")
        adapter = get_llm_adapter()
        assert isinstance(adapter, MockLLMAdapter)

    def test_get_mock_adapter_when_provider_is_mock(self, monkeypatch):
        """测试显式指定 mock。"""
        monkeypatch.setenv("GENERATION_LLM_PROVIDER", "mock")
        adapter = get_llm_adapter()
        assert isinstance(adapter, MockLLMAdapter)

    def test_fallback_to_mock_when_no_api_key(self, monkeypatch):
        """测试无 API Key 时回退到 Mock。"""
        monkeypatch.setenv("GENERATION_LLM_PROVIDER", "openai")
        monkeypatch.setenv("GENERATION_LLM_API_KEY", "")
        adapter = get_llm_adapter()
        # 无 API Key 时应回退到 Mock
        assert isinstance(adapter, MockLLMAdapter)


class TestLLMResponse:
    """LLM 响应测试。"""

    def test_response_creation(self):
        """测试响应创建。"""
        response = LLMResponse(
            content="test content",
            model="test-model",
            usage={"total_tokens": 100},
            finish_reason="stop",
        )
        assert response.content == "test content"
        assert response.model == "test-model"
        assert response.usage == {"total_tokens": 100}
        assert response.finish_reason == "stop"


class TestLLMErrors:
    """LLM 错误测试。"""

    def test_api_error(self):
        """测试 API 错误。"""
        error = LLMAPIError("API failed", status_code=500)
        assert str(error) == "API failed"
        assert error.status_code == 500

    def test_timeout_error(self):
        """测试超时错误。"""
        error = LLMTimeoutError("Request timeout")
        assert isinstance(error, Exception)

    def test_rate_limit_error(self):
        """测试速率限制错误。"""
        error = LLMRateLimitError("Rate limit exceeded")
        assert isinstance(error, Exception)
