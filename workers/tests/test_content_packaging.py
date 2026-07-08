from unittest.mock import MagicMock, patch, mock_open


def test_package_content_batch_task_exists():
    from workers.tasks.content_packaging import package_content_batch

    assert package_content_batch is not None
    assert hasattr(package_content_batch, "delay")


def test_package_content_batch_success(mock_audit_log):
    from workers.tasks.content_packaging import package_content_batch
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    request_response = MagicMock()
    request_response.raise_for_status = MagicMock()
    request_response.json = MagicMock(return_value={
        "data": {"request_id": "gen_20260704_001"},
        "request_id": "req_test",
    })

    objects_response = MagicMock()
    objects_response.raise_for_status = MagicMock()
    objects_response.json = MagicMock(return_value={
        "data": [
            {"object_id": "obj_01", "status": "approved", "type": "npc"},
            {"object_id": "obj_02", "status": "approved", "type": "quest"},
            {"object_id": "obj_03", "status": "pending_review", "type": "event"},
        ],
        "request_id": "req_test",
    })

    package_response = MagicMock()
    package_response.raise_for_status = MagicMock()
    package_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_20260704_001"},
        "request_id": "req_test",
    })

    mock_generation_client = MagicMock()
    mock_generation_client.get_sync = MagicMock(side_effect=[request_response, objects_response])

    mock_content_client = MagicMock()
    mock_content_client.post_sync = MagicMock(return_value=package_response)

    with patch("workers.tasks.content_packaging.GenerationServiceClient", return_value=mock_generation_client):
        with patch("workers.tasks.content_packaging.ContentServiceClient", return_value=mock_content_client):
            with patch("workers.tasks.content_packaging.write_audit_log"):
                result = package_content_batch.delay(
                    request_ids=["gen_20260704_001"],
                    chapter_id="chapter_01",
                    region_id="region_wasteland_01",
                    trace_id=trace_id,
                ).get()

    assert result == {
        "content_package_id": "pkg_20260704_001",
        "object_count": 2,
        "status": "packaged",
    }


def test_validate_package_payload_valid():
    from workers.tasks.content_packaging import validate_package_payload

    payload = {
        "schema_version": 1,
        "package_type": "region",
        "region": {
            "region_id": "region_01",
            "name": "Test Region",
            "schema_version": 1,
        },
        "npcs": [
            {"npc_id": "npc_01", "name": "Test NPC"},
        ],
        "quests": [
            {"quest_id": "quest_01", "title": "Test Quest"},
        ],
    }

    errors = validate_package_payload(payload)
    assert len(errors) == 0


def test_validate_package_payload_missing_fields():
    from workers.tasks.content_packaging import validate_package_payload

    payload = {
        "region": {
            "name": "Test Region",
        },
        "npcs": [
            {"name": "Test NPC"},
        ],
        "quests": [
            {"title": "Test Quest"},
        ],
    }

    errors = validate_package_payload(payload)
    assert "missing schema_version" in errors
    assert "missing package_type" in errors
    assert "region missing region_id" in errors
    assert "region missing schema_version" in errors
    assert "npc missing npc_id" in errors
    assert "quest missing quest_id" in errors


def test_package_content_from_directory_task_exists():
    from workers.tasks.content_packaging import package_content_from_directory

    assert package_content_from_directory is not None
    assert hasattr(package_content_from_directory, "delay")


def test_package_content_from_directory_success(mock_audit_log):
    from workers.tasks.content_packaging import package_content_from_directory
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_dir_001"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    mock_region_json = '{"region_id": "region_01", "name": "Test Region", "schema_version": 1}'
    mock_faction_json = '{"factions": [], "relations": []}'
    mock_npc_json = '{"npcs": [{"npc_id": "npc_01", "name": "Test NPC"}]}'
    mock_quest_json = '{"quests": [{"quest_id": "quest_01", "title": "Test Quest"}]}'
    mock_chapter_json = '{"chapters": []}'

    with patch("workers.tasks.content_packaging.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_packaging.write_audit_log"):
            with patch("workers.tasks.content_packaging.Path") as MockPath:
                mock_path_instance = MagicMock()
                MockPath.return_value = mock_path_instance

                mock_regions_dir = MagicMock()
                mock_regions_dir.exists.return_value = True
                mock_regions_dir.glob.return_value = [MagicMock(name="region_list.json"), MagicMock(name="test_region.json")]

                mock_factions_dir = MagicMock()
                mock_factions_dir.exists.return_value = True
                mock_factions_dir.glob.return_value = [MagicMock(name="faction_list.json")]

                mock_npcs_dir = MagicMock()
                mock_npcs_dir.exists.return_value = True
                mock_npcs_dir.glob.return_value = [MagicMock(name="npc_list.json")]

                mock_quests_dir = MagicMock()
                mock_quests_dir.exists.return_value = True
                mock_quests_dir.glob.return_value = [MagicMock(name="quest_list.json")]

                mock_chapters_dir = MagicMock()
                mock_chapters_dir.exists.return_value = True
                mock_chapters_dir.glob.return_value = [MagicMock(name="chapter_list.json")]

                mock_path_instance.__truediv__ = MagicMock(side_effect=[
                    mock_regions_dir,
                    mock_factions_dir,
                    mock_npcs_dir,
                    mock_quests_dir,
                    mock_chapters_dir,
                ])

                def mock_open_side_effect(path, mode, encoding=None):
                    file_name = str(path)
                    if "test_region.json" in file_name:
                        return mock_open(read_data=mock_region_json).return_value
                    elif "faction_list.json" in file_name:
                        return mock_open(read_data=mock_faction_json).return_value
                    elif "npc_list.json" in file_name:
                        return mock_open(read_data=mock_npc_json).return_value
                    elif "quest_list.json" in file_name:
                        return mock_open(read_data=mock_quest_json).return_value
                    elif "chapter_list.json" in file_name:
                        return mock_open(read_data=mock_chapter_json).return_value
                    return mock_open(read_data="{}").return_value

                with patch("builtins.open", side_effect=mock_open_side_effect):
                    result = package_content_from_directory.delay(
                        data_dir="/test/data",
                        chapter_id="chapter_01",
                        package_version="pkg_ch01_test_20260704_01",
                        title="Test Package",
                        summary="Test Summary",
                        trace_id=trace_id,
                    ).get()

    assert result["content_package_id"] == "pkg_dir_001"
    assert result["package_version"] == "pkg_ch01_test_20260704_01"
    assert result["title"] == "Test Package"
    assert result["status"] == "packaged"