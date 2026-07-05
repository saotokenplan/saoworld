import pytest
from unittest.mock import AsyncMock, patch
from httpx import HTTPError

from app.core.health_check_client import check_service_health, check_all_services_health


@pytest.mark.asyncio
async def test_check_service_health_ok():
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"version": "0.1.0"}}

    with patch("app.core.health_check_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        status, version = await check_service_health("test-service", "http://localhost:8000")
        assert status == "ok"
        assert version == "0.1.0"


@pytest.mark.asyncio
async def test_check_service_health_unavailable():
    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("app.core.health_check_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        status, version = await check_service_health("test-service", "http://localhost:8000")
        assert status == "unavailable"
        assert version == "unknown"


@pytest.mark.asyncio
async def test_check_service_health_timeout():
    with patch("app.core.health_check_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = HTTPError("Timeout")
        mock_client_class.return_value = mock_client

        status, version = await check_service_health("test-service", "http://localhost:8000")
        assert status == "unavailable"
        assert version == "unknown"


@pytest.mark.asyncio
async def test_check_all_services_health():
    mock_response_ok = AsyncMock()
    mock_response_ok.status_code = 200
    mock_response_ok.json.return_value = {"data": {"version": "0.1.0"}}

    mock_response_unavailable = AsyncMock()
    mock_response_unavailable.status_code = 500

    def mock_get(url):
        if "ops-service" in url:
            return mock_response_ok
        return mock_response_unavailable

    with patch("app.core.health_check_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = mock_get
        mock_client_class.return_value = mock_client

        results = await check_all_services_health()
        assert "ops-service" in results
        assert "vote-service" in results