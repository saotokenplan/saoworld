"""LLM 服务适配器模块，支持 OpenAI API 和 Mock 实现。"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应结果。"""

    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str
    cost_usd: float = 0.0


class LLMAdapterError(Exception):
    """LLM 适配器错误基类。"""

    pass


class LLMTimeoutError(LLMAdapterError):
    """LLM 调用超时错误。"""

    pass


class LLMRateLimitError(LLMAdapterError):
    """LLM 速率限制错误。"""

    pass


class LLMAPIError(LLMAdapterError):
    """LLM API 调用错误。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMAdapter(ABC):
    """LLM 服务适配器抽象基类。"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """生成内容。

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大 Token 数
            temperature: 温度参数

        Returns:
            LLM 响应结果

        Raises:
            LLMTimeoutError: 调用超时
            LLMRateLimitError: 速率限制
            LLMAPIError: API 调用错误
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """生成 JSON 格式内容。

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大 Token 数
            temperature: 温度参数

        Returns:
            解析后的 JSON 对象

        Raises:
            LLMTimeoutError: 调用超时
            LLMRateLimitError: 速率限制
            LLMAPIError: API 调用错误
            json.JSONDecodeError: JSON 解析错误
        """
        pass


class MockLLMAdapter(LLMAdapter):
    """Mock LLM 适配器，用于测试环境。"""

    def __init__(
        self,
        model: str = "mock-model",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.mock_response: dict[str, Any] | None = None

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """生成模拟内容。"""
        await asyncio.sleep(0.1)

        if self.mock_response is not None:
            content = json.dumps(self.mock_response)
        else:
            content = self._generate_mock_content(prompt)

        usage = {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
        prompt_cost = (usage["prompt_tokens"] / 1000) * settings.cost_model_price_per_1k_prompt_tokens
        completion_cost = (usage["completion_tokens"] / 1000) * settings.cost_model_price_per_1k_completion_tokens

        logger.info(
            "mock_llm_generate prompt_length=%d usage=%s cost_usd=%.6f",
            len(prompt),
            usage,
            prompt_cost + completion_cost,
        )

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            finish_reason="stop",
            cost_usd=prompt_cost + completion_cost,
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """生成模拟 JSON 内容。"""
        if self.mock_response is not None:
            return self.mock_response.copy()

        response = await self.generate(prompt, system_prompt, max_tokens, temperature)
        try:
            result: dict[str, Any] = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            return self._generate_mock_json(prompt)

    def _generate_mock_content(self, prompt: str) -> str:
        """根据提示词生成模拟内容。"""
        prompt_lower = prompt.lower()

        if "npc" in prompt_lower:
            return json.dumps({
                "name": "艾瑞尔·铁盾",
                "role": "铁匠",
                "personality": "勇敢",
                "faction_id": "faction_iron_guard",
                "region_id": "region_core",
                "description": "一位勇敢的铁匠，在铁卫城工作多年，为冒险者打造武器和护甲。",
                "dialogue": "欢迎来到铁卫城，旅行者。需要武器吗？",
            })
        elif "quest" in prompt_lower or "任务" in prompt_lower:
            return json.dumps({
                "title": "寻找失落的宝藏",
                "type": "side",
                "region_id": "region_core",
                "chapter_id": "chapter_01",
                "description": "在铁卫城周边寻找传说中的宝藏。",
                "objectives": ["前往目标地点", "击败敌人", "收集物品"],
                "rewards": {"experience": 100, "gold": 50},
            })
        elif "region" in prompt_lower or "区域" in prompt_lower:
            return json.dumps({
                "name": "迷雾森林",
                "difficulty": "normal",
                "region_id": "region_forest",
                "chapter_id": "chapter_01",
                "description": "一片神秘的森林，充满危险和机遇。",
                "features": ["神秘遗迹", "危险生物", "宝藏"],
            })
        else:
            return json.dumps({"generated_content": "模拟生成的内容", "prompt": prompt[:100]})

    def _generate_mock_json(self, prompt: str) -> dict[str, Any]:
        """生成模拟 JSON 数据。"""
        return {"generated_content": "模拟生成的内容", "prompt": prompt[:100]}


class OpenAIAdapter(LLMAdapter):
    """OpenAI API 适配器。"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = None

    async def _get_client(self):
        """获取 HTTP 客户端。"""
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """调用 OpenAI API 生成内容。"""
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            prompt_cost = (prompt_tokens / 1000) * settings.cost_model_price_per_1k_prompt_tokens
            completion_cost = (completion_tokens / 1000) * settings.cost_model_price_per_1k_completion_tokens
            total_cost = prompt_cost + completion_cost

            logger.info(
            "openai_llm_generate model=%s usage=%s cost_usd=%.6f finish_reason=%s",
            data["model"],
            usage,
            total_cost,
            choice.get("finish_reason", "stop"),
        )

            return LLMResponse(
                content=choice["message"]["content"],
                model=data["model"],
                usage=usage,
                finish_reason=choice.get("finish_reason", "stop"),
                cost_usd=total_cost,
            )

        except Exception as e:
            if hasattr(e, "response"):
                status_code = getattr(e.response, "status_code", None)
                if status_code == 429:
                    raise LLMRateLimitError(f"Rate limit exceeded: {e}")
                elif status_code == 408:
                    raise LLMTimeoutError(f"Request timeout: {e}")
                else:
                    raise LLMAPIError(f"API error: {e}", status_code)
            raise LLMAPIError(f"Unexpected error: {e}")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """调用 OpenAI API 生成 JSON 内容。"""
        # 添加 JSON 格式提示
        json_prompt = f"{prompt}\n\n请以 JSON 格式返回结果。"
        if system_prompt:
            json_system_prompt = f"{system_prompt}\n\n必须返回有效的 JSON 格式。"
        else:
            json_system_prompt = "你必须返回有效的 JSON 格式。"

        response = await self.generate(
            json_prompt, json_system_prompt, max_tokens, temperature
        )
        result: dict[str, Any] = json.loads(response.content)
        return result

    async def close(self):
        """关闭 HTTP 客户端。"""
        if self._client:
            await self._client.aclose()
            self._client = None


def get_llm_adapter() -> LLMAdapter:
    """获取 LLM 适配器实例。"""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.llm_api_key:
            logger.warning("LLM API key not configured, falling back to mock adapter")
            return MockLLMAdapter(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )

        return OpenAIAdapter(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
        )

    # 默认使用 Mock 适配器
    return MockLLMAdapter(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
    )
