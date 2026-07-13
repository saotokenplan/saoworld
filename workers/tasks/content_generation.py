import json
import uuid
from typing import Any

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import GenerationServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


def _generate_npc_payload(
    template_type: str,
    region_id: str | None,
    chapter_id: str | None,
    index: int,
) -> dict[str, Any]:
    names = ["艾瑞尔·铁盾", "格尔·铁锤", "玛莎·耕地", "雷克斯·金币", "露娜·暗星", "杰克·流浪者"]
    roles = ["铁匠", "草药师", "商人", "守卫", "神秘学者", "探险者"]
    personalities = ["勇敢", "温和", "精明", "严肃", "神秘", "随性"]
    factions = ["faction_iron_guard", "faction_free_lands", "faction_shadow_veil", "faction_harvest_guild"]

    return {
        "name": f"{names[index % len(names)]}_{index}",
        "role": roles[index % len(roles)],
        "personality": personalities[index % len(personalities)],
        "faction_id": factions[index % len(factions)],
        "region_id": region_id or "region_core",
        "chapter_id": chapter_id or "chapter_01",
        "description": f"这是一位{roles[index % len(roles)]}，性格{personalities[index % len(personalities)]}。",
        "dialogue": "欢迎来到这片土地，旅行者。",
    }


def _generate_quest_payload(
    template_type: str,
    region_id: str | None,
    chapter_id: str | None,
    index: int,
) -> dict[str, Any]:
    titles = ["寻找失落的宝藏", "护送商队", "消灭怪物", "调查神秘事件", "收集材料"]
    objectives = [
        ["前往目标地点", "击败敌人", "收集物品"],
        ["保护商队", "到达目的地"],
        ["找到怪物巢穴", "消灭首领"],
        ["调查现场", "收集线索", "报告结果"],
        ["收集5个物品", "返回交差"],
    ]

    return {
        "title": f"{titles[index % len(titles)]}_{index}",
        "type": "side",
        "region_id": region_id or "region_core",
        "chapter_id": chapter_id or "chapter_01",
        "description": f"一个关于{titles[index % len(titles)]}的任务。",
        "objectives": objectives[index % len(objectives)],
        "rewards": {"experience": 100, "gold": 50},
    }


def _generate_region_payload(
    template_type: str,
    region_id: str | None,
    chapter_id: str | None,
    index: int,
) -> dict[str, Any]:
    names = ["迷雾森林", "火山口", "冰原", "沙漠绿洲", "沼泽地"]
    difficulties = ["easy", "normal", "hard", "extreme"]

    return {
        "name": f"{names[index % len(names)]}_{index}",
        "difficulty": difficulties[index % len(difficulties)],
        "region_id": region_id or f"region_new_{index}",
        "chapter_id": chapter_id or "chapter_01",
        "description": f"{names[index % len(names)]}是一片{difficulties[index % len(difficulties)]}难度的区域。",
        "features": ["神秘遗迹", "危险生物", "宝藏"],
    }


def _generate_settlement_payload(
    template_type: str,
    region_id: str | None,
    chapter_id: str | None,
    index: int,
) -> dict[str, Any]:
    names = ["晨光村", "铁砧镇", "月影城", "猎人营地", "石堡要塞", "黄金市场", "边境哨站"]
    settlement_types = ["village", "town", "city", "camp", "fortress", "market", "outpost"]
    economy_types = ["agriculture", "commerce", "mining", "hunting", "fishing", "trade"]
    resources = [
        ["谷物", "木材"], ["矿石", "皮革"], ["宝石", "稀有金属"],
        ["兽皮", "肉类"], ["鱼类", "盐"], ["香料", "丝绸"],
    ]
    statuses = ["peaceful", "thriving", "troubled", "warring"]

    return {
        "settlement_key": f"settlement_{settlement_types[index % len(settlement_types)]}_{index}",
        "name": f"{names[index % len(names)]}_{index}",
        "settlement_type": settlement_types[index % len(settlement_types)],
        "region_key": region_id or "region_core",
        "chapter_id": chapter_id or "chapter_01",
        "faction_key": "faction_iron_guard",
        "description": (
            f"{names[index % len(names)]}是一个"
            f"{settlement_types[index % len(settlement_types)]}，"
            f"以{economy_types[index % len(economy_types)]}为主。"
        ),
        "population": 100 + index * 50,
        "main_resources": resources[index % len(resources)],
        "economy_type": economy_types[index % len(economy_types)],
        "status": statuses[index % len(statuses)],
        "notable_locations": [
            {"location_key": f"loc_settlement_{index}_1", "name": "广场", "description": "聚落中心广场"},
            {"location_key": f"loc_settlement_{index}_2", "name": "旅馆", "description": "旅行者休息处"},
        ],
        "key_npcs": [f"npc_leader_{index}", f"npc_trader_{index}"],
        "faction_influence": {"faction_iron_guard": "主导"},
        "relationships": {},
        "history": f"{names[index % len(names)]}有着悠久的历史，建于数百年前。",
        "culture": "民风淳朴，重视传统。",
        "defenses": ["木墙", "守卫塔"],
        "services": ["旅馆", "商店", "铁匠"],
        "special_features": ["市集", "节日"],
        "location_x": 100 + index * 50,
        "location_y": 200 + index * 30,
        "schema_version": 1,
    }


def _generate_content_payload(
    template_type: str,
    region_id: str | None,
    chapter_id: str | None,
    index: int,
) -> dict[str, Any]:
    match template_type.lower():
        case "npc":
            return _generate_npc_payload(template_type, region_id, chapter_id, index)
        case "quest":
            return _generate_quest_payload(template_type, region_id, chapter_id, index)
        case "region":
            return _generate_region_payload(template_type, region_id, chapter_id, index)
        case "settlement":
            return _generate_settlement_payload(template_type, region_id, chapter_id, index)
        case _:
            return {
                "type": template_type,
                "name": f"generated_object_{index}",
                "region_id": region_id,
                "chapter_id": chapter_id,
            }


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_generation.generate_content_batch")
def generate_content_batch(
    self,
    vote_cycle_id: str | None = None,
    winning_candidate_id: str | None = None,
    template_type: str = "npc",
    count: int = 1,
    region_id: str | None = None,
    chapter_id: str | None = None,
    generated_params: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("generate_content_batch", trace_id)
    logger.info(
        "task_started",
        vote_cycle_id=vote_cycle_id,
        winning_candidate_id=winning_candidate_id,
        template_type=template_type,
        count=count,
        region_id=region_id,
        generated_params=generated_params,
    )

    try:
        client = GenerationServiceClient(settings.generation_service_url)

        resolved_template_type = template_type
        resolved_count = count
        resolved_region_id = region_id
        resolved_chapter_id = chapter_id
        resolved_template_id = f"tpl_{template_type}_v1"
        extra_input_params: dict[str, Any] = {}

        if generated_params:
            resolved_template_type = generated_params.get("template_type", template_type)
            resolved_count = generated_params.get("count", count)
            resolved_region_id = generated_params.get("region_id", region_id)
            resolved_chapter_id = generated_params.get("chapter_id", chapter_id)
            resolved_template_id = generated_params.get("template_id", f"tpl_{resolved_template_type}_v1")
            for key, value in generated_params.items():
                if key not in {"template_type", "count", "region_id", "chapter_id", "template_id"}:
                    extra_input_params[key] = value

        input_payload: dict[str, Any] = {
            "template_type": resolved_template_type,
            "count": resolved_count,
            "region_id": resolved_region_id,
            "chapter_id": resolved_chapter_id,
        }
        input_payload.update(extra_input_params)

        payload = {
            "vote_cycle_id": vote_cycle_id,
            "source_candidate_id": winning_candidate_id,
            "template_id": resolved_template_id,
            "input_payload": input_payload,
            "trace_id": trace_id,
        }

        response = client.post_sync("/api/v1/ops/generation/requests", json=payload)
        response.raise_for_status()
        result = response.json()

        request_id = result["data"]["request_id"]
        logger.info(
            "generation_request_created",
            request_id=request_id,
            vote_cycle_id=vote_cycle_id,
            template_id=resolved_template_id,
        )

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="generation.batch_started",
                resource_type="generation_request",
                resource_id=request_id,
                details_jsonb=json.dumps(payload),
            )

        asyncio.run(_write_audit())

        return {"request_id": request_id, "status": "started"}

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_generation.process_generation_request")
def process_generation_request(
    self,
    request_id: str,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("process_generation_request", trace_id)
    logger.info(
        "task_started",
        request_id=request_id,
    )

    try:
        client = GenerationServiceClient(settings.generation_service_url)

        response = client.get_sync(f"/api/v1/ops/generation/requests/{request_id}")
        response.raise_for_status()
        request_data = response.json()

        input_payload = request_data["data"]["input_payload"]
        template_type = input_payload.get("template_type", "npc")
        count = input_payload.get("count", 1)
        region_id = input_payload.get("region_id")
        chapter_id = input_payload.get("chapter_id")

        update_response = client.post_sync(
            f"/api/v1/ops/generation/requests/{request_id}/status",
            json={"status": "processing"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        update_response.raise_for_status()

        generated_objects = []
        for i in range(count):
            object_payload = _generate_content_payload(template_type, region_id, chapter_id, i)

            create_object_response = client.post_sync(
                f"/api/v1/ops/generation/requests/{request_id}/objects",
                json={
                    "object_type": template_type,
                    "schema_version": 1,
                    "object_payload": object_payload,
                },
                headers={"Idempotency-Key": str(uuid.uuid4())},
            )
            create_object_response.raise_for_status()
            obj_result = create_object_response.json()
            generated_objects.append(obj_result["data"])

        final_update_response = client.post_sync(
            f"/api/v1/ops/generation/requests/{request_id}/status",
            json={"status": "succeeded"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        final_update_response.raise_for_status()

        logger.info(
            "generation_completed",
            request_id=request_id,
            object_count=len(generated_objects),
        )

        return {"request_id": request_id, "status": "succeeded", "object_count": len(generated_objects)}

    except Exception as e:
        logger.error("task_failed", error=str(e))
        try:
            client = GenerationServiceClient(settings.generation_service_url)
            client.post_sync(
                f"/api/v1/ops/generation/requests/{request_id}/status",
                json={"status": "failed_permanent", "error_message": str(e)},
                headers={"Idempotency-Key": str(uuid.uuid4())},
            )
        except Exception:
            pass
        raise self.retry(exc=e)
