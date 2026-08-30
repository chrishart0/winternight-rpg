# Fun QA round 3 — `wn00_tutorial`

**Verdict: FUN. Target met.**

The reported pacing and wording findings are closed. The raven peak now returns map control after exactly **20 settled mandatory boxes** on both the all-content and direct mandatory-only routes, down from 63. The required Fain and Thom material still appears when their Talks are skipped. Rand and Mat still perform the real Attack/weapon/target/confirm flow, the repaired forced-move lock rejects escape inputs, the early-inn detour recovers, and all exercised routes enter `wn01_farm_escape`.

No blocking, major, or minor player-facing finding remains in this focused verification.

## Build and method

- QA compiled its own isolated project through `compile_campaign_project`, following the `compiled_campaign` fixture's API pattern at `tests/conftest.py:40-51`: `/tmp/fun3-wn00-build/winternight.ltproj`.
- Compiled report-tree hash: `a6b14053ed28e56217cb10704868a1f918655f646381a8ed32875364cf3bbebe` — exactly the gated tree.
- Engine: `1820e585450f6f47605aebd686b2a3f13af181f0` / `2026.02.17a` (`engine.lock:1-4`).
- Manifest SHA-256: `6bf0794ca16436c270504b6d94012edbd58765bbd5e237443e3a8f429c06073f`.
- SDL ran headless with `SDL_VIDEODRIVER=dummy`. The driver used `_run_input_flow` and posted pygame keys. It selected units, moved the cursor, selected semantic menu entries, selected Thrown Stone, targeted the raven, confirmed combat, advanced text, opened objectives, and selected Enter Inn. It did not invoke events or mutate flags, units, positions, HP, inventory, objectives, or event state.
- Golden all-content run: **8,106 frames**, complete, no failure, victory on turn 10, then `wn01` turn 1. Evidence: `/tmp/fun3-wn00-final/golden-run.json`, `/tmp/fun3-wn00-final/golden-summary.json`.
- Direct mandatory-only run: **5,744 frames**, complete, no failure, victory on turn 5, then `wn01` turn 1. Evidence: `/tmp/fun3-wn00-final/minimal-run.json`, `/tmp/fun3-wn00-final/minimal-summary.json`.
- Early-inn recovery run: **6,020 frames**, complete, no failure, redirect on turn 2, victory on turn 6, then `wn01` turn 1. Evidence: `/tmp/fun3-wn00/minimal-run.json`, `/tmp/fun3-wn00/minimal-summary.json`.
- The final two runs captured 322 settled boxes (183 golden + 139 minimal); the recovery run captured another 142. Runtime layout inspection found **0 over-height boxes and 0 lost openings** in every run. Changed/fallback material was vision-reviewed at native 240×160. Final contact manifests: `/tmp/fun3-wn00-final/contacts/{golden,minimal}-manifest.json`.

The wrong-unit, wrong-destination, Back, objective-menu, and screenshot probes did not consume turns. Raw and natural completion turns are therefore the same.

## Played routes

### Golden all-content — turn 10

1. Travel to Mat and choose **Talk**.
2. Take Ewin, step on the cider cart, then take Egwene while crossing west with the cask.
3. Cross the cellar trigger, take Perrin, follow Rand's forced gold-space lesson, and perform **Attack → Thrown Stone → raven → confirm**.
4. Follow Mat's forced gold-space lesson and perform the same real Attack flow.
5. Watch the raven fly; advance 20 Moiraine boxes to restored control.
6. Take Fain's Talk, then Thom's Talk, return to the inn, and choose **Enter Inn**.
7. Complete the council/outro and reach `wn01_farm_escape` turn 1.

All five optional Talk flags were true and `talk_options` was empty at victory.

### Direct mandatory-only — turn 5

1. Travel to Mat and choose **Talk**; take no optional village Talks.
2. Lift the one cask, carry it to the cellar, complete both forced-move lessons and both real throws.
3. Advance the 20-box Moiraine scene to restored control, ignore Fain and Thom, and choose **Enter Inn**.
4. Observe the fallback Fain news/aftershock and Thom performance, then the council/outro; reach `wn01` turn 1.

At victory, `talked_to_fain` and `talked_to_thom` were absent/false. Neither `sc_c0_fain_optional` nor `sc_c0_thom_optional` played. The required scenes did play in order: `sc_c0_fain_news` → `sc_c0_fain_aftershock` → `sc_c0_thom_performance` → `sc_c0_inn_council`.

### Early-inn recovery — turn 6

Rand approached the inn before talking to Mat, selected **Inn Before Mat**, received Tam's redirect, and returned to the unchanged **Talk to Mat / Choose Talk** objective. The route then completed the mandatory path, skipped Fain/Thom Talks, won, and reached `wn01`. Native evidence: `/tmp/fun3-wn00/scenes/minimal-009-sc_c0_inn_before_mat.png` and `/tmp/fun3-wn00/objectives/minimal-01-weak_after_redirect.png`.

## Finding-by-finding closure

### Prior MAJOR — 63 mandatory post-throw boxes before control: **CLOSED**

**Repro:** complete Rand's and Mat's throws, end the phase, and advance the raven/Moiraine sequence until the map accepts player input again.

**Observed on all three routes:** exactly **20** settled boxes, all from `sc_c0_moiraine_coin`, before control returns. Native visual evidence for boxes 1–20:

- `/tmp/fun3-wn00-final/contacts/golden-sc_c0_moiraine_coin-{1,2,3}.png`
- control-return frames: `/tmp/fun3-wn00-final/critical/{golden,minimal}-post-throw-control.png`
- restored objective: `/tmp/fun3-wn00-final/objectives/golden-06-inn.png` — **Choose Enter Inn**.

The 20-box block fit cleanly and read coherently in the GBA box. It opens on the raven reaction, covers Moiraine's introduction and coins, and ends by visibly handing the player toward Fain.

The golden route then has real control boundaries: Talk to Fain and Talk to Thom are separate player actions. The direct minimal route proves the skip contract: its Enter Inn input triggers **16 Fain-news + 10 aftershock + 17 Thom-performance = 43 required fallback boxes**, followed by 16 council and 15 outro boxes, before `wn01`. That ending chain follows the explicit chapter-ending action; it does not interrupt a promised return to tutorial play and does not recreate the prior turn-6 control lock.

**Source closure:** the raven event now plays only Moiraine before enabling Fain and the inn at `design/missions/tutorial_emonds_field.yaml:164-175`. Fain and Thom required scenes moved behind player Talks at `:197-214`, with priority-ordered fallback delivery at `:215-227`; Enter Inn wins only afterward at `:228-234`.

### Prior MINOR — one-cask errand says “first”: **CLOSED**

Both final routes displayed **“The cider cask waits on the cart.”** No captured box contained “first cider cask.” Native evidence: `/tmp/fun3-wn00-final/scenes/golden-024-sc_c0_mat_and_news.png`.

**Source closure:** `design/scenes/tutorial/scenes.yaml:132-137`, especially line 134.

## Regression matrix

| Check | Result and evidence |
| --- | --- |
| Rand's real throw | **Pass on golden, minimal, and recovery.** Each traversed `menu → weapon_choice → combat_targeting → combat`; Raven stayed **22/22 HP**; Rand's temporary stone disappeared and Hunting Bow returned. Frames: `/tmp/fun3-wn00-final/critical/minimal-rand-throw-{menu,weapon_choice,combat_targeting,combat}.png`. Source: `design/missions/tutorial_emonds_field.yaml:103-137`. |
| Mat's real throw | **Pass on all routes.** Same real-input state chain; Raven stayed **22/22 HP**; Mat's stone disappeared. Frames: `/tmp/fun3-wn00-final/critical/minimal-mat-throw-{menu,weapon_choice,combat_targeting,combat}.png`. Source: `design/missions/tutorial_emonds_field.yaml:138-163`. |
| Raven resolution | **Pass.** The raven visibly flew before removal; `raven_done` became true. Frame: `/tmp/fun3-wn00-final/critical/minimal-raven-flight.png`. Source: `design/missions/tutorial_emonds_field.yaml:164-175`. |
| Rand forced-move lock | **Pass.** In the direct minimal run, selecting Mat instead of Rand, confirming Rand's origin instead of `[10,7]`, and pressing Back in move state were all rejected; state remained `free`/`move` and `_forced_move_unit` remained `rand`. Frame: `/tmp/fun3-wn00-final/critical/minimal-lock-rand-locked.png`. Authored lock: `design/missions/tutorial_emonds_field.yaml:93-100`; clear at `:103-116`. Engine enforcement: `vendor/lt-maker/app/engine/general_states.py:367-399,801-812,819-828`. |
| Mat forced-move lock | **Pass.** Selecting Rand instead of Mat, confirming Mat's origin instead of `[11,10]`, and pressing Back were rejected; `_forced_move_unit` remained `mat` until the destination. Frame: `/tmp/fun3-wn00-final/critical/minimal-lock-mat-locked.png`. Authored lock: `design/missions/tutorial_emonds_field.yaml:122-150`; same engine lines above. |
| Early-inn recovery | **Pass.** One-shot redirect fired, objective stayed Talk to Mat, Rand recovered, won, and reached `wn01`. Source: `design/missions/tutorial_emonds_field.yaml:60-68`. |
| Required fallback scenes | **Pass.** With both late Talks skipped, all three required scenes played before `sc_c0_inn_council`; neither optional extension played. Compiled priorities are 40 → 30 → 20 at `/tmp/fun3-wn00-build/winternight.ltproj/game_data/events.json:3408-3448`; source: `design/missions/tutorial_emonds_field.yaml:215-234`. |
| Completion and cleanup | **Pass on all routes.** `entered_inn` and `raven_done` were true; stones were gone; final snapshots reached `wn01_farm_escape` turn 1 with active Rand/Tam and no active Mat. Frames: `/tmp/fun3-wn00-final/critical/{golden,minimal}-wn01-start.png`; source: `design/missions/tutorial_emonds_field.yaml:228-238`. |
| Win/loss contract | **Pass within public reachability.** Win fired in every route. The compiled Rand-death `unit_death` event contains `lose_game` at `/tmp/fun3-wn00-build/winternight.ltproj/game_data/events.json:3463-3474`, sourced from `design/missions/tutorial_emonds_field.yaml:10-11`. This scripted-miss, enemy-inert tutorial exposes no public damaging action, so an input-only loss remains intentionally unreachable; no HP/death mutation was used to manufacture one. |
| Native text fit | **Pass.** Runtime geometry: 0 over-height / 0 lost-opening boxes across all runs. Vision review covered the changed 20-box Moiraine block, all 43 required fallback boxes, the corrected cask line, early redirect/objective, both attack flows, both locks, and both control-return frames. No clipping, overflow, or contextually wrong quote was observed. |

## Decision density and FUN verdict

**Core verb:** route-and-Talk through a warm village, then perform a guided two-unit Attack lesson.

Golden dead-turn ledger remains **5 / 10**:

| Turn | Content | Dead? | Reason |
| ---: | --- | :---: | --- |
| 1 | Travel toward Mat | yes | Mat is the only credible destination and cannot be reached this turn. |
| 2 | Talk to Mat | yes | Required handoff. |
| 3 | Ewin versus direct cart route | no | Optional Talk changes route/order. |
| 4 | Cart and Egwene on the westbound route | no | Optional timing and route efficiency matter. |
| 5 | Cellar/Perrin/guide ordering | no | Optional information competes with direct progression. |
| 6 | Rand and Mat throws | yes | Real input, but one weapon, one target, and scripted misses. |
| 7 | Fain versus Thom/inn | no | Optional branch choice. |
| 8 | Westbound transit | yes | No second late interaction is reachable this turn. |
| 9 | Thom versus inn | no | Optional Talk remains a choice. |
| 10 | Return and Enter Inn | yes | Sole destination and ending action. |

The direct minimal route is deliberately **5 / 5 dead turns**, confirming that optional Talks still supply the route expression rather than becoming hidden requirements. That weak route remains coherent, cannot soft-lock, and receives all campaign-required story material.

The tension peak is still the player-performed two-throw omen on golden turn 6. The key change is that the peak now releases into a short 20-box consequence and visible player choice, rather than a 63-box compulsory chain. Golden play regains its social routing immediately; minimal play gets a clear Enter Inn action and a safe fallback ending. That is enough to move `wn00_tutorial` from **MOSTLY FUN** to **FUN** without weakening the locked contracts: one cask, five optional Talks, two real misses, forced lesson movement, raven flight, explicit Enter Inn, and clean transition to `wn01`.

## Findings

**None.** There is no current spec line believed to be at fault in the exercised scope. The source ranges above identify the closed fixes and preserved contracts.
