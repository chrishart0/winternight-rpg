# Round 3 QA — `wn03_return_to_farm` / The Ruined Farm

## Verdict

**COHERENT — PASS.** The round-2 Objective-screen defect is resolved. On the real-input golden path, the formal Objective screen was opened after the farmhouse approach, after the sword/Narg spawn, after the Narg encounter, and after Narg's defeat. At all four stages it matched the active map banner, rendered both authored lines completely at native 240×160, and never showed the stale opening goal **“Reach the house / Through the fog.”**

The chapter also remained completable: the golden route reached the west exit, played the cart-shaft and Tam-reunion outros, and reached chapter save on turn 12. A current-build deliberate-loss regression run reached visible Game Over on turn 9. No player-facing regression was found.

Tested against compiled project tree `624deb7b28bf24d1ee32629ef8215204631cf3805f01414eec00c74d30ae22f5` with pinned engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. The golden run launched the already-compiled `build/winternight.ltproj` through `vendor/lt-maker` with dummy SDL video/audio and posted real pygame key events. It completed across 4,613 frames with 207 select inputs plus real directional, cancel, and skip inputs. The independent loss run completed across 3,205 frames with 122 select inputs plus real directional, cancel, and skip inputs. Every cited PNG is a native 240×160 engine capture and was visually inspected.

## Objective-screen re-verification

The map banner was allowed to settle before capture. The formal Objective screen was then opened through map options with real input and allowed to finish its transition before capture.

| Required stage | Formal Objective screen | Map banner | Result |
| --- | --- | --- | --- |
| After farmhouse approach | **“Find Tam's needs” / “Search the ruin”** — `/tmp/wn03-round3-v2/objective-farmhouse.png` | Same two lines — `/tmp/wn03-round3-v2/banner-farmhouse.png` | **PASS:** current stage shown; both lines complete; no clipping or stale opening goal |
| After sword recovery and Narg spawn | **“Survive Narg” / “Gather the rest”** — `/tmp/wn03-round3-v2/objective-narg-spawn.png` | Same two lines — `/tmp/wn03-round3-v2/banner-narg-spawn.png` | **PASS:** current stage shown before the encounter flag; both lines complete |
| After the Narg encounter | **“Return west” / “Back to Tam”** — `/tmp/wn03-round3-v2/objective-narg-encounter.png` | Same two lines — `/tmp/wn03-round3-v2/banner-narg-encounter.png` | **PASS:** current stage shown with Narg still alive; both lines complete |
| After Narg's defeat | **“Return west” / “With supplies”** — `/tmp/wn03-round3-v2/objective-narg-defeat.png` | Same two lines — `/tmp/wn03-round3-v2/banner-narg-defeat.png` | **PASS:** post-defeat stage shown; both lines complete |

Runtime snapshots corroborate the frames: at each capture, `simple` and `win` contained the same current two-line value. The farmhouse snapshot had `farmhouse_reached: true`; the spawn snapshot had `sword_found: true` and `narg_encountered: false`; the encounter snapshot had `narg_encountered: true` with Narg alive; and the defeat snapshot had `trolloc_defeated: true` with Narg dead. Evidence: `/tmp/wn03-round3-v2-details.json`.

The repaired source locations are `design/missions/return_to_farm.yaml:52` (farmhouse), `:85` (Narg spawn), `:93` and `:100` (either combat direction), and `:105` (Narg defeat). All now use `target: both`, and the observed runtime `win` values confirm that the formal screen—not only the banner—advances.

## Golden-path and regression checks

- **Golden victory: PASS.** The real-input route visited the sheep pen, reached the farmhouse, searched water, clean cloth, and blankets, recovered the sword, survived Narg's first attack, defeated Narg, and returned through the west exit. All four objective checks completed during the route. Evidence: `/tmp/wn03-round3-v2-result.json`, `/tmp/wn03-round3-v2-details.json`.
- **Outro and terminal transition: PASS.** The run captured all eight cart-shaft boxes and all seventeen Tam-reunion boxes, then reached `title_save` on turn 12. Evidence: `/tmp/wn03-round3-v2/event-wn03_return_to_farm_sc_c3_cart_shafts-01.png` through `-08.png`; `/tmp/wn03-round3-v2/event-wn03_return_to_farm_sc_c3_rejoin_tam-01.png` through `-17.png`; `/tmp/wn03-round3-v2-details.json`.
- **Narg dialogue spot-check: PASS.** Settled boxes begin at their authored first words: **“Others go away. Narg stay. Narg smart.”**, **“Narg know some come back sometime.”**, and **“Narg wait. You no need sword. Put sword down.”** Evidence: `/tmp/wn03-round3-v2/event-wn03_return_to_farm_sc_c3_trolloc_appears-03.png`, `-04.png`, and `-05.png`; source: `design/scenes/return_to_farm/scenes.yaml:130-132`.
- **Loss branch: PASS.** In a separate current-build real-input run, Rand equipped the Hunting Bow after the first encounter so Narg could finish the adjacent fight. Rand reached 0 HP with `_lose_game: true`, Narg remained alive at 2 HP, and the engine displayed Game Over on turn 9. Evidence: `/tmp/wn03-round3-loss/game-over.png`, `/tmp/wn03-round3-loss-result.json`, `/tmp/wn03-round3-loss-details.json`.
- **Soft-lock review: PASS.** The required route reached chapter save and the deliberate death route reached Game Over. No required interaction or terminal transition became unavailable.

## Findings

No blocking, major, or minor player-facing findings in this focused round.

## Final chapter verdict

**PASS for round 3.** The formal Objective screen now advances through all four required mid-chapter states, stays synchronized with the map banner, and fits the native GBA-sized display without clipping. Victory, loss, outro, and the sampled Narg dialogue remain healthy on the recompiled project.
