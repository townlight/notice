"""Publication deadline helpers for Townlight Notice v0.3.0."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from townlight_core.notifications import build_deadline_plan as build_townlight_core_deadline_plan
from townlight_notice.notice_registry import DISCLAIMER


@dataclass(frozen=True)
class DeadlinePlan:
    notice_type: str
    event_date: date
    reminders: tuple[str, ...]
    staff_review_required: bool
    disclaimer: str = DISCLAIMER


def build_deadline_plan(*, notice_type: str, event_date: date, lead_days: int = 10) -> DeadlinePlan:
    """Build deterministic publication reminders without declaring legal sufficiency."""

    shared_plan = build_townlight_core_deadline_plan(
        notice_type=notice_type,
        event_date=event_date,
        lead_days=lead_days,
    )
    return DeadlinePlan(
        notice_type=shared_plan.notice_type,
        event_date=shared_plan.event_date,
        reminders=shared_plan.reminders,
        staff_review_required=shared_plan.staff_review_required,
    )
