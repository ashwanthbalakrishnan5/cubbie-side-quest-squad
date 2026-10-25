"""Carpool groups and a transit tip for whoever has no seat."""

from __future__ import annotations

import re

from .models import Car, Member, Rides

_TIPS: list[tuple[tuple[str, ...], str]] = [
    (
        ("downtown", "phoenix"),
        "Valley Metro light rail from Veterans Way/College Ave to Van Buren/Central, about 25 min.",
    ),
    (
        ("west valley", "glendale"),
        "Light rail to 19th Ave/Dunlap, then the 19th Ave bus; give it an hour.",
    ),
    (
        ("polytechnic", "mesa"),
        "The free ASU intercampus shuttle from Tempe to Poly runs every 30 min.",
    ),
]
_TEMPE_TIP = "It's on the Tempe campus: walk, bike, or hop on the free Orbit Jupiter/Mercury circulator."
_DEFAULT_TIP = (
    "Valley Metro light rail or the free Orbit circulator should get you there."
)
_BUILDING_CODE = re.compile(r"\([a-z]{2,6}\)$", re.IGNORECASE)


def transit_tip(location: str) -> str:
    loc = f" {location.lower()} "
    for needles, tip in _TIPS:
        if any(n in loc for n in needles):
            return tip
    if any(
        n in loc for n in ("tempe", "memorial union", " mu ")
    ) or _BUILDING_CODE.search(location.strip()):
        return _TEMPE_TIP
    return _DEFAULT_TIP


def plan_rides(going: list[Member], location: str) -> Rides:
    drivers = sorted(
        (m for m in going if m.seats > 0), key=lambda m: (-m.seats, m.name)
    )
    riders = sorted((m for m in going if m.seats <= 0), key=lambda m: m.name)
    cars = []
    for d in drivers:
        cars.append(Car(driver_id=d.id, rider_ids=[r.id for r in riders[: d.seats]]))
        riders = riders[d.seats :]
    transit_ids = [r.id for r in riders]
    return Rides(
        cars=cars,
        transit_ids=transit_ids,
        transit_tip=transit_tip(location) if transit_ids else "",
    )
