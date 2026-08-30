# Round 2 QA — `wn00_tutorial`

**Assessment:** coherent. The earliest recovery branch now redirects once and returns control, every required state has a truthful persistent objective, crossing the inn doorway is non-committing, and the ending requires the explicit **Enter Inn** action. The complete route with all five optional talks reaches the outro and chapter transition.

**Verdict:** PASS

## Build and method

Tested the already-compiled `build/winternight.ltproj` at tree `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d` with pinned engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. I did not recompile or edit generated data. Both routes ran headless with dummy SDL and posted real pygame key-down/key-up events; the driver did not invoke triggers directly or mutate units, positions, flags, events, or objectives.

- Early-inn stress route: completed in 1,724 frames with no failure. It entered the inn approach before Mat, dismissed the redirect, waited on both entrance tiles, stepped away, re-entered, and then reached Mat. Runtime record: `/tmp/round2-wn00/early-run.json`; state/evidence summary: `/tmp/round2-wn00/early-summary.json`.
- Golden route: completed in 8,288 frames on turn 17 with no failure. It included Egwene, Perrin, Ewin, Fain, and Thom, crossed the active doorway in both directions, explicitly chose **Enter Inn**, played the council and departure scenes, and reached the chapter transition. Runtime record: `/tmp/round2-wn00/golden-run.json`; state/evidence summary: `/tmp/round2-wn00/golden-summary.json`.
- All eight Objective screens and all 198 distinct authored boxes across the 18 exercised scenes were captured at their settled confirmation state at native 240×160. I visually reviewed the Objective montage and every scene contact sheet. Objective montage: `/tmp/round2-wn00/objectives-contact.png`; reviewed scene sheets: `/tmp/round2-wn00/review-contacts/`.

## Round-1 before/after verification

| Round-1 item | After observation | Evidence | Current source anchor |
| --- | --- | --- | --- |
| **BLOCKER: early inn redirect loops forever** (`docs/qa/round1-wn00_tutorial.md:52-68`) | Fixed. The three-box redirect played exactly once. Control returned on `(9, 8)` with `before_mat_gate_active: false`. Waiting on `(9, 8)`, waiting on `(9, 7)`, stepping away to `(10, 7)`, and returning to `(9, 8)` across turns 3–6 produced only **Item / Wait**, no second redirect, no win, and no loop. Rand then talked to Mat normally. | `/tmp/round2-wn00/critical/early-redirect-contact.png`, `/tmp/round2-wn00/critical/early-probes-contact.png`, `/tmp/round2-wn00/early-summary.json` | The condition-gated region is `design/missions/tutorial_emonds_field.yaml:25`; the event now clears the gate, resets Rand, and is one-shot at `design/missions/tutorial_emonds_field.yaml:54-62`. |
| **HIGH: Objective screen remains on Mat and clips** (`docs/qa/round1-wn00_tutorial.md:70-89`) | Fixed. The real Objective screen showed, in order: **Talk to Mat / Choose Talk**, **Lift first cask / Blue cart marker**, **Carry to cellar / Gold marker**, **Back to cart / One trip left**, **Carry last cask / Gold marker**, **Find roof raven / Red marker**, and **Choose Enter Inn**. The final text remained **Choose Enter Inn** after all optional talks. Both runtime `simple` and `win` slots matched at all eight captures. No objective or deduplicated loss text clipped. | `/tmp/round2-wn00/objectives/01-initial.png` through `08-inn_after_all.png`; montage `/tmp/round2-wn00/objectives-contact.png`; records `/tmp/round2-wn00/golden-summary.json:3620-3684` | Both slots are updated at `design/missions/tutorial_emonds_field.yaml:38,51,70,81,92,103,120`. |
| **HIGH: crossing the active inn door auto-wins** (`docs/qa/round1-wn00_tutorial.md:91-109`) | Fixed. After Fain, Rand followed the explicitly selected east-to-west path `(10,9) → (9,9) → (9,8) → (8,8)`, crossing the south door tile; after Thom he crossed back `(8,8) → (9,8) → (9,9) → (10,9)`. Both crossings returned to map control with `entered_inn: false` and no win. Deliberately stopping on `(9,8)` then exposed **Enter Inn / Item / Wait**; the chapter ended only after **Enter Inn** was selected. | `/tmp/round2-wn00/critical/door-crossing-contact.png`; exact paths and flags `/tmp/round2-wn00/golden-summary.json:3687-3819` | `inn_door` is a non-interrupting event region with the **Enter Inn** sub-ID at `design/missions/tutorial_emonds_field.yaml:29`; only that interaction fires the ending at `design/missions/tutorial_emonds_field.yaml:158-164`. |
| **MED: settled boxes lose their openings** (`docs/qa/round1-wn00_tutorial.md:111-136`) | Fixed. The golden route captured 195 settled boxes; the early route supplied the three-box early-inn scene, covering all 198 authored boxes exactly once. Every native frame visibly began with its authored first word and stayed within the two-row box. Runtime render records also report zero boxes over `num_lines` and zero nonzero display starts. No portrait, box, or text overflow was visible. | Native frames `/tmp/round2-wn00/scenes/`; the 32 visually reviewed contact sheets `/tmp/round2-wn00/review-contacts/`; counts `/tmp/round2-wn00/golden-summary.json:3823-3825` and `/tmp/round2-wn00/early-summary.json:658-660` | The fitted tutorial boxes span `design/scenes/tutorial/scenes.yaml:14-420`; representative round-1 cases are now split at lines `14-21`, `35-51`, `140-150`, and `164-179`. |
| **MED: raven scene gives a phantom Attack lesson** (`docs/qa/round1-wn00_tutorial.md:138-154`) | Fixed. The 11-box sequence is cinematic throughout: Rand and Mat stoop for stones, throw together, the raven steps aside, and Moiraine responds. No box says **Attack**, **Choose**, names a target-selection control, or implies that map control will return for a throw. | `/tmp/round2-wn00/review-contacts/sc_c0_raven_attack-1.png`, `/tmp/round2-wn00/review-contacts/sc_c0_raven_attack-2.png` | `design/scenes/tutorial/scenes.yaml:128-150`. |
| **Successful route and five one-shot optional talks** (round-1 coverage `docs/qa/round1-wn00_tutorial.md:9-16` and passed checks `:156-165`) | Still passes. All five talk flags and every mandatory progression flag were true before entry; `talk_options` was empty. The inn council, departure scene, level-end trigger, and transition all fired. | `/tmp/round2-wn00/golden-summary.json:3826-3846`; scene sheets for `sc_c0_egwene`, `sc_c0_perrin`, `sc_c0_ewin`, `sc_c0_fain_optional`, `sc_c0_thom_optional`, `sc_c0_inn_council`, and `sc_c0_depart_for_farm` under `/tmp/round2-wn00/review-contacts/` | Optional interactions are `design/missions/tutorial_emonds_field.yaml:123-157`; entry and outro are lines `158-168`. |

## Coherence trace

| State | Player-facing goal | Visible cue | Public action | Feedback / next goal |
| --- | --- | --- | --- | --- |
| Festival start | Talk to Mat | Mat's **TALK** marker | Move adjacent; choose **Talk** | Blue cart marker activates; Objective changes to the first cask |
| Inn before Mat | Return to Mat | Doorway plus redirect scene | Choose the early door interaction once, then move normally | Control returns; the gate is consumed; Objective remains truthful |
| First pickup | Lift the first cask | Blue cart marker | Enter marker | Gold cellar marker activates; Objective changes to carry |
| First delivery | Deliver the cask | Gold marker | Enter marker | One trip is acknowledged; cart reactivates |
| Second pickup | Lift the last cask | Blue marker | Enter marker | Gold marker returns; Objective names the last cask |
| Second delivery | Finish cider work | Gold marker | Enter marker | Work is complete; red raven marker activates |
| Raven | Investigate the roof watcher | Red marker | Enter marker; advance cinematic boxes | Fain/Thom talks and inn action unlock; Objective becomes **Choose Enter Inn** |
| Post-raven | Optional talks or finish | **TALK** markers and gold doorway | Choose **Talk** or stop on the door and choose **Enter Inn** | Crossing the door is safe; only the explicit entry action commits |
| Inn | Leave the Green | **Enter Inn** menu action | Choose **Enter Inn** | Council and departure scenes play; chapter transitions |

## Findings, severity ordered

No blocking, high, medium, or low player-facing findings were observed in the exercised routes. No round-1 finding reproduced, and no regression was found.

## Loss-path limitation

As in round 1 (`docs/qa/round1-wn00_tutorial.md:26,48`), the only configured failure is Rand's death (`design/missions/tutorial_emonds_field.yaml:10-11`), but this combat-free chapter exposes no enemy or damaging public action. A first-time player cannot deliberately reach that loss state with genuine input. I did not mutate Rand's HP or death state to manufacture evidence. The explicit wrong-door recovery path was exercised instead and is now safe.

**VERDICT: PASS**
