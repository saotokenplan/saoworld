import json
import uuid
from pathlib import Path
from typing import Any

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ContentServiceClient, GenerationServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


def validate_package_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if "schema_version" not in payload:
        errors.append("missing schema_version")
    elif not isinstance(payload["schema_version"], int):
        errors.append("schema_version must be integer")

    if "package_type" not in payload:
        errors.append("missing package_type")

    if "region" in payload:
        region = payload["region"]
        if "region_id" not in region:
            errors.append("region missing region_id")
        if "name" not in region:
            errors.append("region missing name")
        if "schema_version" not in region:
            errors.append("region missing schema_version")

    if "npcs" in payload:
        npcs = payload["npcs"]
        for npc in npcs:
            if "npc_id" not in npc:
                errors.append("npc missing npc_id")
            if "name" not in npc:
                errors.append(f"npc {npc.get('npc_id', 'unknown')} missing name")

    if "quests" in payload:
        quests = payload["quests"]
        for quest in quests:
            if "quest_id" not in quest:
                errors.append("quest missing quest_id")
            if "title" not in quest:
                errors.append(f"quest {quest.get('quest_id', 'unknown')} missing title")

    return errors


def load_content_from_directory(data_dir: str) -> dict[str, Any]:
    data_path = Path(data_dir)

    payload: dict[str, Any] = {
        "schema_version": 1,
        "package_type": "region",
    }

    regions_dir = data_path / "regions"
    if regions_dir.exists():
        region_files = list(regions_dir.glob("*.json"))
        for region_file in region_files:
            if region_file.name != "region_list.json":
                with open(region_file, "r", encoding="utf-8") as f:
                    payload["region"] = json.load(f)

    factions_dir = data_path / "factions"
    if factions_dir.exists():
        faction_files = list(factions_dir.glob("*.json"))
        for faction_file in faction_files:
            with open(faction_file, "r", encoding="utf-8") as f:
                faction_data = json.load(f)
                payload["factions"] = faction_data.get("factions", [])
                payload["relations"] = faction_data.get("relations", [])

    npcs_dir = data_path / "npcs"
    if npcs_dir.exists():
        npc_files = list(npcs_dir.glob("*.json"))
        for npc_file in npc_files:
            with open(npc_file, "r", encoding="utf-8") as f:
                npc_data = json.load(f)
                payload["npcs"] = npc_data.get("npcs", [])

    quests_dir = data_path / "quests"
    if quests_dir.exists():
        quest_files = list(quests_dir.glob("*.json"))
        for quest_file in quest_files:
            with open(quest_file, "r", encoding="utf-8") as f:
                quest_data = json.load(f)
                payload["quests"] = quest_data.get("quests", [])

    chapters_dir = data_path / "chapters"
    if chapters_dir.exists():
        chapter_files = list(chapters_dir.glob("*.json"))
        for chapter_file in chapter_files:
            with open(chapter_file, "r", encoding="utf-8") as f:
                chapter_data = json.load(f)
                payload["chapters"] = chapter_data.get("chapters", [])

    return payload


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_packaging.package_content_batch")
def package_content_batch(
    self,
    request_ids: list[str],
    chapter_id: str | None = None,
    region_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("package_content_batch", trace_id)
    logger.info("task_started", request_ids=request_ids)

    try:
        generation_client = GenerationServiceClient(settings.generation_service_url)
        content_client = ContentServiceClient(settings.content_service_url)

        all_objects = []
        for req_id in request_ids:
            response = generation_client.get_sync(f"/api/v1/generation/requests/{req_id}")
            response.raise_for_status()

            response = generation_client.get_sync(f"/api/v1/generation/requests/{req_id}/objects")
            response.raise_for_status()
            objects = response.json()["data"]

            all_objects.extend([obj for obj in objects if obj.get("status") == "approved"])

        package_payload = {
            "chapter_id": chapter_id,
            "region_id": region_id,
            "schema_version": 1,
            "package_type": "generated",
            "content_jsonb": {
                "objects": all_objects,
                "request_ids": request_ids,
            },
        }

        validation_errors = validate_package_payload(package_payload)
        if validation_errors:
            logger.error("package_validation_failed", errors=validation_errors)
            raise ValueError(f"Package validation failed: {', '.join(validation_errors)}")

        response = content_client.post_sync("/api/v1/content/packages", json=package_payload)
        response.raise_for_status()
        result = response.json()

        content_package_id = result["data"]["content_package_id"]
        logger.info("content_package_created", content_package_id=content_package_id)

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="content.package_created",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(package_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "object_count": len(all_objects),
            "status": "packaged",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(
    bind=True, max_retries=3, retry_backoff=2,
    name="workers.tasks.content_packaging.package_content_from_directory",
)
def package_content_from_directory(
    self,
    data_dir: str,
    chapter_id: str,
    package_version: str,
    title: str,
    summary: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("package_content_from_directory", trace_id)
    logger.info("task_started", data_dir=data_dir, chapter_id=chapter_id)

    try:
        content_client = ContentServiceClient(settings.content_service_url)

        package_payload = load_content_from_directory(data_dir)
        package_payload["release_notes"] = f"Content package generated from directory: {data_dir}"

        validation_errors = validate_package_payload(package_payload)
        if validation_errors:
            logger.error("package_validation_failed", errors=validation_errors)
            raise ValueError(f"Package validation failed: {', '.join(validation_errors)}")

        create_payload = {
            "chapter_id": chapter_id,
            "package_version": package_version,
            "title": title,
            "summary": summary,
            "payload": package_payload,
            "schema_version": package_payload.get("schema_version", 1),
        }

        response = content_client.post_sync("/api/v1/content/packages", json=create_payload)
        response.raise_for_status()
        result = response.json()

        content_package_id = result["data"]["content_package_id"]
        logger.info("content_package_created_from_directory", content_package_id=content_package_id)

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="content.package_created_from_directory",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(create_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "package_version": package_version,
            "title": title,
            "status": "packaged",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)
