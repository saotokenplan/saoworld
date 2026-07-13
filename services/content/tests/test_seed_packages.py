import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_load_json_file():
    test_data = {"test_key": "test_value"}
    test_path = Path("/tmp/test_seed.json")
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f)

    from scripts.seed_initial_packages import load_json_file
    result = load_json_file(test_path)
    assert result == test_data
    test_path.unlink()


@pytest.mark.asyncio
async def test_create_ironward_package():
    from scripts.seed_initial_packages import create_ironward_package
    from app.repositories.content_repo import ContentRepository

    mock_repo = AsyncMock(spec=ContentRepository)
    mock_repo.create_package.return_value = AsyncMock(content_package_id="test_package_id")

    with patch.object(ContentRepository, "__new__", return_value=mock_repo):
        async with TestSessionLocal() as session:
            await create_ironward_package(session)

    mock_repo.create_package.assert_called_once()
    call_args = mock_repo.create_package.call_args
    assert call_args.kwargs["chapter_id"] == "chapter_01"
    assert call_args.kwargs["package_version"] == "pkg_ch01_ironward_20260704_01"
    assert call_args.kwargs["title"] == "铁卫城周边区域包"
    assert "schema_version" in call_args.kwargs


@pytest.mark.asyncio
async def test_create_grayvalley_package():
    from scripts.seed_initial_packages import create_grayvalley_package
    from app.repositories.content_repo import ContentRepository

    mock_repo = AsyncMock(spec=ContentRepository)
    mock_repo.create_package.return_value = AsyncMock(content_package_id="test_package_id")

    with patch.object(ContentRepository, "__new__", return_value=mock_repo):
        async with TestSessionLocal() as session:
            await create_grayvalley_package(session)

    mock_repo.create_package.assert_called_once()
    call_args = mock_repo.create_package.call_args
    assert call_args.kwargs["chapter_id"] == "chapter_02"
    assert call_args.kwargs["package_version"] == "pkg_ch02_grayvalley_20260704_01"
    assert call_args.kwargs["title"] == "灰谷废墟区域包"
    assert "schema_version" in call_args.kwargs


@pytest.mark.asyncio
async def test_package_payload_contains_required_fields():
    from scripts.seed_initial_packages import create_ironward_package
    from app.repositories.content_repo import ContentRepository

    mock_repo = AsyncMock(spec=ContentRepository)
    mock_repo.create_package.return_value = AsyncMock(content_package_id="test_package_id")

    with patch.object(ContentRepository, "__new__", return_value=mock_repo):
        async with TestSessionLocal() as session:
            await create_ironward_package(session)

    call_args = mock_repo.create_package.call_args
    payload = call_args.kwargs["payload"]

    assert "schema_version" in payload
    assert "region" in payload
    assert "factions" in payload
    assert "relations" in payload
    assert "npcs" in payload
    assert "quests" in payload
    assert "chapters" in payload
    assert "package_type" in payload
    assert payload["package_type"] == "region"
