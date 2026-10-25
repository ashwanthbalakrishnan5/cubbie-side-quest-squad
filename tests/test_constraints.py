from datetime import datetime, timedelta

from squad.constraints import request_allows, violations_for
from squad.models import BusyBlock, LearnedFilter, Request
from tests.fakes import TZ, make_event, make_member

FRI_7PM = datetime(2026, 10, 30, 19, 0, tzinfo=TZ)


def lf(kind: str, value: str, text: str = "told you") -> LearnedFilter:
    return LearnedFilter(kind=kind, value=value, source_text=text, created_at=FRI_7PM)


def test_violation_budget_detail_and_label():
    m = make_member(budget_usd=10)
    [v] = violations_for(m, make_event(price_usd=12.0), [], TZ)
    assert v.kind == "budget"
    assert v.member_id == "u1"
    assert v.label_public == "a budget limit"
    assert v.detail_private == "it's $12 and your cap is $10"
    assert violations_for(m, make_event(price_usd=10.0), [], TZ) == []


def test_violation_late_night():
    m = make_member(no_go=["late"])
    late_start = make_event(start=FRI_7PM.replace(hour=22))
    [v] = violations_for(m, late_start, [], TZ)
    assert (v.kind, v.label_public) == ("late", "a late-night limit")
    spill = make_event(start=FRI_7PM.replace(hour=21))  # ends 23:00
    assert [v.kind for v in violations_for(m, spill, [], TZ)] == ["late"]
    assert violations_for(m, make_event(start=FRI_7PM.replace(hour=20)), [], TZ) == []
    assert violations_for(make_member(), late_start, [], TZ) == []


def test_no_go_regex_party():
    m = make_member(no_go=["parties"])
    [v] = violations_for(m, make_event("Halloween Party at the MU"), [], TZ)
    assert v.kind == "no_go"
    assert v.label_public == "a no-go type"
    assert v.detail_private == "it looks like parties & clubs"
    assert violations_for(m, make_event("Partying tips seminar"), [], TZ) == []


def test_learned_filters_each_kind():
    cases = [
        (lf("max_price", "5", "nothing over five bucks"), {"price_usd": 6.0}),
        (lf("latest_start_hour", "19", "nothing after 7"), {}),
        (lf("no_tag", r"\bopen mic\b", "no open mics pls"), {}),
        (lf("no_weekday", "4", "fridays are family night"), {}),
    ]
    for f, overrides in cases:
        m = make_member(learned_filters=[f])
        [v] = violations_for(m, make_event(**overrides), [], TZ)
        assert v.kind == "learned"
        assert v.label_public == "something they told me before"
        assert v.detail_private == f.source_text
    m = make_member(
        learned_filters=[lf("max_price", "5"), lf("latest_start_hour", "20")]
    )
    assert violations_for(m, make_event(price_usd=5.0), [], TZ) == []


def test_note_filter_never_violates():
    m = make_member(learned_filters=[lf("note", "open mic", "likes quiet stuff")])
    assert violations_for(m, make_event(), [], TZ) == []


def test_request_allows_keywords_and_price():
    ev = make_event("Board Game Night", price_usd=5.0)
    assert request_allows(ev, Request(), TZ)
    assert request_allows(ev, Request(keywords=["board games"], max_price=5), TZ)
    assert not request_allows(ev, Request(keywords=["hike"]), TZ)
    assert not request_allows(ev, Request(max_price=4), TZ)
    assert request_allows(
        ev, Request(weekdays=[4], earliest_hour=19, latest_hour=20), TZ
    )
    assert not request_allows(ev, Request(weekdays=[5]), TZ)
    assert not request_allows(ev, Request(earliest_hour=20), TZ)
    assert not request_allows(ev, Request(latest_hour=19), TZ)
    assert not request_allows(
        make_event("Club Night Party"), Request(exclude_no_go=["parties"]), TZ
    )
    assert request_allows(ev, Request(exclude_no_go=["parties", "late"]), TZ)


def full_violator():
    m = make_member(
        budget_usd=0,
        no_go=["late", "parties", "alcohol"],
        learned_filters=[lf("no_weekday", "4", "a"), lf("max_price", "1", "b")],
    )
    ev = make_event(
        "Late Party with beer", start=FRI_7PM.replace(hour=22), price_usd=15.0
    )
    busy = [BusyBlock(start=FRI_7PM.replace(hour=21), end=FRI_7PM.replace(hour=23))]
    return m, ev, busy


def test_violations_order_is_stable():
    m, ev, busy = full_violator()
    vs = violations_for(m, ev, busy, TZ)
    assert [v.kind for v in vs] == [
        "busy",
        "budget",
        "no_go",
        "no_go",
        "late",
        "learned",
        "learned",
    ]
    assert vs[0].detail_private == "you look busy then"
    assert vs[0].label_public == "a schedule clash"
    assert [v.detail_private for v in vs[2:4]] == [
        "it looks like parties & clubs",
        "it looks like alcohol",
    ]
    assert [v.detail_private for v in vs[5:]] == ["a", "b"]
    assert violations_for(m, ev, busy, TZ) == vs


def test_public_labels_never_contain_numbers():
    m, ev, busy = full_violator()
    vs = violations_for(m, ev, busy, TZ)
    assert {v.kind for v in vs} == {"busy", "budget", "no_go", "late", "learned"}
    for v in vs:
        assert not any(c.isdigit() for c in v.label_public)


def test_busy_none_uses_slots():
    m = make_member(free_slots=["sat_day"])
    [v] = violations_for(m, make_event(), None, TZ)
    assert v.kind == "busy"
    assert (
        violations_for(
            m, make_event(start=FRI_7PM + timedelta(days=1, hours=-7)), None, TZ
        )
        == []
    )


def test_malformed_learned_filter_is_ignored():
    m = make_member(learned_filters=[lf("max_price", "cheap"), lf("no_tag", "(")])
    assert violations_for(m, make_event(), [], TZ) == []
