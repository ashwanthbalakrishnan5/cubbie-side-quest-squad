from datetime import datetime

from squad.models import Plan
from tests.fakes import TZ, make_event


def test_plan_json_roundtrip_keeps_timezone():
    plan = Plan(
        id="p1",
        channel_id="c1",
        event=make_event(),
        headline="h",
        why="w",
        created_at=datetime(2026, 10, 25, 9, tzinfo=TZ),
    )
    back = Plan.model_validate_json(plan.model_dump_json())
    assert back.event.start.tzinfo is not None
    assert back.event.start == plan.event.start
    assert back.created_at == plan.created_at
