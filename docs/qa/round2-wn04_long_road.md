# Round 2 QA — `wn04_long_road` / The Long Road

## Verdict

**COHERENT — PASS.** Both round-1 findings are fixed in the compiled project. Following only the presented directions—keep moving east beneath the trees and stay off the pale road—kept Rand ahead of the sweepers, caused no combat, reached the east exit on turn 9, and played the complete outro. All four runtime Objective states fit the 240×160 screen. Deliberately remaining on the watched road still plays the caught scene before Game Over. No new player-facing regression was found in the tested paths.

Tested against compiled tree `a666a9e750c52f07f28e4fdd0e2cd16e5f139f600f3f220962600bb5eea9753d` with engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. Both runs launched `build/winternight.ltproj` through the pinned engine with dummy SDL video/audio and posted real pygame key events. The golden run used 139 select inputs plus real directional/cancel inputs across 6,234 frames; the loss run used real input across 2,688 frames. All cited gameplay captures are native 240×160 PNGs and were inspected visually; the enlarged fever-speech contact sheets are review aids only.

## Intended loop and observed route

- The opening scene establishes the litter. On the map, Rand visibly carries Tam; the banner and Objective screen say **“Pull Tam east / Avoid pale road.”**
- Rand moved east through tree rows `y6` and `y7`, never entering pale road row `y3`. End positions were `(4,6)`, `(7,6)`, `(9,7)`, `(12,7)`, and `(15,7)` on turns 1–5.
- The turn-2 column appeared on the road and marched east. The Objective screen changed to **“Keep moving east / Avoid pale road.”**
- On turn 5, Rand explicitly says **“Sweepers behind us. Keep moving east,” “If the rider returns, keep moving east,”** and **“Stay in the trees. Keep off the pale road.”**
- When the rider returned on turn 6, the scene reinforced **“Rand keeps east beneath the branches”** and **“He moves slowly, never breaking cover.”** The Objective screen changed to **“Go east in trees / Avoid pale road.”**
- Obeying those instructions moved Rand to `(18,7)`, `(20,6)`, and `(23,6)` on turns 6–8. The sweepers did not reach or attack him; the run recorded `saw_combat: false` and unchanged Rand HP.
- On turn 9, the Objective screen changed to **“Reach east edge / Stay off road.”** Rand moved through `(24,6)` to the highlighted exit at `(25,6)`, triggered victory, and reached the outro transition.
- The independent loss run deliberately moved Rand onto road row `y3` and ended turn 6 there. At turn 7, all three `sc_c4_seen` boxes played before Game Over; the run recorded `_lose_game: true`, `saw_caught: true`, and `saw_combat: false`.

## Coherence trace

| State | Player-facing goal | Visible cue/action | Observed result and next goal |
| --- | --- | --- | --- |
| Start | Pull Tam east; avoid the pale road | Attached traveler sprite, map banner, and Objective screen all agree | Moving Rand east also carries Tam; reduced movement is visible |
| Turn 2 column | Keep moving east; avoid the pale road | Six-unit column visibly occupies and marches along the road; Objective screen updates | Rand continues east below the road without combat |
| Turn 5 warning | Stay ahead of sweepers; do not use the road | Three short dialogue boxes repeat “keep moving east,” “stay in the trees,” and “keep off the pale road” | The next turn presents the rider search with the same instruction |
| Turns 6–8 watch | Go east in trees; avoid the pale road | Rider scene, highlighted watched row, map banner, and Objective screen agree | Advancing every turn beneath cover survives both sweepers and the rider watch |
| Turn 9 release | Reach the east edge; stay off road | Objective screen updates and the east exit is highlighted | Entering `(25,6)` wins and starts the outro |
| Detection loss | Be caught if exposed on the watched road | Pale road row is distinct and the warning has named it repeatedly | The empty hood turns, every Trolloc follows, Rand reacts, then Game Over appears |
| Outro | Receive Tam's fever revelation | 25 click-separated, settled boxes over `westwood_road_night` | Full sequence completes and the game transitions onward |

## Round-1 findings re-verification

### RESOLVED — Round 1 HIGH: “Hold still” instruction caused a sweeper attack

**Round-1 item:** `docs/qa/round1-wn04_long_road.md:35-60`.

**Re-test:**

1. Read the opening and turn-5 instructions without using hidden coordinates or enemy AI knowledge.
2. Carry Tam generally east on passable tree tiles and never enter the clearly pale road.
3. When the rider returns, continue east beneath the branches exactly as both the scene and Objective screen direct.
4. Continue until the visible east exit appears, then enter it.

**Observed:** Rand ended turns 5–8 at `(15,7)`, `(18,7)`, `(20,6)`, and `(23,6)`, respectively, then entered `(25,6)` on turn 9. No combat state occurred, Rand remained at 24/24 HP, victory fired, and all 25 outro boxes played. The formerly contradictory “freeze/hold still” language did not appear.

**After-evidence:**

- `/tmp/wn04-f1-golden/scene-sc_c4_sweepers-002.png`
- `/tmp/wn04-f1-golden/scene-sc_c4_sweepers-003.png`
- `/tmp/wn04-f1-golden/scene-sc_c4_sweepers-004.png`
- `/tmp/wn04-f1-golden/scene-sc_c4_rider_stops-010.png`
- `/tmp/wn04-f1-golden/scene-sc_c4_rider_stops-011.png`
- `/tmp/wn04-f1-golden/watched-road-highlight.png`
- `/tmp/wn04-f1-golden-evidence.json` (`saw_combat: false`, turn-by-turn position trace, victory/outro transition)

**Current source:** `design/scenes/long_road/scenes.yaml:166-169` now gives the one-turn sweeper/rider warning, and `design/scenes/long_road/scenes.yaml:89-99` reinforces continued covered movement during the search. The matching runtime objectives are authored at `design/missions/long_road.yaml:65`, `design/missions/long_road.yaml:80`, and `design/missions/long_road.yaml:95`. Sweepers still use pursuing AI at `design/missions/long_road.yaml:38-39`; the repaired text now teaches the mechanically safe behavior rather than contradicting it.

### RESOLVED — Round 1 MED: formal Objective screen clipped the destination

**Round-1 item:** `docs/qa/round1-wn04_long_road.md:62-76`.

**Re-test:** Opened the formal Objective screen after every objective change, waited for the screen to settle, captured it at native resolution, and read every rendered line.

| Stage | Observed Win Conditions text | Evidence |
| --- | --- | --- |
| Start | `Pull Tam east` / `Avoid pale road` | `/tmp/wn04-f1-golden/objective-start.png` |
| Column passing | `Keep moving east` / `Avoid pale road` | `/tmp/wn04-f1-golden/objective-column.png` |
| Rider watching | `Go east in trees` / `Avoid pale road` | `/tmp/wn04-f1-golden/objective-watch.png` |
| Rider released | `Reach east edge` / `Stay off road` | `/tmp/wn04-f1-golden/objective-release.png` |

All four Win Conditions pairs and the repeated Loss Conditions pair **“Rand and Tam / must survive”** render completely. No ellipsis, truncation, overlap, or panel overflow is visible. The runtime evidence records identical `win` and `simple` values at all four stages, confirming that the formal Objective screen updates with the map banner rather than retaining the old start text.

**Current source:** the base display string is shortened at `design/missions/long_road.yaml:22`; the four two-line runtime strings are at `design/missions/long_road.yaml:57`, `:65`, `:80`, and `:95`.

## Required-path and presentation checks

- **Instruction-following golden victory: PASS.** The route followed the visible east/trees/off-road directions, stayed entirely on `y6`/`y7`, survived the sweepers, won on turn 9, and saw no combat. Evidence: `/tmp/wn04-f1-golden-evidence.json` and the instruction/watch frames listed above.
- **Detection loss with caught scene: PASS.** Rand remained on road row `y3` through the active watch; turn 7 played the full caught sequence before Game Over. Evidence: `/tmp/wn04-f1-loss/loss-road-turn6.png`, `/tmp/wn04-f1-loss/scene-sc_c4_seen-001.png` through `-003.png`, `/tmp/wn04-f1-loss/game-over.png`, and `/tmp/wn04-f1-loss-evidence.json`. The trigger and scene remain at `design/missions/long_road.yaml:109-125` and `design/scenes/long_road/scenes.yaml:100-112`.
- **Objective screen at every stage: PASS.** All four runtime states fit, update, and agree with the map banner. Evidence: the four Objective captures in the table above.
- **Carry mechanic legibility: PASS, unchanged.** Personal Data visibly shows `Move 5-2` and `Trv Tam`; the map sprite shows the attached traveler; selecting Move shows the reduced three-tile blue range. Evidence: `/tmp/wn04-f1-golden/carry-unit-info.png`, `/tmp/wn04-f1-golden/carry-map.png`, and `/tmp/wn04-f1-golden/carry-move-range.png`. The pairing contract is authored at `design/missions/long_road.yaml:55`.
- **Column behavior: PASS.** Six tokens visibly march east on the pale road, the Objective banner says to keep moving east and avoid that road, and the golden run records no combat. Evidence: `/tmp/wn04-f1-golden/column-mid-march.png` and `/tmp/wn04-f1-golden-evidence.json`.
- **Watched-road cue: PASS.** The pale horizontal road and watched-row highlight remain visible while both the banner and Objective screen say to go east in trees and avoid the pale road. Evidence: `/tmp/wn04-f1-golden/watched-road-highlight.png` and `/tmp/wn04-f1-golden/objective-watch.png`.
- **Fever-speech outro: PASS.** All **25** current settled boxes were captured and visually re-inspected at native resolution: `/tmp/wn04-f1-golden/scene-sc_c4_dragonmount_speech-001.png` through `-025.png`. Their visible first words are, in order: **Beyond, into, Battles, Sweat, Slope, Had, Heard, fight, Gave, Covered, blown, Child, Crying, I, Always, I, Yes, Rand's, The, Tam, Tam, You, The, Rand, One**. These match the authored starts/splits at `design/scenes/long_road/scenes.yaml:181-205`; no box begins after its authored first word, and no text is clipped, scrolled away, or drawn outside the two-row box. Review contact sheets: `/tmp/wn04-r2-fever-sheet-1.png` through `-5.png`.
- **Background and portrait presentation: PASS.** `westwood_road_night` fills the frame without seams or letterboxing. Tam remains on the right through the memory, Rand appears on the left for “You are my father,” and narration remains readable over both portraits.
- **Soft-lock check: PASS.** The instructed route reaches victory/outro; the watched-road violation reaches Game Over. Neither required branch stalls.

## Findings

No blocking, major, or minor player-facing findings were observed in the tested golden or detection-loss paths.

## Final chapter verdict

**PASS for round 2.** The central instruction/mechanics contradiction and the clipped formal objective are both fixed in-engine, every named acceptance path works, and no regression was observed in carry legibility, detection loss, column behavior, watched-road communication, or the full fever-speech outro.
