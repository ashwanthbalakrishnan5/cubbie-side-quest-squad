from datetime import datetime

from squad.models import Plan, Squad
from squad.store import Store
from tests.fakes import TZ, make_event, make_member


async def test_roundtrip_member_squad_plan(store):
    member = make_member("u1", phone="+14805550123")
    squad = Squad(channel_id="c1", guild_id="g1", member_ids=["u1"])
    plan = Plan(
        id="p1",
        channel_id="c1",
        event=make_event(),
        headline="h",
        why="w",
        votes={"u1": "yes"},
        created_at=datetime(2026, 10, 25, 9, tzinfo=TZ),
    )
    await store.put_member(member)
    await store.put_squad(squad)
    await store.put_plan(plan)

    again = Store(store.path)
    await again.load()
    assert again.member("u1") == member
    assert again.squad("c1") == squad
    assert again.plan("p1") == plan
    assert again.plans("confirming") == [plan]
    assert again.plans("closed") == []


async def test_delete_member_removes_from_squads(store):
    await store.put_member(make_member("u1"))
    await store.put_member(make_member("u2"))
    await store.put_squad(
        Squad(channel_id="c1", guild_id="g1", member_ids=["u1", "u2"])
    )
    await store.delete_member("u1")
    assert store.member("u1") is None
    assert store.squad("c1").member_ids == ["u2"]
    assert store.members(["u1", "u2"]) == [store.member("u2")]


async def test_missing_file_is_empty(store):
    await store.load()
    assert store.squads() == []
    assert store.plans() == []
