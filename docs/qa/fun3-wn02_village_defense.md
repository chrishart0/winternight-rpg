# Fun review round 3 — `wn02_village_defense`

## Verdict

**FUN reached — all requested mechanical and UI fixes pass, with one new MINOR outcome-copy defect.** The Lan-east mastery route now opens all four houses, returns all four residents, suppresses the eastern half of the turn-5 flank, and wins with the mastery tally. Haral's neglect death is reachable on turn 8 while the normal three-house defense keeps him alive. The settled healing instruction and formal Loss Conditions page are both correct at 240×160. Every requested win/loss regression fired through public input without a soft-lock.

The tactical chapter earns FUN: both the mastery and normal three-house routes use all eight player turns, and neither has a dead whole turn. Recruitment/healing order owns turn 1; the four spokes and resident returns compete on turns 2–6; the final wave keeps turns 7–8 live. The one remaining defect does not change those mechanics, but it is player-facing: an all-houses-open win after one resident dies still receives the false line **“Every occupied household reaches the inn.”** Focused QA is therefore not completely clean.

## Runtime evidence and provenance

- Gated tree supplied for this review: `a6b14053ed28e56217cb10704868a1f918655f646381a8ed32875364cf3bbebe`.
- Independent compile: `/tmp/fun3-wn02-build-final/winternight.ltproj`, produced through `winternight_gen.campaign_compiler.compile_campaign_project` following `tests/conftest.py:40-51`.
- Independent project tree hash: **`a6b14053ed28e56217cb10704868a1f918655f646381a8ed32875364cf3bbebe`**, an exact gated-tree match. Manifest SHA-256: `6bf0794ca16436c270504b6d94012edbd58765bbd5e237443e3a8f429c06073f`. Provenance: `/tmp/fun3-wn02-provenance.json`.
- Pinned engine: commit `1820e585450f6f47605aebd686b2a3f13af181f0`, engine `2026.02.17a` (`engine.lock:2-3`). Runtime used a clean `/tmp/fun3-lt-maker` archive of that exact repository-local vendor commit.
- Method: SDL dummy video/audio, seed 5002, and real posted pygame key-down/key-up events for movement, Talk, Visit, Return, Item targeting, attacks, Wait, Objective-menu navigation, and every scene advance. The planner read runtime state only; it never invoked an event, warped a unit, or changed a flag, objective, team, position, inventory, or HP value.
- Every cited PNG is a native 240×160 engine frame and was opened and visually inspected. JSON results record the real input counts, events, combat, turn snapshots, flags, units, and terminal state.

## Finding-by-finding closure

### CLOSED — prior HIGH: all-four mastery was not demonstrated

**PASS.** `/tmp/fun3-wn02-mastery-result.json` completed with no planner failure after the requested route:

1. Lan recruited Mat on turn 1, then committed east; Mat went north, Egwene west, and Nynaeve south after performing the guided heal.
2. `torch_east` remained at `[20,1]` in the turn-1 and turn-2 snapshots, then advanced to `[18,4]` for turn 3. This is the observed delayed clock authored by `design/missions/village_defense.yaml:34,155-158`.
3. Lan reached and used `Visit` at `[16,8]` on turn 4. By the turn-5 snapshot, all four `house_*_saved` flags were true. Visually inspected frame: `/tmp/fun3-wn02-mastery/turn4-east-saved.png`.
4. `residents_returned` progressed from 2 on turn 5 to 3 on turn 6 and **4 on turn 7**. It remained 4 through the turn-9 win.
5. At turn 5, runtime contained only `flank_wave_a` at `[0,13]`; `flank_wave_b` never spawned. The event trace contains `flank_reinforcements_west` and no east-flank event, proving the all-saved suppression at `design/missions/village_defense.yaml:406-418`.
6. Turn 9 played `sc_c2_defense_tally_mastery`, then won. The visually inspected tally fits and reads **“Every occupied household reaches the inn.”** Frame: `/tmp/fun3-wn02-mastery/turn9-sc_c2_defense_tally_mastery-01.png`; source: `design/missions/village_defense.yaml:474-490` and `design/scenes/village_defense/scenes.yaml:334-342`.

Natural turns: 8. Dead whole turns: **0/8**. The inspected turn-8 peak still shows pressure on the inn approach: `/tmp/fun3-wn02-mastery/tension-peak-turn8.png`.

### CLOSED — prior HIGH: Haral neglect death was not reachable

**PASS.** `/tmp/fun3-wn02-loss_haral-result.json` used no Herb Pouch or Mending Weave on Haral. It saved and returned west, east, and south, allowed north to ruin, then issued no attacks after the quota was secure. Lan and Moiraine held the two threshold tiles, but Haral's relevant east/south attack tile `[12,10]` remained open: `final_south_b` reached it and attacked Haral directly. This is not a Haral body-block/screen.

Haral stayed at 28 HP through the turn-7 player snapshot, entered turn 8 at 12 HP, and reached 0 during enemy turn 8. Runtime played `sc_c2_failure_luhhan`, set `_lose_game`, and reached Game Over. Evidence:

- result: `/tmp/fun3-wn02-loss_haral-result.json`;
- open approach at the turn-8 pressure frame: `/tmp/fun3-wn02-loss_haral/tension-peak-turn8.png`;
- inspected cause frame: `/tmp/fun3-wn02-loss_haral/turn8-sc_c2_failure_luhhan-01.png`;
- terminal frame: `/tmp/fun3-wn02-loss_haral/game-over.png`.

The cause frame is complete and unclipped: **“Haral Luhhan falls. The inn approach breaks.”** The causal source is `design/missions/village_defense.yaml:47-48` (the Haral-side final spear), `:10-12` (Haral-only declarative loss), and `design/scenes/village_defense/scenes.yaml:324-332` (cause text).

The protected comparison also passes. `/tmp/fun3-wn02-golden_three-result.json` performed the guided heal, saved west/north/south, allowed only east to ruin, returned exactly 3 residents, and won on turn 9. Haral was 36/40 in every turn-6 through turn-8 snapshot. The normal pressure frame is `/tmp/fun3-wn02-golden_three/tension-peak-turn8.png`.

### CLOSED — prior MEDIUM: guided-heal page lost its subject and movement verb

**PASS.** The tutorial page was allowed to settle before any further Select input. The native frame visibly retains the full two-line instruction:

> Move Nynaeve beside Haral.
> Choose Items and Herb Pouch.

Inspected frame: `/tmp/fun3-wn02-mastery/turn1-recruit_nynaeve-01.png`. No opening words scroll away, no glyph is clipped, and the real Item → Herb Pouch → Haral targeting flow still completes. Source: `design/missions/village_defense.yaml:130-147`, specifically the shortened text at `:139`.

### CLOSED — prior MEDIUM: formal Objective loss contradicted the quota

**PASS.** The Objective menu was opened on turn 1 and scrolled to the settled Loss Conditions panel. It shows only:

> Haral must
> survive

There is no villager/all-four survival claim. Inspected frame: `/tmp/fun3-wn02-ui/objective-menu-scroll.png`; result: `/tmp/fun3-wn02-ui-result.json`. The runtime objective snapshot is `loss: "Haral must,survive"`. Source: `design/missions/village_defense.yaml:9-12`; resident losses now live in explicit events rather than declarative `failure_conditions` (`:327-377`).

## Requested regression matrix

| Contract | Result and real-input evidence |
| --- | --- |
| Normal three-house golden | **PASS.** `/tmp/fun3-wn02-golden_three-result.json`: west/north/south saved, east ruined, exactly 3 returned, Haral 36/40, turn-9 win, no soft-lock. |
| Second occupied-house ruin | **PASS.** `/tmp/fun3-wn02-loss_second_ruin-result.json`: west ruins first; north is the second ruin on enemy turn 3; `sc_c2_failure_quota_impossible` and `_lose_game` fire. Inspected frame: `/tmp/fun3-wn02-loss_second_ruin/turn3-sc_c2_failure_quota_impossible-01.png`. Source: `design/missions/village_defense.yaml:208-290`; scene: `design/scenes/village_defense/scenes.yaml:274-282`. |
| Dawn quota miss | **PASS.** `/tmp/fun3-wn02-loss_quota-result.json`: three houses opened but only 2 residents returned; Haral remained 36/40; turn 9 played `sc_c2_failure_quota` and lost. Inspected frame: `/tmp/fun3-wn02-loss_quota/turn9-sc_c2_failure_quota-01.png`. Source: `design/missions/village_defense.yaml:492-498`; scene: `design/scenes/village_defense/scenes.yaml:264-272`. |
| First resident death with all four houses opened | **PASS mechanically.** `/tmp/fun3-wn02-resident_one_loss-result.json`: all four houses were saved, west/east/south returned, north died on enemy turn 7, `rescue_losses` became 1, play continued through turn 8, and the chapter won on turn 9 with 3 returned. Inspected death frame: `/tmp/fun3-wn02-resident_one_loss/turn7-sc_c2_failure_resident_north-01.png`. |
| Second resident death | **PASS.** `/tmp/fun3-wn02-resident_two_loss-result.json`: all four houses were already open; north died on enemy turn 6 and the next player turn remained available; west then died on enemy turn 7, `rescue_losses` became 2, and the game immediately lost before dawn. Inspected frames: `/tmp/fun3-wn02-resident_two_loss/turn6-sc_c2_failure_resident_north-01.png`, `/tmp/fun3-wn02-resident_two_loss/turn7-sc_c2_failure_resident_west-01.png`, and `/tmp/fun3-wn02-resident_two_loss/game-over.png`. Source: `design/missions/village_defense.yaml:327-377`. |
| Win/loss resolution and soft-lock scan | **PASS.** Mastery, normal three-house, and tolerated-one-resident-loss runs reached level-end victory. Haral death, second ruin, quota miss, and second resident death reached Game Over. Every input driver completed with `failure: null`. |

## Findings, ordered by severity

### MINOR — a tolerated resident death still receives the all-household mastery claim

**Player consequence:** the game correctly tolerates the first resident death after all four houses are opened, but its victory feedback erases that consequence. In the one-loss run, the player first sees **“The north resident falls before reaching shelter.”** and later sees **“Every occupied household reaches the inn.”** Both cannot be true.

**Repro:** open all four houses; return west, east, and south; leave the north resident exposed at `[7,3]`; allow the north wave to kill him; survive through turn 8. The chapter correctly wins with 3 returns, but plays `sc_c2_defense_tally_mastery` before the outro.

**Frame evidence:** `/tmp/fun3-wn02-resident_one_loss/turn7-sc_c2_failure_resident_north-01.png` followed by `/tmp/fun3-wn02-resident_one_loss/turn9-sc_c2_defense_tally_mastery-01.png`. Runtime trace: `/tmp/fun3-wn02-resident_one_loss-result.json`.

**Exact source fault:** `design/missions/village_defense.yaml:474-478`. `defense_tally_mastery` checks that all four houses were opened but only requires `residents_returned >= 3`; the rendered assertion is at `design/scenes/village_defense/scenes.yaml:334-342`.

**Smallest source-level remedy:** require `residents_returned >= 4` for `defense_tally_mastery` (or equivalently require no `rescue_losses`) while leaving the actual three-resident win condition unchanged. Re-run the two resident semantics routes: the one-loss route must still win without the mastery tally, the second loss must still lose, and `/tmp/fun3-wn02-mastery-result.json`'s genuine four-return route must still receive the tally.

## Final chapter verdict

**FUN reached.** The intended expression ceiling is now real, the ordinary three-house recovery remains valid, Haral's mortality is credible without making normal defense brittle, the instructions and formal loss UI agree with the mechanics, and every requested failure path resolves. The chapter should retain its FUN tactical verdict, but the false mastery callback above should be corrected before calling the focused QA pass completely clean.
