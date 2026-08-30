# Round 2 QA — `wn01_farm_escape`

**Assessment:** coherent in its objective, route, turn-8 mercy transition, and failure behavior. Every round-1 objective, location-continuity, reinforcement-warning, and text-fitting defect is fixed in the compiled game. One acceptance-specific pacing discrepancy remains: the unskipped opening requires 22 settled text confirmations, not the stated 16.

**Verdict:** FAIL

## Coverage and evidence

Tested the already-compiled `build/winternight.ltproj` at tree `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d` with pinned engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. The routes used `winternight_gen.interactive_flows._run_input_flow` under dummy SDL and posted real pygame key-down/key-up input. The driver inspected state to choose inputs and request screenshots but did not mutate positions, HP, flags, events, or actions.

- Direct golden route: Rand reached the Westwood region and the wound/outro chain completed on turn 4. Runtime trace: `/tmp/wn01-golden.json`.
- Turn-8 farmyard stall: Rand remained at `(7, 7)` through turn 8 while Tam finished at `(15, 5)`; the mercy transition and outro completed without a soft-lock. Runtime trace: `/tmp/wn01-timeoutfar.json`.
- Coordinated optional-cloth route: Rand used **Clean Cloth**, received the visit flag, and escaped on turn 5 while Tam intercepted enemies. Runtime trace: `/tmp/wn01-kitfight.json`.
- Deliberate Rand-death route: Rand fell during turn 2 and the normal Game Over state appeared. Runtime trace: `/tmp/wn01-loss.json`.
- Repeated Tam combat route: Tam participated in six recorded combat transitions while his combat quote fired exactly once. Runtime trace: `/tmp/wn01-quote.json`.
- Initial and turn-3 Objective screens were opened through the real map option menu. Frames: `/tmp/wn01-objective.png`, `/tmp/wn01-objective-turn3.png`.
- All 48 settled boxes on the golden route were captured and visually reviewed. Contact sheets: `/tmp/wn01-golden-contact-01-08.png` through `/tmp/wn01-golden-contact-41-48.png`.

Other reviewed native 240×160 frames:

- Initial map: `/tmp/round2-wn01-initial-map.png`
- Mid-escape map: `/tmp/wn01-mid-escape.png`
- Opening: `/tmp/wn01-opening.png`
- Turn-3 warning: `/tmp/wn01-golden-dialogue/023-wn01_farm_escape_sc_c1_pursuit.png`
- Golden wound bridge: `/tmp/wn01-golden-dialogue/024-wn01_farm_escape_sc_c1_tam_wounded.png`
- Farmyard-stall wound bridge: `/tmp/wn01-timeoutfar-dialogue/025-wn01_farm_escape_sc_c1_tam_wounded.png`
- Optional cloth: `/tmp/wn01-kitfight-dialogue/023-wn01_farm_escape_sc_c1_farm_kit.png`
- Tam combat quote: `/tmp/wn01-quote-dialogue/023-wn01_farm_escape_sc_c1_tam_combat_quote.png`
- Game Over: `/tmp/wn01-game-over.png`

## Intended and observed route

The presented loop is now internally consistent: calm supper and chores → Tam locks the door and reveals the sword → Trollocs breach the farmhouse → Rand runs west while Tam holds → optional cloth pickup → turn-3 warning identifies new Trollocs to the east → Rand reaches the highlighted Westwood region → the Westwood wound scene establishes Tam's injury and the need to return for supplies.

The direct route completed on turn 4. The optional cloth route completed on turn 5. If the player stalls through turn 7, the turn-8 mercy scene now supplies the missing action and location bridge: over a Westwood background, narration says, “Rand breaks west. Tam escapes the pack / and finds him there.” This is coherent even though the pre-scene runtime positions remain Rand `(7, 7)` and Tam `(15, 5)`.

## Coherence trace

| State | Player-facing goal | Visible cue | Public action | Feedback / next goal |
| --- | --- | --- | --- | --- |
| Opening | Understand why Rand must flee | Calm farm, locked door and heron-marked sword, then the visible breach sequence | Advance 22 settled boxes | Final narration says Rand must run west while Tam holds; map control begins |
| Map start | Reach Westwood; keep Rand and Tam alive | Objective screen fully shows **Reach Westwood** and **Rand and Tam must survive**; three starting enemies are visible | Move Rand west; use Tam to block or attack | Rand advances while Tam delays the pursuit |
| Optional cloth | Take useful cloth without abandoning the escape | Blue interaction tile and **Clean Cloth** menu action | Move Rand onto the tile and select **Clean Cloth** | Field Dressing visit flag is set; Rand says to run west |
| Turn 3 | React to pursuers from behind | Tam says “More from the east”; Objective screen adds **Trollocs east**; two enemies spawn at the east edge before player control | Continue west, pan east, or reposition Tam | The player receives a full reaction phase |
| Westwood | Finish the escape | Westwood is named in the objective and the west region is highlighted | Reach the west region with Rand | Wound scene and supplies outro play; chapter completes |
| Turn 8 stall | Resolve the bounded mercy route | No new input goal; the cinematic itself shows Westwood and narrates Rand breaking west and Tam escaping | Finish turn 7 | The scene bridges both characters into Westwood before the wound dialogue and victory |
| Rand death | Avoid losing Rand | Objective screen explicitly names Rand and Tam's survival | Allow Rand to be killed | Standard Game Over appears on turn 2 |

## Finding

### MED — The opening is 22 confirmation boxes, not the stated 16

**Round-1 item:** MED — “The pre-control scene chain is overlong, and several boxes scroll their setup out of view.”

**Repro**

1. Start `wn01_farm_escape` without skipping.
2. Wait for each text box to settle and press Confirm once.
3. Count the boxes before the first free-map state.

**Observed**

The chain requires 22 distinct settled confirmations: 5 in `sc_c1_farmhouse_calm`, 8 in `sc_c1_locked_doors`, and 9 in `sc_c1_door_bursts`. `/tmp/wn01-golden.json` records each distinct settled box and its event; frames 1–22 are visible in the first three contact sheets.

The sequence itself is clear and correctly paced in narrative order—calm chores, locked-door unease, sword reveal, thump, breach, kettle, Tam's command, control handoff—and it is materially shorter than round 1's 28 boxes. The fitting half of the round-1 defect is fixed: no page scrolls away its setup, every recorded rendered-line range stays within two rows, and no reviewed frame clips or overflows. The remaining player-facing consequence is six more mandatory confirmation stops than the supplied 16-box target, including sentence fragments separated across confirmations such as `Tam returns with a heron-marked` / `sword from beneath his bed.`

**Frame evidence:** `/tmp/wn01-golden-contact-01-08.png`, `/tmp/wn01-golden-contact-09-16.png`, `/tmp/wn01-golden-contact-17-24.png`.

**Runtime evidence:** `/tmp/wn01-golden.json` (`dialogue_frames` 1–22 before the first map-control action).

**Suspected source:** `design/scenes/farm_escape/scenes.yaml:14-18` supplies 5 calm boxes, lines `30-37` supply 8 locked-door/sword boxes, and lines `49-58` supply 9 breach boxes; `design/missions/farm_escape.yaml:32-34` calls all three scenes consecutively before control.

**Smallest remedy:** condense those three scene beat lists to 16 settled boxes while preserving the observed calm → sword → breach ladder and the enforced two-row/56-character fit. Verify by advancing the unskipped compiled scene one settled page at a time, counting exactly 16 confirmations, and visually inspecting all 16 native frames.

## Round-1 finding re-verification

### HIGH — Objective clipping and hidden loss rule: FIXED

- Initial Objective frame `/tmp/wn01-objective.png` cleanly shows **Reach Westwood** and **Rand and Tam must survive** with no panel overlap or duplicate loss text.
- After the turn-3 `change_objective both`, `/tmp/wn01-objective-turn3.png` shows **Reach Westwood** / **Trollocs east** while the complete two-line loss rule remains visible.
- Current authored source is `design/missions/farm_escape.yaml:9-12,35,48`.

### HIGH — Turn-8 farmyard victory lacked a location bridge: FIXED

- `/tmp/wn01-timeoutfar.json` records the wound trigger on turn 8 with Rand still at `(7, 7)` and Tam at `(15, 5)`.
- `/tmp/wn01-timeoutfar-dialogue/025-wn01_farm_escape_sc_c1_tam_wounded.png` then shows the Westwood background and the explicit bridge, “Rand breaks west. Tam escapes the pack”; the next settled box completes “and finds him there.”
- The route reaches the same supplies outro and terminates without a soft-lock.
- Current bridge source: `design/scenes/farm_escape/scenes.yaml:100,108-109`; timeout entry: `design/missions/farm_escape.yaml:60-67`.

### MED — Wound dialogue over the wrong background: FIXED

Both the direct route and farmyard-stall route show `westwood_night`, not the farmhouse exterior: `/tmp/wn01-golden-dialogue/024-wn01_farm_escape_sc_c1_tam_wounded.png` and `/tmp/wn01-timeoutfar-dialogue/025-wn01_farm_escape_sc_c1_tam_wounded.png`. Current source: `design/scenes/farm_escape/scenes.yaml:100`.

### LOW — Turn-3 warning omitted the reinforcement direction: FIXED

`/tmp/wn01-golden-dialogue/023-wn01_farm_escape_sc_c1_pursuit.png` visibly says, “More from the east. West, lad. Run.” The updated Objective screen also shows **Trollocs east**. The turn-3 trace records both pursuers at `(16, 4)` and `(16, 10)` before the player's action, so the player receives a reaction phase rather than an enemy-phase ambush. Current source: `design/scenes/farm_escape/scenes.yaml:82-93` and `design/missions/farm_escape.yaml:43-48`.

## Checks that passed

- Golden escape completes on turn 4 with Rand at the Westwood region `(0, 5)` when the wound event begins.
- The turn-8 farmyard mercy path now bridges the off-objective position coherently and completes without a soft-lock.
- Optional **Clean Cloth** remains usable; the visit flag is present from turn 2 onward and the coordinated route wins on turn 5.
- Rand's deliberate death produces `_lose_game: true` and the standard Game Over screen on turn 2.
- `sc_c1_farmhouse_calm`, `sc_c1_locked_doors`, and `sc_c1_door_bursts` each fire exactly once per run.
- Tam's combat quote fires exactly once despite six recorded combat transitions and shows the correct Tam battle portrait.
- All 48 settled golden-route frames remain within the 240×160 surface; every recorded box uses at most two rendered text rows. The optional cloth and Tam quote frames are also clean.
- No golden, optional, turn-8, or loss route soft-lock was observed.

**VERDICT: FAIL**
