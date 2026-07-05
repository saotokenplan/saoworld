from typing import Any, TypedDict

import httpx

from app.core.config import settings
from app.core.errors import GenerationErrorCodes, raise_generation_error


class WorldSkeleton(TypedDict):
    skeleton_id: str
    world_version: str
    chapter_id: str
    regions: dict[str, Any]
    factions: dict[str, Any]
    reserved_characters: dict[str, Any] | None
    forbidden_tags: list[str]
    reward_limits: dict[str, Any] | None
    is_active: bool


class SkeletonValidator:
    def __init__(self, world_service_url: str | None = None):
        self.world_service_url = world_service_url or "http://localhost:8001"

    async def fetch_current_skeleton(self) -> WorldSkeleton | None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.world_service_url}/api/v1/world/skeleton",
                    headers={"X-Trace-Id": "internal-skeleton-fetch"},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data")
                return None
            except Exception:
                return None

    async def validate_skeleton_exists(self, request_id: str) -> WorldSkeleton:
        skeleton = await self.fetch_current_skeleton()
        if skeleton is None:
            raise_generation_error(
                GenerationErrorCodes.SKELETON_NOT_FOUND,
                "当前没有活跃的世界骨架快照，请先创建骨架快照",
                request_id=request_id,
                status_code=404,
                details=[
                    {
                        "location": "system",
                        "field": "world_skeleton",
                        "issue": "not_found",
                        "rejected_value": None,
                    }
                ],
            )
        return skeleton

    async def validate_forbidden_tags_not_empty(
        self, skeleton: WorldSkeleton, request_id: str
    ) -> None:
        forbidden_tags = skeleton.get("forbidden_tags", [])
        if not forbidden_tags or len(forbidden_tags) == 0:
            raise_generation_error(
                GenerationErrorCodes.FORBIDDEN_TAGS_EMPTY,
                "世界骨架快照的 forbidden_tags 不能为空",
                request_id=request_id,
                status_code=400,
                details=[
                    {
                        "location": "system",
                        "field": "forbidden_tags",
                        "issue": "empty",
                        "rejected_value": forbidden_tags,
                    }
                ],
            )

    async def validate_chapter_exists(
        self, skeleton: WorldSkeleton, chapter_id: str, request_id: str
    ) -> None:
        regions = skeleton.get("regions", {})
        for region_data in regions.values():
            if isinstance(region_data, dict) and region_data.get("chapter_id") == chapter_id:
                return
        raise_generation_error(
            GenerationErrorCodes.INVALID_CHAPTER_ID,
            f"章节 {chapter_id} 不存在于当前世界骨架快照中",
            request_id=request_id,
            status_code=400,
            details=[
                {
                    "location": "body",
                    "field": "chapter_id",
                    "issue": "invalid",
                    "rejected_value": chapter_id,
                }
            ],
        )

    async def validate_region_exists(
        self, skeleton: WorldSkeleton, region_id: str, request_id: str
    ) -> None:
        regions = skeleton.get("regions", {})
        if region_id not in regions:
            raise_generation_error(
                GenerationErrorCodes.INVALID_REGION_ID,
                f"区域 {region_id} 不存在于当前世界骨架快照中",
                request_id=request_id,
                status_code=400,
                details=[
                    {
                        "location": "body",
                        "field": "region_id",
                        "issue": "invalid",
                        "rejected_value": region_id,
                    }
                ],
            )

    async def validate_generation_request(
        self, input_payload: dict[str, Any], request_id: str
    ) -> WorldSkeleton:
        skeleton = await self.validate_skeleton_exists(request_id)
        await self.validate_forbidden_tags_not_empty(skeleton, request_id)

        chapter_id = input_payload.get("chapter_id")
        if chapter_id:
            await self.validate_chapter_exists(skeleton, chapter_id, request_id)

        region_id = input_payload.get("region_id")
        if region_id:
            await self.validate_region_exists(skeleton, region_id, request_id)

        return skeleton


skeleton_validator = SkeletonValidator()