from squad.matching import interest_score, keyword_hits
from tests.fakes import make_event, make_member


def test_keyword_hits_plural():
    event = make_event("Board Game Night")
    assert keyword_hits(event, ["board games"]) == ["board games"]
    assert keyword_hits(event, ["karaoke"]) == []


def test_interest_score_counts_interests_not_keywords():
    event = make_event(
        "Open Mic Night with free pizza", description="live music and a band"
    )
    member = make_member(interests=["music", "food", "outdoors"])
    assert interest_score(member, event) == 2
