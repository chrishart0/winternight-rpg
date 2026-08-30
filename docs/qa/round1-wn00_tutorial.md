# Round 1 QA — `wn00_tutorial`

**Assessment:** incoherent at the earliest recovery branch. The intended festival route is completable and the five optional talks are distinct and one-shot, but stepping toward the inn before speaking to Mat traps the player in an endlessly repeating redirect scene. On the successful route, the persistent Objective screen never advances beyond the initial Mat instruction, the active inn doorway can irreversibly end the chapter while Rand is pathing to optional talks, and many long boxes scroll their setup out of view at native resolution.

**Verdict:** FAIL

## Coverage and evidence

Tested the already-compiled `build/winternight.ltproj` at tree `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a` with pinned engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. Routes were driven through posted pygame key down/up input under dummy SDL. The driver did not invoke actions or triggers and did not mutate positions, flags, events, or game data.

- Full successful route: Mat → Egwene/Perrin/Ewin → exactly two cart/cellar cider trips → raven/Moiraine/Fain/Thom chain → Thom/Fain optional talks → inn. It completed with all progression and talk flags true. Runtime evidence: `/tmp/wn00-run.json`, `/tmp/wn00-runtime-summary.json`.
- Early-inn failure route: Rand entered `inn_before_mat` before speaking to Mat. The two-box redirect restarted indefinitely; the run was stopped after hundreds of repeated boxes. Frames: `/tmp/wn00-early-door.png`, `/tmp/wn00-early-loop-guidance.png`.
- Optional-talk consumption: after each of Egwene, Perrin, Ewin, Thom, and Fain fired, Rand selected the same adjacent position again. The resulting menus contained no **Talk** action. Frames: `/tmp/wn00-repeat-egwene.png`, `/tmp/wn00-repeat-perrin.png`, `/tmp/wn00-repeat-ewin.png`, `/tmp/wn00-repeat-thom.png`, `/tmp/wn00-repeat-fain.png`; reviewed montage: `/tmp/wn00-repeat-talks-contact.png`.
- Optional-route hazard: after the raven chain, routing from Fain on the east side to Thom on the west side crossed the newly active inn region and ended the chapter before Thom could be spoken to. The complete all-talk run required a manual north-of-inn detour through `(13, 2)` and `(6, 2)` and finished on turn 21.
- All seven authored objective transitions plus the post-optional state were opened through the real **Objective** menu and visually reviewed: `/tmp/wn00-objectives/01-initial.png` through `/tmp/wn00-objectives/08-inn_after_all.png`; montage: `/tmp/wn00-objectives-contact.png`.
- All 17 scenes on the successful route produced 122 settled native 240×160 text-box frames. The eighteenth scene, `sc_c0_inn_before_mat`, was exercised on the failure route. Every scene was visually reviewed via `/tmp/wn00-contact-sc_c0_*.png`.

Required native frames were captured and visually inspected:

- Festival map state: `/tmp/wn00-festival.png`, `/tmp/wn00-festival-live.png`
- Mid-cider objective: `/tmp/wn00-objectives/03-carry_first.png`
- Raven scene: `/tmp/wn00-scenes/051-wn00_tutorial_sc_c0_raven_attack.png`
- Moiraine coin: `/tmp/wn00-scenes/063-wn00_tutorial_sc_c0_moiraine_coin.png`
- Inn-door state: `/tmp/wn00-inn-door.png`

A normal Game Over loss is not player-reachable in this combat-free chapter: Rand has no enemy or damaging public action, so the declared unit-death condition cannot be deliberately fired with genuine player input. I did not mutate Rand's HP/death state to manufacture a loss. The deliberate wrong-door/failure route instead exposed the blocker below.

## Intended and observed route

The intended loop is: Quarry Road establishes Rand, Tam, the black rider, and the cider delivery → find and **Talk** to Mat on the Green → make two short cider deliveries between the blue cart and gold cellar markers → investigate the red raven marker → watch the raven, Moiraine coin, Fain news, and Thom performance chain → take any remaining optional talks → enter the inn and leave for the farm.

The direct successful route works if the player remembers each preceding scene and follows the changing colored markers. The persistent Objective screen does not support that route: it continues to say **Talk to Mat** after Mat, both cider trips, the raven, and every optional talk. Exploration also has two destructive boundaries. Entering the inn before Mat never returns control, while entering it after the raven commits immediately to victory even when Rand was merely pathing across the doorway to optional content.

## Coherence trace

| State | Player-facing goal | Visible cue | Public action | Feedback / next goal |
| --- | --- | --- | --- | --- |
| Quarry Road | Reach Bel Tine with Tam and the cider; understand the black-rider concern | Quarry Road background; Rand/Tam portraits | Advance eight boxes | Final narration names Mat, the cart, and **Talk**, although long settled narration loses its opening |
| Festival start | Talk to Mat | Mat has a clear **TALK** marker on the Green | Move adjacent and choose **Talk** | Mat scene fires once; blue cart marker activates |
| Inn before Mat | Return to Mat rather than entering | Doorway is visually legible, but no warning says it is a trap | Step onto `(9, 7)` or `(9, 8)` | Tam redirects Rand, then the same two boxes immediately restart forever |
| First cask pickup | Lift the first cask | Blue marker at `(12, 9)` | Step on marker | Gold cellar marker activates; transient simple objective changes |
| First cellar trip | Deliver first cask | Gold marker at `(9, 6)` | Step on marker | Cider/prank scene; cart reactivates; “one trip remains” |
| Second pickup | Lift second cask | Blue marker returns | Step on marker | Honeycake scene; cellar reactivates |
| Second cellar trip | Finish cider work | Gold marker returns | Step on marker | Work is explicitly complete; red raven marker activates |
| Raven | Investigate the watcher | Red marker at `(11, 8)` | Step on marker | Five scenes play in sequence; no actual **Attack** action is offered |
| Post-raven exploration | Optional Fain/Thom talks, then enter inn | Fain/Thom **TALK** markers and gold inn marker | Move adjacent and **Talk**, or step on door | Talks are one-shot, but shortest east↔west routes can cross the door and win immediately |
| Inn | End the Green segment | Door tile and gold marker | Step on `(9, 7)` or `(9, 8)` | Council scene, victory, and departure scene complete normally |
| Rand death | Keep Rand alive | Objective lists survival, but no damage source exists | No genuine player action can reach this state | Configured loss cannot be exercised without state mutation |

## Findings

### BLOCKER — Entering the inn before talking to Mat soft-locks in an endless redirect loop

**Repro**

1. Start `wn00_tutorial` and advance the Quarry Road intro.
2. Before talking to Mat, move Rand north onto either tile of the inn entrance region at `(9, 7)` / `(9, 8)`.
3. Advance Tam's “None of this is unloading the cart” box and the narration directing Rand back to Mat.

**Observed**

The same Tam and narration boxes immediately begin again. Advancing them repeats the pair indefinitely; control never returns, Rand cannot move away, and the player cannot reach Mat. The gate does prevent early victory, but replaces a recoverable mistake with a chapter soft-lock.

**Frame evidence:** `/tmp/wn00-early-door.png`, `/tmp/wn00-early-loop-guidance.png`

**Suspected source:** `design/missions/tutorial_emonds_field.yaml:25` defines a two-tile interrupting entrance region; `design/missions/tutorial_emonds_field.yaml:53-58` makes its event `only_once: false` and provides no deactivation, reposition, movement cancellation, or refresh that would let Rand leave before the region re-triggers.

**Smallest remedy:** make the redirect consume/deactivate the entrance attempt long enough to return Rand to a free tile, or use a non-interrupting/one-shot gate that leaves control with the player. Verify by entering both gate tiles before Mat, dismissing the redirect once, walking away, then talking to Mat.

### HIGH — The persistent Objective screen stays on the initial Mat goal and clips even that instruction

**Repro**

1. Open **Objective** at mission start.
2. Open it again after Mat, first cart pickup, first cellar delivery, second cart pickup, second cellar delivery, the raven chain, and all five optional talks.

**Observed**

All eight native frames show the original win text. The mid-cider screen still says `Talk to Mat on the... / Move beside him: c...`, even though Mat's one-shot talk is gone and Rand is carrying a cask. The right status panel also cuts off the initial second line, hiding the end of `choose Talk`.

Runtime evidence confirms that the `simple` slot did change correctly at each gate, but the Objective screen presents the unchanged `win` slot. The player therefore receives no persistent truthful task list and must remember transient narration/markers. After every optional talk is consumed (`talk_options: []`), the simple slot also still says `Optional talks remain`, so that transient objective becomes false as well.

**Frame evidence:** `/tmp/wn00-objectives/01-initial.png` through `/tmp/wn00-objectives/08-inn_after_all.png`; especially `/tmp/wn00-objectives/03-carry_first.png` and `/tmp/wn00-objectives-contact.png`. Consumed-talk evidence: `/tmp/wn00-repeat-talks-contact.png`.

**Runtime evidence:** `/tmp/wn00-runtime-summary.json` records every expected simple-objective string, all five optional-talk flags, and an empty final `talk_options` list.

**Suspected source:** every progression action targets only `simple` in `design/missions/tutorial_emonds_field.yaml:37,50,66,77,88,99,116`; the persistent menu continues to render the initial `win` value authored at line 9. The optional-talk events at lines 119-153 never replace line 116 after the final talk.

**Smallest remedy:** keep the persistent `win` objective synchronized with every simple-objective transition, use strings short enough for the native Objective panel, and replace “Optional talks remain” once the last available talk is consumed. Verify all eight states through the real Objective menu at 240×160.

### HIGH — The active inn door can end the chapter while Rand is pathing to optional talks

**Repro**

1. Complete the raven chain so Fain, Thom, and the inn door are active.
2. Talk to Fain on the east side of the inn.
3. Select Rand and choose a normal shortest movement route toward Thom on the west side.

**Observed**

The path crosses the active two-tile inn entrance. `tutorial_enter_inn` interrupts movement, plays the council sequence, and wins before Thom's optional talk can fire. There is no confirmation and no explicit **Enter Inn** action; merely crossing the gold marker commits. The inverse east/west traversal has the same spatial hazard. The all-talk evidence run had to take an unnatural north-edge detour around the blocking inn, reaching `(13, 2)` and `(6, 2)`, and finished on turn 21.

This is irreversible optional-content loss, not a soft-lock: the chapter completes successfully, but a player following visible **TALK** markers can be pulled into the ending while trying to reach them.

**Frame evidence:** `/tmp/wn00-inn-door.png` shows the gold two-tile doorway between the east and west village groups. Optional one-shot frames are `/tmp/wn00-repeat-thom.png` and `/tmp/wn00-repeat-fain.png` from the detoured completion route.

**Suspected source:** `design/missions/tutorial_emonds_field.yaml:20-21` places Fain east and Thom west; line 29 makes the central `inn_door` a two-tile `interrupt_move` event; lines 115-118 activate/highlight it at the same time as the talks; lines 154-160 win immediately on contact.

**Smallest remedy:** require an explicit, confirmable **Enter Inn** action instead of winning on movement interruption, or place the committing region fully inside the doorway rather than on the through-route. Verify Fain→Thom and Thom→Fain shortest paths before separately choosing to enter.

### MED — Long text scrolls its opening out of the settled two-row box in every scene

**Repro**

1. Play the unskipped route with the runner's fastest text setting.
2. Let each box finish rendering before pressing confirm.
3. Inspect the native settled frame for every beat.

**Observed**

Sixty-five of the 122 successful-route boxes wrap to three or more rendered rows, although the GBA box retains only two rows at the confirmation state. At least one box in every successful-route scene loses its opening; the early-inn narration does as well, so all 18 scenes are affected.

Material examples:

- Intro orientation ends as `his father Tam cart cider toward / Bel Tine`, with `On the cold Quarry Road, Rand and` already gone: `/tmp/wn00-scenes/001-wn00_tutorial_sc_c0_quarry_road.png`.
- Mat's first line settles on `badger, all grouchy at being / pulled out of his den`, losing who caught it: `/tmp/wn00-scenes/009-wn00_tutorial_sc_c0_mat_and_news.png`.
- The raven instruction retains only `These two throws are scripted / misses`, losing the **Attack** steps: `/tmp/wn00-scenes/051-wn00_tutorial_sc_c0_raven_attack.png`.
- The coin narration retains only `first into Rand's hand, then / Mat's`, losing the noun “silver coin”: `/tmp/wn00-scenes/063-wn00_tutorial_sc_c0_moiraine_coin.png`.

No pixels were drawn outside the surface, portraits did not overlap the box, and speaker portraits matched. The failure is readability: at the settled prompt the player cannot pause on or re-read the complete line as one page.

**Frame evidence:** all reviewed montages at `/tmp/wn00-contact-sc_c0_*.png`; representative native frames above.

**Suspected source:** overheight lines are authored throughout `design/scenes/tutorial/scenes.yaml`; representative critical cases are lines 14 (orientation), 35 (Mat), 120 (raven instruction), and 145 (coin). The scene text is not split/trimmed to the two-row runtime box.

**Smallest remedy:** shorten or explicitly paginate every line that renders beyond two rows, prioritizing instructions and nouns required for scene comprehension. Re-capture every settled box at 240×160 and confirm that the complete current sentence remains visible.

### MED — The raven sequence labels itself an Attack lesson but never gives the player an Attack action

**Repro**

1. Complete the second cider delivery.
2. Step on the red raven marker.
3. Advance the raven scene while watching for a return to map control, an action menu, target selection, or combat forecast.

**Observed**

The scene says `Choose Attack, choose a target, then confirm`, but it is a continuous cinematic. Rand and Mat throw stones in narration, both misses are declared scripted, and the Moiraine coin scene begins without returning control. The explicit “scripted misses” wording prevents the misses themselves from looking like RNG or a broken hit calculation, but this is a demonstration, not a lesson the player can perform. The actionable instruction is also the portion scrolled out of the settled frame.

**Frame evidence:** `/tmp/wn00-scenes/051-wn00_tutorial_sc_c0_raven_attack.png`, reviewed sequence `/tmp/wn00-contact-sc_c0_raven_attack.png`

**Suspected source:** `design/scenes/tutorial/scenes.yaml:120` tells the player to choose an unavailable action; `design/missions/tutorial_emonds_field.yaml:102-110` only calls five scenes and exposes no attack target/action state.

**Smallest remedy:** describe this as a scripted demonstration and reserve the real **Attack** instruction for the first chapter that actually returns control with a valid target, or implement a genuine target/confirm interaction here. Verify with input that the wording matches the public action the player can actually take.

## Checks that passed

- The full route reaches victory with real input. Final flags include Mat, both cider trips, raven, all five optional talks, `entered_inn`, and level end.
- The Quarry Road scene's authored content answers who/where/want: Rand and Tam are hauling cider to Bel Tine, the black rider is the concern, and Mat beside the cart is the first map goal. Portraits and background match. Its readability is reduced by the overheight-box finding.
- Mat's initial **TALK** marker is clear on the festival map, and the Talk action fires once.
- Exactly two cider deliveries are required. The flags progress `carrying_cider_first` → `cider_trip_one` → `carrying_cider_second` → `cider_delivered`; no third cart activation occurred. Distinct prank/honeycake scenes break up the repeated walk, so the two-trip bound itself did not feel like an unbounded fetch quest.
- Egwene, Perrin, Ewin, Fain, and Thom each fire once and read distinctly: promised dance/future travel; black rider/smithy; Moiraine and Lan; false Dragon/mulled wine; and war/gleeman's art. Re-selecting each target produced no **Talk** action.
- Raven, Moiraine coin, Fain news/aftershock, Thom performance, inn council, and departure scenes fire in the correct order.
- Festival sprites, scene backgrounds, and portraits remain inside the 240×160 surface. No speaker/portrait mismatch or novel-only prerequisite was found.
- The gold inn marker is visually obvious, and normal deliberate entry after the required raven gate completes the chapter rather than soft-locking.

**VERDICT: FAIL**
