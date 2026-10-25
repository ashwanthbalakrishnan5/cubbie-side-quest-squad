"""Fixed choices shared by the forms, the rules and the agents."""

EVENT_HOURS = 2
TRAVEL_MIN = 30
MAX_ROUNDS = 3
CANDIDATES_K = 6

# key: (label, keywords matched case-insensitively against title/description/org/tags)
INTERESTS: dict[str, tuple[str, list[str]]] = {
    "music": ("Live music", ["music", "concert", "band", "open mic", "jam", "dj"]),
    "sports": (
        "Sports & games",
        ["sport", "game", "basketball", "soccer", "volleyball", "tournament"],
    ),
    "food": (
        "Food & free food",
        ["food", "pizza", "boba", "taco", "snack", "dinner", "lunch", "cook"],
    ),
    "outdoors": (
        "Outdoors & hiking",
        ["hike", "outdoor", "climb", "trail", "camp", "kayak"],
    ),
    "arts": (
        "Arts & crafts",
        ["art", "craft", "paint", "draw", "museum", "gallery", "pottery"],
    ),
    "gaming": (
        "Gaming & esports",
        ["gaming", "esport", "video game", "smash", "board game"],
    ),
    "tech": (
        "Tech & hackathons",
        ["hackathon", "coding", "tech", "ai ", "robot", "startup"],
    ),
    "movies": (
        "Movies & shows",
        ["movie", "film", "screening", "theatre", "theater", "comedy"],
    ),
    "dance": ("Dance & parties", ["dance", "party", "salsa", "bhangra", "social"]),
    "chill": (
        "Chill hangouts",
        ["hangout", "chill", "yoga", "meditation", "coffee", "trivia"],
    ),
}

# key: (label, weekdays Mon=0, start_hour, end_hour) in local time; end 24 = midnight
FREE_SLOTS: dict[str, tuple[str, tuple[int, ...], int, int]] = {
    "weeknights": ("Weekday evenings (Mon–Thu)", (0, 1, 2, 3), 17, 22),
    "fri_night": ("Friday night", (4,), 17, 24),
    "sat_day": ("Saturday daytime", (5,), 10, 17),
    "sat_night": ("Saturday night", (5,), 17, 24),
    "sun_day": ("Sunday daytime", (6,), 10, 17),
    "sun_night": ("Sunday night", (6,), 17, 22),
}

BUDGETS: dict[str, tuple[str, int]] = {
    "free": ("Free only", 0),
    "10": ("Up to $10", 10),
    "20": ("Up to $20", 20),
    "40": ("Up to $40", 40),
}

# key: (label, regex searched in title+description+org+tags); "late" is a time rule
NO_GO: dict[str, tuple[str, str | None]] = {
    "parties": ("Parties & clubs", r"\b(party|club night|rave|nightclub)\b"),
    "late": ("Late nights (after 10pm)", None),
    "crowds": ("Big crowds", r"\b(festival|concert|rally|stadium|homecoming)\b"),
    "sports": (
        "Sports",
        r"\b(sport|basketball|football|soccer|volleyball|tournament)\b",
    ),
    "religious": (
        "Religious events",
        r"\b(church|worship|bible|prayer|ministry|mass)\b",
    ),
    "political": (
        "Political events",
        r"\b(republican|democrat|campaign|rally|political)\b",
    ),
    "alcohol": ("Alcohol", r"\b(beer|wine|bar crawl|21\+|cocktail|brewery)\b"),
}

SEATS: dict[str, tuple[str, int]] = {
    "0": ("No car", 0),
    "1": ("Car, 1 seat free", 1),
    "2": ("Car, 2 seats free", 2),
    "3": ("Car, 3 seats free", 3),
    "4": ("Car, 4 seats free", 4),
}

QUIET_HOURS: dict[str, tuple[str, int, int]] = {
    "22-9": ("10pm–9am", 22, 9),
    "23-8": ("11pm–8am", 23, 8),
    "0-10": ("Midnight–10am", 0, 10),
}

VOTE_ANSWERS = ("I'm in ✅", "Maybe 🤔", "Can't make it ❌")
VOTE_KEYS = ("yes", "maybe", "no")
BRAND = 0x8C1D40
