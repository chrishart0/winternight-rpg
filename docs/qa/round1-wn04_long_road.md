# Round 1 QA — `wn04_long_road` / The Long Road

## Verdict

**PARTIALLY COHERENT — FAIL.** The escape, watched-road loss, carry state, column march, background, and Dragonmount outro all work. The earliest material break is the turn-6 instruction to **“Hold still beneath the trees”**: a player who obeys it is caught and attacked by a sweeper on enemy turn 7. The mechanically successful route instead keeps moving east under the trees during the entire watch window.

Tested against compiled tree `92946fb39eee3b164c83858bd189b1522d9ba6524029e4ab3cfa70af0ee9b35a` with engine commit `1820e585450f6f47605aebd686b2a3f13af181f0`. All runs started the compiled `build/winternight.ltproj` through the real engine with dummy SDL video/audio and posted real pygame key events. Frames below are native 240×160 captures inspected visually.

## Intended loop and observed route

- Rand begins with `tam_litter` already paired as his traveler and pulls east through the woods.
- On turn 2, the six-token column appears on road row `y3` and marches east without attacking.
- On turn 5, the pursuing sweepers appear and Rand says that he must keep moving; the same scene warns one turn ahead that he must freeze if the rider returns.
- On turn 6, the rider returns, the road is highlighted, and the objective says to hold still beneath the trees.
- The **successful** route did not hold still: Rand remained off road and advanced from `(15,7)` after turn 5 to `(18,7)`, `(20,6)`, `(23,6)`, then `(25,6)`, escaping on turn 9. No combat occurred.
- A deliberate road violation left Rand at `(12,3)` through turn 6. The turn-7 check played `sc_c4_seen`, set `_lose_game`, and reached the Game Over screen.
- The outro then played all 17 authored `sc_c4_dragonmount_speech` boxes after the successful turn-9 escape.

There are no optional Talk or Visit interactions in this chapter specification.

## Coherence trace

| State | Player-facing goal | Visible cue/action | Observed result |
| --- | --- | --- | --- |
| Start | Pull Tam east; avoid Quarry Road | Intro establishes the litter; map banner says “Pull Tam east through the trees / Keep off the Quarry Road”; move Rand normally | Tam is attached as Rand’s traveler and moves with him |
| Turn 2 | Let the column pass | Six enemy tokens visibly march on `y3`; banner says to keep Tam off the road | Column advances east on enemy phases and never attacks |
| Turn 5 | Stay ahead of sweepers and prepare for the rider | Sweepers scene says “I have to keep moving,” then warns “we freeze beneath the branches” if the rider returns | The warning is diegetic and arrives exactly one turn before the rider |
| Turns 6–8 | Banner says “Hold still beneath the trees” | Entire road row is highlighted and the rider is searching | **Break:** literal waiting lets a sweeper attack on enemy turn 7; successful play requires continued eastward movement |
| Turn 9 | Move to the east edge | Rider-leaves scene, updated objective, and green exit highlight | Rand enters `(25,6)` and wins |
| Road detection | Be caught if on `y3` while watched | Rand remains on highlighted road through turn 6 | Turn-7 caught scene and Game Over both fire |
| Outro | Receive the Dragonmount revelation | 17 click-separated narration/dialogue boxes over `westwood_road_night` | Scene completes cleanly with correct portraits and no clipped text |

## Findings

### HIGH — Obeying “Hold still” causes the sweepers to attack during the watched-road window

**Player consequence:** The chapter explicitly teaches a no-combat hide beat, then punishes the literal instructed action with combat. A first-time player who trusts both the turn-5 warning and turn-6 objective is less safe than a player who disregards them and keeps moving. This is not just pressure: the sweeper reaches Rand and starts a real combat.

**Repro:**

1. Carry Tam east off road for turns 1–5, ending at `(15,7)`.
2. Read the turn-5 warning: “If the rider turns back, we freeze beneath the branches. Not a breath when he comes.”
3. On turn 6, observe “Hold still beneath the trees / The rider is searching.”
4. Use the map menu’s End command without moving on turns 6 and 7.
5. On enemy turn 7, `sweep_b` reaches `(14,7)` beside Rand at `(15,7)` and the engine enters `combat`.

**Evidence:**

- Instruction and watched-road state: `/tmp/wn04-hold/hold-turn6.png`
- Sweeper adjacent to Rand as combat begins: `/tmp/wn04-hold/hold-still-combat.png`
- Real-input state/position trace (`combat_turn: 7`, `combat_state: combat`): `/tmp/wn04-hold-evidence.json`

**Suspected source:**

- `design/missions/long_road.yaml:38-39` gives both sweepers permanent `pursue` AI.
- `design/missions/long_road.yaml:66-81` activates a multi-turn watch and issues the hold-still objective without changing sweeper AI.
- `design/missions/long_road.yaml:104-108` spawns the sweepers immediately before that window.
- `design/scenes/long_road/scenes.yaml:136-138` presents mutually incompatible “keep moving” and “freeze” instructions.

**Smallest remedy:** Decide which behavior is canonical and make prose/mechanics agree. The smallest change to the current successful route is to replace the literal freeze/hold wording with an explicit “keep moving beneath cover; never touch the road while the rider searches.” If the requested hold-still beat is non-negotiable, pause the sweepers for the hold window and rebalance the watch duration/remaining exit distance so waiting does not make the target timing impossible. Recheck by ending turns exactly as above and requiring no combat before movement is explicitly released.

### MED — The formal Objective screen clips the win condition

**Player consequence:** Opening Objective at chapter start renders only **“Bring Tam to the ea…”**; the destination is cut off by the right-side panel at 240×160. The normal map banner does clearly say to pull Tam east, so the route remains discoverable, but the dedicated objective screen fails its purpose and violates the no-overflow requirement.

**Repro:**

1. Finish the intro.
2. Open the map option menu and choose Objective.
3. Read the single-line Win Conditions field.

**Evidence:** `/tmp/wn04-golden/objective-start.png`

**Suspected source:** `design/missions/long_road.yaml:22` (`display_text: Bring Tam to the eastern edge`) exceeds the available one-line field.

**Smallest remedy:** Shorten the formal win text to fit the panel, for example “Get Tam to the east edge,” while retaining the more detailed changing map banners. Re-open Objective at 240×160 and verify the full destination is visible.

## Required-path and presentation checks

- **Golden victory:** PASS. Rand stayed off `y3`, escaped at `(25,6)` on turn 9, and reached the outro. `/tmp/wn04-golden-evidence.json` records real directional/select input and `saw_combat: false`.
- **Detection loss:** PASS. Rand stood on `y3` through the active watch; the turn-7 check played both caught boxes and reached Game Over with `_lose_game: true`. Evidence: `/tmp/wn04-loss/loss-road-turn6.png`, `/tmp/wn04-loss/scene-sc_c4_seen-001.png`, `/tmp/wn04-loss/scene-sc_c4_seen-002.png`, `/tmp/wn04-loss/game-over.png`, and `/tmp/wn04-loss-evidence.json` (`game_over_turn: 7`).
- **Carry legibility:** PASS. Rand’s Personal Data screen visibly shows `Move 5-2` and `Trv Tam`; selecting movement shows the reduced three-tile range and Tam remains attached. Evidence: `/tmp/wn04-golden/carry-unit-info.png`, `/tmp/wn04-golden/carry-move-range.png`.
- **Column behavior:** PASS. The six tokens are clear on the road and march east on successive enemy phases. The golden run saw no combat, and all column HP remained unchanged. Evidence: `/tmp/wn04-golden/column-mid-march.png` and `/tmp/wn04-golden-evidence.json`.
- **Watched-road cue:** PASS. The road row is visibly highlighted and the two-line objective clearly states that the rider is searching. Evidence: `/tmp/wn04-golden/watched-road-highlight.png`.
- **One-turn diegetic warning:** PRESENT but undermined by the HIGH finding. The warning appears in turn 5, exactly one turn before the turn-6 rider event. Evidence: `/tmp/wn04-golden/scene-sc_c4_sweepers-003.png`.
- **Sweeper pressure:** CONDITIONAL FAIL. A continuously advancing competent route stays ahead and wins without combat; an equally competent player who obeys “Hold still” is attacked on turn 7.
- **`westwood_road_night`:** PASS. The panorama fills the native frame without seams, scaling artifacts, bad letterboxing, or competing with text. Portraits and box tails match their speakers in the inspected scenes.
- **Dragonmount fever speech:** PASS. All 17 authored boxes were captured and inspected at 240×160: `/tmp/wn04-golden/scene-sc_c4_dragonmount_speech-001.png` through `-017.png`. No line is clipped or drawn outside its box. Long narration/dialogue scrolls within the standard two-line box, and the 17 separate advances give the revelation appropriate pauses. Tam remains on the right for the fever memory, Rand appears on the left for “You are my father,” and the final identity question closes cleanly.
- **Soft-lock check:** No soft-lock occurred on either required branch. The successful path wins and transitions; the watched-road branch reaches Game Over. The instruction/AI contradiction above is a fairness and coherence failure, not an observed soft-lock.

## Final chapter verdict

**FAIL for round 1** because following the central hold-still instruction provably starts combat during the hide window. All other named acceptance paths and presentation checks passed aside from the clipped formal win-condition line.
