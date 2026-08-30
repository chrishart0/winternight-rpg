# Fun review round 2 — `wn03_return_to_farm`

**Verdict: MOSTLY FUN — target met.** The chapter now sustains its **search / care / escape** verb much better. The sheep-pen visit visibly increases fog vision from radius 3 to 4 and reveals the farmhouse cue; every objective state keeps the turn-12 deadline in view; the turn-10 fever warning fires on both natural branches; killing Narg activates a clearly named quick exit; leaving him alive preserves the longer, pressured west route; and public Wait through turn 12 produces the authored loss at the start of turn 13. The kill route's strict dead-turn ratio improves from baseline **7/11 (64%)** to **5/10 (50%)**, with the resolved return tail cut from four turns to two. It remains MOSTLY FUN rather than FUN because those two post-kill turns are still foregone movement and the exercised kill and evasion branches both finish on turn 10, so the quick exit removes pursuit risk and distance but does not produce a net earlier clear.

## Runtime evidence

- Tested compiled artifact: `build/winternight.ltproj`, report tree **`a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`** and manifest SHA-256 `e20d63d4cceb81952f5cf2db587fc4cfe8e7cfcf90349554b09576a5b9485601`.
- Pinned engine: `vendor/lt-maker`, commit **`1820e585450f6f47605aebd686b2a3f13af181f0`**, engine `2026.02.17a`.
- Method: the pinned engine loaded the already-compiled project under dummy SDL video/audio. All three routes used posted pygame key-down/key-up input for movement, menus, region actions, combat targeting, scene advance, Wait, and ending transitions. The driver read runtime state to choose public inputs but never invoked an event, changed a flag/objective, moved a unit directly, edited HP, or modified project data.
- Golden kill route: `/tmp/fun2-wn03-stable/golden.json`; 4,906 engine frames; real directional, Select, Back/skip inputs; 90 settled event pages plus map/combat captures under `/tmp/fun2-wn03-stable/golden/`.
- Evasion route: `/tmp/fun2-wn03-stable/evasion.json`; 4,935 frames; 90 settled event pages plus map/combat captures under `/tmp/fun2-wn03-stable/evasion/`.
- Deadline-loss route: `/tmp/fun2-wn03-stable/stall.json`; 1,692 frames; public Wait through turn 12, loss on turn 13, and a held Game Over frame under `/tmp/fun2-wn03-stable/stall/`.
- The three accepted runs produced **209 native 240x160 PNGs**. The 90 golden event pages were vision-inspected through `/tmp/fun2-wn03-stable/contact/golden-dialogue-01.png` through `-08.png`; the three unique deadline-loss pages through `/tmp/fun2-wn03-stable/contact/deadline-loss-01.png`; and the key map states individually at their paths below. Contact sheets are inspection aids; cited evidence frames remain the native originals.

## Dual-run fun protocol

### Golden / intended kill route

Player route in public verbs:

1. Turn 1: move into the sheep pen and choose **Visit**.
2. Turn 2: follow the newly visible farmhouse cue and **Visit** the approach.
3. Turns 3-6: **Search** for water, clean cloth, and blankets, with one route-positioning turn between the southern water and northern cloth.
4. Turn 7: **Search** Tam's sword; Narg rises, advances, and hits Rand for 13 damage on the enemy phase. Rand survives at 11/24.
5. Turn 8: choose **Attack** and defeat Narg. The objective immediately becomes **“Quick exit west / By turn 12.”**
6. Turn 9: move west toward the activated quick exit.
7. Turn 10: Tam's fever warning fires, then Rand enters the quick exit at `[4,7]`; the cart-shaft and Tam-reunion scenes play and the route reaches the chapter-save transition.

The clear is on **turn 10**, before the loss event at the start of turn 13, leaving the player all of turns **11 and 12** as spare. Narg's observed maximum single enemy-phase damage was 13 against Rand's 24 HP, preserving the cannot-one-round contract. Evidence: `/tmp/fun2-wn03-stable/golden.json`; `design/missions/return_to_farm.yaml:15,84-116,132-140`.

### Evasion / deliberately weak route

The route performs the same all-content search but does not attack Narg after the mandatory encounter. At the start of turn 8, Rand is `[10,8]` and Narg is adjacent at `[11,8]` with 2 HP. Rand retreats to `[6,7]` on turn 8 and `[1,7]` on turn 9 while Narg pursues to `[9,7]` and then `[6,7]`. The turn-10 warning fires before Rand enters the original long exit at `[0,7]`. Narg remains alive, `trolloc_defeated` remains false, the quick exit never activates, and the chapter still completes without a soft-lock.

This is a real branch rather than a disguised kill route: the destination is farther west, the pursuer remains visible behind Rand, and the long-exit win condition accepts the encountered-but-living Narg. Evidence: `/tmp/fun2-wn03-stable/evasion.json`, `/tmp/fun2-wn03-stable/evasion/evasion-live-narg.png`; `design/missions/return_to_farm.yaml:23-24,128-135,144-150`.

## Dead-turn ledger versus baseline

A dead turn uses the repository's strict definition: one credible action and no risk, reward, ordering, route, or resource tradeoff. Raw and natural turn counts are equal because these runs contain no QA-only probe turns.

| Route | Natural / raw turns | Dead turns | Baseline | Judgment |
| --- | ---: | ---: | ---: | --- |
| Golden kill + quick exit | **10 / 10** | **5/10 (50%)** | **7/11 (64%)** | Dead: turn 2 farmhouse handoff, turn 6 last remaining supply, turn 7 sword, and turns 9-10 after Narg is dead. The post-kill tail is **2 turns**, down from baseline 4. |
| Weak evasion + long exit | **10 / 10** | **4/10 (40%)** | **7/11 (64%)** natural reference | Dead: farmhouse, last supply, sword, and the destination turn. Turns 8-9 are not dead: an adjacent living Narg and the deadline create immediate flee/fight and spacing consequences. The lower ratio is a risk diagnostic, not evidence that weak play is stronger. |
| Full stall | **12 player turns observed; loss starts turn 13** | **12/12 (100%)** | Prior weak route died in combat on turn 9 | Intentionally all dead, but no longer a soft wait or mercy win: turn 10 warns and turn 13 loses. |

Baseline source: `docs/qa/fun-review.md:192-217`. The implementation removes two of the four dead post-kill return turns and introduces deadline pressure without miscrediting the warning itself as a new decision.

## Sheep-pen information payoff

**PASS.** Before the Visit, the opening map uses player and AI fog radius 3 and shows only the near edge of the ruin: `/tmp/fun2-wn03-stable/golden/opening-objective.png`. After the dead-flock scene, the turn-2 runtime snapshot records both `_fog_of_war_radius: 4` and `_ai_fog_of_war_radius: 4`; the native frame visibly exposes another ring of the farmhouse and the gold farmhouse-approach cue: `/tmp/fun2-wn03-stable/golden/sheep-intel-radius4.png`. The objective remains **“Reach farmhouse / By turn 12.”**

This is a genuine next-state payoff rather than optional flavor: the Visit changes available planning information while preserving symmetric fog and no enemy exists on the map yet. Causal source: `design/maps/althor_farm.yaml:32-35`; `design/missions/return_to_farm.yaml:17-18,43-51`.

## Deadline pressure and quick-exit legibility

The runtime objective log in `/tmp/fun2-wn03-stable/golden.json` records the deadline at every gate:

| Gate | Displayed objective |
| --- | --- |
| Opening | `Reach farmhouse / By turn 12` |
| Farmhouse reached | `Find Tam's needs / By turn 12` |
| Sword / Narg reveal | `Survive Narg / Back by turn 12` |
| First Narg combat | `Return west / By turn 12` |
| Narg killed | `Quick exit west / By turn 12` |

Both natural routes reach turn 10, so the warning is not dead code or a QA-only stall bark. Its two native pages—**“Far off, Tam cries out beneath the Westwood trees.”** and **“Light, the fever. I have to get back now.”**—fit cleanly at 240x160: `/tmp/fun2-wn03-stable/golden/event-wn03_return_to_farm_sc_c3_fever_warning-01.png` and `-02.png`. The following free frame still shows the deadline and correct branch objective: `/tmp/fun2-wn03-stable/golden/turn10-warning-pressure.png`.

The kill reward is immediately legible in text: `/tmp/fun2-wn03-stable/golden/quick-exit-highlight.png` shows **“Quick exit west / By turn 12,”** and the runtime trace records the quick region active only after `trolloc_defeated`. The exact strip at x=4 is initially beyond radius-4 fog from Rand at `[10,8]`, so the persistent banner carries the first move; it comes into vision as Rand heads west. The evasion route never receives that objective or region and must reach x=0. Wiring: `design/missions/return_to_farm.yaml:9,58,94,102,110-127`.

## Tension curve and peak

**Fogged approach -> dead-flock dread plus useful information -> care-item ordering under a visible deadline -> sword recovery -> Narg's false-safe speech -> first enemy-phase lunge -> kill-or-evade decision -> fever warning -> release with Tam.** The peak remains Narg's reveal and first attack, but the curve no longer collapses into a four-turn empty return. The kill route releases into two short turns before the warning restores urgency; the evasion route keeps Narg on screen as a pursuer until the final west step.

**Tension-peak frame:** `/tmp/fun2-wn03-stable/golden/event-wn03_return_to_farm_sc_c3_trolloc_appears-03.png`. Narg fills the right side of the native frame and opens with **“Others go away. Narg stay. Narg smart.”** The following thirteen reveal pages and all eight combat-quote pages fit without clipping.

Mandatory pre-control text is **10 pages / 10 natural turns = 1.0 pages per turn**, well below the repository's 4:1 short-chapter budget. Source: `design/scenes/return_to_farm/scenes.yaml:3-22`.

## Mission-coherence and regression checks

| State | Player-facing goal and cue | Public action | Feedback / result |
| --- | --- | --- | --- |
| Start | Reach the farmhouse east through fog by turn 12; sheep pen and near route visible | Move; optional **Visit** at sheep pen | Dead-flock scene, radius 4, farmhouse highlight |
| Farmhouse | Find Tam's needs by turn 12; three colored search markers | Move onto marker; **Search** | Each care item has a scene, item grant, and consumed marker |
| Sword | Recover the final marked sword after all three needs | **Search** | Sword equips, Narg appears, objective changes |
| Encounter | Survive Narg and return west | Allow first combat, then **Attack** or flee | Encounter flag opens the long exit; death opens quick exit |
| Kill branch | Quick exit west by turn 12 | Move into x=4 exit strip | Win, cart shafts, Tam reunion, save transition |
| Evasion branch | Return west by turn 12 with Narg pursuing | Move into x=0 exit strip | Win with Narg alive, same outro/save transition |
| Deadline | Turn-10 audible warning; deadline remains in banner | Continue route | Start of turn 13 plays caught scene, sets loss, shows Game Over |

Additional regression results:

- **Win paths: PASS.** Both quick and long exits fired their independent wins with all supplies, sword, and mandatory encounter complete.
- **Loss path: PASS.** Public Wait through turn 12 fired `sc_c3_fever_caught`, set `tam_fever_caught` and `_lose_game`, and held visible Game Over on turn 13: `/tmp/fun2-wn03-stable/stall/event-wn03_return_to_farm_sc_c3_fever_caught-01.png` through `-03.png`, `/tmp/fun2-wn03-stable/stall/game-over.png`; source `design/missions/return_to_farm.yaml:117-127` and `design/scenes/return_to_farm/scenes.yaml:160-184`.
- **No premature exit: PASS by gate trace.** The quick exit was absent until Narg's death; the long exit required `narg_encountered`; both final events also required all three supplies and the sword (`design/missions/return_to_farm.yaml:128-135`).
- **Fair combat: PASS.** Narg's calculated maximum round was 13 damage against 24 HP. Golden Rand survived the first hit and killed Narg at 11 HP; evasion Rand survived the encounter seed at full HP.
- **Fog contract: PASS.** Radius begins at 3, becomes 4 only after the sheep scene, and remains symmetric for player and AI. Narg does not exist on-map before the authored sword reveal.
- **Objective and next action: PASS.** The native map banner states both current verb and deadline at every gate. Farmhouse/supply cues, west direction, and branch objectives remained understandable without reading internal flags.
- **Outro and soft-lock: PASS.** Both wins played all 8 cart-shaft pages and all 17 Tam-reunion pages and reached the save transition; the stall reached terminal Game Over. No route lost control or exhausted its required interaction.
- **Native text fit: PASS.** All 90 golden event boxes plus the three unique loss boxes were vision-inspected at 240x160. No clipped glyph, lost opening clause, unintended three-line overflow, or quote that read incorrectly in the GBA box was observed.

## Findings, ordered by severity

### MINOR — the quick exit refunds the attack turn but does not create a net faster clear

**Player consequence:** The reward is understandable and halves the resolved return tail, but it does not yet feel like a true clock bonus. The golden route spends turn 8 killing Narg and turns 9-10 reaching x=4; the evasion route spends turns 8-10 reaching x=0. Both clear on turn 10. A player is rewarded with safety and a shorter spatial route, not an earlier finish.

**Repro:** Complete the common search through turn 7. On one run, kill Narg and use the quick exit; on another, leave him alive and use the original west exit. Compare `completed_turn` and the turn-start position traces.

**Evidence:** `/tmp/fun2-wn03-stable/golden.json`, `/tmp/fun2-wn03-stable/evasion.json`, and `/tmp/fun2-wn03-stable/golden/quick-exit-highlight.png`.

**Causal source:** Narg starts at `design/missions/return_to_farm.yaml:15`; the quick strip is `[4,5]` at `:24`; activation/objective/highlight are `:110-116`. From the post-kill `[10,8]`, the current route consumes two player turns.

**Smallest remedy:** If a later pass wants the authored **kill = tempo** distinction to be literal rather than spatial, move only the inactive quick-exit strip so it includes the already verified one-turn-reachable `[6,7]` endpoint (for example `[6,5]`, size `[1,4]`). Preserve its `trolloc_defeated` gate, existing win conditions, long x=0 evasion exit, and turn-12 deadline. A real-input replay should then show kill victory on turn 9 and evasion victory on turn 10.

No blocking or major objective, fog, combat, deadline, win/loss, clipping, or soft-lock finding was observed. Because the chapter meets its **MOSTLY FUN** target, no top-three rescue-fix list is required.
