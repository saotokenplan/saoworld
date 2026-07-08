from celery import Celery

from workers.config import settings
from workers.celery_beat_schedule import beat_schedule
from workers.utils.logging import configure_logging

configure_logging()

app = Celery(
    "game-workers",
    broker=settings.broker_url,
    backend=settings.result_backend,
)

app.conf.update(
    task_serializer=settings.task_serializer,
    accept_content=settings.accept_content,
    result_serializer=settings.result_serializer,
    timezone=settings.timezone,
    enable_utc=True,
    worker_prefetch_multiplier=settings.worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.worker_max_tasks_per_child,
    result_expires=settings.result_expires,
    beat_schedule=beat_schedule,
    task_routes={
        "workers.tasks.content_generation.generate_content_batch": {"queue": "generation"},
        "workers.tasks.content_review.run_world_consistency_review": {"queue": "review"},
        "workers.tasks.content_review.run_balance_review": {"queue": "review"},
        "workers.tasks.content_packaging.package_content_batch": {"queue": "packaging"},
        "workers.tasks.content_release.release_content_package": {"queue": "release"},
        "workers.tasks.content_release.rollback_content_package": {"queue": "release"},
        "workers.tasks.gate_scan.daily_gate_scan": {"queue": "gate"},
        "workers.tasks.scheduled_tasks.daily_gate_scan": {"queue": "scheduled"},
        "workers.tasks.scheduled_tasks.sync_metrics_gauge": {"queue": "scheduled"},
        "workers.tasks.scheduled_tasks.daily_content_review": {"queue": "scheduled"},
    },
)

import workers.tasks.content_generation  # noqa: E402, F401
import workers.tasks.content_review  # noqa: E402, F401
import workers.tasks.content_packaging  # noqa: E402, F401
import workers.tasks.content_release  # noqa: E402, F401
import workers.tasks.gate_scan  # noqa: E402, F401
import workers.tasks.scheduled_tasks  # noqa: E402, F401

app.autodiscover_tasks([
    "workers.tasks.content_generation",
    "workers.tasks.content_review",
    "workers.tasks.content_packaging",
    "workers.tasks.content_release",
    "workers.tasks.gate_scan",
    "workers.tasks.scheduled_tasks",
])