from squad.carpool import plan_rides, transit_tip
from squad.models import Car
from tests.fakes import make_member

LOC = "Memorial Union 202, Tempe Campus"
TEMPE_TIP = (
    "It's on the Tempe campus: walk, bike, or hop on the free Orbit "
    "Jupiter/Mercury circulator."
)


def test_one_driver_fills_seats_then_transit():
    going = [
        make_member("d", name="Dana", seats=2),
        make_member("c", name="Cy"),
        make_member("a", name="Ava"),
        make_member("b", name="Ben"),
    ]
    rides = plan_rides(going, LOC)
    assert rides.cars == [Car(driver_id="d", rider_ids=["a", "b"])]
    assert rides.transit_ids == ["c"]
    assert rides.transit_tip == TEMPE_TIP


def test_two_drivers_biggest_first():
    going = [
        make_member("s", name="Sam", seats=1),
        make_member("z", name="Zoe", seats=3),
        make_member("a", name="Ava", seats=1),
        make_member("r1", name="Rae"),
        make_member("r2", name="Bo"),
        make_member("r3", name="Kit"),
        make_member("r4", name="Lu"),
    ]
    rides = plan_rides(going, LOC)
    assert rides.cars == [
        Car(driver_id="z", rider_ids=["r2", "r3", "r4"]),
        Car(driver_id="a", rider_ids=["r1"]),
        Car(driver_id="s", rider_ids=[]),
    ]
    assert rides.transit_ids == []
    assert rides.transit_tip == ""


def test_no_drivers_everyone_transit():
    going = [make_member("b", name="Ben"), make_member("a", name="Ava")]
    rides = plan_rides(going, "Downtown Phoenix campus")
    assert rides.cars == []
    assert rides.transit_ids == ["a", "b"]
    assert rides.transit_tip.startswith("Valley Metro light rail from Veterans Way")


def test_drivers_only():
    going = [
        make_member("b", name="Ben", seats=1),
        make_member("a", name="Ava", seats=1),
    ]
    rides = plan_rides(going, LOC)
    # everyone with seats drives; with no riders each drives themselves
    assert rides.cars == [
        Car(driver_id="a", rider_ids=[]),
        Car(driver_id="b", rider_ids=[]),
    ]
    assert rides.transit_ids == []
    assert rides.transit_tip == ""


def test_transit_tip_rules():
    assert transit_tip("Downtown Phoenix") == (
        "Valley Metro light rail from Veterans Way/College Ave to "
        "Van Buren/Central, about 25 min."
    )
    assert transit_tip("West Valley campus, Glendale") == (
        "Light rail to 19th Ave/Dunlap, then the 19th Ave bus; give it an hour."
    )
    assert transit_tip("Polytechnic campus, Mesa") == (
        "The free ASU intercampus shuttle from Tempe to Poly runs every 30 min."
    )
    assert transit_tip("MEMORIAL UNION 202") == TEMPE_TIP
    assert transit_tip("Coor Hall 174 (COOR)") == TEMPE_TIP
    assert transit_tip("Meet at the MU fountain") == TEMPE_TIP
    assert transit_tip("Somewhere else") == (
        "Valley Metro light rail or the free Orbit circulator should get you there."
    )
