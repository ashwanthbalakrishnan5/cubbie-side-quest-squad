# Side Quests: Squad Mode — build plan

Track 3 (Group Chat Assistant, kit track id `groupchat`). Track 1 gets you out; Squad Mode gets your friends out together.

## What it is
A Discord bot you add to your friend group's server. It reads the chat, talks only when @-mentioned, and once a week
proposes one real ASU event the whole squad can make, with a native poll.

## How it works
- **Join (DM):** `/squad join` opens a short DM setup: interests, budget cap, no-go types, usual free times, car + seats,
  optional phone (for the voice nudge), and a "Connect calendar" link.
- **Calendars (via Composio):** the bot makes a Composio Connect Link per member
  (`composio.connected_accounts.link(user_id=<discord id>, auth_config_id=<googlecalendar>)`) and sends it in a private
  reply. It only ever calls `GOOGLECALENDAR_FIND_FREE_SLOTS` and keeps busy blocks, never event titles. Composio's
  managed Google app asks for broader calendar access than free/busy; the README says so. No calendar? The free times
  typed during setup are used instead.
- **Agents:** one member agent per person holds that person's private profile. The coordinator never sees the
  profile, only what each agent chooses to share:
  - hard constraints (busy windows, budget cap, no-go types) → used to filter events in code (deterministic, tested);
  - a 0–10 score plus one-line reason for each surviving event (Claude call per member, run in parallel).
  - The coordinator (Claude) picks the plan with the best group score and writes the trade-offs in public
    ("Maya would rather do something outdoorsy, but this is the only slot that works for all 5").
  - **Conflicts:** if nothing fits everyone, the coordinator picks the option that breaks the fewest hard
    constraints, and that member's agent asks them privately first ("It's $20 and your cap is $15, ok just this once?").
    The public post never says whose constraint it was.
- **Weekly plan:** a scheduled job (day/time set per server) searches events via the Track 1 `campus_events.py`
  (cached, ~25 s fetch), runs the agents, posts the plan + link + a native Discord poll (1–2 h).
- **"Why no?":** a "no" vote → DM "Mind sharing why? (optional)". Answers get turned into a remembered filter
  ("no events after 9pm") stored on that member's profile.
- **Travel:** when the poll closes, the "yes" group gets carpools (drivers with seats, riders grouped), otherwise
  Valley Metro light rail / the free Orbit shuttle / walking, based on venue.
- **Manual:** `@Squad something chill Friday under $15, no clubs` → Claude parses filters → same pipeline → reply.
- **Voice nudge (last):** one opt-in WhatsApp call per plan to members who haven't voted, never during quiet hours.
  A small Rust sidecar on [whatsapp-rust](https://github.com/oxidezap/whatsapp-rust) (`voip` feature: 1:1 calls,
  16 kHz PCM in/out) places the call and bridges audio to Gemini Live (`gemini-3.8-live`). The bot asks it to call
  over localhost HTTP. Build from `main`: the fix for outbound calls hearing the callee (issue #1098) landed
  2026-10-23, after the v0.7.0 release. Unofficial client: Meta may suspend the number it runs on. Everything else
  works without it.

## Platform (chosen)
Discord for the group chat; WhatsApp only for the voice nudge call. Judging is a recorded video plus the repo
(submission form: one-liner, GitHub repo, optional website, optional demo video; the gallery opens website, then
video, then repo).

## Demo squad (chosen)
`/squad demo` adds 4 persona friends (e.g. Maya, Jordan, Priya, Leo), each with a profile, mock busy blocks and car/no
car. They speak through webhooks (own name + avatar, labelled demo); their member agents negotiate in the plan thread;
their votes are simulated a few seconds after the poll opens and shown beside the real ones. You are the one real
member: real poll vote, real "why no?" DM, real Google Calendar, real voice call.

## Stack
Python 3.11+, `uv`, `discord.py` (native polls, slash commands, aiohttp web server for the Composio callback and website),
`anthropic` SDK with `claude-opus-5-5` (coordinator and member agents), Google Calendar REST via plain HTTP. State in
one JSON file (shortcut: fine for a few squads; move to SQLite if it ever runs for many servers). Keys only in a
gitignored `.env`.

Hosting: always on, on the OCI server (`openclaw`, ARM, Python 3.12) as a systemd service on port 8090 (free), public
at `squad.ashwanthbk.com` for the Composio connect callback and the project website. Developed and tested on the Mac first; deployed
once steps 1–3 work.

## Access check (2026-10-24)
| Thing | State | Use |
| --- | --- | --- |
| Anthropic key | works (`claude-opus-5-5` answered), in gitignored `squad/.env` | brain |
| GitHub `gh` | signed in as ashwanthbalakrishnan5; `cubbie-side-quest-squad` is free | repo |
| Cloudflare MCP | signed in; `ashwanthbk.com` zone active; 2 tunnels exist (`ashwanth-pi-ha`, `tdfa_django_prod`) | DNS / tunnel |
| openclaw | SSH works; Python 3.12, Docker; no `uv`, no `cloudflared`; **Caddy already serves 80/443** (hermes, media, door subdomains point at it) | hosting |
| gcloud | signed in as `me@ashwanthbk.com` (not needed now that calendars go through Composio) | none |
| Gemini key | works; `gemini-3.8-live` listed (bidiGenerateContent) | voice |
| Discord bot | token works; in Test-Server-Cubbie; role has polls, threads, webhooks, events (no Connect/Speak, not needed for a phone call) | bot |
| Composio | Discord Bot connection = Composio's shared bot, works only in the server it was added to; Google Maps active; Google Calendar revoked | optional: a scripted "friend" in the test server |
| MCP registry | no Discord or Gemini MCP; Twilio MCP is docs search only | none needed |
| Calendar | replaced by Composio managed auth (no Google OAuth client needed); needs a Composio **project** API key in `.env` (the CLI only holds a user key) | calendar connect |
| Rust | installed on the Mac (cargo 1.99.1) | WhatsApp call sidecar |
| WhatsApp | built last; number + QR link given later | voice nudge |

Public URL (chosen): Caddy, like the other subdomains. One `A squad.ashwanthbk.com → 129.146.181.140` record and one
Caddy site block proxying to port 8090. Nothing new installed.

## Build order (each step demos on its own)
1. Bot skeleton: reads all, replies on mention, `/squad join` DM onboarding.
2. Event search + member agents + coordinator → plan post.
3. Poll, timer, "why no?" DM, remembered reasons.
4. Google free/busy connect.
5. Carpool / transit suggestions.
6. Voice call.
Then: unit tests for the filter / scoring / carpool / conflict logic, README (playful tone, demo SVG like Track 1),
`DEMO.md` script for judges, Track 3 submission (preview first, sent only on your yes).

## What I need from you (when we get there)
- Create the Discord app by hand (developer portal → New Application → Bot → turn on Message Content intent → copy token
  into `.env`). No MCP can create Discord apps; the community Discord MCP servers only manage a bot that already
  exists, and our own bot code covers that, so none is needed.
- An Anthropic API key in `.env`.
- `COMPOSIO_API_KEY` (project key, Composio dashboard → Settings → API Keys) in `.env`.
- For voice: a WhatsApp number for the bot to call from (linked by scanning a QR code), and Rust installed on the
  machine that builds the sidecar.
- OK (asked again at the time) to add a systemd service + Caddy site block on `openclaw` and the
  `squad.ashwanthbk.com` DNS record in Cloudflare.
