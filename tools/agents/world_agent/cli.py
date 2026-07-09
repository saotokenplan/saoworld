import click
import json
from .world_agent import WorldAgent
from .world_input_schemas import (
    WorldRules,
    RegionInfo,
    FactionInfo,
    VoteResult,
    ContentTemplate,
    SkeletonSnapshot,
    DesignNote,
    WorldTaskInput,
)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--chapter-id", required=True, help="章节ID")
@click.option("--region-id", required=True, help="区域ID")
@click.option("--region-name", required=True, help="区域名称")
@click.option("--faction-id", default="", help="阵营ID")
@click.option("--faction-name", default="", help="阵营名称")
@click.option("--skeleton-id", required=True, help="骨架快照ID")
def generate_npc(chapter_id, region_id, region_name, faction_id, faction_name, skeleton_id):
    agent = WorldAgent()

    regions = [RegionInfo(region_id=region_id, name=region_name)]
    factions = [FactionInfo(faction_id=faction_id, name=faction_name)] if faction_id else []

    world_rules = WorldRules(
        chapter_id=chapter_id,
        regions=regions,
        factions=factions,
        forbidden_tags=["adult", "violence"],
    )

    skeleton = SkeletonSnapshot(
        skeleton_id=skeleton_id,
        chapter_id=chapter_id,
        forbidden_tags=["adult", "violence"],
    )

    task_input = WorldTaskInput(world_rules=world_rules, skeleton_snapshot=skeleton)

    result = agent.execute_world_generation_flow(task_input, content_types=["npc"])

    if result.status == "completed" and result.npc_configs:
        npc = result.npc_configs[0]
        click.echo(f"NPC生成完成: {npc.npc_id} - {npc.name}")
    else:
        click.echo(f"NPC生成失败: {result.error_message}")


@cli.command()
@click.option("--chapter-id", required=True, help="章节ID")
@click.option("--region-id", required=True, help="区域ID")
@click.option("--region-name", required=True, help="区域名称")
@click.option("--skeleton-id", required=True, help="骨架快照ID")
def generate_quest(chapter_id, region_id, region_name, skeleton_id):
    agent = WorldAgent()

    regions = [RegionInfo(region_id=region_id, name=region_name)]
    world_rules = WorldRules(
        chapter_id=chapter_id,
        regions=regions,
        forbidden_tags=["adult", "violence"],
    )

    skeleton = SkeletonSnapshot(
        skeleton_id=skeleton_id,
        chapter_id=chapter_id,
        forbidden_tags=["adult", "violence"],
    )

    task_input = WorldTaskInput(world_rules=world_rules, skeleton_snapshot=skeleton)

    result = agent.execute_world_generation_flow(task_input, content_types=["npc", "quest"])

    if result.status == "completed" and result.quest_configs:
        quest = result.quest_configs[0]
        click.echo(f"任务生成完成: {quest.quest_id} - {quest.name}")
    else:
        click.echo(f"任务生成失败: {result.error_message}")


@cli.command()
@click.option("--chapter-id", required=True, help="章节ID")
@click.option("--vote-direction", default="", help="投票方向描述")
@click.option("--skeleton-id", required=True, help="骨架快照ID")
def generate_region(chapter_id, vote_direction, skeleton_id):
    agent = WorldAgent()

    world_rules = WorldRules(
        chapter_id=chapter_id,
        forbidden_tags=["adult", "violence"],
    )

    skeleton = SkeletonSnapshot(
        skeleton_id=skeleton_id,
        chapter_id=chapter_id,
        forbidden_tags=["adult", "violence"],
    )

    vote_result = None
    if vote_direction:
        vote_result = VoteResult(
            vote_cycle_id=f"vc_{chapter_id}",
            winning_candidate_id="candidate_001",
            winning_direction=vote_direction,
        )

    task_input = WorldTaskInput(
        world_rules=world_rules,
        vote_result=vote_result,
        skeleton_snapshot=skeleton,
    )

    result = agent.execute_world_generation_flow(task_input, content_types=["region"])

    if result.status == "completed" and result.region_configs:
        region = result.region_configs[0]
        click.echo(f"区域生成完成: {region.region_id} - {region.name}")
    else:
        click.echo(f"区域生成失败: {result.error_message}")


@cli.command()
@click.option("--input-file", required=True, help="输入配置文件路径")
def run_workflow(input_file):
    agent = WorldAgent()

    with open(input_file, "r") as f:
        input_data = json.load(f)

    world_rules = WorldRules(**input_data["world_rules"])
    vote_result = VoteResult(**input_data["vote_result"]) if "vote_result" in input_data else None
    template = ContentTemplate(**input_data["template"]) if "template" in input_data else None
    skeleton = SkeletonSnapshot(**input_data["skeleton_snapshot"]) if "skeleton_snapshot" in input_data else None
    design_note = DesignNote(**input_data["design_note"]) if "design_note" in input_data else None

    task_input = WorldTaskInput(
        world_rules=world_rules,
        vote_result=vote_result,
        template=template,
        skeleton_snapshot=skeleton,
        design_note=design_note,
    )

    result = agent.execute_world_generation_flow(task_input)

    output = {
        "result_id": result.result_id,
        "task_type": result.task_type,
        "status": result.status,
        "npc_count": len(result.npc_configs),
        "quest_count": len(result.quest_configs),
        "region_count": len(result.region_configs),
        "event_count": len(result.event_configs),
    }

    if result.content_package:
        output["content_package_id"] = result.content_package.content_package_id
    if result.review_request:
        output["review_request_id"] = result.review_request.request_id
    if result.error_message:
        output["error_message"] = result.error_message

    click.echo(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
