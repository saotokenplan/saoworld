from unittest.mock import MagicMock, patch


def test_release_content_package_task_exists():
    from workers.tasks.content_release import release_content_package

    assert release_content_package is not None
    assert hasattr(release_content_package, "delay")


def test_release_content_package_gray(mock_audit_log):
    from workers.tasks.content_release import release_content_package
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_test_01", "status": "gray"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_release.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_release.write_audit_log"):
            result = release_content_package.delay(
                content_package_id="pkg_test_01",
                release_mode="gray",
                gray_scope_jsonb={"region_ids": ["region_01"], "player_percent": 10},
                trace_id=trace_id,
            ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "release_mode": "gray",
        "status": "gray",
    }


def test_release_content_package_full(mock_audit_log):
    from workers.tasks.content_release import release_content_package
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_test_01", "status": "live"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_release.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_release.write_audit_log"):
            result = release_content_package.delay(
                content_package_id="pkg_test_01",
                release_mode="full",
                trace_id=trace_id,
            ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "release_mode": "full",
        "status": "live",
    }


def test_release_content_package_with_gray_scope_params(mock_audit_log):
    from workers.tasks.content_release import release_content_package
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_test_01", "status": "gray"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_release.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_release.write_audit_log"):
            result = release_content_package.delay(
                content_package_id="pkg_test_01",
                release_mode="gray",
                region_ids=["region_01", "region_02"],
                player_percent=15,
                player_ids=["player_001"],
                trace_id=trace_id,
            ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "release_mode": "gray",
        "status": "gray",
    }


def test_rollback_content_package_task_exists():
    from workers.tasks.content_release import rollback_content_package

    assert rollback_content_package is not None
    assert hasattr(rollback_content_package, "delay")


def test_rollback_content_package(mock_audit_log):
    from workers.tasks.content_release import rollback_content_package
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_test_01", "status": "rolled_back"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_release.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_release.write_audit_log"):
            result = rollback_content_package.delay(
                content_package_id="pkg_test_01",
                reason="内容质量问题",
                target_version="pkg_ch01_prev_01",
                trace_id=trace_id,
            ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "status": "rolled_back",
        "reason": "内容质量问题",
    }


def test_promote_to_full_release_task_exists():
    from workers.tasks.content_release import promote_to_full_release

    assert promote_to_full_release is not None
    assert hasattr(promote_to_full_release, "delay")


def test_promote_to_full_release_success(mock_audit_log):
    from workers.tasks.content_release import promote_to_full_release
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_test_01", "status": "live"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_release.ContentServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_release.write_audit_log"):
            result = promote_to_full_release.delay(
                content_package_id="pkg_test_01",
                trace_id=trace_id,
            ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "release_mode": "full",
        "status": "live",
    }