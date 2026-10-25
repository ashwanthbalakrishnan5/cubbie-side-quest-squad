import pytest
from discord import ui

from squad.ui.onboarding import (
    CallsValues,
    JoinModal,
    JoinValues,
    apply_calls,
    member_from_join,
)
from tests.fakes import make_member

JOIN = JoinValues(
    interests=["music", "food"],
    free_slots=["fri_night"],
    budget_key="10",
    no_go=["late"],
    seats_key="2",
)


def test_member_from_join_keeps_phone():
    existing = make_member(
        "u1", phone="+14805550123", call_opt_in=True, quiet_hours="23-8"
    )
    m = member_from_join("u1", "Maya", "https://a/b.png", JOIN, existing)
    assert (m.phone, m.call_opt_in, m.quiet_hours) == ("+14805550123", True, "23-8")
    assert m.interests == ["music", "food"]
    assert m.budget_usd == 10 and m.seats == 2 and m.no_go == ["late"]
    fresh = member_from_join("u2", "Leo", "", JOIN, None)
    assert fresh.phone == "" and not fresh.call_opt_in


def test_apply_calls_normalises_us_number():
    m = apply_calls(make_member(), CallsValues("(480) 555-0123", True, "0-10"))
    assert m.phone == "+14805550123"
    assert m.call_opt_in is True and m.quiet_hours == "0-10"
    assert (
        apply_calls(make_member(), CallsValues("+44 20 7946 0958", True, "22-9")).phone
        == "+442079460958"
    )


@pytest.mark.parametrize(
    "raw", ["call me maybe", "480555", "+1 480 555 012x", "1234567890123456"]
)
def test_apply_calls_rejects_letters_and_short(raw):
    with pytest.raises(ValueError, match="phone"):
        apply_calls(make_member(), CallsValues(raw, True, "22-9"))


def test_apply_calls_empty_turns_off_calls():
    m = apply_calls(
        make_member(phone="+14805550123", call_opt_in=True),
        CallsValues("  ", True, "22-9"),
    )
    assert m.phone == "" and m.call_opt_in is False


def test_join_modal_has_five_labels():
    modal = JoinModal()
    labels = [c for c in modal.children if isinstance(c, ui.Label)]
    assert len(labels) == 5
    assert modal.title == "Join the squad (1/2)"
    assert labels[0].text == "What are you into?"
    prefilled = JoinModal(make_member(interests=["music"], budget_usd=20, seats=1))
    group = prefilled.children[0].component
    assert [o.value for o in group.options if o.default] == ["music"]
