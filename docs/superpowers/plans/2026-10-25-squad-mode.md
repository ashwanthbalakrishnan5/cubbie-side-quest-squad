# Side Quests: Squad Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Every decision is made here. If something is truly not covered, pick the simplest option that keeps every listed
> test passing, write it down in `docs/decisions.md` (one line), and keep going.

**Goal:** A Discord bot that plans one real ASU campus event a week for a friend group, with one Claude agent per
member, a coordinator that resolves conflicting constraints and asks before breaking anyone's limit, a native poll, a
"why no?" DM that becomes a remembered filter, carpools, and a WhatsApp voice nudge (Gemini Live).

**Architecture:** One Python 3.12 process (`python -m squad`) runs the discord.py client and a small aiohttp web
server. Pure modules (constraints, availability, carpool) hold all rules and are fully unit-tested; Claude only
scores and explains. A separate Rust sidecar (`wa-voice/`) places WhatsApp calls and pipes 16 kHz PCM over a
localhost WebSocket; the Python bot bridges that audio to Gemini Live. State lives in one JSON file.

**Tech Stack:** Python 3.12, uv, discord.py 2.7.1, anthropic (AsyncAnthropic, `claude-opus-5-5`), composio (Google
Calendar via Connect Links), google-genai (Live API, `gemini-3.8-live`), pydantic v2, pytest + pytest-asyncio, ruff.
Rust stable (cargo 1.99) with whatsapp-rust (git `main`, `voip` features), tokio, axum.

**Spec:** `docs/spec.md` (product decisions), `docs/discord-notes.md` (Discord features chosen).

## Global Constraints

- Python `>=3.12`; dependency pins in `pyproject.toml` exactly as in Task 0. No other runtime dependencies.
- Claude model `claude-opus-5-5` for every Claude call. Member agents `output_config.effort="low"`, coordinator
  `"medium"`, request/reason parsing `"low"`. Never send `temperature`, `top_p`, `top_k`, `thinking` or `budget_tokens`.
- Gemini Live model `gemini-3.8-live`.
- Time zone everywhere: `America/Phoenix` (`settings.tz`). All stored datetimes are timezone-aware.
- Events: `https://sundevilcentral.eoss.asu.edu/rss_events`, campus filter `Tempe Campus`, 7 days ahead.
- An event lasts 2 hours (`EVENT_HOURS = 2`); members need 30 minutes of travel before it (`TRAVEL_MIN = 30`).
- Brand colour `#8C1D40` (ASU maroon) for every Container accent.
- Copy tone: soft and playful, never guilt-tripping or sad. No exclamation-mark spam (max one per message).
- Public messages never reveal one member's private constraint (budget, calendar, learned filter, reason for "no").
- Every secret comes from `.env`; `.env` is gitignored; never log or print a secret.
- Lint: `uv run ruff check . && uv run ruff format --check .` must pass. Rust: `cargo clippy -- -D warnings`.
- Commits: conventional prefixes (`feat:`, `test:`, `fix:`, `docs:`, `chore:`). **Never add a Claude co-author line.**
- Never push to GitHub, create the GitHub repo, touch openclaw, DNS, or Caddy, or submit to the hackathon without the
  user's explicit yes in chat.

## Review Focus

1. **The events feed is slow, down or empty.** `upcoming_events` serves a cache up to 48 h old; with no cache the
   bot replies with a friendly "Sun Devil Central isn't answering" line and makes no plan. Tests in Task 1 and Task 12.
2. **Nothing fits everyone.** The planner returns the option with the fewest broken limits, the people affected are
   asked privately, and if every option is declined after 3 rounds the bot posts a "no plan this week" message
   naming only the near-miss event. Tests in Task 10 and Task 12.
3. **A member's DMs are closed.** `discord.Forbidden` on any DM never crashes a flow: confirmation counts as "no",
   "why no?" is skipped, nudges fall back to a channel mention with no private details. Tests in Task 12 and Task 13.
4. **Junk in the sign-up form.** A phone number that is not 10–15 digits (optionally with `+`, spaces, dashes,
   brackets) is rejected with a friendly ephemeral message and nothing is saved. Test in Task 6.
5. **Claude fails or refuses.** Any `LLMError` makes the planner fall back to a deterministic pick with template
   copy, so a plan is still posted. Tests in Task 4 and Task 10.

---

## Execution: waves, worktrees and verifiers

Parallel tasks touch disjoint files. Each implementer agent works in its own git worktree on branch `ws/<task-id>`
(created from `main` after Task 0 is merged) and merges back with `git merge --no-ff`. Task 0 adds every dependency
and every shared contract up front, so no later task edits `pyproject.toml`, `squad/models.py`, `squad/constants.py`,
`squad/config.py` or `tests/fakes.py`. If one must change, the orchestrator does it on `main` and tells every running
agent to rebase.

| Wave | Tasks (parallel inside a wave) | Needs |
| --- | --- | --- |
| 0 | T0 scaffold + contracts | — |
| 1 | T1 events · T2 availability+constraints · T3 carpool · T4 llm+agents · T5 calendar · T6 UI (cards, onboarding) · T7 personas · T8 wa-voice (Rust) · T9 voice bridge | T0 |
| 2 | T10 planner · T11 bot core (client, join/leave/demo) · T15 web server + site | T10: T2,T4 · T11: T5,T6,T7 · T15: T0 |
| 3 | T12 plan flow · then T13 vote flow and T14 nudge flow in parallel | T10, T11 (T13: +T3; T14: +T9) |
| 4 | T16 live end-to-end + deploy · T17 README, DEMO, CLAUDE.md · T18 submission draft | everything |

**Verifier agents.** Each task gets a separate verifier agent started as soon as its implementer reports done. The
verifier never edits code; it reports PASS or a list of concrete failures, and the implementer fixes them. Verifier
prompt (fill in `<task>`):

> You verify Task `<task>` of `docs/superpowers/plans/2026-10-25-squad-mode.md` on branch `ws/<task>`. Do not edit
> files. 1) Run `uv run pytest -q` and `uv run ruff check . && uv run ruff format --check .` (Rust: `cargo test`,
> `cargo clippy -- -D warnings` in `wa-voice/`). 2) Read the task's Interfaces block and check every listed name,
> signature and type exists exactly as written. 3) Check every Global Constraint against the diff. 4) Run the task's
> **Live check** (if any) and paste its output. 5) Try the Review Focus items that touch this task's code by hand.
> Report PASS, or numbered failures with file:line and the exact command that shows each one.

A standing **integration watcher** agent runs after every merge to `main`: full `uv run pytest -q`, ruff, and
`uv run python -m squad --check` (from Task 15), and reports any break to the orchestrator with the merge commit.

---

## File map

```
squad/                         repo root (becomes github.com/ashwanthbalakrishnan5/cubbie-side-quest-squad)
  pyproject.toml  uv.lock  .env (gitignored)  .env.example  .gitignore  CLAUDE.md (gitignored)
  README.md  DEMO.md
  docs/spec.md  docs/discord-notes.md  docs/decisions.md  docs/superpowers/plans/…
  squad/
    __init__.py  __main__.py (T15)  config.py  constants.py  models.py  store.py (T0)
    campus_events.py (T1, vendored)  assets/sample_campusgroups.xml (T1)  events.py (T1)
    availability.py  constraints.py (T2)   carpool.py (T3)
    llm.py  agents.py  prompts.py (T4)     calendar.py (T5)
    ui/__init__.py  ui/cards.py  ui/onboarding.py (T6)
    personas.py (T7)                       planner.py (T10)
    bot.py (T11)  flows/__init__.py  flows/plan_flow.py (T12)  flows/vote_flow.py (T13)  flows/nudge_flow.py (T14)
    voice/__init__.py  voice/resample.py  voice/bridge.py (T9)
    web.py  site/index.html (T15)
  scripts/preview_cards.py (T6)  scripts/smoke_live.py (T16)
  tests/conftest.py  tests/fakes.py (T0)  tests/test_<module>.py (one per module)
  wa-voice/ Cargo.toml  src/main.rs  src/audio.rs (T8)
```

---

### Task 0: Scaffold, shared contracts, test harness

**Files:**
- Create: `pyproject.toml`, `.env.example`, `squad/__init__.py`, `squad/config.py`, `squad/constants.py`,
  `squad/models.py`, `squad/matching.py`, `squad/store.py`, `tests/conftest.py`, `tests/fakes.py`,
  `tests/test_store.py`, `tests/test_models.py`, `tests/test_matching.py`, `docs/decisions.md`
- Modify: `.gitignore` (already has `.env .venv/ __pycache__/ data/ CLAUDE.md`; add `wa-voice/target/`)

**Interfaces — Produces (every later task relies on these names exactly):**

`pyproject.toml`: project `squad`, version `0.1.0`, `requires-python = ">=3.12"`, dependencies
`discord.py==2.7.1`, `anthropic>=1.0`, `composio>=0.10`, `google-genai>=2.30`, `pydantic>=2.9`,
`python-dotenv>=1.0`; dev group `pytest>=8`, `pytest-asyncio>=0.24`, `ruff>=0.7`. `[tool.pytest.ini_options]`
`asyncio_mode = "auto"`, `testpaths = ["tests"]`. `[tool.ruff]` `target-version = "py312"`.

`squad/config.py`:
```python
@dataclass(frozen=True)
class Settings:
    discord_token: str; anthropic_api_key: str; gemini_api_key: str
    composio_api_key: str          # "" allowed: calendar features turn off
    composio_calendar_auth_config: str   # "ac_aze6I2N0XYM_"
    public_url: str = "http://localhost:8090"   # https://squad.ashwanthbk.com in production
    web_port: int = 8090
    wa_voice_url: str = "http://127.0.0.1:8091" # "" = voice off
    data_dir: Path = Path("data")
    tz: ZoneInfo = ZoneInfo("America/Phoenix")
    events_url: str = "https://sundevilcentral.eoss.asu.edu/rss_events"
    campus: str = "Tempe Campus"
    dev_channel_id: int = 1563800077368295476     # #general in Test-Server-Cubbie
    demo_fast: bool = False   # DEMO_FAST=1: personas vote after 5–20 s, nudge after 1 min, confirm timeout 60 s
def load_settings() -> Settings   # reads .env via python-dotenv; env names are the upper-case field names
```
Timing helpers on `Settings`: `confirm_timeout_s` (60 if demo_fast else 600), `nudge_after_s` (60 if demo_fast else
1800), `persona_vote_delays_s` (`(5, 9, 14, 20)` if demo_fast else `(60, 240, 600, 900)`).

`squad/constants.py` (exact keys and labels; labels ≤ 45 chars):
```python
EVENT_HOURS = 2
TRAVEL_MIN = 30
MAX_ROUNDS = 3
CANDIDATES_K = 6
INTERESTS = {  # key: (label, keywords matched case-insensitively against title/description/org/tags)
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
FREE_SLOTS = {  # key: (label, weekdays Mon=0, start_hour, end_hour) local time; end 24 = midnight
    "weeknights": ("Weekday evenings (Mon–Thu)", (0, 1, 2, 3), 17, 22),
    "fri_night": ("Friday night", (4,), 17, 24),
    "sat_day": ("Saturday daytime", (5,), 10, 17),
    "sat_night": ("Saturday night", (5,), 17, 24),
    "sun_day": ("Sunday daytime", (6,), 10, 17),
    "sun_night": ("Sunday night", (6,), 17, 22),
}
BUDGETS = {
    "free": ("Free only", 0),
    "10": ("Up to $10", 10),
    "20": ("Up to $20", 20),
    "40": ("Up to $40", 40),
}
NO_GO = {  # key: (label, regex searched in title+description+org+tags)
    "parties": ("Parties & clubs", r"\b(party|club night|rave|nightclub)\b"),
    "late": ("Late nights (after 10pm)", None),  # time rule, see constraints
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
SEATS = {
    "0": ("No car", 0),
    "1": ("Car, 1 seat free", 1),
    "2": ("Car, 2 seats free", 2),
    "3": ("Car, 3 seats free", 3),
    "4": ("Car, 4 seats free", 4),
}
QUIET_HOURS = {
    "22-9": ("10pm–9am", 22, 9),
    "23-8": ("11pm–8am", 23, 8),
    "0-10": ("Midnight–10am", 0, 10),
}
VOTE_ANSWERS = (
    "I'm in ✅",
    "Maybe 🤔",
    "Can't make it ❌",
)  # poll answer order; maps to yes / maybe / no
VOTE_KEYS = ("yes", "maybe", "no")
BRAND = 0x8C1D40
```

`squad/models.py` (pydantic `BaseModel`, all datetimes aware):
```python
class BusyBlock(BaseModel):
    start: datetime
    end: datetime


class LearnedFilter(BaseModel):
    kind: Literal["max_price", "latest_start_hour", "no_tag", "no_weekday", "note"]
    value: str
    source_text: str
    created_at: datetime


class Member(BaseModel):
    id: str  # Discord user id as str, or "demo:<name>" for personas
    name: str
    is_demo: bool = False
    avatar_url: str = ""
    interests: list[str]
    free_slots: list[str]
    budget_usd: int
    no_go: list[str] = []
    seats: int = 0
    phone: str = ""
    call_opt_in: bool = False
    quiet_hours: str = "22-9"
    learned_filters: list[LearnedFilter] = []
    demo_busy: list[BusyBlock] = []


class Event(BaseModel):
    id: str  # sha1(title + start.isoformat())[:10]
    title: str
    start: datetime
    end: datetime
    location: str
    org: str = ""
    description: str = ""
    url: str = ""
    tags: list[str] = []
    free_food: bool = False
    price_usd: float = 0.0


class Request(BaseModel):
    vibe: str = ""
    max_price: float | None = None
    weekdays: list[int] = []
    earliest_hour: int | None = None
    latest_hour: int | None = None
    exclude_no_go: list[str] = []
    keywords: list[str] = []


class Violation(BaseModel):
    member_id: str
    kind: Literal["busy", "budget", "no_go", "late", "learned"]
    detail_private: (
        str  # e.g. "costs $15, your cap is $10" — only ever shown to that member
    )
    label_public: str  # e.g. "a budget limit" — safe for the group


class Stance(BaseModel):
    member_id: str
    event_id: str
    score: int
    shared_reason: str
    flex_ok: bool


class Decision(BaseModel):
    event_id: str
    headline: str
    why: str
    tradeoffs: list[str]


class AgentTurn(BaseModel):
    speaker: str
    member_id: str | None = None
    text: str


class Car(BaseModel):
    driver_id: str
    rider_ids: list[str]


class Rides(BaseModel):
    cars: list[Car]
    transit_ids: list[str]
    transit_tip: str


class Squad(BaseModel):
    channel_id: str
    guild_id: str
    member_ids: list[str] = []
    weekly_weekday: int = 2
    weekly_hour: int = 18
    poll_hours: int = 1
    webhook_url: str = ""
    last_weekly_date: date | None = None


class Plan(BaseModel):
    id: str
    channel_id: str
    event: Event
    status: Literal["confirming", "polling", "closed", "cancelled"] = "confirming"
    headline: str
    why: str
    tradeoffs: list[str] = []
    ask_first: list[str] = []
    confirmations: dict[str, bool] = {}
    declined_event_ids: list[str] = []
    turns: list[AgentTurn] = []
    message_id: str = ""
    thread_id: str = ""
    poll_message_id: str = ""
    poll_closes_at: datetime | None = None
    votes: dict[str, Literal["yes", "maybe", "no"]] = {}
    why_no_asked: list[str] = []
    nudged: list[str] = []
    discord_event_url: str = ""
    created_at: datetime


class NoPlan(BaseModel):
    reason: str
    near_miss: Event | None = None
```

`squad/matching.py` (shared by Tasks 2, 4, 10 so they don't depend on each other):
- `keyword_hits(event: Event, keywords: list[str]) -> list[str]` — case-insensitive substring over
  title/description/org/tags; a keyword of ≥ 4 letters ending in `s` also matches without the `s` (same trick as
  `campus_events.rank`).
- `interest_score(member: Member, event: Event) -> int` — number of the member's interests whose `INTERESTS`
  keywords have ≥ 1 hit (0–10).

`squad/store.py`:
```python
class Store:
    def __init__(self, path: Path) -> None          # data/squad.json
    async def load(self) -> None                     # missing file = empty store
    def member(self, member_id: str) -> Member | None
    def members(self, ids: Iterable[str]) -> list[Member]   # skips unknown ids, keeps order
    def squad(self, channel_id: str) -> Squad | None
    def squads(self) -> list[Squad]
    def plan(self, plan_id: str) -> Plan | None
    def plans(self, *statuses: str) -> list[Plan]
    async def put_member(self, m: Member) -> None
    async def put_squad(self, s: Squad) -> None
    async def put_plan(self, p: Plan) -> None
    async def delete_member(self, member_id: str) -> None   # also removes the id from every Squad.member_ids
```
Writes: one `asyncio.Lock`, dump the whole document `{"members": {...}, "squads": {...}, "plans": {...}}` with
`model_dump(mode="json")` to `path.with_suffix(".tmp")`, then `os.replace`.

`tests/fakes.py`: `class FakeLLM` with `parse(self, *, system, user, schema, effort)` returning the next queued object
for that `schema` from `self.queue: dict[type, list]` and recording calls in `self.calls`; raising `LLMError` when the
queued item is an exception instance. Factories `make_member(id="u1", **overrides) -> Member` (defaults: interests
`["music"]`, free_slots all six keys, budget 20, seats 0) and `make_event(title="Open Mic Night", start=<Fri
2026-10-30 19:00 America/Phoenix>, **overrides) -> Event`. `tests/conftest.py` exposes fixtures `tz`, `store`
(tmp_path), `fake_llm`.

- [ ] **Step 1:** `git init -b main` in `squad/`; write the files above; `uv sync`.
- [ ] **Step 2: Write failing tests** `tests/test_store.py::test_roundtrip_member_squad_plan` (put each, new `Store`
  on same path, `load`, objects equal), `::test_delete_member_removes_from_squads`,
  `::test_missing_file_is_empty`; `tests/test_models.py::test_plan_json_roundtrip_keeps_timezone` (dump/load keeps
  `tzinfo` and equal instant); `tests/test_matching.py::test_keyword_hits_plural` (`["board games"]` hits "Board
  Game Night") and `::test_interest_score_counts_interests_not_keywords`.
- [ ] **Step 3:** `uv run pytest -q` → FAIL (store not implemented); implement `Store`; → PASS.
- [ ] **Step 4:** ruff check/format; commit `chore: scaffold squad project and shared contracts`.

---

### Task 1: Campus events

**Files:** Create `squad/campus_events.py` (byte-for-byte copy of `../side-quests/scripts/campus_events.py`),
`squad/assets/sample_campusgroups.xml` (copy of `../side-quests/assets/sample_campusgroups.xml`), `squad/events.py`,
`tests/test_events.py`. In the copy, change only the `SAMPLE` path line to `Path(__file__).parent / "assets" /
"sample_campusgroups.xml"`.

**Interfaces:**
- Consumes: `campus_events.read_feed(url, start, end, zone) -> list[dict]`, `campus_events.rank(events, start, end,
  interests, campus) -> list[dict]` (dict keys: title, start, location, org, description, tags, free_food, url,
  matches, likely_skip).
- Produces:
  - `class EventsUnavailable(Exception)`
  - `def to_event(raw: dict) -> Event` — `end = start + EVENT_HOURS`, `price_usd = price_from_text(title + " " +
    description)`, `id = sha1(f"{title}{start.isoformat()}")[:10]`.
  - `def price_from_text(text: str) -> float` — first `$<number>` (e.g. `$12`, `$7.50`) → float; "free" or none → 0.0.
  - `async def upcoming_events(settings: Settings, now: datetime, days: int = 7) -> list[Event]` — runs read_feed +
    rank (interests `[]`, campus `settings.campus`) via `asyncio.to_thread`; drops `likely_skip` events; memory cache
    6 h; on success also writes `data/events_cache.json` (`{"fetched_at", "events"}`); on any fetch error or
    `SystemExit` from the script, returns the file cache if `fetched_at` is < 48 h old (filtered to `start > now`),
    else raises `EventsUnavailable`.

- [ ] **Step 1: Failing tests:** `test_price_from_text` (`"Tickets $12 at door"`→12.0, `"$7.50 entry"`→7.5,
  `"Free pizza"`→0.0); `test_to_event_sets_two_hour_end_and_stable_id`; `test_upcoming_events_uses_sample_feed` (monkeypatch
  `campus_events.fetch` to return the sample XML text, `now = 2026-10-26 08:00 America/Phoenix`, assert ≥ 3 events,
  all `start > now`, all aware); `test_stale_cache_served_when_feed_fails` (feed raises `SystemExit`, cache 10 h
  old → cached events); `test_no_cache_raises` (feed fails, no file → `EventsUnavailable`);
  `test_cache_older_than_48h_raises`.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** run → PASS. **Step 5:** ruff; commit
  `feat: campus events with cache`.
- **Live check (verifier):** `uv run python -c "import asyncio,datetime as d;from squad.config import load_settings;from squad.events import upcoming_events;s=load_settings();ev=asyncio.run(upcoming_events(s,d.datetime.now(s.tz)));print(len(ev));[print(e.start,e.title,e.location) for e in ev[:5]]"` prints a count ≥ 1 (takes ~25 s).

---

### Task 2: Availability and constraints (pure rules)

**Files:** Create `squad/availability.py`, `squad/constraints.py`, `tests/test_availability.py`,
`tests/test_constraints.py`.

**Interfaces — Produces:**
- `availability.slot_covers(slot_key: str, start: datetime, end: datetime, tz: ZoneInfo) -> bool` — whole window
  inside the slot on the same local day (end hour 24 = midnight of that day).
- `availability.is_free(member: Member, start: datetime, end: datetime, busy: list[BusyBlock] | None, tz) ->
  bool` — window is `[start - TRAVEL_MIN, end]`. If `busy` is not None (calendar or persona blocks): free iff no
  overlap. If None: free iff any of `member.free_slots` covers `[start, end]` (travel not checked against slots).
- `availability.in_quiet_hours(member: Member, at: datetime, tz) -> bool` — uses `QUIET_HOURS`; wraps midnight.
- `constraints.request_allows(event: Event, request: Request, tz) -> bool` — the group's own filters from a manual
  request: `max_price`, `weekdays`, `earliest_hour` (start hour ≥), `latest_hour` (start hour <), `exclude_no_go`
  regexes, and if `keywords` non-empty at least one `matching.keyword_hits`.
- `constraints.violations_for(member: Member, event: Event, busy: list[BusyBlock] | None, tz) ->
  list[Violation]` — one Violation per broken rule, in this order and with these `label_public` strings:
  - not `is_free` → `busy`, "a schedule clash", detail "you look busy then"
  - `price_usd > budget_usd` → `budget`, "a budget limit", detail `f"it's ${price:g} and your cap is ${budget}"`
  - each `no_go` key whose regex matches → `no_go`, "a no-go type", detail `f"it looks like {label.lower()}"`
  - `"late" in no_go` and (start hour ≥ 22 or end after 22:00 local) → `late`, "a late-night limit"
  - each learned filter that matches → `learned`, "something they told me before", detail = `source_text`:
    `max_price` (price > float(value)), `latest_start_hour` (start hour ≥ int(value)), `no_tag` (value regex),
    `no_weekday` (start weekday == int(value)); `note` never matches.

- [ ] **Step 1: Failing tests** (use `make_member`, `make_event`): `test_slot_covers_friday_night`;
  `test_slot_rejects_spill_past_end`; `test_is_free_calendar_overlap_includes_travel` (busy 18:00–18:45, event 19:00
  → not free; busy 17:00–18:20 → free); `test_is_free_without_calendar_uses_slots`;
  `test_quiet_hours_wraps_midnight` (22-9: 23:30 True, 08:59 True, 09:00 False);
  `test_violation_budget_detail_and_label`; `test_violation_late_night`; `test_no_go_regex_party`;
  `test_learned_filters_each_kind`; `test_note_filter_never_violates`; `test_request_allows_keywords_and_price`;
  `test_violations_order_is_stable`; `test_public_labels_never_contain_numbers` (no digit in any `label_public`).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: availability and constraint rules`.

---

### Task 3: Carpool and transit

**Files:** Create `squad/carpool.py`, `tests/test_carpool.py`.

**Interfaces — Produces:**
- `plan_rides(going: list[Member], location: str) -> Rides` — drivers are `going` with `seats > 0`, sorted by seats
  desc then name; riders are the rest sorted by name; fill each driver up to `seats`, in order. Riders left over go
  to `transit_ids`. Drivers with no riders still appear in `cars` (they drive themselves). `transit_tip =
  transit_tip(location)` (empty string if `transit_ids` is empty and every rider has a seat).
- `transit_tip(location: str) -> str` — first match wins (case-insensitive):
  - "downtown" or "phoenix" → "Valley Metro light rail from Veterans Way/College Ave to Van Buren/Central, about 25 min."
  - "west valley" or "glendale" → "Light rail to 19th Ave/Dunlap, then the 19th Ave bus; give it an hour."
  - "polytechnic" or "mesa" → "The free ASU intercampus shuttle from Tempe to Poly runs every 30 min."
  - "tempe" or "memorial union" or " mu " or any location ending in a building code like "(COOR)" → "It's on the
    Tempe campus: walk, bike, or hop on the free Orbit Jupiter/Mercury circulator."
  - else → "Valley Metro light rail or the free Orbit circulator should get you there."

- [ ] **Step 1: Failing tests:** `test_one_driver_fills_seats_then_transit`; `test_two_drivers_biggest_first`;
  `test_no_drivers_everyone_transit`; `test_drivers_only`; `test_transit_tip_rules` (one assert per branch).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: carpool groups and transit tips`.

---

### Task 4: Claude wrapper and the agents

**Files:** Create `squad/llm.py`, `squad/prompts.py`, `squad/agents.py`, `tests/test_llm.py`, `tests/test_agents.py`.

**Interfaces:**
- Produces in `llm.py`:
  - `class LLMError(Exception)`
  - `class LLM: def __init__(self, client: anthropic.AsyncAnthropic, model: str = "claude-opus-5-5")`;
    `async def parse(self, *, system: str, user: str, schema: type[T], effort: Literal["low", "medium"]) -> T` —
    `await client.messages.parse(model=…, max_tokens=4000, system=system, messages=[{"role": "user", "content":
    user}], output_format=schema, output_config={"effort": effort}, extra_headers={"anthropic-beta":
    "server-side-fallback-2026-07-01"}, extra_body={"fallbacks": "default"})`. Raise `LLMError` on any
    `anthropic.APIError`, on `stop_reason in ("refusal", "max_tokens")`, or when `parsed_output` is None. Log the
    stop reason, never the prompt.
- Produces in `agents.py` (all take `llm: LLM`; each wraps its pydantic output model, then maps to shared models):
  - `async def parse_request(llm, text: str, now: datetime) -> Request` — schema `RequestOut` mirroring `Request`;
    `exclude_no_go` only keys of `NO_GO`, unknown keys dropped in code. On `LLMError` return `Request(vibe=text)`.
  - `async def member_stances(llm, member: Member, candidates: list[tuple[Event, list[Violation]]], request: Request)
    -> list[Stance]` — one Claude call per member; schema `StancesOut{stances: list[{event_id, score 0–10,
    shared_reason ≤ 120 chars, flex_ok}]}`; code clamps scores, truncates reasons, drops unknown event ids, and fills
    any missing candidate with `score=min(10, 3 * matching.interest_score(...))`, `shared_reason=""`,
    `flex_ok=False`. On `LLMError` every candidate
    gets that fallback stance.
  - `async def coordinate(llm, members: list[Member], candidates: list[tuple[Event, list[Violation]]], stances:
    list[Stance], request: Request) -> Decision` — schema `DecisionOut{event_id, headline ≤ 80, why ≤ 280,
    tradeoffs ≤ 3 items ≤ 120 chars}`. The coordinator prompt receives per candidate: title, time, location, price,
    every member's `score` and `shared_reason` by name, and violations as `"<name>: <label_public>"` only (never
    `detail_private`). If the returned `event_id` is unknown, or on `LLMError`, use `fallback_decision`.
  - `def fallback_decision(members, candidates, stances) -> Decision` — pick min (number of violations, -sum of
    scores, start); headline `f"{title}, {start:%a %-I:%M %p}"` in local time; why `"It's the option that fits the most of you
    this week."`; tradeoffs = up to 3 `label_public` strings, de-duplicated, phrased "Someone has <label>".
  - `async def learn_from_no(llm, member: Member, reason: str, event: Event) -> LearnedFilter | None` — schema
    `LearnedOut{kind, value, keep: bool}`; `keep=False` or `LLMError` → None. `created_at=now`, `source_text=reason`
    truncated to 140.
- `prompts.py` holds four system prompts as module constants: `REQUEST_SYSTEM`, `MEMBER_SYSTEM`, `COORDINATOR_SYSTEM`,
  `LEARN_SYSTEM`. Required content:
  - `MEMBER_SYSTEM`: "You are {name}'s personal planning agent in a friend group's Discord. You see {name}'s private
    profile. Score each candidate 0–10 for how much {name} would enjoy it. `shared_reason` is the only thing the group
    sees: keep it friendly, first person on {name}'s behalf ('I'd love the open mic'), and never mention budgets,
    calendars, prices they can't afford, or anything from the private profile. Set flex_ok true only if a broken
    limit looks like a mild preference rather than a hard no."
  - `COORDINATOR_SYSTEM`: "You coordinate a friend group's weekly side quest. Pick the one event that the most people
    can and want to do. Hard limits matter more than enthusiasm. Explain the pick in one warm, short paragraph and
    list the trade-offs honestly but without naming whose private limit was involved. Never invent events."
  - `REQUEST_SYSTEM`: turn a casual ask ("something chill Friday under $15, no clubs") into the Request fields; today
    is given in the user message; weekdays use Monday=0.
  - `LEARN_SYSTEM`: turn a friend's optional reason for skipping into at most one reusable filter, or keep=false if
    it was a one-off ("I'm sick").

- [ ] **Step 1: Failing tests** (FakeLLM): `test_parse_request_drops_unknown_no_go`;
  `test_parse_request_falls_back_on_error`; `test_member_stances_clamps_and_fills_missing`;
  `test_member_stances_fallback_on_error`; `test_coordinator_prompt_has_no_private_details` (inspect
  `fake_llm.calls[-1]["user"]`: contains "a budget limit", not "your cap"); `test_coordinate_unknown_event_uses_fallback`;
  `test_fallback_prefers_fewest_violations`; `test_learn_from_no_keep_false_returns_none`;
  `tests/test_llm.py::test_refusal_raises` and `::test_api_error_raises` (stub client object whose `messages.parse`
  returns an object with `stop_reason="refusal"` / raises `anthropic.APIConnectionError`).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: claude member agents and coordinator`.
- **Live check (verifier):** a script in the verifier's scratch dir calls each of the four functions once with
  `LLM(AsyncAnthropic())`, two `make_member`s and three `make_event`s, and prints the outputs. All return without
  `LLMError`; `shared_reason` texts contain no `$`.

---

### Task 5: Google Calendar through Composio

**Files:** Create `squad/calendar.py`, `tests/test_calendar.py`.

**Blocked on the user:** a Composio **project** key (`ak_…`) as `COMPOSIO_API_KEY` in `.env`. The auth config
`ac_aze6I2N0XYM_` already exists (managed Google Calendar, scope requested `calendar.freebusy`). Unit tests do not
need the key; the live check does. If the key is missing at run time, `CalendarLinker` is not created and the bot
hides the calendar button.

**Interfaces — Produces:**
```python
class CalendarLinker:
    def __init__(self, composio: Composio, auth_config_id: str, callback_url: str) -> None
    def connect_url(self, member_id: str) -> str | None
    def is_connected(self, member_id: str) -> bool
    def busy_blocks(self, member_id: str, start: datetime, end: datetime, tz: ZoneInfo) -> list[BusyBlock] | None
    def disconnect(self, member_id: str) -> None
def composio_user_id(member_id: str) -> str    # f"discord:{member_id}"
```
- `connect_url`: `composio.connected_accounts.link(composio_user_id(id), auth_config_id, callback_url=callback_url)
  .redirect_url`; `ComposioMultipleConnectedAccountsError` (already connected) → None.
- `is_connected`: `composio.connected_accounts.list(user_ids=[…], toolkit_slugs=["googlecalendar"],
  statuses=["ACTIVE"])` has ≥ 1 item.
- `busy_blocks`: `composio.tools.execute("GOOGLECALENDAR_FIND_FREE_SLOTS", {"items": ["primary"], "time_min":
  start.isoformat(), "time_max": end.isoformat(), "timezone": tz.key}, user_id=…,
  dangerously_skip_version_check=True)`; read `result["data"]["calendars"][*]["busy"]` (each `{start, end}` ISO) into
  BusyBlocks; any exception, `successful` false, or no connection → None. Never read or store event titles.
- `disconnect`: delete every connected account for that user id (used by `/squad leave`).
- The SDK is synchronous; callers wrap calls in `asyncio.to_thread`.

- [ ] **Step 1: Failing tests** with a stub composio object: `test_connect_url_returns_redirect`;
  `test_already_connected_returns_none`; `test_busy_blocks_parses_nested_calendars`;
  `test_busy_blocks_none_on_failure` (`successful=False` and raised exception); `test_execute_arguments_exact`
  (records slug and arguments; asserts `items == ["primary"]` and timezone `"America/Phoenix"`).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: google calendar busy blocks via composio`.
- **Live check (verifier, needs `ak_` key):** print `connect_url("verifier-test")` (a `https://` URL), then
  `busy_blocks("verifier-test", …)` is None; then `disconnect("verifier-test")`.

---

### Task 6: Discord UI (cards, onboarding forms)

**Files:** Create `squad/ui/__init__.py`, `squad/ui/cards.py`, `squad/ui/onboarding.py`, `scripts/preview_cards.py`,
`tests/test_cards.py`, `tests/test_onboarding.py`.

**Interfaces — Produces:**

`ui/cards.py` (Components V2, `ui.LayoutView(timeout=None)`, one `ui.Container(accent_colour=discord.Colour(BRAND))`):
- `plan_card(plan: Plan, names: dict[str, str], tz: ZoneInfo) -> ui.LayoutView` — TextDisplays in order:
  `"## 🗺️ This week's side quest"`, `f"### {event.title}"`, `f"🕖 <t:{unix}:F> · <t:{unix}:R>"`,
  `f"📍 {location}"` (+ `f" · ${price:g}"` when price > 0, `" · free food 🍕"` when free_food),
  `f"_{plan.headline}_"`, `plan.why`, then `"**Trade-offs**\n" + "\n".join("• " + t)` if any, then a Separator, then
  `who_line(plan, names)`. ActionRow buttons: link "Event page" (if url), `ui.DynamicItem` buttons
  `CloseButton(plan.id)` "Close poll now" (secondary) and `WhyButton(plan.id)` "How did you pick this?" (secondary).
- `who_line(plan, names) -> str` — `"✅ " + ", ".join(yes) + "  🤔 " + … + "  ❌ " + …`, omitting empty groups;
  `"Nobody's voted yet, no pressure 🙂"` when empty. No-voters appear only as a count: `"❌ 1 can't make it"`.
- `results_card(plan: Plan, names: dict[str, str], rides: Rides, tz) -> ui.LayoutView` — `"## 🎉 It's on"`, title,
  time, location, `"**Going:** " + names`, `"**Rides**"` with one line per car `"🚗 {driver} → {riders or 'driving
  solo'}"`, then `f"🚆 {', '.join(transit names)}: {transit_tip}"` when non-empty, then `f"📅 [Discord event]({url})"`
  when set.
- `no_plan_card(reason: str, near_miss: Event | None, tz) -> ui.LayoutView` — `"## 🌙 No side quest this week"`, the
  reason, and the near-miss title/time if given.
- Dynamic items (custom ids, regex templates): `CloseButton` `squad:close:(?P<plan>\w+)`, `WhyButton`
  `squad:why:(?P<plan>\w+)`, `ConfirmButton` `squad:confirm:(?P<plan>\w+):(?P<answer>yes|no)`, `WhyNoButton`
  `squad:whyno:(?P<plan>\w+)`, `Step2Button` `squad:step2`. Each item's `callback` awaits a coroutine on the client:
  `close_poll(interaction, plan_id)`, `explain(interaction, plan_id)`, `confirm(interaction, plan_id, answer)`,
  `why_no(interaction, plan_id)`, `open_step2(interaction)`, all looked up as `interaction.client.flows.<name>`.
  (Flows are attached in Tasks 11–13 with exactly these signatures; `answer` is `"yes"` or `"no"`.)
- `confirm_view(plan_id: str) -> ui.LayoutView` — container with TextDisplay placeholder text set by caller (arg
  `text: str`), and ConfirmButton yes ("Sure, count me in") / no ("Pass on this one").
- `why_no_view(plan_id: str) -> ui.LayoutView` — "Mind sharing why? Totally optional, it just helps me pick better
  next time." + WhyNoButton "Tell you why" + a plain button "Skip" that edits the message to "No worries 🙂".

`ui/onboarding.py`:
- `class JoinModal(ui.Modal, title="Join the squad (1/2)")` with five `ui.Label`s:
  1. "What are you into?" → `ui.CheckboxGroup(options=[CheckboxGroupOption(label, key) for INTERESTS], min_values=1,
     max_values=10)`
  2. "When are you usually free?" → CheckboxGroup over `FREE_SLOTS`, min 1, max 6
  3. "Budget per hangout" → `ui.RadioGroup` over `BUDGETS`
  4. "Hard no's" (description "Optional") → CheckboxGroup over `NO_GO`, `required=False`, min 0, max 7
  5. "Do you drive?" → RadioGroup over `SEATS`
  Pre-filled from an existing member when re-joining (set `default` on options). `on_submit` calls
  `interaction.client.flows.join_submitted(interaction, values: JoinValues)`.
- `class CallsModal(ui.Modal, title="Join the squad (2/2)")` with Labels: "WhatsApp number" → `ui.TextInput(
  required=False, placeholder="+1 480 555 0123", max_length=20)`; "Voice nudge" (description "One friendly call if
  you miss a plan poll") → `ui.Checkbox()`; "Quiet hours" → RadioGroup over `QUIET_HOURS`. `on_submit` →
  `flows.calls_submitted(interaction, values: CallsValues)`.
- `@dataclass JoinValues(interests: list[str], free_slots: list[str], budget_key: str, no_go: list[str],
  seats_key: str)`; `@dataclass CallsValues(phone_raw: str, call_opt_in: bool, quiet_key: str)`.
- `def member_from_join(member_id: str, name: str, avatar_url: str, v: JoinValues, existing: Member | None) ->
  Member` — keeps existing phone/opt-in/quiet/learned filters.
- `def apply_calls(member: Member, v: CallsValues) -> Member` — normalises phone to `+<digits>` (US 10-digit gets
  `+1`); raises `ValueError("phone")` when the digit count is not 10–15 or the raw text has letters; empty phone →
  `phone=""`, `call_opt_in=False`.

`scripts/preview_cards.py`: logs in with `DISCORD_TOKEN`, finds or creates the public thread "🔧 dev previews" in
`settings.dev_channel_id`, sends `plan_card`, `results_card`, `no_plan_card` built from `tests/fakes.py` factories,
then closes. Usage: `uv run python scripts/preview_cards.py`.

- [ ] **Step 1: Failing tests:** `test_plan_card_contains_title_time_and_buttons` (walk `view.walk_children()`:
  TextDisplay texts include title and `<t:`; custom ids include `squad:close:<id>`); `test_who_line_hides_no_names`;
  `test_results_card_rides_lines`; `test_member_from_join_keeps_phone`; `test_apply_calls_normalises_us_number`
  (`"(480) 555-0123"` → `"+14805550123"`); `test_apply_calls_rejects_letters_and_short`; `test_apply_calls_empty_turns_off_calls`;
  `test_join_modal_has_five_labels`.
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: plan cards and sign-up forms`.
- **Live check (verifier):** run `scripts/preview_cards.py`; confirm via REST
  (`GET /channels/<thread>/messages?limit=3`) that three messages with `flags & 32768` (IS_COMPONENTS_V2) exist.

---

### Task 7: Demo personas

**Files:** Create `squad/personas.py`, `tests/test_personas.py`.

**Interfaces — Produces:**
- `PERSONAS: list[Member]` exactly:
  - `demo:maya` "Maya" — interests music, arts, food; slots fri_night, sat_night, sun_day; budget 20; no_go sports;
    seats 0
  - `demo:jordan` "Jordan" — sports, gaming, food; weeknights, sat_day, fri_night; budget 10; no_go late; seats 3
  - `demo:priya` "Priya" — tech, food, chill; all six slots; budget 0; no_go parties, alcohol; seats 0
  - `demo:leo` "Leo" — outdoors, chill, music; sat_day, sat_night, sun_day, fri_night; budget 40; seats 1
  - `avatar_url = f"https://api.dicebear.com/9.x/notionists/png?seed={name}&size=128"`, `is_demo=True`.
- `def persona_busy(member: Member, week_of: datetime, tz) -> list[BusyBlock]` — relative to the Monday of
  `week_of`: Leo busy Friday 18:00–21:00; Maya busy Saturday 12:00–16:00; Jordan, Priya none. Personas always use
  these blocks (never `free_slots`) so they behave like calendar-connected members.
- `INTRO_LINES: dict[str, str]` — Maya "hii, Maya here 🎨 down for anything with music or art", Jordan "Jordan.
  I'll drive if it's not a late one 🚗", Priya "Priya! free stuff only pls, I'm a broke CS major 💻", Leo "Leo 🌵
  outdoorsy, will go anywhere with snacks".
- `DEMO_VOTES: dict[str, tuple[int, str, str | None]]` — index into `settings.persona_vote_delays_s`, vote key,
  reason: maya `(0, "yes", None)`, priya `(1, "yes", None)`, leo `(2, "maybe", None)`, jordan `(3, "no", "I've got
  an 8am shift Saturday, nothing after 9 on Fridays for me")`.
- `async def post_as(webhook: discord.Webhook, name: str, avatar_url: str, text: str, thread: discord.abc.Snowflake |
  None = None) -> None` — `webhook.send(text, username=name, avatar_url=avatar_url, thread=thread or MISSING,
  allowed_mentions=discord.AllowedMentions.none())`.

- [ ] **Step 1: Failing tests:** `test_four_personas_ids_and_seats`; `test_persona_busy_is_relative_to_week`;
  `test_demo_votes_cover_every_persona`; `test_post_as_passes_username_and_no_mentions` (stub webhook records kwargs).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: demo personas`.

---

### Task 8: `wa-voice` Rust sidecar (WhatsApp calls)

**Files:** Create `wa-voice/Cargo.toml`, `wa-voice/src/main.rs`, `wa-voice/src/audio.rs`, `wa-voice/README.md`.

**Decisions:** depend on `whatsapp-rust = { git = "https://github.com/oxidezap/whatsapp-rust", branch = "main",
features = ["sqlite-storage", "tokio-transport", "ureq-client", "tokio-native", <the voip, relay and voip-mlow
features exactly as enabled in that repo's examples/voip-cli/Cargo.toml>] }` and `wacore` from the same git
source; plus `tokio` (full), `axum` (with `ws`), `serde`/`serde_json`, `async-channel`, `anyhow`, `log`,
`env_logger`. Copy the startup and `place_outgoing_call` pattern from `examples/voip-cli/src/main.rs`
(`Bot::builder().with_backend(SqliteStore::open("data/wa-voice.db"))…`, `client.voip().call(&jid).audio(mic_rx,
speaker_tx).start()`), with `mic_rx: async_channel::Receiver<Vec<i16>>` and `speaker_tx:
async_channel::Sender<Vec<i16>>` fed from the WebSocket instead of cpal. 16 kHz mono, 960-sample frames.

**HTTP contract (listen `127.0.0.1:8091`):**
- `GET /status` → `{"paired": bool, "connected": bool, "busy": bool}`
- `POST /call` body `{"phone": "+14805550123"}` → `200 {"call_id": "…"}`; `409` when a call is active; `503` when
  not connected; `400` for a phone that is not `+` and 10–15 digits. JID = `<digits>@s.whatsapp.net`.
- `GET /audio/<call_id>` upgrades to WebSocket. Client → sidecar binary frames: PCM16LE mono 16 kHz the callee
  hears (any length; `audio.rs` re-chunks to 960 samples). Sidecar → client binary frames: PCM16LE mono 16 kHz from
  the callee. Text frames: client `{"cmd":"hangup"}` ends the call; sidecar sends `{"event":"answered"}`,
  `{"event":"ended","reason":"…"}`.
- Pairing: on first start log the QR string and write it to `data/wa-qr.txt`; delete that file once paired.

**Interfaces — Produces (`audio.rs`):** `pub fn bytes_to_frames(buf: &mut Vec<u8>, frame: usize) -> Vec<Vec<i16>>`
(drains whole frames, keeps the remainder), `pub fn frame_to_bytes(frame: &[i16]) -> Vec<u8>`.

- [ ] **Step 1: Failing Rust tests** in `audio.rs`: `chunks_and_keeps_remainder` (2 000 bytes → one 960-sample frame,
  80 bytes left), `roundtrip_little_endian`.
- [ ] **Step 2:** `cargo test` → FAIL; implement `audio.rs`; → PASS.
- [ ] **Step 3:** implement `main.rs`; `cargo build --release` and `cargo clippy -- -D warnings` clean.
- [ ] **Step 4:** commit `feat: wa-voice sidecar for whatsapp calls`.
- **Live check (only when the user has supplied the WhatsApp number and said go):** run the binary, user scans the
  QR from `data/wa-qr.txt` (render with `qrencode -t ansiutf8 < data/wa-qr.txt`), then `curl -XPOST
  127.0.0.1:8091/call -d '{"phone":"<user phone>"}'` rings the user's phone; a WebSocket client that sends 2 s of a
  440 Hz tone is heard. If a PN JID is rejected ("must be LID"), resolve the LID through the client's usync lookup
  before calling and note it in `docs/decisions.md`.

---

### Task 9: Voice bridge (sidecar ↔ Gemini Live)

**Files:** Create `squad/voice/__init__.py`, `squad/voice/resample.py`, `squad/voice/bridge.py`,
`tests/test_resample.py`, `tests/test_bridge.py`.

**Interfaces — Produces:**
- `resample.pcm16_24k_to_16k(data: bytes, carry: bytes = b"") -> tuple[bytes, bytes]` — linear interpolation 3→2
  samples using the stdlib `array` module; returns (output, leftover bytes to pass next time).
- `class CallOutcome(BaseModel): answered: bool; answer: Literal["yes", "maybe", "no"] | None = None; reason: str =
  ""; seconds: float = 0.0`
- `async def nudge_call(settings: Settings, phone: str, name: str, plan: Plan, going_names: list[str], *,
  genai_client=None, ws_connect=None) -> CallOutcome` —
  1. `POST {wa_voice_url}/call`; non-200 → `CallOutcome(answered=False)`.
  2. Open the audio WebSocket (`aiohttp`), and `client.aio.live.connect(model="gemini-3.8-live",
     config={"response_modalities": ["AUDIO"], "system_instruction": VOICE_SYSTEM.format(...), "tools":
     [{"function_declarations": [RECORD_ANSWER]}]})`.
  3. Pump callee audio → `session.send_realtime_input(audio=types.Blob(data=…, mime_type="audio/pcm;rate=16000"))`;
     model audio (`response.data`, 24 kHz) → `pcm16_24k_to_16k` → WebSocket.
  4. On tool call `record_answer(answer, reason)` → store, reply `{"result": "ok"}`, let the model say goodbye, then
     hang up 3 s after its turn completes.
  5. Hard stop at 90 s or on `{"event":"ended"}`; always send `{"cmd":"hangup"}` in `finally`.
- `VOICE_SYSTEM` (exact copy): "You're calling {name} for their friend group's Side Quests squad. They haven't
  answered the poll yet. The plan: {title}, {when}, at {location}. Already going: {going}. Say hi, say it's the squad
  bot calling, give the plan in one sentence, and ask if they're in. Be warm and brief, like a friend, never pushy.
  If they say yes, maybe or no, call record_answer. If they give a reason, include it. Then say a short goodbye. Keep
  the whole call under a minute."
- `RECORD_ANSWER = {"name": "record_answer", "description": "Save their answer to the poll", "parameters": {"type":
  "object", "properties": {"answer": {"type": "string", "enum": ["yes", "maybe", "no"]}, "reason": {"type":
  "string"}}, "required": ["answer"]}}`

- [ ] **Step 1: Failing tests:** `test_resample_length_ratio` (2 400 samples in → 1 600 out);
  `test_resample_carry_between_chunks` (split input equals whole input); `test_nudge_call_records_answer` (fake
  sidecar via `aiohttp.test_utils.TestServer` + fake genai session that emits one audio chunk then a `record_answer`
  tool call; outcome `answered=True, answer="yes"`; the fake sidecar received a hangup);
  `test_nudge_call_sidecar_busy_returns_unanswered` (409); `test_nudge_call_times_out` (patch the 90 s limit to 0.2 s).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: gemini live voice bridge`.
- **Live check (verifier):** with a fake sidecar that plays `say -o hi.aiff "hey, sure, I'm in" && afconvert -f WAVE
  -d LEI16@16000 -c 1 hi.aiff hi.wav` audio, `nudge_call` against the real Gemini API returns `answered=True` and
  `answer="yes"`.

---

### Task 10: Planner

**Files:** Create `squad/planner.py`, `tests/test_planner.py`.

**Interfaces:**
- Consumes: Task 0 `matching.interest_score`, Task 2 `violations_for`, `request_allows`, Task 4 `member_stances`,
  `coordinate`, and the output models `StancesOut`, `DecisionOut` from `squad.agents` (for FakeLLM queues in tests).
- Produces:
  - `def pick_candidates(members: list[Member], events: list[Event], busy: dict[str, list[BusyBlock] | None],
    request: Request, tz, exclude: set[str]) -> list[tuple[Event, list[Violation]]]` — drop excluded ids and events
    failing `request_allows`; sort by (number of members with ≥1 violation, -sum `matching.interest_score`, start); top
    `CANDIDATES_K`.
  - `async def build_plan(*, members: list[Member], events: list[Event], busy: dict[str, list[BusyBlock] | None],
    request: Request, llm: LLM, now: datetime, channel_id: str, tz, exclude: set[str] = frozenset()) -> Plan | NoPlan`
    — no members → `NoPlan("Nobody's in the squad yet. Try /squad join or /squad demo.")`; no candidates →
    `NoPlan("Nothing on Sun Devil Central fits this week.", near_miss=None)`; else stances for every member in
    parallel (`asyncio.gather`), `coordinate`, then build the Plan: `id = uuid4().hex[:10]`, `ask_first` = ids of
    members with violations on the chosen event (computed in code, never by the model), `turns` = one AgentTurn per
    member `f"{name}'s agent"` with that member's `shared_reason` for the chosen event (skip empty) plus a final
    `AgentTurn("Coordinator", None, why)`; status `"confirming"` if `ask_first` else `"polling"`.
- Busy for personas comes from `persona_busy`; the caller (Task 12) assembles `busy`.

- [ ] **Step 1: Failing tests** (FakeLLM queued with StancesOut/DecisionOut): `test_no_members_no_plan`;
  `test_everyone_fits_status_polling`; `test_conflict_sets_ask_first_from_code_not_model` (model picks event with
  budget violation for u2; ask_first == ["u2"]); `test_exclude_skips_declined_event`;
  `test_llm_down_still_plans` (FakeLLM raises for every call → Plan with fallback headline);
  `test_turns_never_contain_private_detail` (no turn text contains "cap" or "$").
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: planner with conflict handling`.

---

### Task 11: Bot core (client, sign-up, leave, demo)

**Files:** Create `squad/bot.py`, `squad/flows/__init__.py`, `tests/test_bot_core.py`.

**Interfaces — Produces:**
```python
class Flows:   # attribute bag; Tasks 12–14 add methods via their setup()
    ...
class SquadBot(discord.Client):
    settings: Settings; store: Store; llm: LLM; calendar: CalendarLinker | None; flows: Flows
    tree: app_commands.CommandTree
    def __init__(self, settings: Settings, store: Store, llm: LLM, calendar: CalendarLinker | None) -> None
    async def setup_hook(self) -> None   # load store, add DynamicItems, register command group, call flows setups, sync
    async def squad_for(self, channel: discord.abc.Messageable) -> Squad   # get or create for this channel
    async def webhook_for(self, squad: Squad, channel: discord.TextChannel) -> discord.Webhook  # create "Squad Mode" once, store url
    async def dm(self, user_id: str, *, content: str | None = None, view: ui.LayoutView | None = None) -> bool  # False on Forbidden/NotFound
```
- Intents: `default()` + `message_content=True` + `polls=True`. `allowed_mentions` default: users only.
- Slash group `/squad` (guild + DM contexts, `@app_commands.allowed_installs(guilds=True, users=True)`):
  - `join` → `JoinModal` (pre-filled). `flows.join_submitted` saves the member, adds them to this channel's Squad,
    replies ephemeral: "You're in 🎉 One more step:" + Step2Button "Calls & quiet hours" + link button "Connect Google
    Calendar" (only when `calendar` exists and `connect_url` returns a URL) + text "No calendar? I'll use the free
    times you ticked."
  - `flows.open_step2` → `CallsModal`; `flows.calls_submitted` → `apply_calls`; ValueError → ephemeral "That number
    doesn't look right. Try something like +1 480 555 0123." and nothing saved; else save, ephemeral "Saved ✨".
  - `leave` → `store.delete_member`, `calendar.disconnect` (thread), ephemeral "Done. I forgot everything about you
    (calendar link too). Come back anytime with /squad join."
  - `demo` → adds the four PERSONAS to the store and to this Squad, posts each `INTRO_LINES` via `post_as`, replies
    ephemeral "Your demo squad is here: Maya, Jordan, Priya and Leo. Try /squad plan."
  - `plan vibe:<optional str, multiline>` → `flows.plan_requested_from_interaction(interaction, vibe or "")`.
  - `weekly day:<Choice Mon–Sun> hour:<int 8–21>` → saves `weekly_weekday`, `weekly_hour`; ephemeral confirmation
    with the next run as `<t:…:F>`.
- `on_message`: ignore bots and webhooks; if the bot is mentioned → `flows.plan_requested(message, text)` (text with
  the mention removed). Everything else is read and not stored (we keep no chat logs).
- Context menu "Plan this" (message) → `flows.plan_requested_from_interaction(interaction, message.content)`.

- [ ] **Step 1: Failing tests** (call the flow functions directly with stub interactions/users; no gateway):
  `test_join_submitted_creates_member_and_adds_to_squad`; `test_calls_submitted_bad_phone_saves_nothing`;
  `test_leave_deletes_member_and_calendar`; `test_demo_adds_four_personas_once` (running twice doesn't duplicate);
  `test_dm_returns_false_on_forbidden`.
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: bot core, sign-up and demo squad`.

---

### Task 12: Plan flow (manual, weekly, confirmation, card, thread, poll)

**Files:** Create `squad/flows/plan_flow.py`, `tests/test_plan_flow.py`.

**Interfaces — Produces** `def setup(bot: SquadBot) -> None` adding to `bot.flows`: `plan_requested(message,
text)`, `plan_requested_from_interaction(interaction, text)`, `confirm(interaction, plan_id, answer)`,
`explain(interaction, plan_id)`, `run_plan(squad, channel, request)`, and starting `weekly_loop`
(`discord.ext.tasks.loop(minutes=1)`).

Flow `run_plan(squad, channel, request) -> None` (shared by all triggers):
1. Reply/typing: "On it 🗺️ checking Sun Devil Central and everyone's week…".
2. `upcoming_events`; `EventsUnavailable` → reply "Sun Devil Central isn't answering right now. I'll try again in a
   bit 🌵" and stop.
3. Members = `store.members(squad.member_ids)`; busy per member: personas → `persona_busy`; humans → `await
   to_thread(calendar.busy_blocks, …)` over `[now, now + 7 days]` when `calendar` exists, else None.
4. `build_plan`. `NoPlan` → post `no_plan_card`, stop.
5. While `plan.ask_first` not empty and rounds < `MAX_ROUNDS`: for each id in `ask_first`, a persona answers yes
   unless one of its violations on that event has kind `late` or `no_go` (then no); queue a thread line for after
   the card is posted: `f"{name}'s agent checked with {name} privately: {'all good' if yes else 'not this one'}."`;
   humans get a DM: `confirm_view` text `f"Quick check before I post this week's plan: {title}, <t:…:F>. Heads up:
   {detail_private}. Still up for it?"`. Wait for every answer or `settings.confirm_timeout_s`; no answer or DM
   failure = no. Any no → add event to `declined_event_ids`, rebuild with `exclude`. After `MAX_ROUNDS` → `no_plan_card`
   with the last plan's event as near miss.
6. Post `plan_card` in the channel; create a public thread on it named `f"🗺️ {title[:80]}"`; post each `AgentTurn`
   in the thread through the squad webhook (`post_as`, username = speaker, avatar = member avatar, or the bot's
   avatar for "Coordinator"); post the native poll **in the channel** right below the card: `discord.Poll(question=f"{title[:250]}, you in?", duration=timedelta(hours=squad.poll_hours))` with
   `VOTE_ANSWERS`. Save `message_id`, `thread_id`, `poll_message_id`, `poll_closes_at`, status `"polling"`.
7. Start persona votes (Task 13 owns `schedule_persona_votes(plan)`; call it if `bot.flows` has it).
- `explain` → ephemeral: `plan.why` + "**What each agent said**" + turns (no private details exist in turns).
- `weekly_loop`: for each Squad whose local weekday/hour equals now and `last_weekly_date != today` → set
  `last_weekly_date`, `run_plan(squad, channel, Request())`.
- Manual triggers: `parse_request(llm, text, now)` first.

- [ ] **Step 1: Failing tests** (stub channel/thread/webhook objects recording sends; FakeLLM; monkeypatched
  `upcoming_events`): `test_feed_down_posts_friendly_message`; `test_happy_path_posts_card_thread_turns_and_poll`
  (poll has 3 answers in `VOTE_ANSWERS` order, duration 1 h); `test_conflict_dm_yes_then_posts`;
  `test_conflict_dm_forbidden_counts_as_no_and_replans`; `test_three_declines_posts_no_plan`;
  `test_weekly_loop_runs_once_per_day`; `test_card_and_turns_have_no_private_detail`.
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: plan flow with consent and poll`.

---

### Task 13: Vote flow (votes, persona votes, why-no, closing, rides, Discord event)

**Files:** Create `squad/flows/vote_flow.py`, `tests/test_vote_flow.py`.

**Interfaces — Produces** `def setup(bot)` adding: `on_raw_poll_vote_add` / `on_raw_poll_vote_remove` listeners,
`schedule_persona_votes(plan)`, `why_no(interaction, plan_id)`, `close_poll(interaction, plan_id)`, `finish(plan)`,
and `closer_loop` (`tasks.loop(seconds=30)`: plans with status polling and `poll_closes_at <= now` → `finish(plan)`).
- Vote add: map `answer_id` 1/2/3 → `VOTE_KEYS`; set `plan.votes[user_id]`; edit the card (`who_line`). If "no",
  the voter is a squad member, and not in `why_no_asked` → DM `why_no_view`; append to `why_no_asked`. Vote remove →
  delete `plan.votes[user_id]`, edit card.
- Persona votes: `asyncio.sleep(settings.persona_vote_delays_s[i])` per `DEMO_VOTES`, set vote, edit card, post in
  the thread via webhook as the persona: yes "count me in 🙌", maybe "probably! will confirm tonight", no "can't
  this time 😔". For Jordan's no, also post as "Jordan's agent": `f"Jordan shared why privately. I'll remember: no
  events after 9pm on Fridays."` and save the LearnedFilter from `learn_from_no` (skip the post if it returns None).
- `why_no` → modal "Why not this time?" one paragraph TextInput (optional, 300 chars) → `learn_from_no` → append to
  the member's `learned_filters` → ephemeral "Got it, I'll keep that in mind 🙏" (or "Thanks for telling me 🙏" when
  None). Never posted publicly.
- `close_poll` (button): only the plan's channel members may close; call `poll_message.poll.end()` (discord.py
  `Poll.end`) then `finish(plan)`.
- `finish(plan)`: idempotent (return if status closed); `going` = members with yes (personas included); `rides =
  plan_rides(going, event.location)`; create the Discord scheduled event (`guild.create_scheduled_event(name=title[:100],
  start_time=event.start, end_time=event.end, entity_type=discord.EntityType.external, location=location[:100],
  privacy_level=discord.PrivacyLevel.guild_only, description=f"{why}\n{url}"[:1000])`; on `Forbidden` skip) and save
  its URL; post `results_card` in the thread and the channel; status `"closed"`. Nobody going → "Nobody could make it
  this time. Totally fine, there's always next week 🌙".

- [ ] **Step 1: Failing tests:** `test_vote_add_updates_card_and_dms_no_once`; `test_vote_by_non_member_counts_no_dm`;
  `test_vote_remove`; `test_persona_votes_and_jordan_learned_filter` (delays patched to 0);
  `test_why_no_saves_filter_privately`; `test_finish_creates_event_and_rides_once` (called twice → one event);
  `test_finish_event_forbidden_still_posts_results`; `test_nobody_going_message`.
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: votes, why-no memory, rides and event`.

---

### Task 14: Nudge flow

**Files:** Create `squad/flows/nudge_flow.py`, `tests/test_nudge_flow.py`.

**Interfaces — Produces** `def setup(bot)` starting `nudge_loop` (`tasks.loop(seconds=30)`) and adding
`nudge_due(plan, now) -> list[Member]`.
- `nudge_due`: plan status polling, `now >= created_at + settings.nudge_after_s`, member in squad, not in
  `plan.votes`, not in `plan.nudged`, not a persona, not `in_quiet_hours(member, now)`.
- For each due member (append to `nudged` first, so it happens at most once per plan):
  - `call_opt_in` and `phone` and `settings.wa_voice_url` and `GET /status` says connected → `nudge_call(...)`; if
    `answered` and `answer` → set `plan.votes[member.id]`, edit the card, post in the thread "📞 {name} picked up and
    said {answer}" (reason never posted).
  - otherwise (or the call was not answered) → DM: `f"Hey {name} 👋 the squad's planning {title} <t:…:R>. You in?
    The poll's in #{channel}."`; DM failure → one channel message `f"<@{id}> psst, there's a poll waiting for you 🗺️"`.

- [ ] **Step 1: Failing tests:** `test_due_skips_voted_personas_quiet_and_already_nudged`;
  `test_nudge_once_per_plan`; `test_call_answer_sets_vote_and_posts_without_reason`;
  `test_voice_off_falls_back_to_dm`; `test_dm_forbidden_falls_back_to_channel_mention`.
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: nudges by whatsapp call or dm`.

---

### Task 15: Web server, entry point and project site

**Files:** Create `squad/web.py`, `squad/site/index.html`, `squad/__main__.py`, `tests/test_web.py`.

**Interfaces — Produces:**
- `def make_app(settings: Settings) -> aiohttp.web.Application` with `GET /` (serves `site/index.html`), `GET
  /health` → `{"ok": true}`, `GET /calendar/done` → small HTML page "Calendar connected ✨ You can close this tab and
  head back to Discord." (the Composio `callback_url` is `f"{public_url}/calendar/done"`).
- `__main__`: `python -m squad` loads settings, builds `Store`, `LLM(AsyncAnthropic(api_key=…))`, `CalendarLinker`
  only when `composio_api_key` is set, `SquadBot`, starts `make_app` on `web_port` with `aiohttp.web.AppRunner`,
  then `bot.start(token)`. `python -m squad --check` validates settings (required keys non-empty), imports every
  module, prints `ok`, exits 0 without network.
- `site/index.html`: one self-contained page (inline CSS, no external JS) in the Track 1 README tone: title "Side
  Quests: Squad Mode", one-liner, a `<video>`/YouTube embed placeholder `<!-- DEMO_VIDEO -->`, "Add to Discord"
  button linking to `https://discord.com/oauth2/authorize?client_id=1563800334231670835`, GitHub link, three short
  "how it works" cards (agents per friend · asks before breaking a limit · calls the friend who forgot). Works at 375 px.

- [ ] **Step 1: Failing tests:** `test_health`; `test_calendar_done_page`; `test_index_has_install_link`;
  `test_check_mode_exits_zero` (subprocess with dummy env vars).
- [ ] **Step 2–4:** fail → implement → pass. **Step 5:** ruff; commit `feat: web server, entry point and site`.

---

### Task 16: Live end-to-end and deploy

**Files:** Create `scripts/smoke_live.py`; modify nothing else unless a bug is found (fix it in the owning module
with a regression test).

- [ ] **Step 1:** `scripts/smoke_live.py` (logged-in `SquadBot` with `DEMO_FAST=1`, against `dev_channel_id`):
  seed the demo personas into that channel's Squad, call `run_plan` directly with `Request()`, wait for persona
  votes, call `finish`, then assert via REST: a components-v2 card, a thread with ≥ 4 webhook messages, a poll message
  with 3 answers, a results message, and a guild scheduled event. Print every message link.
- [ ] **Step 2:** start the bot locally (`DEMO_FAST=1 uv run python -m squad`) in the background; the user does the
  manual checklist in `#general`: `/squad join` (both forms, calendar link opens and comes back to
  `/calendar/done`), `/squad demo`, `@Side Quests Squad something chill Friday under $15`, vote "Can't make it" and
  answer the DM, press "Close poll now", see rides and the Discord event, `/squad leave`. Record results in
  `docs/decisions.md` under "E2E <date>".
- [ ] **Step 3 (ask the user first):** deploy to openclaw: install uv for user `ubuntu`, `git clone` (or rsync) to
  `~/squad`, copy `.env` with `PUBLIC_URL=https://squad.ashwanthbk.com`, systemd unit `squad.service`
  (`ExecStart=/home/ubuntu/.local/bin/uv run python -m squad`, `Restart=always`), Cloudflare DNS `A squad →
  129.146.181.140` (DNS only, like the other subdomains), Caddy site block `squad.ashwanthbk.com { reverse_proxy
  host.docker.internal:8090 }` (check how the existing Caddy container reaches host services first and copy that
  pattern), reload Caddy. Verify `curl https://squad.ashwanthbk.com/health`.
- [ ] **Step 4 (when the user provides WhatsApp creds and says go):** build `wa-voice` on openclaw (`cargo build
  --release`; install rustup there after asking), second systemd unit `wa-voice.service`, pair via QR, then the
  Task 8 live check and one real nudge on the user's phone.

---

### Task 17: README, DEMO script, project CLAUDE.md

**Files:** Create `README.md`, `DEMO.md`, `CLAUDE.md` (gitignored), `docs/assets/hero.svg`,
`docs/assets/chat-demo.svg`.

- README sections, soft playful tone like the Track 1 repo ("your group chat says 'we should hang out' every week…
  let's actually go"): hero SVG (animated, dark-mode safe, like Track 1), one-liner, 30-second demo video link, "How
  it works" (diagram of member agents → coordinator → poll → why-no memory → rides → call), "What agents share and
  what stays private" table, "When it asks you first" (the consent rule), setup (Discord app, `.env.example`, Composio
  key, `uv run python -m squad`, optional `wa-voice`), privacy (busy blocks only, no chat logs, `/squad leave`
  forgets everything; Composio's consent screen asks for broader calendar access than the bot uses), tests (`uv run
  pytest`, exact count), tech stack, Track 1 link (https://github.com/ashwanthbalakrishnan5/cubbie-side-quest).
- `DEMO.md`: a 2:30 shot list for the recorded video: 0:00 hook · 0:15 `/squad demo` + join form · 0:45 `@bot
  something chill Friday under $15` · 1:05 thread with agents arguing + private consent DM · 1:30 poll + persona votes
  + "why no" DM · 1:55 close poll → rides + Discord event · 2:10 WhatsApp call on the Mac app (screen-record with
  system audio) · 2:25 outro. Include exact commands, `DEMO_FAST=1`, and which windows to have open.
- `CLAUDE.md`: concise project notes (run, test, lint, layout, decisions file, deploy, never-commit rules).
- Verify every README claim (test count, commands) against the repo; ruff clean; commit `docs: readme and demo
  script`.

---

### Task 18: Submission draft (no sending)

- [ ] Ask the user before creating the public GitHub repo `cubbie-side-quest-squad` and pushing.
- [ ] Prepare the Track 3 entry with the kit script `python3 <kit>/skills/cubbie-hackathon/scripts/hackathon.py
  submit --track groupchat …` **preview only**: one-liner "Your group chat says 'we should hang out' every week.
  Squad Mode picks the night, the event and the ride, then calls the friend who didn't answer.", repo URL, website
  `https://squad.ashwanthbk.com`, video URL from the user. Show the preview; send with `--yes` only after the user's
  explicit yes.
