from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from workers.config import settings

logger = structlog.get_logger()


async def clean_player_events(start_date: datetime, end_date: datetime) -> dict[str, Any]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import select, func, and_
        from app.domain.models import PlayerEvent

        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            count_stmt = select(func.count(PlayerEvent.event_id)).where(
                and_(
                    PlayerEvent.occurred_at >= start_date,
                    PlayerEvent.occurred_at <= end_date,
                )
            )
            result = await conn.execute(count_stmt)
            total_events = result.scalar_one()

        logger.info(
            "player_events_cleaned",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_events=total_events,
        )

        return {
            "status": "success",
            "total_events": total_events,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    except Exception as exc:
        logger.error(
            "player_events_clean_failed",
            error=str(exc),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        raise


async def aggregate_player_metrics(stat_date: datetime) -> dict[str, Any]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select, func, distinct, and_
        from app.domain.models import PlayerEvent
        from app.repositories.analytics_repo import AnalyticsRepository

        engine = create_async_engine(settings.database_url)
        async with AsyncSession(engine) as session:
            repo = AnalyticsRepository(session)

            start_of_day = stat_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            player_events_stmt = select(
                PlayerEvent.player_id,
                func.count(PlayerEvent.event_id).label("events_count"),
                func.count(distinct(PlayerEvent.region_id)).label("regions_visited"),
            ).where(
                and_(
                    PlayerEvent.occurred_at >= start_of_day,
                    PlayerEvent.occurred_at < end_of_day,
                )
            ).group_by(PlayerEvent.player_id)

            result = await session.execute(player_events_stmt)
            player_stats = result.all()

            total_players = 0
            for player_id, events_count, regions_visited in player_stats:
                quests_completed = 0
                votes_submitted = 0
                npcs_interacted = 0

                detail_stmt = select(PlayerEvent.event_type).where(
                    and_(
                        PlayerEvent.player_id == player_id,
                        PlayerEvent.occurred_at >= start_of_day,
                        PlayerEvent.occurred_at < end_of_day,
                    )
                )
                detail_result = await session.execute(detail_stmt)
                event_types = [row[0] for row in detail_result.all()]

                quests_completed = sum(1 for et in event_types if "quest" in et and "complete" in et)
                votes_submitted = sum(1 for et in event_types if "vote" in et)
                npcs_interacted = sum(1 for et in event_types if "npc" in et)

                await repo.upsert_player_metrics(
                    player_id=player_id,
                    stat_date=start_of_day,
                    total_session_seconds=0,
                    regions_visited=regions_visited,
                    quests_completed=quests_completed,
                    votes_submitted=votes_submitted,
                    npcs_interacted=npcs_interacted,
                    events_count=events_count,
                    detail_jsonb=None,
                )
                total_players += 1

            await session.commit()

        logger.info(
            "player_metrics_aggregated",
            stat_date=stat_date.isoformat(),
            total_players=total_players,
        )

        return {
            "status": "success",
            "stat_date": stat_date.isoformat(),
            "total_players": total_players,
        }
    except Exception as exc:
        logger.error(
            "player_metrics_aggregation_failed",
            error=str(exc),
            stat_date=stat_date.isoformat(),
        )
        raise


async def aggregate_region_metrics(stat_date: datetime) -> dict[str, Any]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select, func, distinct, and_
        from app.domain.models import PlayerEvent
        from app.repositories.analytics_repo import AnalyticsRepository

        engine = create_async_engine(settings.database_url)
        async with AsyncSession(engine) as session:
            repo = AnalyticsRepository(session)

            start_of_day = stat_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            region_events_stmt = select(
                PlayerEvent.region_id,
                func.count(distinct(PlayerEvent.player_id)).label("unique_players"),
                func.count(PlayerEvent.event_id).label("total_visits"),
            ).where(
                and_(
                    PlayerEvent.occurred_at >= start_of_day,
                    PlayerEvent.occurred_at < end_of_day,
                    PlayerEvent.region_id.isnot(None),
                )
            ).group_by(PlayerEvent.region_id)

            result = await session.execute(region_events_stmt)
            region_stats = result.all()

            total_regions = 0
            for region_id, unique_players, total_visits in region_stats:
                await repo.upsert_region_metrics(
                    region_id=region_id,
                    stat_date=start_of_day,
                    unique_players=unique_players,
                    total_visits=total_visits,
                    total_duration_seconds=0,
                    quests_started=0,
                    quests_completed=0,
                    events_count=total_visits,
                    detail_jsonb=None,
                )
                total_regions += 1

            await session.commit()

        logger.info(
            "region_metrics_aggregated",
            stat_date=stat_date.isoformat(),
            total_regions=total_regions,
        )

        return {
            "status": "success",
            "stat_date": stat_date.isoformat(),
            "total_regions": total_regions,
        }
    except Exception as exc:
        logger.error(
            "region_metrics_aggregation_failed",
            error=str(exc),
            stat_date=stat_date.isoformat(),
        )
        raise


async def generate_daily_report(report_date: datetime) -> dict[str, Any]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from app.repositories.analytics_repo import AnalyticsRepository

        engine = create_async_engine(settings.database_url)
        async with AsyncSession(engine) as session:
            repo = AnalyticsRepository(session)

            start_of_day = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            player_metrics, player_total = await repo.get_player_metrics(
                player_id="",
                start_date=start_of_day,
                end_date=end_of_day,
                limit=1,
            )

            region_metrics, region_total = await repo.get_region_metrics(
                start_date=start_of_day,
                end_date=end_of_day,
                limit=100,
            )

            total_unique_players = sum(r.unique_players for r in region_metrics)
            total_region_visits = sum(r.total_visits for r in region_metrics)

            summary = {
                "total_unique_players": total_unique_players,
                "total_region_visits": total_region_visits,
                "regions_covered": region_total,
            }

            report = await repo.create_report(
                report_type="daily_summary",
                period_start=start_of_day,
                period_end=end_of_day,
                status="completed",
                summary_jsonb=summary,
                detail_jsonb={
                    "region_metrics_count": region_total,
                    "player_metrics_count": player_total,
                },
                generated_by="system",
                trace_id=None,
                schema_version=1,
            )

            await session.commit()

        logger.info(
            "daily_report_generated",
            report_date=report_date.isoformat(),
            report_id=str(report.report_id),
        )

        return {
            "status": "success",
            "report_date": report_date.isoformat(),
            "report_id": str(report.report_id),
        }
    except Exception as exc:
        logger.error(
            "daily_report_generation_failed",
            error=str(exc),
            report_date=report_date.isoformat(),
        )
        raise


async def run_daily_analytics(stat_date: datetime | None = None) -> dict[str, Any]:
    if stat_date is None:
        stat_date = datetime.now(timezone.utc) - timedelta(days=1)

    logger.info("Starting daily analytics pipeline", stat_date=stat_date.isoformat())

    results: dict[str, Any] = {}

    try:
        clean_result = await clean_player_events(
            start_date=stat_date - timedelta(days=7),
            end_date=stat_date,
        )
        results["clean_events"] = clean_result
    except Exception as exc:
        results["clean_events"] = {"status": "failed", "error": str(exc)}

    try:
        player_result = await aggregate_player_metrics(stat_date)
        results["player_metrics"] = player_result
    except Exception as exc:
        results["player_metrics"] = {"status": "failed", "error": str(exc)}

    try:
        region_result = await aggregate_region_metrics(stat_date)
        results["region_metrics"] = region_result
    except Exception as exc:
        results["region_metrics"] = {"status": "failed", "error": str(exc)}

    try:
        report_result = await generate_daily_report(stat_date)
        results["daily_report"] = report_result
    except Exception as exc:
        results["daily_report"] = {"status": "failed", "error": str(exc)}

    all_success = all(
        v.get("status") == "success" for v in results.values()
    )

    logger.info(
        "daily_analytics_pipeline_completed",
        stat_date=stat_date.isoformat(),
        all_success=all_success,
        results=results,
    )

    return {
        "status": "success" if all_success else "partial_failure",
        "stat_date": stat_date.isoformat(),
        "results": results,
    }
