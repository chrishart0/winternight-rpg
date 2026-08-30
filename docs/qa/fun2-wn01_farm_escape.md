# Fun review 2 — `wn01_farm_escape`

**Verdict: FUN.** The core verb is **escape**. It stays decision-bearing through the
turn-4 target window, the pursuit now peaks while Rand is still moving, the optional
Clean Cloth creates a real one-turn preparation cost, and refusing to escape now ends in
a caught scene and Game Over rather than the old mercy victory.

**Coherence: coherent.** The opening and Objective screen both tell Rand to run west to
Westwood before dawn; the west edge is highlighted; the turn-2 scene names the new
threat as coming from the east; reaching `[0,5]` succeeds; and failing to reach it before
turn 8 loses. A first-time player can identify the destination, the pressure direction,
and the consequence of delay from information shown in the game.

## Build and method

Tested the already-compiled `build/winternight.ltproj` at report tree
`a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a` with pinned
engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`.

The runs used SDL dummy video/audio and the pinned engine. The driver posted real
pygame key-down/key-up input and read runtime state only to choose ordinary movement,
Attack, Clean Cloth, Wait, Escape, and menu inputs. It did not invoke an event, move a
unit directly, change HP or flags, or mutate the objective. All accepted traces record
the gated report-tree hash above.

Run artifacts:

- Intended direct escape, wound trigger on turn 4:
  `/tmp/fun2-wn01-golden.json`.
- Deliberately weak farmyard stall, caught loss on turn 8:
  `/tmp/fun2-wn01-timeoutfar.json`.
- Optional Clean Cloth plus coordinated Tam cover, wound trigger on turn 5:
  `/tmp/fun2-wn01-kitcover2.json`.
- Initial and post-wave Objective screens:
  `/tmp/fun2-wn01-objective.png` and
  `/tmp/fun2-wn01-objective-turn3.png`.
- Reviewed native-resolution dialogue contacts:
  `/tmp/fun2-wn01-opening-contact.png` and
  `/tmp/fun2-wn01-success-dialogue-contact.png`.

## Dual-run fun protocol

### Golden route — turn-4 escape

The played route was: advance the opening normally; move Rand west while Tam selects
which breached-house enemy to intercept; react to the turn-2 eastern wave; keep Rand
moving while Tam covers the pursuit; then use Escape on the highlighted Westwood tile
at `[0,5]` on turn 4.

| Turn | Observed state and player decision | Dead? |
| --- | --- | --- |
| 1 | Rand chooses direct speed over the visible Clean Cloth detour; Tam chooses an interception target. | No |
| 2 | Two pursuers appear to the east; Rand continues west while Tam chooses how to cover the remaining breach enemy and the new wave. | No |
| 3 | Rand is at `[3,6]`; Tam is at `[10,7]` with 22 HP while two pursuers have closed to `[13,6]` and `[14,7]`. Continuing Rand versus Tam's target/risk remains live. | No |
| 4 | All enemies are down and Rand at `[1,5]` has one safe, useful action: enter Westwood. | **Yes** |

**Decision density: 1 dead turn / 4 natural turns (25%).** Baseline was **2/4
(50%)**. Moving the wave from turn 3 to turn 2 converts the old dead turn 3 into the
chapter's strongest cover/targeting turn; only the destination turn remains forced.

Tam fell from 36 HP to 9 HP before the turn-4 release, so the pursuit was not cosmetic.
The event sequence then contained `sc_c1_tam_wounded` and `sc_c1_supplies_needed`, and
the wound trigger snapshot recorded Rand `[0,5]`, Tam `[10,7]`, turn 4. The chapter
completed without a soft-lock.

### Weak route — turn-8 caught loss

Rand remained at `[7,7]`. Tam fought the map clear by the start of turn 4, after which
both units used only public Wait actions through turn 7. At the start of turn 8, before
another player action, `sc_c1_caught` played and the standard Game Over state appeared.

- Runtime flags at Game Over were exactly `_lose_game: true` and
  `caught_by_dawn: true`.
- Rand was alive at 24 HP at `[7,7]`; Tam was alive at 9 HP at `[12,6]`.
- No unit death manufactured the result.
- `sc_c1_tam_wounded`, `sc_c1_supplies_needed`, and all wound flags were absent.
- Weak-route frame: `/tmp/fun2-wn01-timeoutfar-dialogue/021-wn01_farm_escape_sc_c1_caught.png`.
- Loss frame: `/tmp/fun2-wn01-caught-game-over.png`.

**Weak-route dead turns: 4 dead controlled player phases / 7 controlled phases
(57%), on turns 4–7; raw resolution is turn 8.** On the baseline chapter-turn
convention this is **4/8**, versus the old **3/8** mercy-win ledger. Turn 8 itself is a
terminal caught scene, not another empty player phase. The tail still correctly feels
bad when deliberately chosen, but it can no longer invalidate **escape** by winning.

Causal source: the turn-8 condition sets `caught_by_dawn`, plays the caught scene, and
loses at `design/missions/farm_escape.yaml:60-66`; the three fitted caught pages are at
`design/scenes/farm_escape/scenes.yaml:89-102`. The success-only wound flags and scene
remain separate at `design/missions/farm_escape.yaml:52-59`.

## Tension curve and peak

The domestic opening rises through the locked door and sword, the breach hands control
over under immediate pressure, and the turn-2 wave sustains rather than restarts that
pressure. The playable peak is turn 3: Rand is already west of the house, Tam is still
inside the pursuit lane, and both new enemies are visible closing from the east. The
turn-4 escape is a short release rather than another combat spike.

**Peak frame:** `/tmp/fun2-wn01-tension-peak.png` (native 240×160). It visibly places
Rand near the highlighted west edge, Tam between him and the farmhouse, and both
pursuers at the east side of the frame.

The two-unit turn-2 wave is authored at
`design/missions/farm_escape.yaml:20-21,25-26,43-48`. In the direct runtime snapshot,
Rand was `[7,7]`, Tam `[10,7]`, and the new units were `[16,4]` and `[16,10]` when the
player received control. Each spawn was Manhattan distance 9 from the nearer player
unit, exceeding the required 6-tile reaction distance. The last opening page already
says “More shapes close from the east”
(`design/scenes/farm_escape/scenes.yaml:53`), and the landing scene repeats “More from
the east” (`:77-88`). `/tmp/fun2-wn01-golden-dialogue/018-wn01_farm_escape_sc_c1_pursuit.png`
shows the fitted in-engine telegraph.

## Optional Clean Cloth tempo check

The Clean Cloth branch is optional and meaningfully expensive rather than free texture.
Rand used the visible **Clean Cloth** action on turn 1, which set
`farm_kit_collected` and ended his action. With Tam prioritizing the spear that could
cut Rand off, the route succeeded on turn 5 rather than the direct route's turn 4.
Rand reached the wound trigger at 10 HP and Tam reached his survival floor at 1 HP.
Thus the item costs one full escape turn and materially changes target order and risk.

The branch and Field Dressing grant are at
`design/missions/farm_escape.yaml:24,36-42`; its two fitted pages are at
`design/scenes/farm_escape/scenes.yaml:54-65`. The reviewed frame
`/tmp/fun2-wn01-kitcover2-dialogue/019-wn01_farm_escape_sc_c1_farm_kit.png` clearly
states why Rand is taking it. The run then used the normal success/wound/outro chain,
not a special victory path.

## Opening pacing and native-resolution text

The unskipped pre-control opening required exactly **17 settled A-press pages**:

- 3 pages in `sc_c1_farmhouse_calm`;
- 7 pages in `sc_c1_locked_doors`;
- 7 pages in `sc_c1_door_bursts`.

The source beats are at `design/scenes/farm_escape/scenes.yaml:14-16,28-34,46-53`, and
the mission calls them before control at `design/missions/farm_escape.yaml:28-35`.
This is 4.25 pre-control pages per natural turn, narrowly over the review's 4:1 guide,
but the played sequence earns the one-page exception: home, unease/sword, and breach
advance without a redundant fragment, and page 17 hands the east/west spatial rule
directly into control.

I visually inspected all 17 native 240×160 pages in
`/tmp/fun2-wn01-opening-contact.png` and all 29 optional/wound/outro pages in
`/tmp/fun2-wn01-success-dialogue-contact.png`. I also inspected both Objective screens,
the pursuit page, the caught page, the peak map, and Game Over frame. No dialogue,
objective, portrait, or map cue was clipped or overflowed; every recorded rendered text
range stayed within two rows. The initial Objective screen cleanly shows **Reach
Westwood / by dawn** and **Caught by dawn**. The post-wave screen adds **Trollocs east**
without hiding the loss rule.

## Regression checks

| Contract | Result | Evidence |
| --- | --- | --- |
| Golden turn-4 escape | PASS | `/tmp/fun2-wn01-golden.json`; wound trigger Rand `[0,5]`, turn 4 |
| Turn-8 stall must lose | PASS | `_lose_game` + `caught_by_dawn`, caught scene, standard Game Over in `/tmp/fun2-wn01-timeoutfar.json` |
| Old mercy victory disproved | PASS | No wound, outro, win, or chapter continuation on the stall path |
| Wound success-only | PASS | Wound/outro present in turn-4 and turn-5 successes; absent from caught loss |
| Turn-2 wave telegraphed | PASS | Opening page 17, pursuit page, and post-wave Objective all name the east |
| Fair spawn distance | PASS | Both spawn tiles were 9 Manhattan tiles from the nearest player at landing |
| Clean Cloth costs tempo | PASS | Successful optional route turn 5 versus direct turn 4; `farm_kit_collected: true` |
| 17-page opening | PASS | 3 + 7 + 7 settled pages before first control |
| Win and loss terminate | PASS | Both paths reached their normal terminal state without soft-lock |
| Native 240×160 fit | PASS | Reviewed contacts and individual objective/peak/caught/Game Over frames; no clipping |

## Findings ordered by severity

**None.** No blocking, major, or minor player-facing regression was observed. The
chapter reaches its FUN target, so no ranked implementation fixes are required.
