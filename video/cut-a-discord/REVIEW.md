# REVIEW: Cut A "Hook + Discord" (v2, 150.767 s, 4523 frames, 1920×1080, 30 fps)

Contract: `../SCRIPT.md` v2 (wins) + `../SPEC.md` section 10. Times from `assets/timing.json` v2, highlight words from
`assets/vo/words/*.json`, copy from `assets/story.json`.

## What changed for v2

- **Assets** copied in from `../shared-assets` (all 14 VO WAVs incl. new `s11.wav`, words, env, sfx, story, timing);
  `music-bed.*` deleted. Shared scenes S01, S02, S05, S09, S11, S12, `wipes.html` and the new
  `s04-watch-board.html` copied unchanged from `../shared/compositions/`.
- **S04 "It watches"** replaces the old "ask" (`s04-ask.html` deleted). Two hosts back to back: the shared board
  (`s04`, film 38.800–55.900) and `compositions/s04-chat.html` (`s04chat`, 55.900–60.733). The chat part starts on
  the board's last frame (bare stage, Open Mic card centred at 1.4), lands `#squad`, flies the card into it, then
  the bot posts the watcher intro as a normal Discord bot message (APP badge, "Today at 4:03 PM", bold title,
  `<t:f>` rendered as "October 30, 2026 7:00 PM"). Nobody types or @-mentions. Rings: title 58.22, date 59.26.
- **History fixed** in S06, S07, S10: Ash's "@Side Quests Squad something chill…" and the "On it 🗺️" reply are gone;
  the bot's watcher intro sits where they were, so #squad matches S04 frame for frame.
- **Retimed to timing.json, rings on the VO word** (SPEC 10.3, `hl-<scene>-<n>` ids):
  - S03 (18.533): /squad join autocomplete row 2.91 · What are you into? 5.32 (ticks follow) · usually free 6.30 ·
    Up to $20 7.60 · Hard no's 8.29 · Do you drive? 10.44 · Car, 2 seats free 11.46 · Connect Google Calendar 13.73 ·
    locked calendar chips pulse 16.56 · super 16.95. Modal (2/2) is no longer shown (not narrated); ends on bare stage.
  - S06 (14.7): limit 2.12 · pull back to show the DM header 7.44 · tap + ring "Sure, count me in" 8.28 · whip to
    #squad 9.40 · super 9.90.
  - S07 (15.767): card 0.60 · when 1.90 · where 2.39 · headline + why 2.76 · trade-offs 4.36 · thread 6.70 (posts from
    7.31) · poll 8.95 · votes 9.54 / 10.34 (Ash's click) / 11.14 / 11.94 · "❌ 1 can't make it" 13.91 · bloom 15.12.
  - S08 (13.0): DM 2.25 · [Skip] 4.97 · his reason typed 5.95–7.20 · "Got it, I'll keep that in mind 🙏" 8.78 ·
    chip lands + ring 9.96 · super 10.50.
  - S10 (5.7): close poll 0.60 · results 1.35 · Going 2.15 · Rides 2.97 · Discord event ring + "1 Event" 4.16.
- **index.html** rebuilt from timing.json: 13 scene hosts, wipes (13.233 / 143.6 / 146.333), one VO clip per WAV
  (14), S09 bot (0.75) and Leo (0.9) through the phone EQ. **No music anywhere.** Scene SFX all ≤ 0.5, retimed onto
  the visible actions (key ticks, clicks, card place, pops, lock).

## Late VO swaps (after the first v2 pass)

- **s01.wav** replaced with the new hook ("We should hang out. The most-sent, least-done text in college…", 12.129 s):
  re-ran whisper (small.en) into `assets/vo/words/s01.json` + `s01.transcript.json`; S01 re-synced: Priya's bubble on
  the hook 0.40, header push 1.63, "fr" 5.94, "down" 6.45, Leo 7.30, ring "pick something" 7.87, typing 8.40-9.07 +
  ring on "nobody ever picks" 9.07, super 12.00 (the WAV pauses 1.14 s before "Sound familiar?"). VO clip 12.129.
- **s04.wav** regenerated ("…real campus events from Sun Devil Central…", 21.528 s, timing.json still says 21.227):
  VO clip set to 21.528 (ends 60.628, inside the scene); `words/s04.json` refreshed from whisper. Board: Sun Devil
  Central ring + feed stream 6.74, push into calendars 8.72, Paint Your 3D Print verdict 9.80; quiet card-place as it slides back at 10.90 (the new WAV pauses 1.5 s after
  "what they like"). Chat: post on "group"
  17.82, rings "Open Mic Night" 19.70 and "Friday at seven" 20.80; the chip fades as the camera pushes in.
- So the cut-a copies of `s01-cold-open.html` and `s04-watch-board.html` now differ from `../shared/compositions/`
  (only these timings + one SFX in the board); port them back to shared and Cut B.

## Gates

- `npx hyperframes check --json`: **ok, 0 errors** (lint 0, runtime 0, layout 0, motion 0, contrast 0, craft 0).
  The one `dead_stretch` (S06 DM hold) was fixed with a slow push.
- `npx hyperframes snapshot` at all 13 scene midpoints and every SPEC 10.3 highlight time (+0.3 s so the ring has
  drawn): 74 frames looked at, plus re-shots after fixes (S03 join ring, S03 label ring clip, S04 chat framing).

## Fixed after looking

- S03 "/squad join" ring was clipped by the composer field (overflow hidden): moved to the autocomplete row.
- S03 "What are you into?" ring was clipped by the modal header: list gets 10 px head-room, scrolls stop 14 dp early.
- S04 chat first framing left the window high with empty cream below: message now sits at screen y 700.

## Warnings kept on purpose

- `text_below_floor` / `line_unread`: establishing shots (window at 1.0 / 0.82 / 0.90, the board) and VO-paced UI;
  every read the narrator names is ringed at ≥ 28 px.
- `contrast_aa_failure`: Discord's own greys and the shared iMessage greys.
- `composition_file_too_large` (s03, s07, shared s05/s04 board); `gsap_repeated_fromto_without_baseline` in shared S09.

## Final polish (before the final render)

- Section chips in S03, S06, S07, S08, S10 moved to the bottom-right cream corner (the app window owns the top-left).
  Where the camera fills that corner too they leave: S03 at 3.4 (modal shots fill the frame), S08 at 5.6, S10 at 3.6.
- Maroon wipes added at S03→S04 (start 38.6) and S04→S05 (start 60.533) (`w4`, `w5` in `wipes.html`). S03's exit
  moved +0.2 s so it is still moving under the incoming panel; the S04 board lands at 0.0 (its SFX too) and the S05
  event cards fade in from 0.0, so the reveal never shows a bare stage.
- S06: buttons stay until "if she'd said no" (9.63): gold ring `hl-s06-2` on "Pass on this one", then "Got it,
  thanks 🙏" (10.05), whip to #squad 10.75, super 11.16.
- Silences: only the 1.43 s beat after "Sound familiar?" (12.35) is over 1.2 s.

## Known gaps

- Bot intro (4:03) and plan card (4:05) are shown as separate Discord groups; real Discord would merge them.
- craft `dead_stretch` in S01 (2.77–5.79 s) after the S01 VO swap; left as is.
