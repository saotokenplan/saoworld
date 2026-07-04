def test_celery_app_initialization():
    from workers.celery_app import app

    assert app is not None
    assert app.conf.broker_url == "redis://localhost:6379/0"
    assert app.conf.result_backend == "redis://localhost:6379/1"
    assert app.conf.timezone == "UTC"
    assert app.conf.enable_utc is True


def test_celery_task_routes():
    from workers.celery_app import app

    routes = app.conf.task_routes
    assert "workers.tasks.content_generation.generate_content_batch" in routes
    assert routes["workers.tasks.content_generation.generate_content_batch"]["queue"] == "generation"
    assert "workers.tasks.content_review.run_world_consistency_review" in routes
    assert routes["workers.tasks.content_review.run_world_consistency_review"]["queue"] == "review"
    assert "workers.tasks.content_release.release_content_package" in routes
    assert routes["workers.tasks.content_release.release_content_package"]["queue"] == "release"


def test_celery_app_discovery():
    from workers.celery_app import app

    task_names = list(app.tasks.keys())
    assert "workers.tasks.content_generation.generate_content_batch" in task_names
    assert "workers.tasks.content_review.run_world_consistency_review" in task_names
    assert "workers.tasks.content_review.run_balance_review" in task_names
    assert "workers.tasks.content_packaging.package_content_batch" in task_names
    assert "workers.tasks.content_release.release_content_package" in task_names
    assert "workers.tasks.content_release.rollback_content_package" in task_names
    assert "workers.tasks.gate_scan.daily_gate_scan" in task_names