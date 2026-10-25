# SPEC — Side Quests: Squad Mode, demo film (two cuts)

> **DECISION (user, overrides everything below): NO MUSIC.** The film is voiceover only, plus the small UI sound
> effects on visible actions (bubble pops, key ticks, clicks, card places, ring, the one bell in S11). Do not place,
> duck, automate or fade any music bed; remove `music-bed` / `bed-*` audio clips if present. Ignore every music,
> bed, duck, BPM, bar-seam and beat-cue instruction in this file. S11 and the S12 tail play with SFX only.


The HyperFrames build contract for both cuts of `SCRIPT.md`. The script owns the story and the words; this file
turns every adjective in it into a number. Built as **two separate HyperFrames projects** that share
`shared-assets/` (copy it into each project's `assets/`):

- **Cut A "Hook + Discord"** → `squad-mode-A-discord.mp4`
- **Cut B "All iMessage"** → `squad-mode-B-imessage.mp4`

Same VO, music, SFX, timing and beats. Only the chat skin changes in S03, S04, S06, S07, S08, S10.
All on-screen words come from `shared-assets/story.json`; all times from `shared-assets/timing.json`.

```text
GOAL:    a judge (or an ASU student) ends the film thinking "our group chat needs this": they saw a real campus
         problem, four agents with conflicting limits, what is shared vs kept private, the bot asking before it
         bends a limit, and the squad actually going.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, one root index.html + 12 scene sub-compositions per project.
TIME:    v2: 150.767 s x 30 = 4523 frames (see section 10). No music.
```

---

## 1. Timing (from `shared-assets/timing.json`)

VO measured with ffprobe, 0.4 s head, ≥ 0.6 s tail, never shorter than the script target. Only S09 (+2.5 s,
two call lines) and S12 (+0.3 s) grew. Total 152.8 s (2:32.8), inside 2:25–2:35.

| Scene | Start (s) | Dur (s) | Frames (abs) | VO clips: in-scene offset → file [media start, dur] |
| --- | --- | --- | --- | --- |
| S01 cold open | 0.0 | 14.0 | 0–419 | 7.0 → s01 [0, 4.800] |
| S02 title | 14.0 | 8.0 | 420–659 | 3.0 → s02 [0, 4.096] |
| S03 join | 22.0 | 18.0 | 660–1199 | 1.0 → s03 [0, 13.333] |
| S04 ask | 40.0 | 12.0 | 1200–1559 | 1.0 → s04 [0, 7.744] |
| S05 agents | 52.0 | 22.0 | 1560–2219 | 1.0 → s05 [0, 9.0] · 10.4 → s05 [9.0, 5.6] · 18.4 → s05 [14.6, 2.04] |
| S06 asks first | 74.0 | 16.0 | 2220–2699 | 1.0 → s06 [0, 4.45] · 8.0 → s06 [4.45, 6.067] |
| S07 plan | 90.0 | 18.0 | 2700–3239 | 1.0 → s07 [0, 5.05] · 10.0 → s07 [5.05, 3.334] |
| S08 remembers | 108.0 | 14.0 | 3240–3659 | 1.0 → s08 [0, 4.35] · 8.0 → s08 [4.35, 2.242] |
| S09 nudge | 122.0 | 13.5 | 3660–4064 | 1.4 → s09 · 6.2 → s09-bot · 11.85 → s09-leo |
| S10 go | 135.5 | 8.0 | 4065–4304 | 0.4 → s10 [0, 4.736] |
| S11 payoff | 143.5 | 5.0 | 4305–4454 | no VO |
| S12 end card | 148.5 | 4.3 | 4455–4583 | 0.4 → s12 [0, 3.285] |

Split points sit inside measured silences (≥ 0.12 s at −40 dB), so the splits restore the script's own cue times
(S05 1:02 and 1:11, S06 1:22, S07 1:40, S08 1:56). Each split is a second `<audio>` of the same WAV with
`data-media-start`. Word timings per file: `shared-assets/vo/words/*.json` (whisper small.en; use the times,
never its spellings: it hears "Meyer" for Maya). Every "@t" below is scene-local seconds, `fN` = scene-local frame.

---

## 2. LOOK

**Medium: the project site's neobrutalist sticker stage, with real chat apps set on it as physical devices.**
This is the brand's own material (`squad/site/index.html`), so its cream ground and gold tag are allowed; the
generic cream-serif look is not (see BANNED).

### Stage (every product shot)
- Ground `#fff4e0`, flat, no gradient. Dot grid: dots radius 2 px, pitch 44 px, colour `#111` at 16 % (`#d6cdbd`),
  grid origin (22, 22). Grain 0 %, vignette 0 %.
- Ink `#111`: all stage text, borders, shadows.
- Stage objects (cards, chips, supers, buttons): border 3 px `#111`; hard shadow `8px 8px 0 #111` (small objects
  under 120 px tall: `5px 5px 0 #111`); radius 14 px for cards, 10 px for chips, 0 for supers.
- Device shadows: iPhone `0 30px 60px rgba(17,17,17,0.22)` plus hard `8px 8px 0 #111` on the frame silhouette;
  Discord window `10px 10px 0 #111`, border 3 px `#111`, radius 14 px.

### Colour roles (rationed)
| Colour | Hex | May appear on |
| --- | --- | --- |
| Maroon (brand) | `#8c1d40` | act wipes, the SQUAD MODE sticker, Coordinator header, Ash's avatar, plan-card accent bar, bot avatar ground |
| Gold | `#ffc627` | supers, focus ring, score-bar fills, Leo's colour, number digits in section chips |
| Pink / Mint / Sky | `#ff8fb1` / `#7cffb2` / `#8fd3ff` | only Maya / Jordan / Priya avatars, their card headers and Discord name colour |
| Blurple | `#5865f2` | Discord UI only, "Add to Discord →" button |
| iOS blue / grey | `#0a84ff` / `#e9e9eb` | iMessage bubbles only |

### Type
| Role | Face | Size / weight / leading / tracking |
| --- | --- | --- |
| Hero title (S02, S12) | Archivo Black 400 | 150 px, line-height 0.95, tracking −0.01 em, uppercase |
| Super | Archivo Black 400 | 52 px, line-height 1.0, tracking −0.01 em, uppercase, max 2 lines, max box width 680 px |
| Section chip | Archivo Black 400 | 26 px, uppercase, tracking 0.02 em |
| Stage card name | Archivo Black 400 | 30 px |
| Stage body (bubbles, chips, rows) | Space Grotesk 500 / 700 | 28 px (never below 28 px for words meant to be read), line-height 1.25 |
| S02 / S12 sub line | Space Grotesk 500 | 36 px, line-height 1.35, max width 1080 px |
| Tag chip | Space Grotesk 700 | 24 px (decorative label, read as a shape; holds ≥ 2.5 s) |
| iMessage UI | Inter 400 / 600 (SF Pro stand-in) | iOS pt × 1.1 px (body 17 pt = 18.7 px at camera 1.0) |
| Discord UI | Inter 400 / 600 (gg sans stand-in) | Discord px × 1.4 (body 16 = 22.4 px at camera 1.0) |
| Emoji | system emoji font | never re-drawn; same em size as the text it sits in |

Fonts: `shared-assets/fonts/fonts.css` (Archivo Black 400, Space Grotesk 500/700, Inter 400/600). Inter has no
italic file: the plan-card headline uses `font-style: italic` (synthetic oblique, accepted). The TTFs have no `→`:
draw it as an inline SVG arrow (stroke 0.09 em, `currentColor`, 0.9 em wide, baseline-aligned).

**Reading rule:** device text is shown at 1.0× only while it is not meant to be read. Every line the viewer must
read is framed at a camera scale that puts it at ≥ 28 px: iMessage camera ≥ 1.5, Discord camera ≥ 1.25.

### Layout grid (1920 × 1080)
- Margins 96 px. Title-safe box x 192–1728, y 108–972 for supers and titles.
- **Section chip:** top-left anchor (96, 72), stage layer (does not move with the camera).
- **Super zone:** bottom-left, box anchored at left 96, bottom 972; zone x 96–720, y 812–972. While a super is up
  nothing else may sit in that zone (device boxes stay right of x 728 or above y 800 in the framed shot).
- **iPhone base:** centred (960, 540) at camera 1.0; outer 462 × 981 px.
- **Discord window base:** 1224 × 640 px at x 348–1572, y 152–792.

---

## 3. OBJECTS

### 3.1 iPhone (iMessage, iOS 26, light) — Cut A S01/S11; Cut B everywhere
Authored at 1.1 px per iOS pt. Screen 402 × 874 pt = 442 × 961 px.
- **Frame:** titanium band 8 px `#2c2c2e` → inner black bezel 6 px `#000`; outer radius 66 px, screen radius 58 px;
  side buttons as 4 px bumps (`#3a3a3c`) on the left edge at y 190/260/330 and right edge at y 280. Dynamic Island
  126 × 37 pt black pill centred 11 pt from the top. No reflections, no gloss.
- **Status bar:** 54 pt tall. Clock Inter 600 17 pt `#000` left at x 34 pt (centre of the left ear). Right: signal
  (4 bars), Wi-Fi, battery (27 × 13 pt, 2 pt radius, 85 % fill) as SVG `#000`.
- **Header (group):** 4 stacked avatars 34 pt (overlap −10 pt) with 2 pt white ring, centred; below them the group
  name in a pill `#f2f2f7` radius 13 pt, Inter 600 13 pt + `›` chevron. Back chevron `#0a84ff` at left 16 pt.
  Header height 110 pt, background `#f9f9f9`, hairline 0.5 pt `#c6c6c8`. DM header: one avatar 50 pt + name.
- **Thread:** background `#ffffff`. Side insets 16 pt (received bubbles start at 50 pt when avatars show).
- **Timestamp separator:** centred, Inter 11 pt `#8e8e93`, day in 600 weight ("**Mon** 9:41 PM"), 12 pt above and
  8 pt below.
- **Sender name** (group, received, first bubble of a run): Inter 400 11 pt `#8e8e93`, 12 pt inset from the bubble,
  2 pt above it.
- **Bubble:** max width 266 pt; padding 7 pt top/bottom, 12 pt left/right; radius 18 pt; text Inter 400 17 pt,
  line-height 22 pt. Sent `#0a84ff`/`#ffffff`; received `#e9e9eb`/`#000000`. Tail on the last bubble of a run only:
  the iOS curl (start from registry `chat-message`/`chat-thread`, keep their tail path). Spacing: 2 pt within a run,
  10 pt between senders (+ name line).
- **Avatar** (received, last bubble of a run): 28 pt circle in the friend's colour, white Inter 600 13 pt initial.
  The bot: maroon `#8c1d40` circle with 🗺️ at 15 pt.
- **Tapback:** 30 pt white circle, 1 pt `#e5e5ea` border, `0 1px 3px rgba(0,0,0,.18)`, emoji 16 pt, overlapping the
  bubble's top-right corner by (−12 pt, −14 pt) (top-left for sent bubbles).
- **Delivered / Read:** Inter 600 11 pt `#8e8e93`, right-aligned under the last sent bubble, 3 pt gap.
- **Typing dots:** received bubble 56 × 36 pt, three 8 pt dots `#8e8e93`, opacity wave 0.35→1 per dot, period
  0.9 s, dot phase 0.15 s, computed from timeline time (no CSS animation). Registry `typing-indicator`.
- **Input bar:** "+" 34 pt circle `#e9e9eb` left; field 36 pt tall, radius 18 pt, 1 pt `#c6c6c8` border, placeholder
  "iMessage" Inter 17 pt `#c4c4c6`; send button 28 pt `#0a84ff` circle with white ↑ when text is present.
- **Keyboard (Cut B typing):** iOS light keyboard 291 pt tall, ground `#d1d3d9`, keys white radius 5 pt with
  `0 1px 0 #898a8d`, Inter 400 22 pt letters, QWERTY rows. Rises in 0.35 s `power3.out`, leaves in 0.25 s `power3.in`.
- **Rich link bubble:** 266 pt wide, `#e9e9eb`, radius 18 pt; body card white inside with 8 pt inset; footer line
  domain Inter 400 13 pt `#8e8e93`.
- **Buttons under a bot bubble (Cut B only):** stacked, each 266 pt × 40 pt, white, 1 pt `#c6c6c8`, radius 12 pt,
  Inter 600 17 pt `#0a84ff`, 6 pt gap. (Stands in for Discord buttons; same labels.)
- **iOS sheet (S03 B):** slides from bottom, top radius 38 pt, ground `#f2f2f7`, grabber 36 × 5 pt `#c7c7cc`.
  Nav row: "Cancel" `#0a84ff` 17 pt left, title Inter 600 17 pt centre, "Next"/"Done" Inter 600 17 pt right.
  Section headers Inter 400 13 pt uppercase `#6d6d72`; rows 44 pt in white inset groups radius 10 pt; toggles
  51 × 31 pt (on `#34c759`); radio picks as `#0a84ff` checkmark at the right.
- **Incoming call (S09, WhatsApp via CallKit):** ground `#1c1c1e` → `#2c2c2e` vertical (only gradient allowed,
  it is the real OS screen; no banding at this size). Bot avatar 110 pt maroon circle with 🗺️ 56 pt at y 230 pt;
  name Inter 600 30 pt white; label Inter 400 17 pt `#aeaeb2`. Buttons 76 pt circles at y 720 pt: Decline
  `#ff3b30` left, Accept `#34c759` right, white glyphs, labels Inter 400 15 pt white. In-call: timer Inter 400
  17 pt `#aeaeb2` under the name, 24-bar waveform (each bar 6 pt wide, 4 pt gap, radius 3 pt, white, height
  6–60 pt = 6 + 54 × `shared-assets/vo/env/<file>.json` `rms01[frame]`), bottom row: speaker, mute (`#3a3a3c`
  70 pt circles) and End `#ff3b30`.

### 3.2 Discord desktop window (dark) — Cut A S03, S04, S06–S08, S10
Authored at 1.4 px per Discord px. 1224 × 640 px = 874 × 457 Discord px.
- **Title bar** 22 dp `#1e1f22` with three 12 px traffic lights (`#ff5f57`, `#febc2e`, `#28c840`) at left 12 dp.
- **Server rail** 72 dp `#1e1f22`; 48 dp server icons radius 16 dp; the current server icon is a maroon square with
  🌵; pill indicator 4 × 40 dp white at left.
- **Channel sidebar** 240 dp `#2b2d31`: server name "ASU friends" Inter 600 16 dp `#f2f3f5` in a 48 dp header;
  channels Inter 500→600 16 dp `#949ba4`, selected `#squad` on `#404249` radius 4 dp with `#f2f3f5` text. User
  panel 52 dp `#232428` at the bottom: Ash avatar (maroon) + "Ash".
- **Chat** `#313338`. Header 48 dp: `#` + "squad" Inter 600 16 dp `#f2f3f5`, divider 1 dp `#1f2023`, topic
  Inter 400 14 dp `#949ba4` (`story.json` groups.discord_server.channel_topic). Channel start: "Welcome to #squad!"
  Inter 700 32 dp and "This is the start of the #squad channel." 16 dp `#b5bac1` (real Discord copy).
- **Message:** avatar 40 dp at left 16 dp; content at x 72 dp; name Inter 600 16 dp in the friend's colour (Ash
  `#f2f3f5`, bot `#ffffff`); APP badge 15 dp tall `#5865f2` radius 3 dp, "APP" Inter 600 10 dp white; timestamp
  Inter 400 12 dp `#949ba4` ("Today at 4:03 PM"); body Inter 400 16 dp/22 dp `#dbdee1`. Mention: `#5865f2` at 30 %
  ground, `#c9cdfb` text, radius 3 dp. Message groups 17 dp apart.
- **Components V2 container:** max width 520 dp, ground `#2b2d31` (as in `docs/assets/chat-demo.svg`), radius 8 dp,
  padding 16 dp, left accent bar 4 dp `#8c1d40`.
  `##` heading Inter 600 20 dp `#f2f3f5`; `###` Inter 600 16 dp; text 16 dp `#dbdee1`; italic headline 16 dp
  `#dbdee1`; `**bold**` Inter 600; separator 1 dp `#3f4147` with 8 dp margins.
- **Buttons:** 32 dp tall, radius 8 dp, padding 0 16 dp, Inter 600 14 dp white. Secondary `#4e5058`; success
  `#248046`; primary `#5865f2`; link button secondary with a 14 dp ↗ glyph. 8 dp gaps.
- **Poll:** ground `#2b2d31`, 1 dp `#3f4147` border, radius 8 dp, padding 16 dp, width 440 dp. Question Inter 600
  17 dp `#f2f3f5`; "Select one answer" 12 dp `#949ba4`; answer rows 44 dp, radius 8 dp, ground `#383a40`, fill
  `#5865f2` at 35 % growing left→right with the vote share, label Inter 500 16 dp, right side "3 votes 75%" 14 dp
  `#b5bac1`; footer "4 votes · 1h left" 14 dp `#949ba4`.
- **Modal:** 440 dp wide, ground `#313338`, radius 8 dp, backdrop `#000` at 70 % over the window; title Inter 600
  20 dp `#f2f3f5`, close × top-right; label Inter 600 16 dp `#f2f3f5`, description 14 dp `#b5bac1`; checkbox
  20 dp radius 4 dp (off: 2 dp `#4e5058` border; on: `#5865f2` fill + white check); radio 20 dp circle (on:
  `#5865f2` ring + 10 dp dot); option text 16 dp `#dbdee1`, rows 36 dp; text input 40 dp `#1e1f22` radius 8 dp.
  Footer `#2b2d31` 72 dp with "Cancel" (text button `#f2f3f5`) and "Submit" (primary). Body scrolls inside the
  modal (max visible 360 dp).
- **Ephemeral marker:** under the message, eye glyph + "Only you can see this • Dismiss message" 12 dp `#949ba4`
  ("Dismiss message" in `#00a8fc`).
- **Slash autocomplete:** popover above composer, `#2b2d31`, row "/squad join" Inter 600 16 dp + description
  "Join this channel's squad" 14 dp `#949ba4`, bot avatar left.
- **Typing indicator:** under the composer, "**Side Quests Squad** is typing…" Inter 400 14 dp `#dbdee1` with
  three 6 dp dots (same timeline-driven wave as iMessage).
- **Composer:** 44 dp tall, `#383a40`, radius 8 dp, "+" left, placeholder "Message #squad" `#6d6f78`.
- **Thread panel:** slides over the chat's right side, 400 dp wide, `#313338`, 1 dp `#1f2023` left border,
  header "🗺️ Open Mic Night" with the thread glyph, Inter 600 16 dp.
- **DM view (S06, S08):** sidebar shows "Direct Messages" with "Side Quests Squad" selected; header shows the bot
  avatar + name + APP.

### 3.3 Stage objects (both cuts)
- **Super:** gold `#ffc627` box, 3 px ink border, `8px 8px 0 #111`, padding 14 px 22 px, Archivo Black 52 px
  uppercase ink. Rotation 0. One per beat.
- **Section chip:** `#111` ground, 3 px ink border, radius 10 px, padding 8 px 16 px, rotation −2°, `5px 5px 0
  #8c1d40`; digits gold `#ffc627`, words cream `#fff4e0`, Archivo Black 26 px. Example: **01** JOIN.
- **Friend card (S03):** 340 × auto, white, 3 px ink, radius 14, shadow 8 px. Header 64 px in the friend's colour:
  avatar 44 px white circle with Archivo 22 px initial + name Archivo Black 30 px. Body padding 18 px: three picks,
  Space Grotesk 500 28 px, 6 px gap; then two lock chips.
- **Lock chip:** cream `#fff4e0`, 3 px ink, radius 10 px, padding 6 px 12 px, Space Grotesk 700 28 px; lock glyph
  24 px SVG (closed: shackle down; open: shackle raised 6 px and rotated 30° about its left post). Never pill-shaped.
- **Agent card (S05, S08):** 380 × 470 px, white, 3 px ink, radius 14, shadow 8 px, rotations −2°, 1°, −1°, 2°
  and y offsets 0, +18, −10, +12 px (Maya, Jordan, Priya, Leo) so the row is not a grid. Header 72 px friend colour
  with avatar 48 px + "Maya's agent" Archivo Black 30 px. Four score rows (one per event): event icon 34 px, track
  190 × 18 px (radius 9, 3 px ink, cream ground), fill gold, value "9/10" Space Grotesk 700 28 px. Chips below.
  Card x lefts 150, 570, 990, 1410; top 330.
- **Speech bubble (shared reason):** white, 3 px ink, radius 16 px, tail 18 px toward its card, Space Grotesk 500
  28 px, max width 360 px, sits 24 px above its card.
- **Coordinator card:** 560 px wide, white, 3 px ink, radius 14, shadow 8 px; header 68 px maroon with
  "COORDINATOR" Archivo Black 30 px white; inbox row (the public chip lands here); four rank rows 56 px: rank digit
  Archivo Black 30 px, title Space Grotesk 700 28 px, total right-aligned; the "best fit · 1 limit to check" tag is a
  gold chip, rotation 3°. Lands top-centre at (680, 96).
- **Event card (S04):** 300 × 380 px, white, 3 px ink, radius 16, shadow 8 px. Top 150 px colour block (Open Mic
  pink, Paint sky, Hike gold, Board Game mint) with a flat 2-colour SVG icon 96 px (mic, paintbrush, mountain + sun,
  two dice) in ink. Title Archivo Black 30 px (2 lines max); meta Space Grotesk 500 28 px ("Fri 7:00 PM", place);
  price sticker pink, radius 10, rotation 6°, Space Grotesk 700 28 px. "+ 104 more" card: gold ground, Archivo Black
  44 px.
- **Sun Devil Central panel:** white, 3 px ink, radius 14, header bar maroon 64 px with "Sun Devil Central" Archivo
  Black 30 px white.
- **Caption card (S09):** white, 3 px ink, radius 14, shadow 8 px, 620 px wide, left of the phone at (180, 300):
  speaker label Space Grotesk 700 26 px (bot maroon, Leo `#111` on a gold underline), text Space Grotesk 500 34 px;
  the word being spoken is ink, upcoming words `#111` at 35 %.
- **Focus ring:** gold `#ffc627` stroke 6 px, plus a 2 px ink outer stroke, rounded rect radius 12 px, 10 px outset
  from the target; drawn with stroke-dashoffset 100→0 in 0.35 s `power2.out`; leaves with opacity 0 in 0.15 s.
- **Cursor (Cut A):** macOS arrow, 56 px tall, black fill, 3 px white outline, `2px 3px 0 rgba(17,17,17,.35)`.
- **Touch (Cut B):** registry `touch-indicator`: 44 pt circle `#000` at 18 %, scale 0.8→1 on touch, 0.12 s.
- **Photo (S11):** flat vector illustration 266 × 200 pt inside a bubble, radius 18 pt: night sky `#1b1a3a`, the
  Memorial Union facade in maroon/gold blocks, a string of 14 warm bulbs, four figures from behind (pink, mint, sky,
  gold tops), no faces. Built as inline SVG.
- **End card buttons:** "Add to Discord →" `#5865f2` white text, "See the code" `#7cffb2` ink text; Space Grotesk
  700 30 px, padding 18 px 30 px, 3 px ink, radius 12 px, `5px 5px 0 #111`.

---

## 4. MOTION

| Role | Curve | Duration / numbers |
| --- | --- | --- |
| Bubble / message arrive | linear scale 0.92→1 + opacity 0→1 | 2 frames (0.067 s); origin = sender's bottom corner; the thread above slides up by the new height in 0.2 s `power3.out` from the same frame |
| Sticker land (cards, chips, avatars, buttons, title sticker) | `back.out(1.0)` (overshoot 3.7 %) | scale 0.6→1, 0.30 s; opacity 0→1 in the first 0.08 s |
| Super slam | `power3.in`, then dead still | scale 1.35→1 + opacity 0→1 + blur 8→0 px in 0.18 s |
| Super / card exit | `power2.in` | opacity →0 + blur 0→6 px, 0.20 s (exits 40–50 % of entrances) |
| Title words (S02, S12 line 1) | blur-in | per word blur 6→0 px + opacity, 0.13 s, 0.067 s apart, no translate |
| Sub line (S02, S12) | colour | per word `#111` at 25 % → 100 %, 0.07 s apart |
| Camera push (hold) | `sine.inOut` | +3 % scale across the hold (2–4 % range); never on a title |
| Camera focus move | `power3.inOut` | 0.6–0.7 s, after the focus ring finishes drawing |
| Camera pull-back | `power2.inOut` | 0.7–1.2 s |
| Cursor travel | `power3.inOut` | 0.45 s along a 6 % arc; press: scale 0.88 in 0.06 s, release 0.10 s; the UI reacts on the press frame |
| Discord typing | step | 0.045 s per character; iMessage 0.05 s |
| Score bar fill | `power2.out` | 0.5 s; 0.15 s between cards, 0.08 s between rows |
| Speech-bubble reasons | per word blur-in | 0.13 s each, 0.07 s apart |
| Modal open (Discord) | `power3.out` | scale 0.96→1 + opacity, 0.2 s; backdrop 0→70 % in 0.15 s |
| iOS sheet | `power4.out` | translateY 100 %→0 in 0.45 s; out `power3.in` 0.3 s |
| Chip split (S05) | `power2.inOut` | public half lifts 24 px in 0.3 s, then flies on a 12 % arc in 0.7 s; private half blur 0→6 px, opacity →0.55 in 0.6 s |
| Rank reorder (S05) | FLIP `power3.inOut` | 0.5 s |
| Text swap (who line) | blur swap | out 0.13 s blur 8 px, in 0.13 s |
| Clock time-lapse (S01) | slot roll | each digit rolls through values 0.1 s per roll, 0.8 s total |

**Camera rig:** every scene has `#<scene>-cam` (a wrapper inside the scene root, `transform-origin: 0 0`) carrying
`scale`, `x`, `y`. The section chip and supers live outside the camera. Focus moves always: ring draws (0.35 s) →
camera moves (0.6–0.7 s) → hold ≥ 1.2 s. No spinning, no 3D tilt, no shake.

**Transitions (5 kinds, each caused by something on screen):**
1. **Maroon wipe** (act changes: S01→S02, S10→S11, S11→S12): full-frame `#8c1d40` panel with a 6 px `#111` leading
   edge; covers x −1920→0 in 0.2 s `power3.in`, the cut happens under it, reveals 0→+1920 in 0.2 s `power3.out`.
   One root-level overlay clip, 0.4 s, centred on the seam. Adapt registry `directional-wipe`.
2. **Blur swap on one stage** (S02→S03): title out opacity→0 + blur 8 px in 0.15 s; the device lands as a sticker;
   the ground never cuts.
3. **Carry across** (S03→S04, S04→S05, S09→S10): one object keeps moving across the seam (the window, the event
   cards, the who-line chip) with blur peaking at 6 px mid-move.
4. **Object becomes the world** (S05→S06 Priya's card → her DM; S07→S08 the "Can't make it ❌" row → Jordan's DM):
   the object grows past the frame in 0.65 s `power2.inOut`, its radius shrinking to 0, surroundings blur 15 px and
   fade in 0.3 s, the new UI fades in while it still grows.
5. **Whip** (S06 DM→group at 7.2 s; S08→S09): 0.25 s horizontal (S06) / vertical (S08→S09) smear, blur peak 18 px
   along the move; the arriving element lands blurred and sharpens in 0.13 s.

---

## 5. SOUND

### 5.1 Music bed — REMOVED (no music; see the decision at the top) — `assets/audio/music-bed.mp3` (Happy Beats / Business Moves vol 10, ende.app; 60.0 s)
Cue file `music-bed.cues.json`. Strong cues used: **2.461 s** (bar downbeat, intensity 0.80) for the S02 sticker;
**17.473 s** (start of section C, the track's loudest stretch) for the S11 payoff; **20.190 s** (strongest cue,
1.00) for the S11 bell + super. The track's last 0.5 s decays, so it loops on whole bars: file 0.267 → 56.738 s
(104 beats = 26 bars, 56.471 s), placed so section C lands exactly on S11's first frame.

| Clip id | Film start | `data-media-start` | Duration | Fades |
| --- | --- | --- | --- | --- |
| `bed-1` | 14.000 | 0.915 | 55.823 | in 0.20 s, out 0.03 s |
| `bed-2` | 69.823 | 0.267 | 56.471 | in 0.03 s, out 0.03 s |
| `bed-3` | 126.294 | 0.267 | 26.506 | in 0.03 s, out 1.50 s (151.3→152.8) |

Volume automation (`data-automation` on each clip, film times): 0.35 from 14.0; ramp to 0.13 at 16.8→17.0; hold
0.13 through S10; ramp to 0.35 at 143.2→143.5; hold to 148.6; ramp to 0.13 by 148.8; fade to 0 at 151.3→152.8.
No music in S01 (13.8–14.0 is the wipe; the bed starts under its reveal). Bar seams at 69.823 and 126.294 fall
between VO words (S05 18.4 gap, S09 before "your quiet hours" = 4.29 local: check it is inaudible; if not, add a
0.08 s crossfade).

### 5.2 Voice
VO `data-volume` 1.0 (peaks −1.0 to −6.5 dBFS measured). S09 call lines: `s09-bot.wav` (Kokoro `am_adam`, peak
−0.3 dBFS) at 0.75, `s09-leo.wav` (Kokoro `am_michael`) at 0.9, both through a phone band-pass (high-pass 300 Hz,
low-pass 3400 Hz, `/hyperframes-audio` EQ). Narrator `af_heart`. Note: the script named `am_puck` for the bot; it
is not in this CLI's `--list`, so `am_adam` stands in.

### 5.3 SFX — `assets/audio/sfx/…` (Kenney CC0)
Rule: the SFX peak lands one frame after its picture → clip start = picture time + 0.033 − peak. Max one SFX per
0.4 s. Volumes: drop 0.50, ui click 0.45, keypress 0.12 (texture under VO), card-place 0.55, switch 0.45, select
0.50, glass 0.60, bell 0.70. Peaks (s): drop 0, select 0, switch 0, glass 0, bell 0, click1 0.020, click2 0.012,
click3 0.028, keypress-001…008 0.040/0.047/0.017/0.017/0.032/0.012/0.011/0.132, card-place-1 0.175, -2 0.200,
-3 0.456, -4 0.337.

| Picture (film s) | Scene · what | File | Clip start (film s) |
| --- | --- | --- | --- |
| 0.80 / 1.90 / 2.60 / 3.50 | S01 bubbles Priya, Maya, Jordan, Leo | interface/drop_001, 002, 003, 001 | +0.033 each |
| 7.30 | S01 Maya "ok next week for real" | interface/drop_002 | 7.333 |
| 15.546 | S02 SQUAD MODE sticker lands (bar downbeat) | casino/card-place-1 | 15.404 |
| 22.60 / 23.00 | S03 "/squad join" typing ticks (A); field taps (B: none) | keyboard/keypress-001, 003 | −0.007 / +0.016 |
| 23.60 | S03 Enter (A) / link card arrives (B: drop_001 at 22.70) | keyboard/keypress-006 | 23.621 |
| 25.75 / 26.15 / 26.55 | S03 tick Live music, Food & free food, Chill hangouts | ui/click1, click2, click3 | 25.763 / 26.171 / 26.555 |
| 28.75 | S03 Up to $20 | ui/click1 | 28.763 |
| 31.45 | S03 Car, 2 seats free | ui/click2 | 31.471 |
| 31.75 | S03 Submit / Next | ui/click3 | 31.755 |
| 32.15 | S03 B only: bot "You're in 🎉" bubble | interface/drop_002 | 32.183 |
| 33.10 / 33.75 / 34.25 | S03 Calls & quiet hours, Voice nudge, Submit | ui/click1, click2, click3 | 33.113 / 33.771 / 34.255 |
| 40.75 … 42.75 (every 0.4) | S04 typing ticks (6) | keyboard/keypress-002…007 | +0.033 − peak |
| 43.40 | S04 Ash's message posts / sends | interface/drop_001 | 43.433 |
| 44.25 | S04 bot "On it 🗺️" | interface/drop_002 | 44.283 |
| 46.65 | S04 first event card lands | casino/card-place-1 | 46.508 |
| 52.10 | S05 agent cards land | casino/card-place-3 | 51.677 |
| 62.50 | S05 Priya's lock opens, chip splits | interface/switch_002 | 62.533 |
| 74.40 | S06 bot DM arrives | interface/drop_003 | 74.433 |
| 80.20 | S06 "Sure, count me in" | interface/select_008 | 80.233 |
| 80.80 | S06 B only: "Got it, thanks 🙏" bubble | interface/drop_001 | 80.833 |
| 91.40 | S07 plan card lands | casino/card-place-1 | 91.258 |
| 95.30 | S07 poll posts | interface/drop_002 | 95.333 |
| 98.90 / 99.70 / 100.50 / 101.30 | S07 votes Maya, Ash, Priya, Jordan | ui/click1, click2, click3, click1 | +0.033 − peak |
| 108.30 | S08 bot DM arrives | interface/drop_001 | 108.333 |
| 111.40 | S08 "Tell you why" | ui/click2 | 111.421 |
| 112.30 … 114.30 (every 0.4) | S08 Jordan typing ticks (6) | keyboard/keypress-001…008 rotating | +0.033 − peak |
| 114.80 | S08 Submit (A) / send (B: drop_001) | ui/click3 | 114.805 |
| 115.20 | S08 "Got it, I'll keep that in mind 🙏" | interface/drop_002 | 115.233 |
| 118.25 | S08 new chip's lock snaps shut | interface/switch_002 | 118.283 |
| 122.15 / 122.75 | S09 two ring pulses | impact/impactGlass_light_001 | 122.183 / 122.783 |
| 128.00 | S09 Accept | ui/click2 | 128.021 |
| 134.95 | S09 who-line sticker lands | casino/card-place-2 | 134.783 |
| 136.10 | S10 "Close poll now" (A only) | ui/click1 | 136.113 |
| 137.10 | S10 results card / bubble lands | casino/card-place-2 | 136.933 |
| 140.70 | S10 Events chip (A) / calendar invite bubble (B) | casino/card-place-3 | 140.277 |
| 143.90 | S11 photo bubble | interface/drop_003 | 143.933 |
| 144.80 | S11 "we actually came 😭" | interface/drop_001 | 144.833 |
| 146.217 | S11 super + payoff (strongest cue) | impact/impactBell_heavy_000 | 146.250 |

Not in the shared folder on purpose: room tone (none in the library; S01 sits on bubble pops alone) and whooshes
(not named by the script; wipes and whips are silent under the music).

---

## 6. SHOTS BY FRAME

Times are scene-local seconds (frame = s × 30). "Both" = identical in both cuts. Copy in quotes is verbatim from
`story.json`. Unless stated, everything not named holds still.

### S01 — Cold open (0.0–14.0 s, f0–419) — both cuts: iMessage, Ash's phone, group "the squad 🌵"
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| f0 | Frame 0 (thumbnail): cream stage, iPhone at camera 1.50 framed on the thread (header top at y 40); screen black (asleep) | the phone | silence |
| 0.30 (f9) | Screen wakes: black → thread in 0.25 s (opacity of a black cover) | header "the squad 🌵", timestamp "**Mon** 9:41 PM" | — |
| 0.80 / 1.90 / 2.60 / 3.50 | Bubbles pop (2 frames): Priya, Maya, Jordan, Leo | "we should actually hang out this week 😩" · "fr" · "down" · "someone pick something" | drops |
| 4.60–6.00 | Maya typing dots in, hold, out (no message) | the dots | — |
| 0.3–6.2 | Camera push 1.50→1.545 `sine.inOut` | | |
| 6.20–7.00 | Time-lapse: status clock rolls 9:41→11:58; thread scrolls up one screen (old bubbles blur 0→4 px) | — | — |
| 7.00 | Separator "**Fri** 11:58 PM" lands (2-frame pop) | | VO starts 7.0 |
| 7.30 | Maya "ok next week for real" pops | the line | drop |
| 8.40 | Jordan 💯 tapback pops on it | 💯 | — |
| 9.20–10.40 | Camera pulls back 1.545→1.00 (`power2.inOut`, 1.2 s): the whole phone on the dotted stage | | |
| 10.62 (f319) | Super slams (on "Nobody" 10.68): line 1 "“WE SHOULD HANG OUT.”", line 2 "×52 WEEKS" (×52 in maroon) | the super, held 3.1 s | VO "Nobody picks a thing." |
| 13.80 | Maroon wipe covers (root overlay 13.8–14.2) | | |

### S02 — Title (14.0–22.0 s, f0–239) — both
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.0–0.2 | Wipe reveals cream stage | | bed-1 in (0.35) |
| 0.25 | "SIDE QUESTS:" words blur in (2 words, 0.067 s apart); left-aligned at x 192, cap top y 330 | title | |
| 1.546 (f46) | "SQUAD MODE" maroon sticker (white Archivo Black 150 px, padding 0 24 px, 4 px ink border, `10px 10px 0 #111`, rotation −1.5°) lands below line 1 on the bar downbeat | the name | card-place-1 |
| 2.30–3.30 | Sub line per word (grey→ink), x 192, top y 690, max width 1080 px: "Your group chat keeps saying "we should hang out." Squad Mode makes you actually go." | sub, held 4.5 s | VO 3.0 "This is Squad Mode…" |
| 3.90 | Tag chip "Cubbie Hackathon · Track 3 · ASU" lands above line 1 at (192, 236), rotation −2°, gold pill (site style) | tag | — |
| 0.2–7.6 | Camera push 1.00→1.03 on the stage (title block does not move inside it) | | |
| 7.85–8.00 | Blur swap out (title, sub, tag) | | |

### S03 — Join (22.0–40.0 s, f0–539) — chip "**01** JOIN" lands 0.30
**Cut A (Discord):**
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.00–0.35 | Discord window lands as a sticker (scale 0.96→1, `back.out(1.0)`) at base rect, `#squad` empty channel start | "Welcome to #squad!" | — |
| 0.40–1.40 | Camera → composer, scale 1.35 | | |
| 0.60–1.50 | Ash types "/squad join"; autocomplete row "/squad join — Join this channel's squad" appears at 1.20 | the command | ticks 0.60, 1.00 |
| 1.60 | Enter | | keypress |
| 1.80 | Modal "Join the squad (1/2)" opens; camera → modal, scale 1.35 (1.8–2.5) | modal title + "What are you into?" | VO 1.0 "Everyone joins once…" |
| 2.60 | Cursor enters from bottom-right | | |
| 3.75 / 4.15 / 4.55 | Ticks "Live music", "Food & free food", "Chill hangouts" | | clicks |
| 4.90–5.50 | Modal body scrolls to "When are you usually free?" (3 pre-ticked) | | VO "usually free" |
| 5.90–6.40 | Scroll to "Budget per hangout" | | |
| 6.75 | Click "Up to $20" | | click1 (VO "spend" 6.87) |
| 7.00–7.50 | Scroll to "Hard no's" / "Optional" (none ticked) | | VO "hard no's" 7.61 |
| 7.90–8.40 | Scroll to "Do you drive?" | | |
| 9.45 | Click "Car, 2 seats free" | | click2 (VO "car" 9.62) |
| 9.75 | Click "Submit"; modal closes 9.80–9.95 | | click3 |
| 10.15 | Ephemeral reply pops: "You're in 🎉 One more step:" · [Calls & quiet hours] [Connect Google Calendar] · "No calendar? I'll use the free times you ticked." · "Only you can see this • Dismiss message" | | — |
| 10.20–10.55 | Focus ring draws on [Connect Google Calendar]; camera → reply, scale 1.40 | the button | VO "Connect a calendar" 10.13 |
| 11.10 | Cursor clicks [Calls & quiet hours]; modal "Join the squad (2/2)" opens 11.30 | "Voice nudge" / "One friendly call if you miss a plan poll" | click1 |
| 11.75 | Tick "Voice nudge"; "Quiet hours" shows "10pm–9am" selected | | click2 |
| 12.25 | Submit; 12.40 ephemeral "Saved ✨" | | click3 |
| 12.60–13.30 | Camera pulls back to 0.82, window stays centred | | |
| 13.30 / 13.60 / 13.90 / 14.20 | Friend cards land (sticker): Maya at (120, 150), Jordan (1500, 130), Leo (120, 470), Priya (1480, 520); each: three picks + "🔒 budget" "🔒 calendar"; the calendar chips read "🔒 calendar: busy / free only" | picks + locks | VO "busy, never what" 13.0–14.3 |
| 14.70 | Super "ONE AGENT PER FRIEND" slams; holds to 17.75 | super | — |
| 14.7–17.6 | Camera push 0.82→0.845 | | |
| 17.60–18.00 | Friend cards fly off outward (0.25 s `power3.in`), super exits (blur), camera returns to 1.0 | | |

**Cut B (iMessage):** same clock. iPhone lands as a sticker 0.00–0.35 on DM "Side Quests Squad", camera 1.50.
0.70 bot link card "Join the squad · squad.ashwanthbk.com" pops (drop). 1.60 touch on the card → 1.80 iOS sheet
"Join the squad (1/2)" rises. Toggles at 3.75/4.15/4.55 ("Live music", "Food & free food", "Chill hangouts"),
scrolls at the same times as A, checkmark "Up to $20" 6.75, "Car, 2 seats free" 9.45, "Next" 9.75 → sheet drops.
10.15 bot bubbles: "You're in 🎉 One more step:", then two link cards "Calls & quiet hours" and "Connect Google
Calendar · calendar.google.com", then "No calendar? I'll use the free times you ticked." (0.15 s apart; one drop).
10.20 focus ring on the calendar card. 11.10 tap "Calls & quiet hours" → sheet "Join the squad (2/2)": Voice nudge
toggle on 11.75, Quiet hours "10pm–9am" ✓, "Done" 12.25 → 12.40 bot "Saved ✨". From 12.60 identical to A (pull
back to 0.82, friend cards, super).

### S04 — The ask (40.0–52.0 s, f0–359) — chip "**02** ASK" lands 0.25
**Cut A:**
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.00–0.60 | Camera → composer, scale 1.35 | | |
| 0.70–1.15 | Ash types "@Side"; mention autocomplete "Side Quests Squad APP" 1.00; Tab 1.15 → mention pill | | ticks |
| 1.25–3.20 | Types "something chill Friday under $15, no clubs" | the ask | ticks every 0.4 s; VO 1.0 "Then anyone just asks…" |
| 3.40 | Message posts (Ash, "Today at 4:03 PM"); camera follows it, scale 1.35 | the whole message | drop |
| 3.60–4.20 | "Side Quests Squad is typing…" | | |
| 4.25 | Bot reply pops: "On it 🗺️ checking Sun Devil Central and everyone's week…" (APP badge) | reply | drop |
| 5.30–5.65 | Focus ring on "Sun Devil Central"; camera → it, scale 1.60 (5.65–6.30) | | VO "Sun Devil Central" 6.01 |
| 6.05–6.40 | Morph: the phrase's box widens into the Sun Devil Central panel (110→1300 px, blur 12→0, `power3.out` 0.35 s); camera pulls back to 1.0 (6.10–6.90) | panel header | |
| 6.65 / 6.95 / 7.25 / 7.55 / 7.85 | Event cards fan out of the panel (sticker, rotations −6°, −2°, 2°, 6°, 4°) at x 300, 600, 900, 1200, 1500 (y 300–680): Open Mic Night "Fri 7:00 PM" "Memorial Union 202" "$5" "free food 🍕" · Paint Your 3D Print "Tue 4:30 PM" · Desert Sunset Hike "Sat 5:00 PM" · Board Game Night "Thu 7:00 PM" · "+ 104 more" | titles and times | card-place-1 at the first |
| 8.95 | Super "REAL ASU EVENTS"; holds to 11.70 | super | — |
| 11.55–12.00 | Carry across: window and panel slide off left (`power3.in`, blur 6 px); the four event cards stay and start travelling to S05 | | |

**Cut B:** group "the squad 🌵" (bot is a member, its avatar in the header stack) on Ash's phone, camera 1.50,
separator "**Today** 4:03 PM". 0.60 tap field, keyboard rises; typing at the same times into the field (mention
"@Side Quests Squad" turns bold when the name completes at 1.15). 3.40 send: blue bubble, keyboard drops (3.45–3.70).
3.60 typing dots from Side Quests Squad, 4.25 its grey bubble with the same text. 5.30 focus ring on "Sun Devil
Central" inside the grey bubble, camera 1.60 → 2.0; from 6.05 identical to A (the panel grows out of the bubble).

### S05 — The agents work it out (52.0–74.0 s, f0–659) — both; chip "**03** AGENTS" lands 0.30
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.00–0.60 | Carry across: the four event cards shrink into the icon column of each agent card as the cards land (stagger 0.12 s) at their row positions | four agent cards | card-place-3 |
| 1.0–5.0 | Camera push 1.00→1.02 | names | VO 1.0 "Here's the part we're proud of…" |
| 5.40–6.90 | Score bars fill (values in `story.json`), value labels count up with the fill | scores | VO "scores the options" 5.62 |
| 7.00 / 7.25 / 7.50 / 7.75 | Speech bubbles type in above each card: "I'd love the open mic 🎤" (9/10) · "happy to drive if it's not a late one" (7/10) · "free food and a chill crowd, yes" (8/10) · "I'd pick the hike, but I'm in for music" (5/10) | reasons | VO "only shares what's safe" 7.85 |
| 9.75–10.10 | Focus ring on Priya's chips + Open Mic row | | |
| 9.85–10.45 | Camera → Priya's card, scale 1.70 | "🔒 budget: free only", "🔒 no parties" | |
| 10.30 | "$5" pink price sticker pops on her Open Mic row | $5 | |
| 10.50 | Lock opens (shackle lifts), chip starts to split: public half (gold chip "someone has a budget limit") lifts 24 px; private half blurs to 6 px / 0.55 | the split | switch_002 |
| 11.60–12.30 | Camera pulls back to 1.00; speech bubbles exit (blur); the agent-card row scales to 0.85 about (960, 330) and drops 60 px (bottom edge 790, clear of the super zone) | | VO "The coordinator learns" 10.78 |
| 12.00 | Coordinator card (header + inbox row only, 148 px tall) lands top-centre (680, 96) | "COORDINATOR" | |
| 11.90–12.60 | Public half flies on a 12 % arc into the coordinator inbox row; lands 12.60 | "someone has a budget limit" | VO "someone has a budget limit" 12.50–13.40 |
| 13.4–16.0 | Hold; Priya's blurred private half stays on her card | | VO "Never who, and never the number." |
| 14.30 | Super "SHARES THE VIBE. KEEPS THE DETAILS." (2 lines); holds to 17.55 | super | — |
| 17.60–17.90 | Maya's, Jordan's and Leo's cards exit downward (`power3.in`, 0.3 s); Priya's card (still showing the blurred half) moves to (1380, 420) at 0.85 | | |
| 17.80–18.50 | The coordinator grows to 560 × 400 at (520, 120) and its rank rows land in feed order (Paint, Hike, Board, Open Mic); camera → coordinator, scale 1.50 | | |
| 18.60 | FLIP reorder: Open Mic Night rises to rank 1 (29), then Paint 22, Board 21, Hike 20 | ranking | VO "It finds the best fit" 18.66 |
| 19.20 | Tag "best fit · 1 limit to check" lands on rank 1 (gold, 3°) | tag | — |
| 20.60–21.20 | Camera pulls back to 1.00 | | |
| 21.35–22.00 | Object becomes the world: Priya's agent card grows past the frame into her DM | | |

### S06 — Asks first (74.0–90.0 s, f0–479) — chip "**04** ASKS FIRST" lands 0.30
**Cut A:** Priya's Discord window in DM view ("Direct Messages" → "Side Quests Squad"), camera 1.00 at 0.0.
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.40 | Bot DM pops ("Today at 4:04 PM"): container with "Quick check before I post this week's plan: Open Mic Night, Friday, October 30, 2026 7:00 PM. Heads up: it's $5 and your cap is $0. Still up for it?" + [Sure, count me in] (success) [Pass on this one] | | drop_003 |
| 0.40–1.10 | Camera → message, scale 1.45 | the whole text (31 words, on screen 5.8 s before the click) | VO 1.0 "And when the best plan bends someone's limit…" |
| 2.30–2.65 | Focus ring on "Heads up: it's $5 and your cap is $0." | the limit | VO "limit" 2.84 |
| 5.60 | Cursor enters | | |
| 6.20 | Click [Sure, count me in] (button darkens 10 % for 0.1 s) | | select_008 |
| 6.35 | Container blur-swaps to "Got it, thanks 🙏" | | |
| 7.20–7.45 | Whip left: Priya's window exits; Ash's `#squad` window enters from the right, camera 1.10; last message is still the bot's "On it 🗺️ checking Sun Devil Central and everyone's week…" | nothing new in the group | — |
| 8.10 | Super "ASKS BEFORE IT BENDS YOUR LIMIT"; holds to 15.75 | super | VO 8.0 "If Priya had said no…" |
| 8.1–15.9 | Camera push 1.10→1.13 | | |

**Cut B:** Priya's iPhone (DM "Side Quests Squad"), camera 1.50. 0.40 grey bubble with the same text and the two
stacked buttons under it. 2.30 focus ring on the same phrase. 6.00 touch on "Sure, count me in"; 6.20 the buttons
collapse (0.15 s) and Priya's blue bubble "Sure, count me in" pops 6.35; 6.80 bot "Got it, thanks 🙏". 7.20 whip to
Ash's phone, group "the squad 🌵", last bubble the bot's "On it 🗺️…". Super and push identical.

### S07 — The plan lands (90.0–108.0 s, f0–539) — chip "**05** PLAN" lands 0.30
**Cut A:** `#squad`, camera 1.10 (continuing from S06).
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 1.40 | Plan card lands (bot, "Today at 4:05 PM"): "🗺️ This week's side quest" / "Open Mic Night" / "🕖 Friday, October 30, 2026 7:00 PM · in 5 days" / "📍 Memorial Union 202 · $5 · free food 🍕" / *"Live music, free pizza, and home by 9"* / why / "**Trade-offs**" "• Someone has a budget limit" "• Leo would've picked the hike" / separator / "Nobody's voted yet, no pressure 🙂" / [Event page ↗] [Close poll now] [How did you pick this?] | | card-place-1; VO "posts the plan" 1.48 |
| 1.60–2.30 | Camera → card top, scale 1.30 | title, when, where | |
| 2.60–3.30 | Camera pans down to headline + why | why | VO "with the reasons" 2.59 |
| 3.40–4.00 | Pan to Trade-offs; focus ring on "Someone has a budget limit" 3.70 | trade-offs | VO "trade-offs out in the open" 3.68–4.88 |
| 5.30 | Poll posts below the card: "Open Mic Night, you in?" "I'm in ✅" "Maybe 🤔" "Can't make it ❌", footer "0 votes · 1h left"; camera → poll, scale 1.30 (5.3–6.0) | poll | drop_002; VO "and a poll" 5.21 |
| 6.00–6.30 | Thread panel "🗺️ Open Mic Night" slides over the chat's right side; camera → panel, scale 1.30 | | |
| 6.20 / 6.55 / 6.90 / 7.25 / 7.60 | Thread posts pop: Maya's agent, Jordan's agent, Priya's agent, Leo's agent, Coordinator (names in their colours, Coordinator in gold) | the five lines (recap of S05) | — |
| 8.60–8.80 | Thread panel slides out (`power3.in`); camera → who line + poll, scale 1.25 | | |
| 8.90 / 9.70 / 10.50 / 11.30 | Votes: Maya ✅, Ash ✅, Priya ✅, Jordan ❌; poll fills (0.4 s `power2.out`), the card's who line blur-swaps: "✅ Maya" → "✅ Maya, Ash" → "✅ Maya, Ash, Priya" → "✅ Maya, Ash, Priya  ❌ 1 can't make it"; footer counts "1 vote" … "4 votes · 1h left" | who line | clicks; VO 10.0 "Notice it never names who said no. Just a count." |
| 12.40–12.75 | Focus ring on "❌ 1 can't make it" | the count | VO "just a count" 12.47 |
| 13.3–14.5 | Hold, push 1.25→1.28 | | |
| 14.60–15.40 | Camera pulls back to 1.00 | | |
| 16.60–16.95 | Focus ring on the poll row "Can't make it ❌" | | |
| 17.35–18.00 | Object becomes the world: the row grows into Jordan's DM | | |

**Cut B:** Ash's phone, group, camera 1.50. 1.40 rich link bubble from Side Quests Squad: maroon top strip
"🗺️ This week's side quest", then the same fields, footer "squad.ashwanthbk.com"; the camera pans it like A. 5.30
iOS 26 poll bubble "Open Mic Night, you in?" with the three answers, each row a 22 pt circle + label + count (no
voter avatars, so a no stays anonymous). 6.00–8.60 the iOS inline-reply view opens on the link bubble (background
blurred 20 px, the link bubble at top, the five agent lines as grey reply bubbles with sender labels), then closes.
Votes at the same four times (Ash's is a touch); the who line updates as a footer line under the link bubble,
Inter 600 15 pt. Ring, pull-back and the grow into Jordan's DM identical.

### S08 — "Why no?" memory (108.0–122.0 s, f0–419) — chip "**06** REMEMBERS" lands 0.30
**Cut A:** Jordan's Discord DM view, camera 1.00.
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.30 | Bot DM pops ("Today at 4:07 PM"): "Mind sharing why? Totally optional, it just helps me pick better next time." [Tell you why] (primary) [Skip] | the ask | drop_001 |
| 0.30–0.90 | Camera → message, scale 1.45 | | VO 1.0 "Say no, and it asks why." |
| 3.00 | Cursor enters | | |
| 3.40 | Click [Tell you why]; modal "Why not this time?" opens 3.55: "What got in the way?" / "Only I see this" | modal | click2; VO "Only you see that" 3.05 |
| 3.70–4.05 | Focus ring on "Only I see this" | | |
| 4.30–6.55 | Jordan types "8am shift Saturday, nothing late on Fridays for me" | the reason | ticks every 0.4 s; VO "Answer if you want" 4.29 |
| 6.80 | Submit; modal closes 6.85–7.00 | | click3 |
| 7.20 | Ephemeral reply "Got it, I'll keep that in mind 🙏" + "Only you can see this • Dismiss message" | | drop_002 |
| 7.60–8.20 | Camera pulls back to 0.90; window slides right 260 px; Jordan's agent card (S05 design, scores hidden) lands left at (150, 220) with "🔒 budget: up to $10", "🔒 no late nights" | | |
| 8.30–8.90 | New chip "🔒 no events after 9pm on Fridays" flies from the reply to the card on an arc, lands with its lock open | the new chip | VO 8.0 "Next week, his agent just remembers." |
| 10.25 | The chip's lock snaps shut | | switch_002 |
| 10.60 | Super "LEARNS WHAT YOU CAN'T SAY OUT LOUD" (2 lines); holds to 13.70 | super | — |
| 13.75–14.00 | Whip down into S09 | | |

**Cut B:** Jordan's iPhone, DM "Side Quests Squad", camera 1.50. 0.30 grey bubble + buttons [Tell you why] [Skip].
3.40 touch "Tell you why"; buttons collapse; keyboard rises 3.55. 4.30–6.55 typing in the field. 6.80 send: blue
bubble. 7.20 bot "Got it, I'll keep that in mind 🙏". From 7.60 identical to A (the phone slides right, card, chip,
lock, super, whip).

### S09 — The nudge (122.0–135.5 s, f0–404) — both; chip "**07** NUDGE" lands 0.30
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.00–0.25 | Whip: Leo's iPhone arrives from below, lands blurred, sharpens 0.13 s; centred at x 1180, camera 1.10 | incoming call: "Side Quests Squad", "WhatsApp audio call", Decline / Accept | |
| 0.15 / 0.75 | Avatar ring pulses (scale 1→1.08→1, 0.3 s each), exactly two | | ring pulses |
| 1.4–5.9 | Hold; camera push 1.10→1.13 | | VO "Forgot to vote? One friendly call. Once. Never during your quiet hours." |
| 4.40 | Stage chip lands left of the phone at (330, 520): "🌙 quiet hours: 10pm–9am" | chip | VO "quiet hours" 5.21 |
| 6.00 | Touch on Accept; in-call screen 6.10 (timer 0:00, counts each second) | | click2 |
| 6.10 | Quiet-hours chip exits (blur); caption card lands at (180, 300) | | |
| 6.20–11.66 | Bot line plays; caption "Hey Leo! The squad's doing Open Mic Night Friday at 7. Maya and Priya are in. You in?" with word highlight from `vo/words/s09-bot.json`; waveform from `vo/env/s09-bot.json` | caption | s09-bot |
| 11.85–12.90 | Leo line; caption swaps to "Leo" / "yeah, I'm in" | | s09-leo |
| 12.95 | Who-line sticker lands under the caption card: "✅ Maya, Ash, Priya, Leo  ❌ 1 can't make it" | who line | card-place-2 |
| 13.20–13.50 | Carry across: the sticker starts flying toward S10's card position | | |

### S10 — It's on (135.5–143.5 s, f0–239) — chip "**08** GO" lands 0.30
**Cut A:**
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.00–0.50 | Leo's phone exits right (`power3.in`); Ash's `#squad` window enters to base; the who-line sticker lands into the plan card's who line (0.5 s) | updated card | |
| 0.60 | Cursor clicks [Close poll now] | | click1; VO 0.4 "When the poll closes" |
| 1.60 | Results card lands: "🎉 It's on" / "Open Mic Night" / when / where / "**Going:** Maya, Ash, Priya, Leo" / "**Rides**" "🚗 Ash → Maya, Priya" "🚗 Leo → driving solo" / "📅 Discord event" (link `#00a8fc`) | | card-place-2 |
| 1.60–2.20 | Camera → card, scale 1.30 | | |
| 1.85–2.20 | Focus ring on the Going line | going | VO "who's going" 1.84 |
| 2.90–3.25 | Ring moves to the Rides block | rides | VO "driving whom" 3.27 |
| 3.95–4.30 | Ring moves to "📅 Discord event" | | VO "a reminder for everyone" 3.96 |
| 5.20 | Sidebar "📅 1 Event" row lands above the channel list | | card-place-3 |
| 5.3–7.8 | Hold, push 1.30→1.34 | | |
| 7.80 | Maroon wipe covers (root overlay 7.8–8.2) | | |

**Cut B:** Ash's phone, group, camera 1.50. 0.00–0.50 Leo's phone exits; the sticker lands into the link bubble's
who-line footer. No close click (0.60 is a hold). 1.60 grey bubble from Side Quests Squad with the same results lines
(bold "Going:" and "Rides"). Rings at the same times on the same lines; 3.95 the ring sits on the calendar invite
bubble, which lands at 5.20: "Open Mic Night" · "Fri, Oct 30 · 7:00 – 9:00 PM" · "Memorial Union 202" · [Add to
Calendar]. Wipe identical.

### S11 — Friday payoff (143.5–148.5 s, f0–149) — both cuts: iMessage, Ash's phone
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.0–0.2 | Wipe reveals the group thread, camera 1.50, status clock 7:02, separator "**Fri** 7:02 PM" | | music section C starts at f0, bed → 0.35 |
| 0.40 | Priya's photo bubble pops (illustration) | the photo | drop_003 |
| 1.30 | Priya "we actually came 😭" | the line | drop_001 |
| 1.95 | Maya ❤️ tapback on the photo | ❤️ | — |
| 2.717 (f82) | Super "YOU ACTUALLY WENT." slams; holds to 4.80 | super | bell (strongest cue) |
| 0.2–4.8 | Camera push 1.50→1.545 | | |
| 4.80 | Maroon wipe covers (148.3–148.7) | | |

### S12 — End card (148.5–152.8 s, f0–128) — both, Cut B adds one chip
| Time | Hero move | Viewer reads | Sound |
| --- | --- | --- | --- |
| 0.0–0.2 | Wipe reveals the cream stage | | |
| 0.20 | "SIDE QUESTS:" words blur in at x 192, cap top y 250 | | |
| 0.45 (f13) | "SQUAD MODE" sticker lands (as S02) | the mark | VO 0.4 "Squad Mode." |
| 0.90–1.60 | One-liner per word: "Squad Mode picks the event, the time and the ride, so you actually go." (Space Grotesk 500 36 px, top y 610, max 1080 px) | | VO "Let's get the whole squad…" |
| 1.70 / 1.85 | Buttons land at y 760: "Add to Discord →", "See the code" | CTA | |
| 2.00 | URL "squad.ashwanthbk.com" Archivo Black 44 px ink, gold underline 8 px, at y 880 | URL, held 2.3 s | |
| 2.20 | Small line "Cubbie Hackathon · Track 3 · team NRK" Space Grotesk 700 24 px `#3d3d3d`, right-aligned to x 1728, y 960 | | |
| 2.40 | **Cut B only:** chip "Live now on Discord." (gold, 3 px ink, radius 10, rotation 3°, Space Grotesk 700 30 px) lands right of the buttons | chip | |
| 0.2–4.3 | No camera move: the end card is dead still once built | | bed fades out 151.3→152.8 |

---

## 7. BANNED

Defaults (from `references/spec.md`), each banned here:
- a black or dark navy void as the ground; small UI floating in the middle of an empty frame (devices are always at
  ≥ 40 % of the frame height or framed by the camera);
- glow, bloom, neon, lens flares, glowing orbs and rings; floating particles;
- purple or blue gradients, mesh gradients, glass cards (the only gradient is the real CallKit ground in S09);
- the generic cream-paper look: serif display, italic accent words, small monospace caps labels, pill-shaped chips.
  Allowed exceptions are the brand's own, used as the site uses them: the cream dotted stage, the gold pill tag in
  S02 (only there), the numbered section chips (Archivo Black on ink, never monospace);
- everything centred (titles are left-aligned at x 192; devices sit centre but supers and chips anchor left);
  everything fading in at once; every element fading and sliding up;
- text that moves while it is read; titles that drift, breathe or scale after they land (S02 title holds inside a
  3 % stage push only; S12 holds dead still);
- corner labels, frame borders, corner brackets, HUD readouts as decoration;
- three cards in a row as a layout, KPI grids, a title over a dimmed screenshot, the logo docked in a corner.

This film:
- spinning, 3D flips, product UI tilted in 3D, glitch, chromatic aberration, camera shake;
- click rings and ripple effects (the cursor press scale and the gold focus ring are the only feedback);
- breathing, floating or pulsing idle loops on UI or titles (the two S09 ring pulses are tied to the ring sound);
  the registry `device-frame-stage` idle float must be removed if that item is used;
- placeholder boxes, grey skeleton bars, lorem ipsum, invented UI copy, invented buttons;
- any word in a public post (Discord channel, plan card, thread, iMessage group, poll, results) that names whose
  limit it was, the amount, or why Jordan said no;
- text meant to be read under 28 px in the framed shot; any super over 2 lines or wider than 680 px;
- real faces, network avatars (dicebear), logos of Discord/WhatsApp/Apple drawn from memory (UI shapes and colours
  only; no wordmarks);
- SF Pro, gg sans, Helvetica or any font not in `assets/fonts/`; Impact fallbacks;
- VO words on screen word for word (supers say something else);
- the words "streamline", "seamless", "revolutionize", "AI-powered", "leverage", "unlock", "effortless";
- a whoosh on every cut, synthesised tones, room tone from elsewhere; more than one SFX inside 0.4 s;
- `Date.now()`, `Math.random()` without a seed, CSS animations, network fetches (all typing dots, waveforms and
  key-tick choices come from timeline time or a seeded index).

---

## 8. QA

Gates: `npx hyperframes check --json` with zero errors in both projects; `snapshot --review`; full watch of both
renders; `npx hyperframes audio <render> --json`: VO peaks −1 to −6.5 dBFS, mix −16 to −14 LUFS, true peak ≤ −1
dBTP, the bed never above 0.13 under a VO word.

| Film t (s) | Both / skin | Must show |
| --- | --- | --- |
| 0.0 | both | cream stage + phone (not black) — the thumbnail |
| 3.6 | both | four bubbles legible (≥ 28 px), names above received bubbles |
| 11.5 | both | whole phone + super, super inside the zone, no overlap |
| 16.0 | both | SIDE QUESTS: + maroon SQUAD MODE sticker, left-aligned |
| 26.6 | A / B | modal or sheet with three ticks, text ≥ 28 px |
| 32.4 | A / B | "You're in 🎉 One more step:" + ring on Connect Google Calendar |
| 37.0 | both | four friend cards, super, nothing in the super zone but the super |
| 43.5 | A / B | the ask message exactly as in story.json |
| 48.0 | both | five event cards fanned, readable titles |
| 59.5 | both | four agent cards, bubbles, filled bars |
| 64.6 | both | Priya close-up → coordinator: public chip in, private half blurred |
| 71.3 | both | coordinator ranking with the gold tag on Open Mic Night |
| 76.5 | A / B | Priya's DM text exact, ring on "$5 and your cap is $0" |
| 85.0 | A / B | the group with nothing about Priya, super |
| 93.6 | A / B | plan card trade-offs legible, ring on "Someone has a budget limit" |
| 101.6 | A / B | who line "✅ Maya, Ash, Priya  ❌ 1 can't make it", no voter faces on the no row |
| 111.8 | A / B | "Only I see this" (A) / the DM buttons (B) |
| 118.5 | both | Jordan's card with the new chip |
| 122.3 | both | incoming call, ringing |
| 131.0 | both | in-call caption with word highlight, waveform moving |
| 137.5 | A / B | results card: Going + Rides exactly as story.json |
| 146.4 | both | photo, "we actually came 😭", ❤️, super |
| 152.0 | A / B | end card complete; B shows "Live now on Discord." |

Seams to snapshot ±0.2 s: 14.0, 22.0, 40.0, 52.0, 74.0, 81.2, 90.0, 108.0, 122.0, 135.5, 143.5, 148.5.

---

## 9. Deviations from SCRIPT.md (product truth wins, per the script's own rule)

1. **S10 rides.** With the cast's seats (Ash 2, Leo 1, Maya 0, Priya 0), `carpool.plan_rides` gives
   "🚗 Ash → Maya, Priya" and "🚗 Leo → driving solo", not the script's "🚆 Leo: Valley Metro light rail…". (And for
   Memorial Union the code's tip would be the Tempe one.) `story.json` uses the code-true lines and keeps the
   script's line under `script_variant_rides_not_code_true`. Change only with the team's yes.
2. **S06 date.** The code renders `<t:unix:F>` → "Friday, October 30, 2026 7:00 PM"; the script wrote "Fri, Oct
   30, 7:00 PM". The spec uses the rendered form in both skins.
3. **S03 order.** The code shows "You're in 🎉 One more step:" (with "Calls & quiet hours" and "Connect Google
   Calendar") before step 2; the script listed step 2 first. The spec follows the code.
4. **Bot name in Cut B.** "Side Quests Squad" (matches the @mention and Discord), not "Squad 🗺️"; 🗺️ is its avatar.
5. **Cut B poll** shows counts without voter avatars so the no stays anonymous (real iOS polls show voters).
6. **S09 bot voice** `am_adam` (the script's `am_puck` is not in this CLI's voice list).

---

## 10. v2 delta (SCRIPT.md v2 wins over everything above)

Applies on top of sections 1–9. Where they disagree, this section and SCRIPT.md v2 win. Built from the regenerated
VO in `shared-assets/vo/` (Kokoro `af_heart` speed 1.0; S09 call lines `am_adam` bot, `am_michael` Leo) and the
whisper (small.en) word times in `shared-assets/vo/words/*.json`.

**Music: every music clip is removed.** `music-bed.mp3` and any `music-bed` / `bed-*` `<audio>` clip, its fades,
ducking and automation come out of both cuts (and out of `shared/`). Nothing replaces it; the narrator talks through
the whole film. SFX stay quiet (≤ 0.5) on visible actions only, never on a meaning-carrying VO word. The v1 BPM, bar
and beat-cue numbers (section 1 `TIME`, section 5.1) are void.

**VO placement:** one `<audio>` clip per WAV (no more split segments); `data-start` = `vo_start`,
`data-media-start` 0, `data-duration` = the WAV length. Scene = 0.3 s head + VO + 0.4 s tail; S01 ends on a 1.0 s
beat after "Sound familiar?"; S09 plays narrator, then the bot call line 0.5 s later, then Leo 0.5 s after that.
S11 now has VO ("And Friday night? They actually went.").

### 10.1 Timing (from `shared-assets/timing.json` v2)

| Scene | Film s | Dur s | Frames | VO clips (offset in scene) |
| --- | --- | --- | --- | --- |
| S01 Cold open | 0.000–13.433 | 13.433 | f0–402 | s01.wav @0.30 (12.14 s) |
| S02 Title | 13.433–20.266 | 6.833 | f403–607 | s02.wav @0.30 (6.14 s) |
| S03 Join | 20.267–38.800 | 18.533 | f608–1163 | s03.wav @0.30 (17.84 s) |
| S04 It watches (new) | 38.800–60.733 | 21.933 | f1164–1821 | s04.wav @0.30 (21.23 s) |
| S05 The agents | 60.733–80.433 | 19.700 | f1822–2412 | s05.wav @0.30 (18.99 s) |
| S06 Asks first | 80.433–95.133 | 14.700 | f2413–2853 | s06.wav @0.30 (13.99 s) |
| S07 The plan | 95.133–110.900 | 15.767 | f2854–3326 | s07.wav @0.30 (15.08 s) |
| S08 Remembers | 110.900–123.900 | 13.000 | f3327–3716 | s08.wav @0.30 (12.31 s) |
| S09 Nudge | 123.900–138.100 | 14.200 | f3717–4142 | s09.wav @0.30 (6.00 s) + s09-bot.wav @6.80 (5.46 s) + s09-leo.wav @12.77 (1.04 s) |
| S10 It's on | 138.100–143.800 | 5.700 | f4143–4313 | s10.wav @0.30 (5.01 s) |
| S11 Friday | 143.800–146.533 | 2.733 | f4314–4395 | s11.wav @0.30 (2.03 s) |
| S12 End card | 146.533–150.766 | 4.233 | f4396–4522 | s12.wav @0.30 (3.54 s) |

Total **150.767 s = 2:30.8**, 4523 frames at 30 fps.

Every scene's internal beats from sections 6.x are retimed to this table: keep the order and motion, move each beat
to the word it belongs to (10.3). The old S04 "The ask" (section 6, `02 ASK`, Ash's @-mention, the "On it 🗺️" reply,
"REAL ASU EVENTS") is deleted; nobody @-mentions the bot anywhere in the film.

### 10.2 S04 — It watches (38.800–60.733 s, f0–657 in scene) — chip "**02** WATCHES" lands 0.30

Both cuts identical until 16.49. Data: `story.json` `scenes.s04` (board, event_cards, candidates, intro).

**The watching board** (stage object, centred, 1500 × 760, cream card, 3 px `#111` border, 8 px hard shadow): header
"Watching this week" (Space Grotesk 600 28 px) with a pulsing maroon dot; five columns Maya, Jordan, Priya, Leo, Ash
(name chips in cast colours, Space Grotesk 600 22 px), each column split into seven day rows Mon–Sun on a
9 AM–11 PM axis (left time ruler, Inter 14 px `#555`). Busy blocks: grey `#c9c2b4` with 2 px `#111` border, label
"busy" or "class" only (never what it is). Mon–Fri 9 AM–4 PM for all five, Leo Thu 6–9 PM, Maya Sat 12–4 PM.
Sun Devil Central feed rail on the board's right (320 px), label ring-able.

| Time (f) | Hero move | Viewer reads | VO word |
| --- | --- | --- | --- |
| 0.00–0.40 (f0–12) | Carry across from S03: the five pick cards shrink into the five column heads | | |
| 0.30 (f9) | Chip "02 WATCHES" lands | chip | |
| 0.40–1.60 (f12–48) | Board lands (sticker), columns build left→right 0.08 s apart, busy blocks fade in per column | five calendars | "favourite part" |
| 1.98 (f59) | Super "IT WATCHES, SO NOBODY HAS TO ASK" slams; holds to 3.6, exits | super | "nobody" |
| 3.75 (f113) | Watching pulse: a thin gold scan line sweeps the board once (1.2 s, `sine.inOut`) | | "background" |
| 7.74 (f232) | Ring on "Sun Devil Central"; event cards stream down the rail (0.3 s apart): Paint Your 3D Print Tue 4:30 PM · Board Game Night Thu 7:00 PM · Open Mic Night Fri 7:00 PM · Desert Sunset Hike Sat 5:00 PM · "+100 more" | titles, times | "Sun Devil Central" |
| 9.75–10.45 (f292–313) | Camera pushes into the columns (scale 1.0→1.08) | | "calendars" |
| 10.50 (f315) | Paint Your 3D Print card slides onto Tue 4:30–6:30 PM: calendars clear, but Jordan, Leo, Ash columns get a grey "not into it" dot; card shakes once, slides back | | "what they like" |
| 12.34 (f370) | Board Game Night slides onto Thu 7–10 PM: Leo's Thu 6–9 PM block flashes red `#e5484d` twice (0.15 s each); card slides back | red block | "clash" |
| 13.10 (f393) | Desert Sunset Hike slides onto Sat 5–7 PM: four grey "not into it" dots (all but Leo); card slides back | | "somebody… but" |
| 15.06 (f452) | Open Mic Night lands on Fri 7–9 PM; a gold `#ffc627` band sweeps across all five columns (0.45 s `power3.out`) | gold band | "fits" |
| 15.55–15.87 (f466–476) | ✓ per friend pops on the band, Maya→Ash 0.08 s apart | five ✓ | "whole squad" |
| 16.49–17.10 (f495–513) | Carry across: the Open Mic card lifts off the band and flies into the chat device as the board blurs out (6 px) | | "posts" |
| 17.94 (f538) | Bot intro message pops (see skins) | intro | "right in the group" |
| 19.42 (f583) | Ring on the bold "Open Mic Night" | title | "Open Mic Night" |
| 20.46 (f614) | Ring on "October 30, 2026 7:00 PM"; hold, push +3 % to scene end | date | "Friday at seven" |

**Cut A (Discord):** `#squad` window (the S03 window, now on the channel), camera 1.35 on the composer area. 17.94 the
bot message lands under "Side Quests Squad" + APP badge, "Today at 4:03 PM":
"👀 Spotted something that fits everyone's week: **Open Mic Night**, October 30, 2026 7:00 PM. Want to go?"
(bold via markdown; `<t:f>` rendered). No typing indicator for the user; nobody types.
**Cut B (iMessage):** Ash's phone, group "the squad 🌵", separator "**Today** 4:03 PM", camera 1.50. 17.40 typing
dots from Side Quests Squad, 17.94 its grey bubble with the same text, title in plain text (no asterisks, no bold).
Both: the plan card itself does not appear here; it lands in S07.

### 10.3 Narration-synced highlights

Times from `vo/words` (whisper start of the first word of the phrase; scene time = VO offset + word start). The ring
(0.35 s draw) or push starts on that frame; the camera move follows per section 4. Name the clip ids
`hl-<scene>-<n>` so they can be retimed together.

| Scene | Word(s) | Scene s (frame) | Film s | What gets ringed / pushed in |
| --- | --- | --- | --- | --- |
| S01 | group chat | 1.47 (f44) | 1.47 | push into the header "the squad 🌵" (+3 %) |
| S01 | "pick something" | 8.36 (f251) | 8.36 | gold ring on Leo's bubble "someone pick something" |
| S01 | nobody picks | 9.80 (f294) | 9.80 | ring on Maya's typing dots as they stop |
| S01 | Sound familiar? | 12.00 (f360) | 12.00 | super slam "WE SHOULD HANG OUT." ×52 WEEKS (holds through the 1 s beat) |
| S02 | Squad Mode | 1.19 (f36) | 14.62 | title sticker "SQUAD MODE" lands |
| S02 | does the picking | 5.64 (f169) | 19.07 | sub line word "picks" goes to 100 % first |
| S03 | You join | 2.91 (f87) | 23.18 | Cut A `/squad join` ring · Cut B "Join the squad" link card ring |
| S03 | what you're into | 5.32 (f160) | 25.59 | ring "What are you into?" field; ticks follow |
| S03 | usually free | 6.30 (f189) | 26.57 | ring "When are you usually free?" |
| S03 | what you can spend | 7.60 (f228) | 27.87 | ring "Up to $20" |
| S03 | hard no's | 8.29 (f249) | 28.56 | ring "Hard no's" |
| S03 | got a car | 10.44 (f313) | 30.71 | ring "Do you drive?" |
| S03 | two free seats | 11.46 (f344) | 31.73 | "Car, 2 seats free" gets selected + ring |
| S03 | Google Calendar | 13.73 (f412) | 34.00 | ring "Connect Google Calendar" |
| S03 | when you're busy | 16.56 (f497) | 36.83 | 🔒 calendar chips pulse on the five pick cards |
| S04 | nobody has to ask | 1.98 (f59) | 40.78 | super slam "IT WATCHES, SO NOBODY HAS TO ASK" |
| S04 | Sun Devil Central | 7.74 (f232) | 46.54 | ring the feed label "Sun Devil Central"; event cards start streaming |
| S04 | everyone's calendars | 9.75 (f292) | 48.55 | push into the five columns (+3 %) |
| S04 | clash | 12.34 (f370) | 51.14 | red flash on Leo's Thu 6–9 PM block under Board Game Night |
| S04 | something that fits | 15.06 (f452) | 53.86 | Open Mic Night lands on Fri 7–9 PM; gold band sweeps all five columns |
| S04 | the whole squad | 15.55 (f466) | 54.35 | five ✓ pop, 0.08 s apart (Maya→Ash) |
| S04 | it posts it | 16.49 (f495) | 55.29 | cut to the chat (carry: the Open Mic card flies into it) |
| S04 | right in the group | 17.94 (f538) | 56.74 | bot intro message pops (Cut A #squad / Cut B grey bubble) |
| S04 | Open Mic Night | 19.42 (f583) | 58.22 | ring the bold title "Open Mic Night" in the intro |
| S04 | Friday at seven | 20.46 (f614) | 59.26 | ring "October 30, 2026 7:00 PM" |
| S05 | their own agent | 3.19 (f96) | 63.92 | four agent cards land |
| S05 | Maya's | 4.01 (f120) | 64.74 | push to Maya's card; "I'd love the open mic 🎤" + 9/10 |
| S05 | Jordan's | 6.34 (f190) | 67.07 | ring Jordan's "happy to drive…" |
| S05 | Leo… hiking | 8.09 (f243) | 68.82 | ring Leo's Desert Sunset Hike 9/10 bar |
| S05 | what's safe | 12.55 (f376) | 73.28 | ring the four shared lines; 🔒 chips dim |
| S05 | the coordinator | 14.03 (f421) | 74.76 | Coordinator card lands / ring |
| S05 | a budget limit | 16.20 (f486) | 76.93 | Priya's chip splits; public half flies to the Coordinator |
| S05 | Not who | 17.45 (f524) | 78.18 | the private half blurs (6 px) |
| S06 | Priya | 1.17 (f35) | 81.60 | Priya's DM fills the frame |
| S06 | five dollars | 2.12 (f64) | 82.55 | ring "it's $5 and your cap is $0" |
| S06 | privately | 7.44 (f223) | 87.87 | push into the DM header (only her) |
| S06 | She's in | 8.28 (f248) | 88.71 | tap + ring "Sure, count me in" |
| S06 | quietly pick something else | 11.16 (f335) | 91.59 | ghost ring on "Pass on this one" |
| S07 | The time | 1.90 (f57) | 97.03 | ring the when line |
| S07 | the place | 2.39 (f72) | 97.52 | ring the where line |
| S07 | why it picked | 2.76 (f83) | 97.89 | ring headline + why |
| S07 | the trade-offs | 4.36 (f131) | 99.49 | ring "Trade-offs" bullets |
| S07 | every agent's take | 7.31 (f219) | 102.44 | thread / inline replies open |
| S07 | there's a poll | 8.95 (f269) | 104.08 | poll lands; camera to it |
| S07 | Votes start rolling in | 9.54 (f286) | 104.67 | first vote (Maya ✅); then Ash, Priya, Jordan ❌ ≥0.8 s apart |
| S07 | only shows a count | 13.91 (f417) | 109.04 | ring "❌ 1 can't make it" |
| S08 | a private message | 2.25 (f68) | 113.15 | Jordan's DM lands |
| S08 | Totally optional | 4.97 (f149) | 115.87 | ring [Skip] |
| S08 | early shift Saturday | 6.48 (f194) | 117.38 | his reply bubble "8am shift Saturday…" |
| S08 | remembers | 8.78 (f263) | 119.68 | "Got it, I'll keep that in mind 🙏" pops |
| S08 | Nothing late on Fridays | 9.96 (f299) | 120.86 | chip "🔒 no events after 9pm on Fridays" lands + ring |
| S09 | one friendly call | 2.65 (f80) | 126.55 | incoming call screen "Side Quests Squad" |
| S09 | quiet hours | 5.42 (f163) | 129.32 | ring Leo's 🔒 quiet-hours chip (value from personas.py; now is outside it) |
| S09 | (bot) Open Mic Night | 8.60 (f258) | 132.50 | caption bubble BOT line |
| S09 | (Leo) I'm in | 13.00 (f390) | 136.90 | caption LEO line; poll gains Leo ✅ |
| S10 | who's going | 2.15 (f64) | 140.25 | ring "Going: Maya, Ash, Priya, Leo" |
| S10 | who's driving who | 2.97 (f89) | 141.07 | ring the two ride lines |
| S10 | a reminder | 4.16 (f125) | 142.26 | Cut A "📅 Discord event" / Cut B calendar invite bubble |
| S11 | Friday night | 0.46 (f14) | 144.26 | timestamp "Fri 7:02 PM" + photo bubble |
| S11 | actually went | 1.40 (f42) | 145.20 | super "YOU ACTUALLY WENT."; the one bell after "went." ends (≈ +0.5 s) |
| S12 | Squad Mode | 0.71 (f21) | 147.24 | title builds |
| S12 | grass to touch | 2.93 (f88) | 149.46 | "Add to Discord →" + URL land |
