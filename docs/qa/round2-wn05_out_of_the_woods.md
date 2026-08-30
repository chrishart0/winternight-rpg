# Round 2 QA — `wn05_out_of_the_woods`

**Verdict: PASS — coherent.** Every round-1 finding is fixed in the tested build. The first- and second-leg objectives agree with the actual route, the bonfire destination has a persistent native-resolution landmark, all 140 settled text/card frames retain their authored text without clipping or scroll-loss, both optional Talks and the Wisdom interrupt complete, and the full ending returns cleanly to the title.

## Runtime evidence

- Compiled project: `build/winternight.ltproj`
- Tested project tree: `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d`
- Pinned engine: `vendor/lt-maker`, commit `1820e585450f6f47605aebd686b2a3f13af181f0` (`engine.lock:2`)
- Method: pinned engine under dummy SDL video/audio. Movement, menu navigation, both Talks, Objective-screen navigation, `Deliver`, scene advances, End-turn confirmation, the bonfire arrival, ending-card advance, and title return were all posted as real pygame key events. No event, flag, unit, resource, or build data was mutated.
- Golden route: burned-dawn opening -> Rand/Luhhan `Talk` -> Tam crosses `wisdom_rows` and triggers Nynaeve -> Rand/Egwene `Talk` -> Tam `Deliver`s at the inn -> Dragon's Fang -> Bran/Thom -> post-delivery Objective screen -> Rand enters `bonfires` -> any-price -> Moiraine's promise/return -> ending card -> title.
- Golden completion: **turn 5**, inside the authored 4–6-turn target. The engine processed 5,299 frames and real inputs comprising 169 Select, 14 Down, 8 Left, 19 Right, 8 Up, and 4 Back presses. Event order is recorded in `/tmp/wn05-round2-golden/result.json`.
- Text coverage: all **140 settled native 240x160 text/card frames** were captured and visually inspected: burned dawn 4, Luhhan 12, Nynaeve 19, Egwene 13, Dragon's Fang 8, Bran/Thom 30, bonfires 11, any-price 15, Moiraine 27 text frames plus one non-text close transition, and ending card 1. All captures measured 240x160. Review sheets are under `/tmp/wn05-round2-golden/sheets/`.
- No-progress probe: the public **End** option and its confirmation were used through turn 10. No Game Over, damage, timeout, state drift, or soft-lock occurred. Rand remained 24/24 at `[1,8]`, Tam remained 20/20 at `[2,8]`, `tam_at_inn` remained false, and both Talk options remained available. Evidence: `/tmp/wn05-round2-loss/turn10-no-loss.png` and `/tmp/wn05-round2-loss/result.json`.

## Round-1 finding verification

### PASS — Round 1 HIGH: settled scene boxes no longer lose their openings

**Repro**

1. Start `wn05_out_of_the_woods` without skipping the opening.
2. Advance only after each box reaches LT's settled `wait` state.
3. Complete both Talks, the `wisdom_rows` interrupt, inn delivery, bonfire arrival, outro, and ending card.
4. Inspect every settled frame at native 240x160.

**After evidence**

- The opening now begins and remains settled as **“At gray dawn, Rand hauls Tam into town.”** Evidence: `/tmp/wn05-round2-golden/frames/001_wn05_out_of_the_woods_sc_c5_burned_dawn.png` and `/tmp/wn05-round2-golden/sheets/burned_dawn-1.png`.
- Nynaeve's refusal now preserves both halves in order: **“Yes, I am. I know what I can do with my medicines,”**, **“and I know when it's too late.”**, **“Don't you think I would do something if I could?”**, and **“But I can't. I can't, Rand.”** Evidence: frames `025`–`028` and `/tmp/wn05-round2-golden/sheets/nynaeve-2.png`.
- The Dragon's Fang text preserves **“The inn survived, but a charred stick has”** followed by **“scrawled the Dragon's Fang across its door.”** Evidence: frames `053`–`054` and `/tmp/wn05-round2-golden/sheets/dragons_fang-1.png`.
- The bonfire reveal preserves **“Beyond the last houses,”** followed by **“the Bel Tine bonfires burn Trolloc dead.”** Evidence: frames `087`–`088` and `/tmp/wn05-round2-golden/sheets/bonfires-1.png`.
- Moiraine's answer preserves **“I will do what I can, but it is beyond”** followed by **“my power to stop the Wheel from turning.”** Evidence: frames `111`–`112` and `/tmp/wn05-round2-golden/sheets/any_price-2.png`.
- The return narration preserves both the departure from the bonfires and the Winespring Inn destination. Evidence: frames `127`–`128` and `/tmp/wn05-round2-golden/sheets/moiraine_heals-2.png`.
- No settled frame showed a third line, clipped glyph, overflow beyond its box, automatic-scroll loss, wrong portrait, or missing opening clause across the 22 inspected review sheets.

**Current source:** the fitted beats are in `design/scenes/out_of_the_woods/scenes.yaml:14-17`, `:29-40`, `:52-64`, `:76-94`, `:105-112`, `:125-154`, `:167-177`, `:189-203`, and `:216-242`.

### PASS — Round 1 HIGH: post-delivery Objective screen is stage-correct

**Repro**

1. Open **Objective** before delivery.
2. Complete both optional Talks and deliver Tam at the inn.
3. Finish the Dragon's Fang and Bran/Thom scenes.
4. At the first free second-leg state, open **Objective** again with real input.

**After evidence**

- Before delivery, Win Conditions reads **“Get Tam to inn”**. Evidence: `/tmp/wn05-round2-golden/initial-objective.png`.
- After delivery, with `tam_at_inn: true` and `tam_litter.position: null`, both the transient objective and Win Conditions read **“Find Moiraine / At the bonfires”**. Loss Conditions reads **“Keep Rand alive”** once. There is no Tam, carrying, litter, or inn reference. Evidence: `/tmp/wn05-round2-golden/leg2-objective.png` and the `objective_snapshots.leg2` record in `/tmp/wn05-round2-golden/result.json`.
- The update occurs on the same `inn_delivery` event that removes Tam and activates `bonfires`; it is not merely a later transient banner.

**Current source:** `design/missions/out_of_the_woods.yaml:59-70`, specifically `change_objective target: both` at line 68 and the deduplicated loss update at line 69. The first-leg static objective remains at line 14.

### PASS — Round 1 MED: bonfire destination now has a persistent, matching landmark

**Repro**

1. Deliver Tam and let the one-time target highlight finish.
2. Move the cursor away, then inspect the second-leg map at native resolution.
3. Select Rand and move the cursor onto the reachable destination at `[13,14]`.

**After evidence**

- Three animated fire tiles form an unmistakable horizontal fire line at `[12,13]`–`[14,13]`, immediately above the two nonblocking arrival tiles. Moiraine and Lan remain visible beside the destination. Evidence: `/tmp/wn05-round2-golden/leg2-map.png`.
- With Rand's movement overlay active, the fire line is still visible directly above the selected arrival tile; the required tile itself remains passable. Evidence: `/tmp/wn05-round2-golden/bonfire-landmark-move.png`.
- The persistent banner says **“Find Moiraine / At the bonfires”**. Thom points southeast and says **“Black smoke marks the Bel Tine fires.”** The old unsupported bridge reference is absent. The spatial cue, objective, guidance, and trigger now agree.

**Current source:** the arrival region is `design/missions/out_of_the_woods.yaml:31`; the stage objective is line 68; the `BBB` landmark is `design/maps/emonds_field.yaml:71`; guidance is `design/scenes/out_of_the_woods/scenes.yaml:153-154`; the arrival description is lines 167–170.

## Golden-path regression checks

### Both Talks and Wisdom interrupt

- Luhhan had a visible `TALK` tag; Rand's adjacent action menu exposed `Talk`, and `sc_c5_luhhan` fired on turn 1. Evidence: `/tmp/wn05-round2-golden/luhhan-talk-menu.png` and frames `005`–`016`.
- Tam's real movement through `[5,8]` interrupted into `sc_c5_nynaeve` on turn 1 and returned control without consuming or blocking the route. Evidence: the event timeline plus frames `017`–`035`.
- Egwene retained a visible `TALK` tag; Rand's adjacent action menu exposed `Talk`, and `sc_c5_egwene` fired on turn 3. Evidence: `/tmp/wn05-round2-golden/egwene-talk-menu.png` and frames `036`–`048`.
- Both Talk options were absent by the second-leg Objective capture, proving both one-shot events were consumed. The relevant event contracts are `design/missions/out_of_the_woods.yaml:39-58`.

### Inn delivery, bonfire win, and full ending

- `Deliver` at the inn fired Dragon's Fang, removed Tam, played Bran/Thom, changed the objective, activated `bonfires`, and returned a controllable second leg. The golden route then reached `[13,14]` on turn 5 without a soft-lock.
- Natural event order was `sc_c5_dragons_fang` -> `sc_c5_bran_and_thom` -> `inn_delivery` completion -> `sc_c5_bonfires` -> `sc_c5_any_price` -> `sc_c5_moiraine_heals` -> `sc_c5_ending_card`. Evidence: `/tmp/wn05-round2-golden/result.json`.
- The win/outro wiring is `design/missions/out_of_the_woods.yaml:71-82`; the ending scenes are `design/scenes/out_of_the_woods/scenes.yaml:155-253`.

### Ending-card pacing

- The final promise and two closing narration pages settle in sequence at frames 5,059, 5,087, and 5,115.
- The authored close transition (`design/scenes/out_of_the_woods/scenes.yaml:243`) separates the last narration from the ending card; the ending card settles at frame 5,164 rather than appearing in the same input beat.
- The card remained in LT's input-wait state for a further 105 engine frames during the explicit hold probe. It neither flashed past nor double-advanced. Evidence: `/tmp/wn05-round2-golden/ending-card-held.png`.
- One real Select then dismissed the card, and the engine reached the title at frame 5,269. Evidence: `/tmp/wn05-round2-golden/return-to-title.png`.

## Coherence trace

| State | Player-facing goal | Visible cue / public action | Observed result |
| --- | --- | --- | --- |
| Burned-dawn opening | Get Tam to the inn | Marked inn door; first-leg banner and Objective agree | Four complete, settled opening pages hand control to the player. |
| Optional village contact | Speak with Luhhan and Egwene | Persistent `TALK` tags and adjacent `Talk` action | Both scenes fire once and their Talk options disappear. |
| Wisdom rows | Continue down the Green with Tam | Highlighted route; automatic movement interrupt | Nynaeve's refusal plays completely and returns control. |
| Inn delivery | Put Tam at the marked door | Distinct doorway and `Deliver` action | Tam is removed; Dragon's Fang and Bran/Thom complete; second leg activates. |
| Second-leg handoff | Find Moiraine at the bonfires | Updated banner and Objective, southeast direction, persistent three-fire landmark | No stale Tam instruction remains; destination is identifiable after the highlight ends. |
| Bonfire arrival | Enter the passable tile below the fire line | Movement overlay reaches `[13,14]`; Moiraine/Lan stand beside it | Bonfire and any-price scenes fire and the chapter wins on turn 5. |
| Close | Bring Moiraine back to Tam | Promise, two closing narration beats, close transition, ending card | Card waits for input, then returns cleanly to title. |
| Loss/recovery | Trigger an authored loss | No enemies or damaging public action exist in this denouement | A real-input turn-10 probe produced no loss or drift. The formal unit-death loss hooks remain unexercisable without forbidden state mutation, unchanged from round 1. |

## Findings

No blocking, high, medium, or low player-facing findings were observed. The unchanged lack of a public-input loss route is an explicit consequence of the zero-enemy denouement (`design/missions/out_of_the_woods.yaml:4`, `:15-17`, `:32`, `:84-85`), not a new regression; no loss was fabricated by mutating runtime state.

## Final verdict

**PASS.** `wn05_out_of_the_woods` is coherent and soft-lock-free on the tested golden route. All three round-1 findings are fixed in-engine, both optional Talks and the Wisdom interrupt still complete, the objective and fire-line landmark make the second leg clear, all settled text is visible, and the paced ending completes to title.
