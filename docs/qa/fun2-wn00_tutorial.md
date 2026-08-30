# Fun QA round 2 — `wn00_tutorial`

**Verdict: MOSTLY FUN. Target: missed (`FUN`).**

The redesign fixes the old chapter's largest mechanical problems: there is only one cider trip, Rand and Mat each perform a real player-driven Attack flow, Mat's temporary deployment is clean, and the five optional Talks now create a useful route-order layer. The golden route is shorter and has fewer dead turns than the baseline. It does not quite reach **FUN**, because the turn-6 input lesson hands control directly to **63 consecutive settled dialogue/narration boxes** before the player can act again. That interruption drains the momentum created by the two throws. One stale line also still promises a “first” cask in a one-cask errand.

## Build and run evidence

- Gated report-tree provenance: `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`.
- QA isolation: the campaign was deterministically compiled to `/tmp/fun2-wn00-build/winternight.ltproj` to avoid shared-build replacement. Both runs independently report the exact same tree hash above.
- Engine: `1820e585450f6f47605aebd686b2a3f13af181f0` (`2026.02.17a`).
- Manifest SHA-256: `e20d63d4cceb81952f5cf2db587fc4cfe8e7cfcf90349554b09576a5b9485601`.
- Golden all-content run: real pygame input from the title screen through the start of `wn01_farm_escape`; 8,352 frames, no failure, victory on turn 10. Artifacts: `/tmp/fun2-wn00/golden-run.json`, `/tmp/fun2-wn00/golden-summary.json`.
- Weak dawdle run: real pygame input from `wn00_tutorial`; early inn approach, the one-shot redirect, four deliberate wait turns on/around the entrance, then the mandatory route; 6,252 frames, no failure, victory on turn 10. Artifacts: `/tmp/fun2-wn00/weak-run.json`, `/tmp/fun2-wn00/weak-summary.json`.
- Native visual review: all 183 settled golden boxes and all 142 settled weak boxes were captured at 240×160 and reviewed in 49 contact sheets under `/tmp/fun2-wn00/contacts/`. Runtime layout records found 0 over-height boxes and 0 boxes whose rendered text lost its opening. Review sheets: `/tmp/fun2-wn00/super-contact-{1..7}.png`.
- Mandatory pages before first control: **8 pages / 10 golden turns = 0.8 pages per turn**, within the 4:1 short-chapter budget.

The drivers selected units, moved cursors, chose semantic menu entries, chose the Thrown Stone, selected the raven, confirmed combat, and advanced text with posted pygame keys. They did not call actions/triggers or mutate level flags, units, HP, inventory, or event state.

## Actual routes

### Golden all-content

1. Follow the visible Talk marker and Talk to Mat.
2. Take Ewin on the east branch, then step on the cider cart.
3. Take Egwene while crossing west with the cask; deliver it at the cellar.
4. Take Perrin beside the cellar, then follow Rand's gold line.
5. With Rand, choose **Attack → Thrown Stone → raven → confirm**.
6. Follow Mat's gold line; with Mat, choose the same real Attack flow.
7. Let the unharmed raven fly; take Fain first, cross west to Thom, then return and choose **Enter Inn**.
8. Complete the council/outro and transition into `wn01_farm_escape`.

All five optional flags were true and `talk_options` was empty at victory. The route is recorded turn by turn at `/tmp/fun2-wn00/golden-summary.json:3496-3913`.

### Weak dawdle

1. Ignore the Mat objective and walk to the inn approach.
2. Trigger the one-shot redirect, which says to Talk to Mat.
3. Wait four turns at `[9,8]`, `[9,7]`, `[10,7]`, and `[9,8]`; the redirect does not repeat and the menu remains **Item / Wait**.
4. Recover to Mat and complete only the mandatory cart, cellar, Rand throw, Mat throw, and inn-entry actions.

The weak route won on turn 10 with all five optional Talks still available, proving that they remain optional. Recovery evidence: `/tmp/fun2-wn00/scenes/weak-011-sc_c0_inn_before_mat.png`, `/tmp/fun2-wn00/critical/weak-dawdle-4-wait-menu.png`, and `/tmp/fun2-wn00/weak-objectives-contact.png`.

## Decision density

A dead turn uses the repository definition: one credible action with no risk, reward, ordering, route, or resource tradeoff. Guided inputs with exactly one weapon, one target, and a forced result are still counted dead even though they are more engaging than an automated cutscene.

### Golden: **5 dead / 10 natural turns (50%)**

| Turn | Played content | Dead? | Rationale |
| ---: | --- | :---: | --- |
| 1 | South-edge travel toward Mat | yes | Mat is the sole credible destination and is one tile beyond Rand's first move. |
| 2 | Talk to Mat | yes | Required handoff with no competing unlocked action. |
| 3 | Ewin | no | Optional Talk versus the direct cart route. |
| 4 | Cart, then Egwene on the westbound route | no | Talk order and route efficiency matter. |
| 5 | Cellar, then Perrin versus immediate raven lesson | no | Optional information versus direct progression. |
| 6 | Rand throw, Mat throw, raven flight | yes | Real input, but one weapon, one target, no danger, and two authored misses. |
| 7 | Fain versus Thom/inn | no | Optional branch choice. |
| 8 | Westbound transit toward Thom | yes | The all-content route cannot reach the second late Talk this turn. |
| 9 | Thom versus returning to the inn | no | Optional Talk remains a choice. |
| 10 | Return and Enter Inn | yes | Sole destination and ending action. |

Baseline golden: **7/13 (54%)**. New golden: **5/10 (50%)** — two fewer dead turns and three fewer natural turns. The ratio changes only slightly, but the turn-6 dead turn is materially richer because both public Attack flows are now learned by doing.

### Weak: **10 dead / 10 exercised turns (100%)**

The wrong-way opening has no payoff or tradeoff, turns 3–6 are explicit dawdle, and the recovered mandatory-only route has one prescribed safe action at every stage. Removing the four intentional wait turns gives a natural mandatory-only equivalent of **6/6 (100%)**, improved from the baseline mandatory-only **7/7 (100%)** by removing the second cider trip.

## Tension curve and peak

- **Turns 1–2:** low-pressure arrival and work handoff.
- **Turns 3–5:** social/route decisions build village attachment while the raven omen approaches.
- **Turn 6:** mechanical and tonal peak — Rand misses, Mat misses, and the raven visibly escapes east unharmed.
- **Between turns 6 and 7:** the peak stalls in the 63-box mandatory scene chain described below.
- **Turns 7–10:** release through optional news/story Talks and explicit inn entry.

**Core verb:** route-and-Talk into a guided two-unit Attack lesson.

**Peak native frame:** `/tmp/fun2-wn00/critical/golden-raven-flight.png`. The reviewed 240×160 frame visibly shows the raven in motion with Rand and Mat below the inn. Supporting real-input frames: `/tmp/fun2-wn00/critical/golden-{rand,mat}-throw-menu.png`, `...-weapon_choice.png`, and `...-combat_targeting.png`.

## Regression checks

| Check | Result and evidence |
| --- | --- |
| Single cider trip | **Pass.** The run sets `carrying_cider`, delivers once, then proceeds directly to the raven lesson; no second cart/cellar loop exists. Runtime route: golden turns 4–5 and weak turns 8–9. Source contract: `design/missions/tutorial_emonds_field.yaml:69-99,216-223`. |
| Rand throw is real input | **Pass.** Observed state chain `free → move → menu → weapon_choice → combat_targeting → combat → exp → combat → alert`. Menu and weapon frames: `/tmp/fun2-wn00/critical/golden-rand-throw-{menu,weapon_choice,combat_targeting,combat}.png`. The raven remains 22/22 HP; the stone is removed and Rand's Hunting Bow is restored (`/tmp/fun2-wn00/golden-summary.json:3914-3978`). |
| Mat throw is real input | **Pass.** Observed the same input chain through combat. Frames: `/tmp/fun2-wn00/critical/golden-mat-throw-{menu,weapon_choice,combat_targeting,combat}.png`. The raven remains 22/22 HP and Mat's stone is removed (`/tmp/fun2-wn00/golden-summary.json:3926-4000`). |
| Guide lines and public wording | **Pass.** The gold foreground routes and arrowheads are visible, the destination squares are highlighted, and prompts name Rand/Mat and **Attack**. Native prompts: `/tmp/fun2-wn00/scenes/golden-062-wn00_tutorial_tutorial_cider_cellar.png`, `/tmp/fun2-wn00/scenes/golden-073-wn00_tutorial_tutorial_rand_throw_done.png`. Source: `design/missions/tutorial_emonds_field.yaml:32-34,93-109,124-140`. |
| Mat transitions in and out | **Pass.** Mat begins `other` with `Tile`, becomes `player` with no `Tile` after cellar delivery, remains controllable through the lesson and victory, carries no temporary stone at victory, and is absent from the active `wn01` map (`position: null`; active players are only Rand and Tam). Evidence: `/tmp/fun2-wn00/golden-summary.json:4003-4219,4256-4264,4275-4318`. Source: `design/missions/tutorial_emonds_field.yaml:88-90,130-153`. |
| Early inn and dawdle recovery | **Pass.** The redirect fires once, its text fits, the objective remains **Talk to Mat / Choose Talk** after redirect and after four waits, no stale entrance action repeats, and the run recovers and wins. Evidence above plus `/tmp/fun2-wn00/weak-summary.json:2667-2694`. Source: `design/missions/tutorial_emonds_field.yaml:60-68`. |
| Objective screen tracks every stage | **Pass.** Reviewed, in order: **Talk to Mat**, **Lift one cask**, **Carry to cellar**, **Move Rand**, **Attack raven / With Rand**, **Move Mat**, **Attack raven / With Mat**, **End turn / Watch the raven**, **Choose Enter Inn**. All fit at 240×160 and both objective slots matched. Montage: `/tmp/fun2-wn00/all-objectives-contact.png`; focused end-turn frame: `/tmp/fun2-wn00-end-turn.png`. Source transitions: `design/missions/tutorial_emonds_field.yaml:44,57,76,97,109,128,139,153,168`. |
| Raven flight and lesson cleanup | **Pass.** Enemy-turn movement visibly occurs before removal and before the Moiraine scene; `raven_done` is true, the raven is off-map, and both temporary stones are gone. Evidence: `/tmp/fun2-wn00/critical/golden-raven-flight.png`, `/tmp/fun2-wn00/golden-summary.json:3952-4000,4221-4272`. Source: `design/missions/tutorial_emonds_field.yaml:146-169`. |
| Optional Talks | **Pass.** Golden takes all five and leaves none; weak skips all five and still wins. Source: `design/missions/tutorial_emonds_field.yaml:170-204`. |
| Win/outro/next chapter | **Pass.** Explicit **Enter Inn** sets `entered_inn`, triggers level end and the outro, and the golden run reaches `wn01_farm_escape` turn 1. Evidence: `/tmp/fun2-wn00/golden-summary.json:4221-4318`; source: `design/missions/tutorial_emonds_field.yaml:205-215`. |
| Loss contract | **Present but not input-reachable.** The compiled event is `unit_death` for Rand and executes `lose_game` (`build/winternight.ltproj/game_data/events.json:3446-3457`; source `design/missions/tutorial_emonds_field.yaml:10-11`). This combat-free, scripted-miss chapter exposes no public damaging action, so a genuine-input loss cannot be produced. I did not mutate HP/death state to manufacture one. |
| Text fit and quote review | **One wording finding below; otherwise pass.** All 325 reviewed settled frames fit their two-row boxes; no portrait or game text overflow was visible in the seven visual-review sheets. |

## Findings by severity

### MAJOR — The turn-6 payoff is followed by 63 consecutive mandatory boxes before control

**Repro**

1. Deliver the cider and complete both real raven Attacks.
2. End the player phase and watch the raven fly.
3. Advance the mandatory scenes until map control returns on turn 7.

**Observed:** the event chains `sc_c0_moiraine_coin` (20 settled boxes), `sc_c0_fain_news` (16), `sc_c0_fain_aftershock` (10), and `sc_c0_thom_performance` (17): **63 consecutive A-press pages**. The block opens at `/tmp/fun2-wn00/scenes/golden-075-sc_c0_moiraine_coin.png` and ends at `/tmp/fun2-wn00/scenes/golden-137-sc_c0_thom_performance.png`; the per-event capture ledger is in `/tmp/fun2-wn00/golden-summary.json:31-3421`.

**Player consequence:** the newly interactive two-throw peak is immediately converted into a long noninteractive reading block. The village material is coherent and every page fits, but the loss of control is long enough to keep the chapter below `FUN`.

**Likely fault:** four mandatory scenes are chained without a playable boundary at `design/missions/tutorial_emonds_field.yaml:161-164`. Their authored pages are at `design/scenes/tutorial/scenes.yaml:202-513`.

**Smallest remedy:** preserve the approved facts and scene IDs, but merge adjacent same-speaker fragments/narration into native two-line boxes and remove repeated handoff phrasing, reducing the chain from 63 to **no more than 32 settled boxes**. Re-run native frame review to prove zero clipping and verify that every approved story fact still appears.

### MINOR — The one-cask errand still calls its cask “first”

**Repro:** Talk to Mat and advance `sc_c0_mat_and_news` to the errand narration.

**Observed:** “The **first** cider cask waits on the cart.” Frame: `/tmp/fun2-wn00/scenes/golden-024-sc_c0_mat_and_news.png`.

**Player consequence:** “first” briefly primes the player for another trip even though the redesign and next objectives require exactly one cask.

**Likely fault:** `design/scenes/tutorial/scenes.yaml:132-137`, specifically line 134.

**Smallest remedy:** change the line to “The cider cask waits on the cart.” Re-capture that native page and complete the one-trip route once.

## Top three ranked fixes to reach `FUN`

1. **Halve the post-throw mandatory page block.** At `design/scenes/tutorial/scenes.yaml:202-513`, pair adjacent short fragments into two-line boxes and trim repeated transition narration; acceptance is ≤32 consecutive settled boxes, all current story facts retained, and zero native overflow. Preserve the four scene IDs and the raven/Moiraine/Fain/Thom ordering at `design/missions/tutorial_emonds_field.yaml:161-164`.
2. **Remove the empty opening travel turn.** Move Rand's start from `[9,14]` to `[9,13]` at `design/missions/tutorial_emonds_field.yaml:14`; acceptance is that a 5-MOV Rand can reach a legal Talk-adjacent square and choose **Talk** on turn 1, while the south-edge arrival framing and early-inn recovery remain intact.
3. **Remove the all-content dead transit between late Talks without making them mandatory.** After `sc_c0_thom_performance` and before the two `add_talk` actions at `design/missions/tutorial_emonds_field.yaml:164-166`, move Fain to the now-deactivated cart square `[12,9]` and Thom to `[7,7]`. Acceptance is that either Talk may still be chosen first, both remain optional, and an all-content player can take the second Talk on the next turn without an intermediate Wait, then reach the inn on the following turn.

Locked contracts for all three: one cider trip; all five village Talks optional; Rand and Mat both use the real Attack/weapon/target/confirm flow; both stones miss without damage; Mat's temporary player deployment and cleanup remain; raven flight precedes Moiraine; every objective stage and explicit Enter Inn win remain.
