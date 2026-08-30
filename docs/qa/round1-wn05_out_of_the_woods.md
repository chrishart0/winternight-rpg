# Round 1 QA — `wn05_out_of_the_woods`

**Verdict: FAIL — partially coherent.** The route is completable, the two-leg structure works, and the chapter finishes naturally in five turns with both optional Talks. The earliest player-understanding break is the opening scene: at the settled input prompt, overlength text has already scrolled its opening clauses out of the two-line GBA box. The second leg then presents a stale Win Condition in the Objective screen and points to “bonfires”/“bridges” that have no corresponding map art.

## Runtime evidence

- Compiled project: `build/winternight.ltproj`
- Project tree: `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a`
- Engine commit: `1820e585450f6f47605aebd686b2a3f13af181f0`
- Method: pinned engine under dummy SDL video/audio; all movement, menus, Talks, region actions, scene advances, Objective-screen navigation, and End-turn confirmations were posted as real pygame key events. No events, flags, actions, units, or build data were mutated.
- Golden route: burned-dawn intro -> Rand/Luhhan Talk -> Tam crosses `wisdom_rows` and triggers Nynaeve -> Rand/Egwene Talk -> Tam `Deliver`s at the inn -> Dragon's Fang -> Bran/Thom -> open Objective screen -> Rand reaches `bonfires` -> any-price -> Moiraine's promise/return -> ending card.
- Golden completion: **turn 5**, within the authored 4–6-turn target. Both Talks were consumed, `wisdom_rows` fired, `tam_at_inn` became true, and the ending returned cleanly to the title. The run used 132 Select presses, 10 Down, 9 Left, 20 Right, 6 Up, and 2 Back presses over 3,897 engine frames.
- Visual coverage: all **96 settled text frames** were captured and inspected at native 240x160: intro 3, Luhhan 8, Nynaeve 14, Egwene 9, Dragon's Fang 4, Bran/Thom 21, bonfires 8, any-price 10, Moiraine 18, ending card 1.
- Deliberate no-progress probe: used the public **End** option and its confirmation through turn 10. No timeout, Game Over, damage, or state drift occurred; Rand remained 24/24 at `[1,8]`, Tam remained 20/20 at `[2,8]`, and `tam_at_inn` remained false. Evidence: `/tmp/wn05-loss-attempt-turn10.png`.

## Findings

### HIGH — Overlength scene beats lose their openings before the settled prompt

**Player consequence:** Essential setup and connective prose are absent from the frame where the engine waits for the player's next input. At instant text speed, scenes read as sentence fragments. This damages the burned-dawn reveal, Nynaeve's refusal, Dragon's Fang, the explanation of the bonfires, Rand's any-price plea, and Moiraine's closing promise.

**Repro**

1. Start `wn05_out_of_the_woods` without skipping the intro and wait for each text prompt.
2. Continue through the `wisdom_rows`, inn delivery, bonfires, and ending, advancing only after each box reaches its wait state.
3. Compare the settled frame with the authored beat.

**Observed examples**

- Intro frame 1 begins **“At gray first light…”**; the authored opening “Rand has hauled his fevered father all night toward safety” is no longer visible. Evidence: `/tmp/wn05-frames/001_wn05_out_of_the_woods_sc_c5_burned_dawn_01.png` and `/tmp/wn05-sheets/sc_c5_burned_dawn-1.png`.
- Nynaeve's medicine line settles on **“with my medicines, and I know / when it's too late.”**, losing “Yes, I am. I know what I can do”. Her next line loses “Don't you think I would do”. Evidence: `/tmp/wn05-frames/018_wn05_out_of_the_woods_sc_c5_nynaeve_07.png`, `/tmp/wn05-frames/019_wn05_out_of_the_woods_sc_c5_nynaeve_08.png`, and `/tmp/wn05-sheets/sc_c5_nynaeve-1.png`.
- The Dragon's Fang reveal settles on the uncapitalized fragment **“stick has scrawled the Dragon's / Fang across its door.”**, losing “The inn survived, but a charred”. Evidence: `/tmp/wn05-frames/037_wn05_out_of_the_woods_sc_c5_dragons_fang_03.png` and `/tmp/wn05-sheets/sc_c5_dragons_fang-1.png`.
- The bonfire scene's first box settles on **“dead. Oily black smoke bends away…”**, losing the only clause that says the Bel Tine bonfires are burning Trolloc dead. Evidence: `/tmp/wn05-frames/060_wn05_out_of_the_woods_sc_c5_bonfires_01.png` and `/tmp/wn05-sheets/sc_c5_bonfires-1.png`.
- The last any-price box settles on **“beyond my power to stop the / Wheel from turning.”**, losing Moiraine's crucial “I will do what I can”. Evidence: `/tmp/wn05-frames/077_wn05_out_of_the_woods_sc_c5_any_price_10.png` and `/tmp/wn05-sheets/sc_c5_any_price-2.png`.
- The return-to-inn narration settles on **“Inn. Rand keeps darting ahead, / then waiting.”**, losing “They turn from the bonfires and start back toward the Winespring”. Evidence: `/tmp/wn05-frames/087_wn05_out_of_the_woods_sc_c5_moiraine_heals_10.png` and `/tmp/wn05-sheets/sc_c5_moiraine_heals-2.png`.

**Suspected source:** `design/scenes/out_of_the_woods/scenes.yaml`, especially lines 14–16, 28–29, 47, 50, 67, 73–74, 79, 91–93, 107–111, 115, 140–141, 145, 160, 163, 168, and 181–198.

**Smallest remedy:** Split every beat that renders beyond two native-resolution lines into separate narration/dialogue beats (or explicit supported pages), preserving the speaker and wording. Do not rely on automatic scrolling to retain the opening at the input wait.

**Retest:** Capture every text wait at 240x160 again; each frame must begin with the authored first word for that page, contain complete clauses, and retain the correct speaker portrait.

### HIGH — The leg-two Objective screen still orders the player to bring the now-removed Tam to the inn

**Player consequence:** After delivery, a player who checks **Objective** sees an impossible old win condition and can reasonably conclude that the chapter failed to register the delivery. The transient event objective and Bran/Thom's direction say to find Moiraine, but the durable Objective screen contradicts them.

**Repro**

1. Deliver `tam_litter` to the inn and finish the Dragon's Fang plus Bran/Thom scenes.
2. At the next free state, open the map option menu and choose **Objective**.
3. Observe the Win Conditions panel after `tam_at_inn` is true and Tam has been removed.

**Observed:** The screen still shows **“Bring Tam to the Wi…”** instead of “Run to the bonfires / Find Moiraine beyond the bridges.” Evidence: `/tmp/wn05-leg2-objective.png`. The contemporaneous map state is `/tmp/wn05-leg2-map.png`.

**Suspected source:** `design/missions/out_of_the_woods.yaml:14` supplies the static win-condition text, while the attempted second-leg switch at `design/missions/out_of_the_woods.yaml:68` only produces the transient simple objective and does not replace the Objective-screen entry.

**Smallest remedy:** Make the durable objective state stage-aware. If the engine cannot replace the Objective-screen text from this event action, use a static two-stage objective that remains true in both legs (for example, get Tam to the inn, then find Moiraine) while retaining the shorter transient current-step prompts.

**Retest:** Open **Objective** before and after inn delivery with real input. Before delivery it must direct Tam to the inn; after delivery it must mention only Rand, Moiraine, and the bonfire destination.

### MED — The bonfire destination is reachable but is ordinary grass with no bridge or bonfire landmark

**Player consequence:** The second-leg destination is discoverable only from the one-time cursor flicker and the nearby Moiraine/Lan sprites. Once the cursor moves, the named landmark has no persistent map identity. The dialogue says “the other side of the bridges,” but the map contains no bridge/water feature, and the two target tiles contain no fire or bonfire prop.

**Repro**

1. Complete the inn delivery and observe the one-time target flicker.
2. Move Rand toward `[13,14]`/`[14,14]`.
3. Inspect the destination before confirming movement.

**Observed:** The region is reachable on turn 5, but both target tiles are plain grass. `/tmp/wn05-leg2-map.png` shows the only persistent visual context (Moiraine and Lan at the lower right); `/tmp/wn05-bonfires.png` shows Rand's movement overlay reaching an otherwise unmarked grass tile.

**Suspected source:** `design/missions/out_of_the_woods.yaml:31` places `bonfires` at `[13,14]`, while the `burned_dawn` rows in `design/maps/emonds_field.yaml:58-73` contain grass at that destination. `design/scenes/out_of_the_woods/scenes.yaml:126-127` names bridges that the map does not depict, and line 140 names bonfires that have no map landmark.

**Smallest remedy:** Add an unmistakable nonblocking bonfire/pyre marker on or adjacent to the destination and either depict the referenced crossing or remove “bridges” from the direction. The existing `B` fire terrain is blocking, so do not make the required arrival tile itself impassable.

**Retest:** After moving the cursor away from the initial flicker, a first-time player viewing the native map must still be able to point to the bonfires and trace the route without knowing coordinates.

## Coherence trace

| State | Player-facing goal | Visible cue/action | Result |
| --- | --- | --- | --- |
| Burned-dawn reveal | Get Tam to the surviving inn | Intact inn/door tile, yellow doorway, initial current-step prompt | Route is clear, but intro prose openings scroll away (HIGH). |
| Optional village contact | Talk to Luhhan and Egwene | Both have persistent `TALK` tags; Rand gets `Talk` in the action menu | Both Talks fired with correct portraits; no speaker mismatch observed. |
| Wisdom rows | Pass Nynaeve while carrying Tam down the Green | Automatic interrupt on the highlighted route; no hidden menu verb | Fired on turn 1 and returned control; refusal lands emotionally, but several long lines lose their openings (HIGH). |
| Inn delivery | Move Tam to the marked inn door and choose `Deliver` | Door is distinct and the action label matches the objective | Dragon's Fang and Bran/Thom fire, Tam is removed, and the chapter advances. |
| Leg-two handoff | Run Rand to Moiraine at the bonfires | Bran/Thom give the new direction and the cursor flickers at the destination | Durable Objective screen is stale (HIGH); destination lacks its named landmarks (MED). |
| Bonfire arrival | Enter `[13,14]`/`[14,14]` with Rand | Reachable grass beside Moiraine/Lan; `Bonfires` event interrupts movement | Win path fires on turn 5 with no soft-lock. |
| Close | Bonfires -> any-price -> Moiraine promises help -> ending question | 37 consecutive settled frames, then `winternight_ending` card | Logical sequence and portraits are coherent; ending card is legible, but overflow removes crucial opening clauses (HIGH). |
| Loss/recovery | Trigger an authored loss | Only unit-death conditions exist; there are no enemies or damaging hazards | No public-input loss path exists. Ten deliberate empty turns caused no loss or timeout. This is consistent with the zero-enemy denouement but means the formal loss path could not be exercised in play. |

## Checks that passed

- `burned_dawn` continuity is strong: the native map retains the intact inn, converts two of the four house clusters to rubble, and shows rubble in the opening camera; the panorama shows gray dawn, smoke, damaged roofs, villagers, and foreground wreckage. Evidence: `/tmp/wn05-burned-dawn-map.png`, `/tmp/wn05-burned-dawn-reveal.png`, and `/tmp/wn05-golden-start-map.png`.
- Both optional Talks were available, visibly labeled, triggered, and removed after use.
- `wisdom_rows` interrupted real movement and did not consume or strand the route.
- Tam's inn delivery removed Tam and activated the second leg.
- The bonfire region is reachable; the win event, outro, and ending card all fired.
- Five turns with both optional Talks is within the authored target and does not drag mechanically despite the zero-enemy structure.
- Nynaeve/Rand, Luhhan/Rand, Egwene/Rand, Bran/Rand/Thom, and Lan/Rand/Moiraine portraits matched their speakers in all inspected frames.
- The ending card cleanly displays **“Light, who am I?”** against the night-road art. Evidence: `/tmp/wn05-frames/096_wn05_out_of_the_woods_sc_c5_ending_card_01.png`.

## Final verdict

**FAIL.** The chapter is soft-lock-free and mechanically completable in the intended turn range, but the settled-frame text loss is pervasive and removes essential story clauses. The stale second-leg Objective screen is a direct progression contradiction, and the unmarked bonfire/bridge destination weakens the final required route.
