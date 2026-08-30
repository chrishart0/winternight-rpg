# Round 1 QA — `wn01_farm_escape`

**Assessment:** partially coherent. The direct westward escape is playable and resolves correctly, the deliberate Rand-death loss works, the optional cloth can be collected on a coordinated route, and the scripted scenes do not double-fire. The chapter still fails first-time-player QA because the Objective screen clips both the destination and the meaningful loss rule, and turn 8 awards victory from the farmyard without Rand using the stated Escape action.

**Verdict:** FAIL

## Coverage and evidence

Tested the already-compiled `build/winternight.ltproj` at tree `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a` with the pinned engine. All routes were driven through posted pygame key down/up input under dummy SDL; no event, action, position, HP, or flag was mutated by the driver.

- Direct golden route: Rand ran west, Tam held, the turn-3 wave arrived, Rand selected **Escape** at `(0, 5)`, and the wound/outro chain completed on turn 4. Runtime trace: `/tmp/wn01-golden.json`.
- Coordinated optional route: Rand selected **Clean Cloth** at `(10, 5)` while Tam attacked the immediate threats; Rand then escaped on turn 5. Runtime trace: `/tmp/wn01-kitfight.json`.
- Deliberate loss: both units waited; Rand took 12 damage on turn 1, was killed on turn 2, and the normal Game Over state appeared. Runtime trace: `/tmp/wn01-loss.json`.
- Turn-8 stall near the exit: Rand stopped at `(1, 6)` and waited through turn 8. Runtime trace: `/tmp/wn01-timeout.json`.
- Turn-8 stall away from the Westwood: Rand stopped at farmyard tile `(7, 7)` while Tam fought eastward to `(15, 5)`. Turn 8 still played the Westwood wound scene and awarded victory. Runtime trace: `/tmp/wn01-timeoutfar.json`.
- Tam quote repeat check: Tam initiated attacks on turns 1, 2, and 3. `sc_c1_tam_combat_quote` fired exactly once. Runtime trace: `/tmp/wn01-quote.json`.

Required native 240×160 frames were captured and visually inspected:

- Opening cutscene: `/tmp/wn01-opening.png`
- Initial map: `/tmp/wn01-initial-map.png`
- Mid-escape map: `/tmp/wn01-mid-escape.png`
- Turn-8 wound: `/tmp/wn01-wound-timeout.png`
- Game Over: `/tmp/wn01-game-over.png`

Additional reviewed frames:

- Objective screen: `/tmp/wn01-objective.png`
- Optional cloth dialogue: `/tmp/wn01-kitfight-dialogue/029-wn01_farm_escape_sc_c1_farm_kit.png`
- Optional-route failure variant: `/tmp/wn01-kit-game-over.png`
- Tam combat quote: `/tmp/wn01-quote-dialogue/029-wn01_farm_escape_sc_c1_tam_combat_quote.png`
- Distant-stall wound narration: `/tmp/wn01-timeoutfar-dialogue/031-wn01_farm_escape_sc_c1_tam_wounded.png`

## Intended and observed route

The intended loop is: calm supper and sword reveal → door breach/kettle throw → send Rand west while Tam holds → optional clean-cloth pickup → react to the turn-3 pursuers → use **Escape** on the Westwood tile → see Tam wounded and prepare to return for supplies.

The direct observed route matches that loop and ends on turn 4. The optional route also works, but only if Tam proactively kills the Trolloc next to the cloth route on turn 1; taking the cloth while leaving Tam in place for that first turn causes Rand to die on turn 2 even if Tam attacks on turn 2. That danger is visible and the coordinated route is valid, so it is not filed as an unfair ambush. The turn-8 route does not match the loop: it converts waiting into unconditional victory regardless of Rand's location.

## Coherence trace

| State | Player-facing goal | Visible cue | Public action | Feedback / next goal |
| --- | --- | --- | --- | --- |
| Opening | Get Rand out west while Tam holds | Final breach narration names the Westwood; three starting Trollocs are visible around the farmhouse | Advance 28 text boxes, then move Rand | Control begins with Rand selected |
| Map start | Escape into the Westwood | West is named, but the exit is off-camera; the Objective screen clips its full name | Move Rand west; inspect threat ranges | Rand advances while Tam blocks or attacks |
| Optional cloth | Take useful cloth without abandoning the escape | Blue-highlighted `(10, 5)` tile; **Clean Cloth** appears in the action menu | Move Rand onto the tile and select **Clean Cloth**; use Tam to intercept | Field Dressing is given and Rand says to run west |
| Turn 3 | React to another wave | Tam says “Another pack,” but gives no direction; the spawned units are off-camera | Pan east or continue west; move/attack normally | Pursuers act only after the player receives a phase |
| Westwood exit | Finish the escape | Green exit tile at `(0, 5)` and **Escape** menu action | Select **Escape** with Rand | Wound scene, victory, then supplies scene |
| Turn 8 without Escape | No new goal is shown | No deadline or objective change | Merely finish turn 7 | Wound scene and victory fire from any Rand position, contradicting the stated action |
| Rand death | Avoid losing Rand | Objective screen shows only the clipped prefix “Rand must survive;” | Let enemies kill Rand | Standard Game Over screen appears; no soft-lock |

## Findings

### HIGH — The Objective screen clips the destination and hides Tam's loss condition

**Repro**

1. Start `wn01_farm_escape` and advance the opening scenes.
2. Open the map option menu with real input.
3. Select **Objective**.

**Observed**

At 240×160, the right status panel covers the end of the win string. The visible line stops at `Escape into the Wes`, so the named destination is not readable in the persistent objective UI. The loss line stops at `Rand must survive;`, hiding the fact that Tam's death also loses the chapter until `tam_wound_started` becomes true. This matters because Tam is expected to hold several enemies and his survival rule changes later.

**Frame evidence:** `/tmp/wn01-objective.png`

**Suspected source:** `design/missions/farm_escape.yaml:9-12` — the authored win text and two synthesized unit-death clauses exceed the Objective panel's usable width.

**Smallest remedy:** use short strings that fit the native panel, for example a shorter westward escape label and a compact loss label naming both Rand and Tam. Verify by opening the real Objective screen at 240×160 and confirming every target/rule is visible without overlap.

### HIGH — Turn 8 awards an unannounced false victory from the farmyard

**Repro**

1. Move Rand only to `(7, 7)`, a grass/farmyard tile east of the blocked Westwood boundary.
2. Use Tam to kill the visible attackers and turn-3 pursuers.
3. Keep Rand at `(7, 7)` and end turns through turn 7 without ever selecting **Escape**.

**Observed**

At the start of turn 8, the chapter plays `sc_c1_tam_wounded`, sets the wound flags, and wins. Rand is still at `(7, 7)` and Tam is at `(15, 5)`, but the scene says Tam “finds Rand under the Westwood trees.” No deadline, alternate survival objective, or “Tam will find you” condition was ever presented. The stall route therefore rewards failure to perform the only stated action and teleports the fiction to a location neither unit reached.

The softer stall at `(1, 6)` behaves the same way. In that run all five enemies were dead by turn 5, leaving turns 5–7 as empty waits before the automatic win.

**Frame evidence:** `/tmp/wn01-timeoutfar-dialogue/031-wn01_farm_escape_sc_c1_tam_wounded.png`, `/tmp/wn01-wound-timeout.png`

**Runtime evidence:** `/tmp/wn01-timeoutfar.json` records `wound_trigger_turn: 8`, Rand at `[7, 7]`, and Tam at `[15, 5]`.

**Suspected source:** `design/missions/farm_escape.yaml:58-65` — `farm_timeout_success` checks only `tam_wound_started == false`; it neither checks `westwood_exit` nor changes/presents an alternate objective before calling `win`.

**Smallest remedy:** keep victory gated on Rand's **Escape** action. If turn 8 must be a hard bound, state it in the objective and make the turn-8 result match the stated rule; if the authored intent is a story rescue, visibly change the objective before the timeout and move the units/scene to a location consistent with what happened. Verify from both `(7, 7)` and `(1, 6)`.

### MED — The pre-control scene chain is overlong, and several boxes scroll their setup out of view

**Repro**

1. Start the chapter without skipping.
2. Advance each settled text box with confirm input.
3. Count the boxes before map control and inspect the settled native frames.

**Observed**

The chain fires in the correct order and exactly once, but requires 28 text confirmations before the player can move: 9 calm-farmhouse boxes, 13 locked-door/sword boxes, and 6 visible door-burst text boxes. Five opening messages render as four text rows in a two-row GBA box. By the confirmation state only the trailing fragment remains; for example, the opening frame shows `and his father Tam find the flock / quiet and the house whole.` rather than the sentence's opening, and the kettle frame retains only `it and the second creature behind / it.` There is no pixel overflow beyond the box, but the player cannot pause on or re-read the complete line as one page. With the playable escape itself ending on turn 4, the long ordinary-supper and sword-question sequence dominates the chapter's pacing.

**Frame evidence:** `/tmp/wn01-opening.png`, `/tmp/wn01-golden-dialogue/005-wn01_farm_escape_sc_c1_farmhouse_calm.png`, `/tmp/wn01-golden-dialogue/025-wn01_farm_escape_sc_c1_door_bursts.png`

**Suspected source:** the three consecutive calls in `design/missions/farm_escape.yaml:32-34`, plus long/redundant beats in `design/scenes/farm_escape/scenes.yaml:14-22`, `34-46`, and `58-64`.

**Smallest remedy:** trim repeated supper/chores and sword follow-up beats, and split or shorten any line that exceeds two rendered rows. Keep the calm → locked doors → burst escalation, which otherwise reads in the correct order. Verify the full unskipped opening and retain native frames for every remaining long box.

### MED — The wound scene says “Westwood trees” over the farm exterior

**Repro**

1. Complete the normal Escape route or trigger the turn-8 route.
2. Inspect the first visible wound narration and its background.

**Observed**

The narration places Rand beneath the Westwood trees, but the frame shows the farmhouse and yard. The immediately following supplies scene switches to the actual forest background, making the location discontinuity especially obvious. Rand's frightened portrait and Tam's wounded portrait otherwise match their dialogue and fit without clipping.

**Frame evidence:** `/tmp/wn01-golden-dialogue/030-wn01_farm_escape_sc_c1_tam_wounded.png`, `/tmp/wn01-timeoutfar-dialogue/031-wn01_farm_escape_sc_c1_tam_wounded.png`; compare the correct forest in `/tmp/wn01-golden-dialogue/040-wn01_farm_escape_sc_c1_supplies_needed.png`.

**Suspected source:** `design/scenes/farm_escape/scenes.yaml:105` selects `farm_night`, while line 113 places the scene under the Westwood trees. The next scene correctly selects `westwood_night` at line 129.

**Smallest remedy:** use the Westwood background for `sc_c1_tam_wounded`. Verify both the Escape and turn-8 entry paths.

### LOW — The turn-3 warning does not identify the reinforcement edge

**Repro**

1. Run west normally through turn 3.
2. Advance `sc_c1_pursuit` and inspect the returned map before moving.

**Observed**

Tam says only “Another pack.” The scene uses a full background, and control returns centered on Rand in the west; both new enemies at `(16, 4)` and `(16, 10)` are off-camera. A first-time player must pan the map to learn whether the threat is ahead, behind, or flanking.

This is not an enemy-phase ambush: the group spawns at turn start before player phase, both units are Manhattan distance 9 from Tam at spawn, and neither can attack before the player receives a reaction turn. Starting enemies are also visible in `/tmp/wn01-initial-map.png`.

**Frame evidence:** `/tmp/wn01-golden-dialogue/029-wn01_farm_escape_sc_c1_pursuit.png`, `/tmp/wn01-mid-escape.png`

**Suspected source:** `design/scenes/farm_escape/scenes.yaml:98` omits the direction; the spawn/scene sequence is `design/missions/farm_escape.yaml:42-46`.

**Smallest remedy:** name the east/farmyard edge in Tam's warning or briefly frame the spawn tiles before returning control. Recheck that the wave still acts only after a full player phase.

## Checks that passed

- Direct victory is reachable with real input on turn 4; Rand must select the visible **Escape** action at `(0, 5)`.
- The optional **Clean Cloth** visit is reachable and winnable on turn 5 when Tam intercepts the immediate enemy on turn 1. A variant that leaves Tam in place for the first turn demonstrates the visible tactical risk and loses Rand on turn 2 rather than soft-locking.
- Deliberately letting Rand die produces the normal Game Over screen on turn 2: `/tmp/wn01-game-over.png`.
- `sc_c1_farmhouse_calm`, `sc_c1_locked_doors`, and `sc_c1_door_bursts` each fired once per run; no opening double-fire was observed.
- Tam initiated combat on three successive player turns in the quote-focused run; `sc_c1_tam_combat_quote` fired exactly once and displayed the correct Tam battle portrait: `/tmp/wn01-quote-dialogue/029-wn01_farm_escape_sc_c1_tam_combat_quote.png`.
- Starting enemy pressure is readable before input. The two-unit pursuing wave spawns at turn start, outside immediate attack distance, and gives a full player reaction phase. No same-turn/enemy-phase ambush was observed.
- Other reviewed dialogue and narration frames stayed inside the 240×160 surface. No speaker/portrait mismatch or novel-only prerequisite was found.
- Neither victory, optional visit, timeout, nor loss route soft-locked.

**VERDICT: FAIL**
