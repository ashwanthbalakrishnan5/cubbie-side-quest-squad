from datetime import datetime, timedelta

from squad.availability import in_quiet_hours, is_free, slot_covers
from squad.models import BusyBlock
from tests.fakes import TZ, make_member


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=TZ)


# 2026-10-30 is a Friday, 2026-10-29 a Thursday


def test_slot_covers_friday_night():
    assert slot_covers("fri_night", at(30, 19), at(30, 21), TZ)
    assert slot_covers("fri_night", at(30, 22), at(31, 0), TZ)  # ends at midnight
    assert not slot_covers("fri_night", at(29, 19), at(29, 21), TZ)  # Thursday
    assert not slot_covers("fri_night", at(30, 15), at(30, 17), TZ)


def test_slot_rejects_spill_past_end():
    assert not slot_covers("weeknights", at(29, 21), at(29, 23), TZ)
    assert not slot_covers("fri_night", at(30, 23), at(31, 1), TZ)
    assert slot_covers("weeknights", at(29, 20), at(29, 22), TZ)


def test_is_free_calendar_overlap_includes_travel():
    m = make_member()
    start, end = at(30, 19), at(30, 21)
    assert not is_free(
        m, start, end, [BusyBlock(start=at(30, 18), end=at(30, 18, 45))], TZ
    )
    assert is_free(m, start, end, [BusyBlock(start=at(30, 17), end=at(30, 18, 20))], TZ)
    assert is_free(m, start, end, [], TZ)


def test_is_free_without_calendar_uses_slots():
    m = make_member(free_slots=["sat_day"])
    assert not is_free(m, at(30, 19), at(30, 21), None, TZ)
    assert is_free(m, at(31, 12), at(31, 14), None, TZ)
    # travel is not checked against slots: 10:00 start still fits sat_day
    assert is_free(m, at(31, 10), at(31, 12), None, TZ)
    m2 = make_member(free_slots=["sat_day", "fri_night"])
    assert is_free(m2, at(30, 19), at(30, 19) + timedelta(hours=2), None, TZ)


def test_quiet_hours_wraps_midnight():
    m = make_member(quiet_hours="22-9")
    assert in_quiet_hours(m, at(30, 23, 30), TZ)
    assert in_quiet_hours(m, at(30, 8, 59), TZ)
    assert not in_quiet_hours(m, at(30, 9, 0), TZ)
    assert not in_quiet_hours(m, at(30, 21, 59), TZ)
    m0 = make_member(quiet_hours="0-10")
    assert in_quiet_hours(m0, at(30, 0, 30), TZ)
    assert not in_quiet_hours(m0, at(30, 23, 0), TZ)
