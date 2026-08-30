# Fun review round 2 — `wn04_long_road` / The Long Road

## Verdict

**FUN — target met.** The core verb is now **carry Tam through cover, then Hide and hold while detection pressure peaks**. The intended run no longer reduces the rider set piece to another maximum-east input: both shelter choices are visible and exactly reachable on turn 6, entering the lower `Hide` shelter changes the runtime state, and the next player turn is an earned held breath. The turn-3 warning and turn-4 sweepers make the approach matter, while the rider is shown before the watched strip. The chapter wins naturally on turn 11, within its 9–12-turn window, and the full fever revelation lands afterward.

No blocking, major, or minor player-facing finding was observed in the required routes.

## Build, engine, and method

- Gated provenance: report tree `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a` (`build/REPORT.md:3-7`).
- Every completed run independently reported that same project tree hash and pinned engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`.
- The engine ran headless with dummy SDL video/audio. The drivers used `_run_input_flow`, posting real pygame key-down/key-up input. They did not invoke events or mutate positions, flags, objectives, HP, AI, or turn state.
- All cited gameplay frames are native 240×160 PNGs and were visually inspected. The five fever contact sheets are review aids assembled from the inspected native frames, not substitute evidence.

### Run ledger

| Run | Player route and observed result | Evidence |
| --- | --- | --- |
| Golden | Followed all presented east/trees/off-road instructions; entered the lower highlighted `Hide` shelter at `[16,8]` on turn 6; explicitly used map **End** to hold turn 7; resumed on turn 8; entered `[25,6]` and triggered the outro on turn 11. No combat; Rand remained 24/24 and Tam remained carried. | `/tmp/fun2-wn04-golden-evidence.json`; frames under `/tmp/fun2-wn04-golden/` |
| Deliberately weak: unhidden at watch | Followed the same route through turn 5, then ignored both shelters and ended turn 6 at `[15,7]` with `rand_hidden: false`. The caught scene fired at the start of turn 7, followed by Game Over; no combat. | `/tmp/fun2-wn04-unhidden-evidence.json`; `/tmp/fun2-wn04-unhidden/unhidden-watch-turn6.png`; `/tmp/fun2-wn04-unhidden/scene-sc_c4_seen-001.png` through `-003.png`; `/tmp/fun2-wn04-unhidden/game-over.png` |
| Regression: road detection | Approached from `[12,5]`, entered pale-road tile `[12,3]` during the active watch on turn 6, and immediately received the caught scene and Game Over; `_lose_game: true`, `rand_hidden: false`, no combat. | `/tmp/fun2-wn04-road-evidence.json`; `/tmp/fun2-wn04-road/scene-sc_c4_seen-001.png` through `-003.png`; `/tmp/fun2-wn04-road/game-over.png` |
| Visual/state probe | Used public event-skip and cursor-pan inputs only. Confirmed the two sweepers visibly present at the west edge on turn 4 and captured the settled hidden turn-7 state. This QA-only cursor work consumed no gameplay turn and is excluded from the fun ledger. | `/tmp/fun2-wn04-probe-evidence.json`; `/tmp/fun2-wn04-probe/sweepers-visible-turn4-spawn.png`; `/tmp/fun2-wn04-probe/turn7-hidden-settled.png` |

The golden evidence's post-transition `completed_turn` resets with the next level state; the exact natural completion is still directly recorded by its turn-11 `[25,6]` event position and the turn-11 `sc_c4_dragonmount_speech` event entry.

## Golden turn ledger and dead-turn ratio

A dead turn has one credible action and no risk, reward, ordering, route, or resource tradeoff. QA-only objective/info screens do not consume or count as turns.

| Turn | End state / decision | Dead? |
| ---: | --- | :---: |
| 1 | `[4,6]`; select an eastward tree lane around the bounded terrain. | No |
| 2 | `[7,6]`; the six-token column appears on pale road, making covered lane choice concrete. | No |
| 3 | `[9,7]`; the west-edge brush warning adds a pace consequence before the units arrive. | No |
| 4 | `[12,7]`; two sweepers spawn at `[0,6]` and `[0,7]` and begin pursuing. | No |
| 5 | `[15,7]`; preserve a turn-6 route to one of two shelters while sweepers close from `[5,6]` and `[5,7]`. | No |
| 6 | `[16,8]`; choose the lower of two highlighted, reachable shelters and enter its real `Hide` region. | No |
| 7 | `[16,8]`; **Stay hidden / Hold still** leaves only the instructed End action. This is deliberately counted even though the pause is emotionally effective. | **Yes** |
| 8 | `[18,7]`; leave the lower pocket through trees while the watched road remains active and the rider still holds. | No |
| 9 | `[20,6]`; the rider releases, the sweepers resume pursuit, and the route changes lane around the blocker/deadfall pattern. | No |
| 10 | `[23,6]`; sweepers advance from `[13,7]`/`[14,7]` to `[18,7]`/`[19,7]`, so pace remains consequential. | No |
| 11 | `[25,6]`; entering the only safe destination is the sole credible action, so the destination turn counts. | **Yes** |

**Golden: 2/11 dead turns (18%)**, down from the baseline **4/9 (44%)**. The two counted turns are separated by active route pressure rather than forming the old four-turn corridor tail.

**Weak unhidden run: 0/6 dead turns (0%) before failure.** Turns 1–5 retain the golden approach decisions. Turn 6 is not dead: two visible safe shelters exist, and the player deliberately rejects that meaningful choice. The consequence arrives before turn-7 control. The baseline weak evidence only recorded that an exposed route lost on turn 7; it did not publish a weak-route ratio.

Mandatory pre-control text is 15 settled pages against 11 natural gameplay turns, **1.36 pages/turn**, below the 4:1 short-chapter budget.

## Tension curve and peak

- **Turns 1–2 — burden and unease:** three-MOV litter travel establishes the cost; the column makes the pale road visibly hostile.
- **Turn 3 — warning:** “Behind Rand, brush snaps at the west edge.”
- **Turns 4–5 — pursuit:** two visible sweepers advance behind the litter and turn shelter approach into a pace problem.
- **Turns 6–7 — mechanical peak:** the camera shows the rider at `[25,3]` while `rider_watching` is still false, then presents the watched strip and both shelters. Rand chooses shelter, hides, and holds.
- **Turns 8–11 — pressured release:** the route resumes through cover; sweepers reactivate and close during the final lane changes.
- **Outro — emotional peak:** the 25-page Dragonmount/baby revelation interrupts the physical release and ends on “Light, who am I?”

**Native-resolution tension-peak frame:** `/tmp/fun2-wn04-golden/rider-visible-before-danger-strip.png`. It visibly relates Rand, the road, and the rider before the danger overlay appears. The decision frame is `/tmp/fun2-wn04-golden/watched-road-highlight.png`; the settled consequence is `/tmp/fun2-wn04-probe/turn7-hidden-settled.png`.

## Regression checks

### PASS — rider appears before the danger strip

At turn 6, the golden run captured the rider at `[25,3]`, camera `[11,0]`, with `rider_watching: false`: `/tmp/fun2-wn04-golden/rider-visible-before-danger-strip.png`. Its event ordering then records `rider_visible` before `danger_strip_active`; the later watched frame shows **Hide in trees / Hold still** and the active map cues. This matches the authored sequence `spawn rider -> activate/highlight rider_stop -> rider scene -> activate shelters/watched road -> shelter highlights -> watched-strip highlight` at `design/missions/long_road.yaml:75-99`.

### PASS — turn-3 warning and turn-4 sweeper spawn

The golden event sequence records `sc_c4_sweeper_warning` on turn 3 and `sc_c4_sweepers` on turn 4. The warning fits its native box: `/tmp/fun2-wn04-golden/scene-sc_c4_sweeper_warning-001.png`. The public-cursor probe visually shows both west-edge tokens on turn 4, while its runtime snapshot records `sweep_a: [0,6]`, `sweep_b: [0,7]`, both with `pursue`: `/tmp/fun2-wn04-probe/sweepers-visible-turn4-spawn.png` and `/tmp/fun2-wn04-probe-evidence.json`. Causal source: `design/missions/long_road.yaml:48-51,71-74,141-145`; warning/spawn dialogue: `design/scenes/long_road/scenes.yaml:156-180`.

### PASS — shelters are telegraphed and reachable

The turn-6 frame visibly presents both green/cyan shelter tiles with **Hide in trees / Hold still**: `/tmp/fun2-wn04-golden/watched-road-highlight.png`. From the actual `[15,7]` turn-6 position with carried MOV 3, runtime pathfinding measured both exact-cost routes:

- upper `[15,5]`: `[15,7] -> [15,6] -> [15,5]`, cost 3, reachable;
- lower `[16,8]`: `[15,7] -> [16,7] -> [16,8]`, cost 3, reachable.

The golden player entered the lower tile on turn 6. At settled turn 7, the real state is Rand `[16,8]`, `rand_hidden: true`, `rider_watching: true`, both sweepers paused with `do_nothing`, and the objective visibly reads **Stay hidden / Hold still**: `/tmp/fun2-wn04-probe/turn7-hidden-settled.png`. Causal source: shelter regions at `design/missions/long_road.yaml:43-44`, activation/highlights and sweeper pause at `:92-99`, Hide outcomes at `:105-120`, and the turn-7 unhidden check at `:146-156`.

### PASS — held turn 7 and both detection losses

The golden route does not move on turn 7 and survives to the turn-8 objective change. The unhidden route reaches Game Over on turn 7 with `_lose_game: true`, and the road-entry route reaches Game Over immediately on turn 6 at `[12,3]`. Both play all three caught pages before Game Over and record `saw_combat: false`. The two separate loss causes remain authored at `design/missions/long_road.yaml:146-162`.

### PASS — victory, carry, pressure, and soft-lock checks

- Golden victory/outro occurs naturally on turn 11 after entering `[25,6]`; the exit and win are at `design/missions/long_road.yaml:175-182`.
- Rand remains at 24/24 HP, Tam remains his traveler through the played map route, and no combat state occurs.
- Sweepers are `do_nothing` during the rider hold and return to `pursue` after release, observed in the turn snapshots and authored at `design/missions/long_road.yaml:94-95,127-129`.
- Golden play reaches victory/outro; unhidden watch and road exposure both reach Game Over. No tested branch soft-locks.
- The formal watch and release Objective screens fit without clipping: `/tmp/fun2-wn04-golden/objective-watch.png` and `/tmp/fun2-wn04-golden/objective-release.png`.

### PASS — fever speech is intact at native resolution

The golden run captured and visually inspected all **25** settled `sc_c4_dragonmount_speech` pages: `/tmp/fun2-wn04-golden/scene-sc_c4_dragonmount_speech-001.png` through `-025.png`. Their first visible words are, in order: **Beyond, into, Battles, Sweat, Slope, Had, Heard, fight, Gave, Covered, blown, Child, Crying, I, Always, I, Yes, Rand's, The, Tam, Tam, You, The, Rand, One**. This matches `design/scenes/long_road/scenes.yaml:181-217`; no line is clipped, scrolled away, overlapped, or outside its GBA-sized box. Review aids: `/tmp/fun2-wn04-fever-sheet-1.png` through `-5.png`.

## Findings by severity

No blocking, major, or minor player-facing finding was observed. Because the chapter reaches the requested **FUN** target, no ranked implementation fixes are required.

## Locked contracts preserved

Tam remains the carried traveler; Rand and Tam must survive; the column and rider remain non-attacking; detection rather than combat causes failure; both turn-start threats are telegraphed; the rider is shown before its danger zone; the chapter retains real Hide/hold play; and the uninterrupted fever speech remains the ending payoff (`design/missions/long_road.yaml:183-192`).
