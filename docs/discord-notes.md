# Discord features for Squad Mode (read 2026-10-24)

Sources: Discord changelog (docs.discord.com/developers/change-log), discord.py 2.7.1 docs (latest on PyPI).

## Use (each one earns its place)
| Feature | Since | Where in Squad Mode |
| --- | --- | --- |
| Components V2 (`ui.LayoutView`: Container, Section, TextDisplay, Thumbnail, MediaGallery, Separator; 40 components/msg) | Apr 2025 / dpy 2.6 | The plan card: event photo, time, place, who's in, travel, trade-offs, buttons, all one message |
| Modals with Label + String/User/Channel selects, TextDisplay | Aug–Sep 2025 / dpy 2.6 | Onboarding form: interests (multi-select), budget, no-go types |
| Modal Checkbox, CheckboxGroup, RadioGroup | Feb 2026 / dpy 2.7 | Onboarding: "I have a car" checkbox, seats radio, quiet hours, voice-call opt-in |
| Native polls + poll vote events (`GUILD_MESSAGE_POLLS`, not privileged) | 2024 | Yes / Maybe / No vote, 1–2 h |
| Guild Scheduled Events (`CREATE_EVENTS`, required for bots since Feb 23 2026) | 2025 | When the poll passes, post a Discord event with the real time and place; members tap "Interested" and get Discord's own reminder |
| `@time` timestamp markdown + `app_commands.Timestamp` | dpy 2.7 | Times show in each viewer's own time zone; `/squad plan when:` takes a time |
| Slash commands: multiline string options, fuzzy autocomplete | Sep 2026 | `/squad plan` with free-text vibe, autocomplete for interests |
| Context menu commands (limit now 15) | Mar 2026 | Right-click a message → "Plan this" (turns "we should go bowling" into a plan) |
| Threads | — | One thread per weekly plan keeps the main chat clean; the "agent room" where member agents negotiate is visible there |
| Search Guild Messages endpoint | Mar 2026 | Optional: read recent squad chat for vibes ("everyone's been saying they're broke") |
| Message forwarding (`Message.is_forwardable()`) | 2024 / dpy 2.7 | Forward the plan card to a member's DM with their private carpool note |
| User-installable app (Guild + User install) | 2024 | Optional: use `/squad` in any DM or group DM, not just servers |

## Skip (doesn't help this product)
Activities / Embedded App SDK, Social SDK, monetization / premium buttons, game stats widgets, lobbies, account linking,
gradient roles, voice channel status, soundboard.

## Limits to remember
- Bots cannot vote in polls; only real accounts can.
- Unverified bots under 10,000 users get Message Content without review (Jun 2026 rule).
- More DMs from apps can land in Message Requests (age assurance, Sep 2026); onboarding should start from a button
  in the server (interaction → modal), not a cold DM.
- Upload limit 20 MiB.
