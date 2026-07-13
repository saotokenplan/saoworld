import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.core.errors import GenerationErrorCodes
from app.core.skeleton_validator import SkeletonValidator


@pytest.mark.asyncio
async def test_validate_forbidden_tags_empty():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": [],
    }

    with pytest.raises(Exception) as exc_info:
        await validator.validate_forbidden_tags_not_empty(skeleton, "test-req-001")

    assert GenerationErrorCodes.FORBIDDEN_TAGS_EMPTY in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_forbidden_tags_valid():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": ["tag1", "tag2"],
    }

    await validator.validate_forbidden_tags_not_empty(skeleton, "test-req-002")


@pytest.mark.asyncio
async def test_validate_chapter_exists_valid():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": ["tag1"],
    }

    await validator.validate_chapter_exists(skeleton, "chapter_01", "test-req-003")


@pytest.mark.asyncio
async def test_validate_chapter_exists_invalid():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": ["tag1"],
    }

    with pytest.raises(Exception) as exc_info:
        await validator.validate_chapter_exists(skeleton, "chapter_02", "test-req-004")

    assert GenerationErrorCodes.INVALID_CHAPTER_ID in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_region_exists_valid():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_core_ironward": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": ["tag1"],
    }

    await validator.validate_region_exists(skeleton, "region_core_ironward", "test-req-005")


@pytest.mark.asyncio
async def test_validate_region_exists_invalid():
    validator = SkeletonValidator()

    skeleton = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_core_ironward": {"chapter_id": "chapter_01"}},
        "factions": {},
        "forbidden_tags": ["tag1"],
    }

    with pytest.raises(Exception) as exc_info:
        await validator.validate_region_exists(skeleton, "region_invalid", "test-req-006")

    assert GenerationErrorCodes.INVALID_REGION_ID in str(exc_info.value)
