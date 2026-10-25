# Side Quests: Squad Mode — demo film (v2, ~2:35)

> **DECISIONS (user, override everything else, including SPEC.md where it disagrees):**
> 1. **No music.** Voiceover plus small UI sound effects on visible actions only.
> 2. **The voice runs the whole film, like a real person demoing at a hackathon.** No long silent stretches: the
>    narrator explains what is on screen as it happens, conversationally ("watch this", "notice…"), but the film opens on a hook, never on "okay" or "so".
>    Gaps between lines ≤ 0.6 s except the 1 s beat after the cold-open question and the call audio in S09.
> 3. **New feature in the story (S04): the bot watches on its own.** It keeps checking ASU's real events against
>    everyone's calendars and likes, and when something fits, it posts in the group by itself. This is real code
>    (`watch_tick` in `squad/flows/plan_flow.py`); nobody @-mentions the bot in this film.

Two cuts of the same film, same voiceover and timing, different chat skin:

- **Cut A "Hook + Discord"**: the problem (S01) and payoff (S11) in an iMessage group chat; the product as it ships, in
  Discord.
- **Cut B "All iMessage"**: every scene in iMessage; the bot is a group member named "Side Quests Squad". End card adds
  the chip **"Live now on Discord."**

Audience: Cubbie Hackathon Track 3 judges. The film must show: a real campus problem; that it acts on its own; one
agent per friend with conflicting constraints; what agents share vs keep private; when it asks a student to confirm;
and why students would say "we need this".

---

## 1. Story and cast

**Logline.** Every group chat says "we should hang out." Nobody picks. Squad Mode watches everyone's calendar and ASU's
real events, gives every friend their own agent, and posts the plan when something fits, without anyone having to say
"I can't afford that" out loud.

**Tone.** A friendly student builder showing their project: warm, quick, a little cheeky, never salesy. Banned words:
streamline, seamless, revolutionize, AI-powered, leverage, game-changer.

**Cast** (from `squad/personas.py` plus the real member):

| Friend | Colour | Into | Budget | Hard no's | Car |
| --- | --- | --- | --- | --- | --- |
| Maya | pink `#ff8fb1` | music, arts, food | $20 | sports | no |
| Jordan | mint `#7cffb2` | sports, gaming, food | $10 | late nights | 3 seats |
| Priya | sky `#8fd3ff` | tech, food, chill | free only | parties, alcohol | no |
| Leo | gold `#ffc627` | outdoors, chill, music | $40 | — | 1 seat |
| Ash (you) | maroon `#8c1d40` | music, food, chill | $20 | — | 2 seats |

**The week.** The watcher finds **Open Mic Night**, Friday Oct 30, 7:00 PM, Memorial Union 202, **$5**, free food. It
fits every calendar (classes end by 4; Leo's evening block is Thursday 6–9 PM, Maya's is Saturday 12–4 PM; everyone is
free Friday 7–9). Priya's cap is free only → private check → she says yes.
Card + thread + poll. Jordan votes "Can't make it" (8am shift Saturday) → private "why?" → learned "no events after
9pm on Fridays". Leo hasn't voted → one call → "yeah, I'm in". Results: going Maya, Ash, Priya, Leo; rides
"🚗 Ash → Maya, Priya" and "🚗 Leo → driving solo" (real `carpool.py` output); Discord event (Cut A) / calendar invite
(Cut B). Friday 7:02 PM the group chat: "we actually came 😭".

**Product truth.** UI copy in product scenes is the real copy from the code (`squad/ui/cards.py`, `squad/flows/*.py`,
`squad/constants.py`, `squad/personas.py`), including the watcher intro:
`👀 Spotted something that fits everyone's week: **Open Mic Night**, Friday, October 30 7:00 PM. Want to go?`
(Discord renders `<t:…:f>` as "October 30, 2026 7:00 PM"; show it that way). Private details appear only in private
DMs and locked chips. The voiceover is skin-neutral: never say "Discord" or "iMessage" in it.

---

## 2. Visual system (unchanged from v1, see SPEC.md)

Neobrutalist stage (cream `#fff4e0`, dotted grid, 3px `#111` borders, 8px hard shadows, Archivo Black supers on gold
labels, Space Grotesk labels); chat apps as devices on the stage. **Reference art to match:**
`video/reference/imessage-track1-demo.svg` (iMessage look) and `video/reference/discord-chat-demo.svg` (Discord look).
Camera: slow push-ins and gold highlight rings on what the narrator names, exactly when they name it.

**New S04 visuals (both cuts identical until the post lands):** a "watching" board on the stage: five calendar
columns (Maya, Jordan, Priya, Leo, Ash) for Mon–Sun with grey busy blocks; a stream of real-looking ASU event cards
(Sun Devil Central: Paint Your 3D Print Tue 4:30 PM, Board Game Night Thu 7:00 PM, Open Mic Night Fri 7:00 PM,
Desert Sunset Hike Sat 5:00 PM, "+100 more") slides past; each candidate tries the calendars (red blocks flash where
someone is busy); Open Mic Night lands on Friday 7–9 where all five columns are free: a gold band sweeps across all
five columns, a ✓ per friend. Then cut to the chat where the bot's intro message pops in (Cut A: `#squad` in Discord;
Cut B: the iMessage group), followed by the card arriving in S07.

---

## 3. Audio

- **Voiceover:** one narrator (Kokoro `af_heart`, natural pace, speed 1.0), one WAV per scene; call lines in S09 in two
  other voices (bot + Leo), placed through a phone-speaker EQ.
- **Music: none.**
- **SFX** (brag library, Kenney CC0), quiet (≤ 0.5) and only on visible actions: bubble send/receive, key ticks,
  checkbox clicks, card place, vote clicks, lock/unlock switch, ring pulses. No bell anywhere (user removed it). Never over a VO word that
  carries meaning.

---

## 4. Script (A/V)

Timecodes are targets; final timing follows the generated VO (+0.3 s head, +0.4 s tail per scene). Target total
2:30–2:40.

### S01 — Cold open — 0:00–0:15 — *iMessage in both cuts*
| Video | Voiceover |
| --- | --- |
| iPhone, group "the squad 🌵". Mon 9:41 PM. Bubbles one by one: Priya "we should actually hang out this week 😩" · Maya "fr" · Jordan "down" · Leo "someone pick something" · typing dots that stop. Clock spins to Fri 11:58 PM: Maya "ok next week for real" · Jordan 💯. Super **"WE SHOULD HANG OUT." ×52 WEEKS** *(story)* | "'We should hang out.' The most-sent, least-done text in college. Every week, somebody says it, everybody agrees, someone says 'pick something'… and nobody ever picks. Sound familiar?" |

### S02 — Title — 0:15–0:23
| Video | Voiceover |
| --- | --- |
| Maroon wipe; site hero builds: "SIDE QUESTS:" + maroon sticker "SQUAD MODE"; sub "Squad Mode picks the event, the time and the ride, so you actually go."; chip "Cubbie Hackathon · Track 3 · ASU". | "So we built Squad Mode. It's a bot that lives in your friend group's chat, and it actually does the picking for you." |

### S03 — Join — 0:23–0:44 — chip "01 JOIN"
| Video | Voiceover |
| --- | --- |
| Cut A: Discord `/squad join` → "Join the squad (1/2)" form (real fields from `squad/ui/onboarding.py`); cursor ticks Live music, Food & free food, Chill hangouts; free times; budget "Up to $20"; "Car, 2 seats free"; Submit → "You're in 🎉 One more step:" with "Calls & quiet hours" and "Connect Google Calendar". Cut B: same fields as an iOS sheet from a "Join the squad" link card. Then the five friends' pick cards pop in around the device with 🔒 chips on budget and calendar. Super **"ONE AGENT PER FRIEND"**. | "Setting up takes about thirty seconds. You join, and you tell your own agent what you're into, when you're usually free, what you can spend, any hard no's, and whether you've got a car. I've got two free seats. You can connect your Google Calendar too, and it only ever sees when you're busy. Never what you're doing." |

### S04 — It watches — 0:44–1:03 — chip "02 WATCHES" — **new**
| Video | Voiceover |
| --- | --- |
| The watching board (section 2): calendars, event stream, red clash flashes, then the gold band on Friday 7–9 with five ✓. Super **"IT WATCHES, SO NOBODY HAS TO ASK"**. Cut to the chat: the bot posts the watcher intro (real copy). | "And here's my favourite part: nobody has to ask. In the background, it keeps checking real campus events from Sun Devil Central against everyone's calendars and what they like. Most things clash with somebody… but the second it finds something that fits the whole squad, it posts it right in the group. Like this. Open Mic Night, Friday at seven." |

### S05 — The agents — 1:03–1:25 — chip "03 AGENTS"
| Video | Voiceover |
| --- | --- |
| Four agent cards (Maya, Jordan, Priya, Leo) score the options with filling bars; shared reasons type in: Maya "I'd love the open mic 🎤" (9/10) · Jordan "happy to drive if it's not a late one" (7) · Priya "free food and a chill crowd, yes" (8) · Leo "I'd pick the hike, but I'm in for music" (5). Close-up on Priya: "🔒 budget: free only" and "$5"; her chip splits, the public half "someone has a budget limit" flies to the Coordinator card; the private half stays blurred. Super **"SHARES THE VIBE. KEEPS THE DETAILS."** | "So how did it decide? Every friend has their own agent. Maya's is all in on the open mic, Jordan's happy to drive, and Leo would honestly rather go hiking. But each agent only shares what's safe for the group. The coordinator just hears that someone has a budget limit. Not who, and not how much." |

### S06 — Asks first — 1:25–1:41 — chip "04 ASKS FIRST"
| Video | Voiceover |
| --- | --- |
| Priya's private DM (Cut A Discord DM, Cut B iMessage DM), real copy: "Quick check before I post this week's plan: Open Mic Night, Friday, October 30, 2026 7:00 PM. Heads up: it's $5 and your cap is $0. Still up for it?" [Sure, count me in] [Pass on this one]; she taps "Sure, count me in". Super **"ASKS BEFORE IT BENDS YOUR LIMIT"**. | "That someone is Priya. It's five dollars, and she said free only. So before anything goes out, her agent checks with her, privately. She's in. And if she'd said no, it would just quietly pick something else, and nobody would ever know why." |

### S07 — The plan — 1:41–2:01 — chip "05 PLAN"
| Video | Voiceover |
| --- | --- |
| The plan card lands (Cut A Components V2 card; Cut B rich bubble) with real fields; highlight rings follow the VO: time → place → "Trade-offs • Someone has a budget limit • Leo would've picked the hike" → the thread / inline agent replies → the poll "Open Mic Night, you in?" (I'm in ✅ / Maybe 🤔 / Can't make it ❌). Votes arrive ≥ 0.8 s apart: Maya ✅, Ash ✅, Priya ✅, Jordan ❌; who-line "✅ Maya, Ash, Priya  ❌ 1 can't make it". | "Then the plan goes up. The time, the place, why it picked this one, and the trade-offs, out in the open. You can read every agent's take, and there's a poll. Votes start rolling in… and notice, when somebody says no, it only shows a count. Never a name." |

### S08 — Remembers — 2:01–2:14 — chip "06 REMEMBERS"
| Video | Voiceover |
| --- | --- |
| Jordan's private DM: "Mind sharing why? Totally optional, it just helps me pick better next time." [Tell you why] [Skip]; he answers "8am shift Saturday, nothing late on Fridays for me"; "Got it, I'll keep that in mind 🙏". His agent card gains "🔒 no events after 9pm on Fridays". Super **"REMEMBERS WHAT YOU CAN'T SAY OUT LOUD"**. | "Jordan can't make it, so he gets a private message asking why. Totally optional. He's got an early shift Saturday, so his agent just remembers. Nothing late on Fridays for Jordan, from now on." |

### S09 — Nudge — 2:14–2:26 — chip "07 NUDGE"
| Video | Voiceover |
| --- | --- |
| Leo's phone: incoming WhatsApp call "Side Quests Squad"; he answers; caption bubbles for the call audio: BOT "Hey Leo! The squad's doing Open Mic Night Friday at seven. Maya and Priya are in. You in?" · LEO "yeah, I'm in". The poll gains his ✅. | "Leo hasn't voted yet, so he gets one friendly call. Just one, and never during his quiet hours." Then the call lines play. |

### S10 — It's on — 2:26–2:34 — chip "08 GO"
| Video | Voiceover |
| --- | --- |
| Results (real copy): "🎉 It's on" · "Going: Maya, Ash, Priya, Leo" · "Rides" "🚗 Ash → Maya, Priya" "🚗 Leo → driving solo" · Cut A "📅 Discord event"; Cut B a calendar invite bubble. | "When the poll closes, you get who's going, who's driving who, and a reminder for everyone." |

### S11 — Friday — 2:34–2:39 — *iMessage in both cuts*
| Video | Voiceover |
| --- | --- |
| Group chat, Fri 7:02 PM: Priya's illustrated photo bubble + "we actually came 😭", Maya ❤️. Super **"YOU ACTUALLY WENT."** No bell (user removed it). | "And Friday night? They actually went." |

### S12 — End card — 2:39–2:45
| Video | Voiceover |
| --- | --- |
| Site-style end card: "SIDE QUESTS: SQUAD MODE", one-liner, "Add to Discord →", "See the code", **squad.ashwanthbk.com**, "Cubbie Hackathon · Track 3 · team NRK". Cut B adds "Live now on Discord." | "That's Squad Mode. Let's get your whole squad some grass to touch." |

---

## 5. Full voiceover (for TTS, one file per scene)

S01: "We should hang out." The most-sent, least-done text in college. Every week, somebody says it, everybody
agrees, someone says "pick something"… and nobody ever picks. Sound familiar?
S02: So we built Squad Mode. It's a bot that lives in your friend group's chat, and it actually does the picking for you.
S03: Setting up takes about thirty seconds. You join, and you tell your own agent what you're into, when you're usually
free, what you can spend, any hard no's, and whether you've got a car. I've got two free seats. You can connect your
Google Calendar too, and it only ever sees when you're busy. Never what you're doing.
S04: And here's my favourite part: nobody has to ask. In the background, it keeps checking real campus events from Sun
Devil Central against everyone's calendars and what they like. Most things clash with somebody… but the second it finds
something that fits the whole squad, it posts it right in the group. Like this. Open Mic Night, Friday at seven.
S05: So how did it decide? Every friend has their own agent. Maya's is all in on the open mic, Jordan's happy to drive,
and Leo would honestly rather go hiking. But each agent only shares what's safe for the group. The coordinator just
hears that someone has a budget limit. Not who, and not how much.
S06: That someone is Priya. It's five dollars, and she said free only. So before anything goes out, her agent checks
with her, privately. She's in. And if she'd said no, it would just quietly pick something else, and nobody would ever
know why.
S07: Then the plan goes up. The time, the place, why it picked this one, and the trade-offs, out in the open. You can
read every agent's take, and there's a poll. Votes start rolling in… and notice, when somebody says no, it only shows a
count. Never a name.
S08: Jordan can't make it, so he gets a private message asking why. Totally optional. He's got an early shift Saturday,
so his agent just remembers. Nothing late on Fridays for Jordan, from now on.
S09: Leo hasn't voted yet, so he gets one friendly call. Just one, and never during his quiet hours.
S10: When the poll closes, you get who's going, who's driving who, and a reminder for everyone.
S11: And Friday night? They actually went.
S12: That's Squad Mode. Let's get your whole squad some grass to touch.

Call lines (S09): BOT "Hey Leo! The squad's doing Open Mic Night Friday at seven. Maya and Priya are in. You in?" ·
LEO "yeah, I'm in."

About 400 narrator words: speech fills the film end to end.

---

## 6. Production

Two separate HyperFrames projects already exist: `video/cut-a-discord/` and `video/cut-b-imessage/`, built from
`video/shared/` (shared scenes and components) and `video/shared-assets/`. v2 changes: regenerate all VO WAVs and
`timing.json`; retime every scene to its new VO; replace S04 ("the ask") with "It watches" in both cuts; S11 gets VO;
remove any music; SFX quiet and only on visible actions; narration-synced highlights (each thing the narrator names
gets a gold ring or push-in at that word, using the whisper word timings in `shared-assets/vo/words/`).
Renders: `video/renders/squad-mode-A-discord.mp4`, `video/renders/squad-mode-B-imessage.mp4` + poster JPGs.
QC: `npx hyperframes check` zero errors; snapshots of every scene in both cuts reviewed; no silent stretch > 1.2 s
except where noted; text readable; real copy matches code.
