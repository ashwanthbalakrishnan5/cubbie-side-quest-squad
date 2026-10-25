# Demo video: 2:30 shot list

One take per beat, cut together. Real bot, real ASU events, four demo friends.

## Live table demo (judges, about 3 minutes)

Hosted bot, nothing to start. `/squad demo` is fully scripted: no events feed, no Claude, no calendars, so it runs
the same every time in about 30 seconds.

1. **Play the film** (squad.ashwanthbk.com plays it, or the local render).
2. **Fresh channel:** make `#demo-N` in Test-Server-Cubbie and run `/squad demo`. Maya, Jordan, Priya and Leo say hi,
   the bot posts "👀 Spotted something that fits everyone's week: **Open Mic Night**…", then the card, the thread
   (each agent's line, the coordinator, "Priya's agent checked with Priya privately: all good.") and the poll. The
   friends vote a few seconds apart; Jordan's agent remembers "no events after 9pm on Fridays". If you haven't
   joined, it signs you up (music, food, chill, $20, 2 seats).
3. **Don't vote yet: let it ring.** About 8 s after the friends vote, the demo nudges you on its own: your phone
   rings over WhatsApp from the bot's number (`DEMO_PHONE` on the server). Show the judges, then decline; you get
   "📞 Rang …, no answer" privately, nothing public. Quiet hours still apply (default 10pm–9am).
4. **Now vote live.** Pick **Can't make it ❌** to show the private "Mind sharing why?" DM (only you see it).
   Changing to **I'm in ✅** afterwards is fine; it won't ask again.
5. **Close poll now** on the card: "🎉 It's on" with going, rides and the 📅 Discord event, instantly.

Backup: `/squad nudge` rings you on demand if the automatic call didn't fire (for example you voted too early).

Again? Run `/squad demo` once more (same channel works: new plan, no repeat intros) or use a new channel.

## Before you record

The shot list below was for the film. `/squad demo` now runs the scripted demo above, so for these beats use a
channel that already has the demo friends and plan with `/squad plan` or an @-mention.

**Use the hosted bot.** It runs on openclaw with `DEMO_FAST=1` already, so there is nothing to start. (To record
against a local copy instead, stop the hosted one first, because two processes on one token both answer:
`ssh openclaw sudo systemctl stop squad`, then `DEMO_FAST=1 uv run python -m squad` from `squad/`, and
`sudo systemctl start squad` when you're done.)

`DEMO_FAST=1` changes only the waits: demo friends vote 5–20 s after the poll, the private check waits 60 s (not
10 min), and the nudge comes 60 s after the plan (not 30 min). The poll itself still runs an hour, so you close it
with the button.

**Warm the events feed.** The first fetch from Sun Devil Central takes about 25 s. Before recording, run
`/squad plan` once in a scratch channel. The same process then serves events instantly for 6 hours.

**Windows to have open**

1. Discord desktop on `#general` of the test server (Test-Server-Cubbie), zoomed in one step (Ctrl/Cmd +).
2. The plan thread: it opens as a side panel when you click it on the card.
3. A DM window with the bot (Direct Messages → Side Quests Squad).
4. Optional: the WhatsApp Mac app, only if `wa-voice` is paired (see the end).
5. `docs/assets/hero.svg` open in a browser tab for the hook and outro (it's animated).

Turn on Do Not Disturb and record with system audio.

**Your join answers (they make the private check happen):** interests Live music + Chill hangouts + Food; free
times Weekday evenings + Saturday daytime, **not** Friday night; budget Up to $20; hard no's none; Do you drive?
**Car, 2 seats free**. Skip the calendar link for the recording: with a calendar connected, your calendar replaces
the ticked times, and Friday has to look busy for the check to fire. Step 2: quiet hours **Midnight–10am** (the
default 10pm–9am blocks the nudge if you record late).

## Shot list

| Time | On screen | Do | Say (one line) |
|---|---|---|---|
| 0:00 | `hero.svg` in the browser | Nothing, let it animate | "Every group chat says 'we should hang out.' Nobody picks the thing." |
| 0:15 | `#general` | `/squad join` → fill form 1/2 → "You're in 🎉" → **Calls & quiet hours** → form 2/2 → "Saved ✨" | "Everyone fills one quick form. Your own agent keeps it private." |
| 0:35 | `#general` | `/squad demo` → Maya, Jordan, Priya and Leo say hi | "No friends online at 2 am? Four demo friends, each with their own agent." |
| 0:45 | `#general` | Type `@Side Quests Squad something chill Friday under $15, no clubs` → "On it 🗺️ checking Sun Devil Central…" | "Just ask like a human. It reads the real ASU events feed." |
| 1:05 | DM window | "Quick check before I post this week's plan… Heads up: you look busy then. Still up for it?" → **Sure, count me in** (within 60 s) | "That plan breaks my limit, so code makes it ask me privately first. The group never sees why." |
| 1:15 | `#general`, then the thread | Card + poll appear. Open the thread: each agent's line, the coordinator, "checked with … privately" | "Every friend's agent argued for its person. The coordinator picked one." |
| 1:30 | `#general` card | Watch the card's vote line fill in: ✅ Maya, Priya · 🤔 Leo · ❌ 1 can't make it | "The squad votes on a real Discord poll." |
| 1:40 | The thread | "Jordan's agent: Jordan shared why privately. I'll remember: no events after 9pm on Fridays." | "A no isn't a dead end. It learns, privately." |
| 1:45 | Poll, then DM window | Vote **Can't make it ❌** → DM "Mind sharing why?" → **Tell you why** → type a reason → "Got it, I'll keep that in mind 🙏" | "Only I see this. Next week's pick gets smarter." |
| 1:55 | Poll, then card | Remove your vote, pick **I'm in ✅** (it won't ask why again) → **Close poll now** | "Changed my mind. Close it." |
| 2:00 | `#general` | "🎉 It's on": Going, Rides (🚗 you → Maya, Priya), 📅 Discord event → click it | "Who drives whom, and a real Discord event so everyone gets reminded." |
| 2:10 | DM window (or WhatsApp) | The nudge (recorded earlier, see below) | "Forgot to vote? One friendly nudge. Never in your quiet hours." |
| 2:25 | `hero.svg`, then the README | Show the Add to Discord link | "Side Quests: Squad Mode. Your group chat, but you actually go." |

### Recording the nudge (2:10)

The nudge goes to members who haven't voted, so record it **before** the 1:45 vote: after the card posts, wait
(up to about a minute and a half) for the DM "Hey … 👋 the squad's planning … You in? The poll's in #general." Then do the 1:30–1:55
beats and cut the nudge in at 2:10.

If `wa-voice` is paired and you ticked the voice nudge with your number, it's a WhatsApp call instead: pick it up on
the Mac app, say "yeah I'm in", and the thread shows "📞 … picked up and said yes". That sets your vote, so do the
"why no?" beat in a second take. Not paired (the current state)? It's the DM, and that's fine to show.

## If something goes sideways

- **Feed slow or down.** The "On it 🗺️" reply comes at once, so cut the wait. If Sun Devil Central fails, the bot
  uses `data/events_cache.json` when it's under 48 h old; otherwise it says "Sun Devil Central isn't answering right
  now". Warm the feed (above) before the real take.
- **No private check DM.** The pick didn't break your limit. Keep going; skip the 1:05 beat or re-run the plan.
- **"No side quest this week".** Nothing on Friday fit everyone. Re-run with a looser ask, e.g.
  `@Side Quests Squad something chill this weekend`.
- **Thread lines are posted by the bot itself, as `Maya's agent: …` in bold.** The bot lost Manage Webhooks in that channel; it still
  works, it just looks plainer. Fix the permission before the real take.

## Reset between takes

- **New channel (easiest):** squads are per channel. Make `#demo-2`, run `/squad join` there (it pre-fills your
  answers) and `/squad demo`.
- **Full reset:** stop the bot (Ctrl+C), then `rm -rf data/squad.json` and start it again. That clears squads,
  profiles and plans and stops nothing else: the events cache stays, and your calendar stays linked on Composio's
  side. Delete the file only while the bot is stopped, or it writes everything back from memory.
- Jordan's learned filter survives `/squad demo` re-runs on purpose. The full reset clears it.

When you're done: `ssh openclaw sudo systemctl start squad`.
