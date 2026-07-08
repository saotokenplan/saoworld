import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from world_agent import WorldAgent
from input_schemas import (
    WorldRules,
    RegionInfo,
    FactionInfo,
    VoteResult,
    ContentTemplate,
    TemplateField,
    SkeletonSnapshot,
    DesignNote,
    WorldTaskInput,
)
from error_handler import (
    MissingSkeletonError,
    TemplateMismatchError,
    ContentViolationError,
)


def _make_valid_task_input(**overrides) -> WorldTaskInput:
    world_rules = WorldRules(
        chapter_id="chapter_01",
        regions=[RegionInfo(region_id="region_core", name="铁卫城周边")],
        factions=[FactionInfo(faction_id="faction_iron", name="铁卫联盟")],
        forbidden_tags=["adult", "violence"],
    )

    skeleton = SkeletonSnapshot(
        skeleton_id="skel_001",
        chapter_id="chapter_01",
        forbidden_tags=["adult", "violence"],
    )

    defaults = {
        "world_rules": world_rules,
        "skeleton_snapshot": skeleton,
    }
    defaults.update(overrides)
    return WorldTaskInput(**defaults)


def test_read_input_data():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    result = agent.read_input_data(task_input)

    assert result["chapter_id"] == "chapter_01"
    assert result["regions_count"] == 1
    assert result["factions_count"] == 1
    assert result["forbidden_tags_count"] == 2
    assert result["has_skeleton_snapshot"] is True


def test_read_input_data_with_vote_result():
    vote_result = VoteResult(
        vote_cycle_id="vc_001",
        winning_candidate_id="candidate_003",
        winning_direction="新增迷雾森林区域",
        voter_count=500,
        winning_percentage=40.0,
    )
    task_input = _make_valid_task_input(vote_result=vote_result)
    agent = WorldAgent()
    result = agent.read_input_data(task_input)

    assert result["has_vote_result"] is True
    assert result["winning_direction"] == "新增迷雾森林区域"
    assert result["voter_count"] == 500


def test_validate_input_success():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    result = agent.validate_input(task_input)

    assert result["is_valid"] is True
    assert len(result["errors"]) == 0


def test_validate_input_missing_skeleton():
    task_input = _make_valid_task_input(skeleton_snapshot=None)
    agent = WorldAgent()

    with pytest.raises(MissingSkeletonError):
        agent.validate_input(task_input)


def test_validate_input_empty_forbidden_tags():
    skeleton = SkeletonSnapshot(
        skeleton_id="skel_001",
        chapter_id="chapter_01",
        forbidden_tags=[],
    )
    task_input = _make_valid_task_input(skeleton_snapshot=skeleton)
    agent = WorldAgent()

    with pytest.raises(MissingSkeletonError):
        agent.validate_input(task_input)


def test_match_template_with_template():
    template = ContentTemplate(
        template_id="tpl_npc_v2",
        type="npc",
        schema_version=2,
        fields=[
            TemplateField(name="personality", type="string", options=["friendly", "neutral"]),
        ],
    )
    task_input = _make_valid_task_input(template=template)
    agent = WorldAgent()
    result = agent.match_template(task_input)

    assert result["template_id"] == "tpl_npc_v2"
    assert result["type"] == "npc"


def test_match_template_mismatch():
    template = ContentTemplate(
        template_id="tpl_region_v2",
        type="region",
        schema_version=1,
        fields=[],
    )
    design_note = DesignNote(
        note_id="note_001",
        chapter_id="chapter_01",
        content_type="npc",
    )
    task_input = _make_valid_task_input(template=template, design_note=design_note)
    agent = WorldAgent()

    with pytest.raises(TemplateMismatchError):
        agent.match_template(task_input)


def test_match_template_default():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    result = agent.match_template(task_input)

    assert result["template_id"] == "tpl_npc_default"
    assert result["type"] == "npc"


def test_generate_npc():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)

    npcs = agent.generate_content(task_input, "npc")

    assert len(npcs) == 1
    assert npcs[0].npc_id.startswith("npc_")
    assert npcs[0].faction_id == "faction_iron"
    assert npcs[0].region_id == "region_core"
    assert "greeting" in npcs[0].dialogs


def test_generate_quest():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)

    agent.generate_content(task_input, "npc")
    quests = agent.generate_content(task_input, "quest")

    assert len(quests) == 1
    assert quests[0].quest_id.startswith("quest_")
    assert quests[0].type == "side"
    assert len(quests[0].objectives) >= 1


def test_generate_region():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)

    regions = agent.generate_content(task_input, "region")

    assert len(regions) == 1
    assert regions[0].region_id.startswith("region_")
    assert regions[0].status == "locked"
    assert regions[0].region_scope is not None
    assert regions[0].region_scope.biome == "forest"


def test_generate_event():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)

    events = agent.generate_content(task_input, "event")

    assert len(events) == 1
    assert events[0].event_id.startswith("event_")
    assert events[0].type == "discovery"


def test_apply_rules_success():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)
    agent.generate_content(task_input, "npc")
    agent.generate_content(task_input, "quest")

    result = agent.apply_rules(task_input)

    assert result["world_consistency"] == "passed"
    assert result["reward_boundary"] == "passed"
    assert result["content_safety"] == "passed"
    assert result["duplication"] == "passed"


def test_apply_rules_content_violation():
    world_rules = WorldRules(
        chapter_id="chapter_01",
        regions=[RegionInfo(region_id="region_core", name="铁卫城周边")],
        factions=[FactionInfo(faction_id="faction_iron", name="铁卫联盟")],
        forbidden_tags=["violence"],
    )
    skeleton = SkeletonSnapshot(
        skeleton_id="skel_001",
        chapter_id="chapter_01",
        forbidden_tags=["violence"],
    )
    task_input = WorldTaskInput(world_rules=world_rules, skeleton_snapshot=skeleton)

    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)
    agent.generate_content(task_input, "npc")

    agent.generated_npcs[0].name = "暴力战士violence"

    with pytest.raises(ContentViolationError):
        agent.apply_rules(task_input)


def test_refine_text():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)
    agent.generate_content(task_input, "npc")
    agent.generate_content(task_input, "quest")
    agent.generate_content(task_input, "region")
    agent.generate_content(task_input, "event")

    result = agent.refine_text(task_input)

    assert result["refined"] is True
    assert result["npc_count"] == 1
    assert result["quest_count"] == 1
    assert result["region_count"] == 1
    assert result["event_count"] == 1

    assert agent.generated_npcs[0].name == "神秘的旅者"
    assert agent.generated_quests[0].name == "未知的探索"
    assert agent.generated_regions[0].name == "神秘领域"
    assert agent.generated_events[0].name == "异常波动"


def test_package_content():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)
    agent.generate_content(task_input, "npc")
    agent.generate_content(task_input, "quest")

    content_package = agent.package_content(task_input)

    assert content_package.content_package_id.startswith("pkg_")
    assert content_package.chapter_id == "chapter_01"
    assert "npcs" in content_package.content
    assert "quests" in content_package.content


def test_submit_for_review():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    agent.validate_input(task_input)
    agent.match_template(task_input)
    agent.generate_content(task_input, "npc")
    agent.package_content(task_input)

    review_request = agent.submit_for_review(task_input)

    assert review_request.request_id.startswith("gen_")
    assert review_request.type == "content_review"
    assert len(review_request.checks) == 4


def test_handle_review_result_approved():
    agent = WorldAgent()
    result = agent.handle_review_result("approved")

    assert result["action"] == "notify_build_agent"
    assert result["status"] == "approved"


def test_handle_review_result_rejected():
    from error_handler import ReviewFailedError

    agent = WorldAgent()
    with pytest.raises(ReviewFailedError):
        agent.handle_review_result("rejected")


def test_handle_review_result_needs_revision():
    agent = WorldAgent()
    result = agent.handle_review_result("needs_revision")

    assert result["action"] == "revise_content"
    assert result["status"] == "needs_revision"


def test_execute_world_generation_flow_full():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    result = agent.execute_world_generation_flow(task_input)

    assert result.status == "completed"
    assert result.task_type == "full"
    assert len(result.npc_configs) == 1
    assert len(result.quest_configs) == 1
    assert len(result.region_configs) == 1
    assert len(result.event_configs) == 1
    assert result.content_package is not None
    assert result.review_request is not None


def test_execute_world_generation_flow_single_type():
    task_input = _make_valid_task_input()
    agent = WorldAgent()
    result = agent.execute_world_generation_flow(task_input, content_types=["npc"])

    assert result.status == "completed"
    assert result.task_type == "npc"
    assert len(result.npc_configs) == 1
    assert len(result.quest_configs) == 0
    assert len(result.region_configs) == 0
    assert len(result.event_configs) == 0


def test_execute_world_generation_flow_failure():
    task_input = _make_valid_task_input(skeleton_snapshot=None)
    agent = WorldAgent()
    result = agent.execute_world_generation_flow(task_input)

    assert result.status == "failed"
    assert "缺少骨架快照" in result.error_message


def test_execute_world_generation_flow_with_vote_result():
    vote_result = VoteResult(
        vote_cycle_id="vc_001",
        winning_candidate_id="candidate_003",
        winning_direction="新增迷雾森林区域",
        voter_count=500,
        winning_percentage=40.0,
    )
    task_input = _make_valid_task_input(vote_result=vote_result)
    agent = WorldAgent()
    result = agent.execute_world_generation_flow(task_input)

    assert result.status == "completed"
    assert len(result.region_configs) == 1


def test_default_template_types():
    agent = WorldAgent()

    for content_type in ["npc", "quest", "region", "event"]:
        template = agent._get_default_template(content_type)
        assert template["type"] == content_type
        assert template["template_id"].startswith("tpl_")
