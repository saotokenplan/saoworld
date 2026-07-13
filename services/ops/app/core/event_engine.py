from datetime import datetime, timezone
from typing import Any

from app.domain.models import OpsEvent


class EventEngine:
    @staticmethod
    def is_event_active(event: OpsEvent, at_time: datetime | None = None) -> bool:
        if at_time is None:
            at_time = datetime.now(timezone.utc)

        if event.status != "active":
            return False

        return event.start_at <= at_time <= event.end_at

    @staticmethod
    def get_applicable_events(
        events: list[OpsEvent],
        *,
        player_level: int | None = None,
        region_id: str | None = None,
        guild_id: str | None = None,
        at_time: datetime | None = None,
    ) -> list[OpsEvent]:
        if at_time is None:
            at_time = datetime.now(timezone.utc)

        applicable = []
        for event in events:
            if not EventEngine.is_event_active(event, at_time):
                continue

            if event.target_scope == "all":
                applicable.append(event)
                continue

            scope_config = event.target_scope_jsonb or {}

            if event.target_scope == "region" and region_id:
                allowed_regions = scope_config.get("region_ids", [])
                if region_id in allowed_regions:
                    applicable.append(event)

            elif event.target_scope == "player_level" and player_level is not None:
                min_level = scope_config.get("min_level", 0)
                max_level = scope_config.get("max_level", 999)
                if min_level <= player_level <= max_level:
                    applicable.append(event)

            elif event.target_scope == "guild" and guild_id:
                allowed_guilds = scope_config.get("guild_ids", [])
                if guild_id in allowed_guilds:
                    applicable.append(event)

        return applicable

    @staticmethod
    def calculate_reward_multiplier(
        events: list[OpsEvent],
        reward_type: str = "exp",
    ) -> float:
        multiplier = 1.0

        for event in events:
            if not event.multiplier_config_jsonb:
                continue
            mult_config = event.multiplier_config_jsonb
            event_mult = mult_config.get(reward_type, 1.0)
            if event_mult > 1.0:
                if mult_config.get("stack_mode", "additive") == "additive":
                    multiplier += (event_mult - 1.0)
                else:
                    multiplier *= event_mult

        return max(multiplier, 1.0)

    @staticmethod
    def apply_event_rewards(
        events: list[OpsEvent],
        base_rewards: dict[str, float],
    ) -> dict[str, float]:
        result = {}
        for reward_type, base_value in base_rewards.items():
            mult = EventEngine.calculate_reward_multiplier(events, reward_type)
            result[reward_type] = base_value * mult
        return result

    @staticmethod
    def validate_event_config(event_data: dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []

        if "event_name" not in event_data or not event_data["event_name"]:
            errors.append("event_name is required")

        if "event_type" not in event_data:
            errors.append("event_type is required")
        elif event_data["event_type"] not in (
            "double_reward", "login_bonus", "limited_time", "sale", "custom"
        ):
            errors.append(f"invalid event_type: {event_data['event_type']}")

        if "start_at" not in event_data:
            errors.append("start_at is required")
        if "end_at" not in event_data:
            errors.append("end_at is required")

        if "start_at" in event_data and "end_at" in event_data:
            start = event_data["start_at"]
            end = event_data["end_at"]
            if isinstance(start, datetime) and isinstance(end, datetime):
                if start >= end:
                    errors.append("start_at must be before end_at")

        if "target_scope" in event_data:
            scope = event_data["target_scope"]
            if scope not in ("all", "region", "player_level", "guild"):
                errors.append(f"invalid target_scope: {scope}")

        if "multiplier_config_jsonb" in event_data and event_data["multiplier_config_jsonb"]:
            mult_cfg = event_data["multiplier_config_jsonb"]
            for key, value in mult_cfg.items():
                if key == "stack_mode":
                    continue
                if not isinstance(value, (int, float)):
                    errors.append(f"multiplier value for {key} must be a number")
                elif value <= 0:
                    errors.append(f"multiplier value for {key} must be positive")

        return len(errors) == 0, errors
