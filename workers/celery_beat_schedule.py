from celery.schedules import crontab

beat_schedule = {
    "daily-gate-scan": {
        "task": "workers.tasks.scheduled_tasks.daily_gate_scan",
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {},
    },
    "hourly-metrics-sync": {
        "task": "workers.tasks.scheduled_tasks.sync_metrics_gauge",
        "schedule": crontab(minute=0),
        "kwargs": {},
    },
    "daily-content-review": {
        "task": "workers.tasks.scheduled_tasks.daily_content_review",
        "schedule": crontab(hour=2, minute=0),
        "kwargs": {},
    },
    "daily-analytics-pipeline": {
        "task": "workers.tasks.scheduled_tasks.daily_analytics_pipeline",
        "schedule": crontab(hour=4, minute=0),
        "kwargs": {},
    },
}
