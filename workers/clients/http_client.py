import asyncio

import httpx

from workers.clients.auth_client import get_system_token


class ServiceClient:
    def __init__(self, base_url: str, required_scopes: list[str]) -> None:
        self.base_url = base_url
        self.required_scopes = required_scopes
        self._async_client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None

    @property
    def async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_auth_headers(),
                timeout=httpx.Timeout(30.0),
            )
        return self._async_client

    @property
    def sync_client(self) -> httpx.Client:
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                headers=self._get_auth_headers(),
                timeout=httpx.Timeout(30.0),
            )
        return self._sync_client

    def _get_auth_headers(self) -> dict[str, str]:
        token = get_system_token(self.required_scopes)
        return {"Authorization": f"Bearer {token}"}

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.async_client.get(path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.async_client.post(path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.async_client.put(path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        return await self.async_client.patch(path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.async_client.delete(path, **kwargs)

    def get_sync(self, path: str, **kwargs) -> httpx.Response:
        return self.sync_client.get(path, **kwargs)

    def post_sync(self, path: str, **kwargs) -> httpx.Response:
        return self.sync_client.post(path, **kwargs)

    def put_sync(self, path: str, **kwargs) -> httpx.Response:
        return self.sync_client.put(path, **kwargs)

    def patch_sync(self, path: str, **kwargs) -> httpx.Response:
        return self.sync_client.patch(path, **kwargs)

    def delete_sync(self, path: str, **kwargs) -> httpx.Response:
        return self.sync_client.delete(path, **kwargs)

    def run_async(self, coro):
        return asyncio.run(coro)

    async def close(self) -> None:
        if self._async_client:
            await self._async_client.aclose()
        if self._sync_client:
            self._sync_client.close()


class VoteServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["votes:read", "votes:history:read", "ops:vote-cycles:write"])


class WorldServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["world:read", "ops:*"])


class ContentServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["content:read", "content:release", "content:rollback", "ops:*"])


class GenerationServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["ops:*"])


class ReviewServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["review:approve", "ops:*"])


class PlayerServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["world:read", "quests:read", "ops:*"])


class OpsServiceClient(ServiceClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url, ["ops:*"])