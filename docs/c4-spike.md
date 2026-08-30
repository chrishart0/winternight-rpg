# C4 "Long Road" engine spike — runtime evidence

Date: 2026-08-27. Engine: pinned LT-Maker `1820e585450f6f47605aebd686b2a3f13af181f0`
(`2026.02.17a`, per `engine.lock`). All prototyping was done on throwaway copies under
`/tmp/c4spike/` (engine copy + hand-edited copy of the compiled
`winternight.ltproj`); no repo build/vendor files were touched. Evidence files
referenced below live in `/tmp/c4spike/` (`evidence_triggers.json`,
`evidence_column.json`, `column-march-turn5.png`) — key numbers are inlined here since
`/tmp` is scratch.

Method: a prototype level `c4_proto` (cloned from `wn01_farm_escape`, tilemap
`althor_farm__night_attack`) was hand-added to the project copy with hand-written LT
event JSON, then exercised two ways:

1. **Trigger-router run** (`run_triggers.py`) — same pattern as
   `src/winternight_gen/mechanics.py`: `game_state.start_level`, events driven through
   `game.events.trigger(...)`, actions through `app.engine.action`.
2. **Real input-driven game loop** (`run_column.py`) — same pattern as
   `src/winternight_gen/interactive_flows._run_input_flow`: full `driver.run(game)`
   under SDL dummy, posting pygame key events, real player/enemy phases.

**Overall: GO.** Every C4 mechanic works in the pinned engine with data-level changes
only. Nothing requires a `vendor/lt-maker` patch (which would be out of bounds without
an approved entry in `EXEC_PLAN.md` per AGENTS.md rule 2).

---

## Q1 — Carried/litter unit (Rand moves with Tam attached)

**VERDICT: supported natively (engine); needs small compiler additions to express in
mission specs.**

LT vocabulary (classic FE rescue; `pairup` constant is `false` in our project, which
selects rescue semantics):

- Level-unit field `starting_traveler: "<unit>"` — Tam starts attached to Rand, off-map.
- Event commands `pair_up;<follower>;<carrier>` (nickname `rescue`) and
  `separate;<unit>` (nickname `drop`) — attach/detach from events, **no stat gate**
  (`event_functions.pair_up` falls through to `action.Rescue` when pairup is off).
- Interactive `Rescue`/`Drop`/`Take`/`Give` menu commands exist for free and are
  stat-gated: `RESCUE_AID = max(0, CON - 1)` vs `RESCUE_WEIGHT = CON`
  (project `equations.json`).
- Carry penalty: if a skill with nid `Rescue` exists in `skills.json`, the engine
  auto-applies it to the carrier on `action.Rescue` and removes it on drop
  (`action.py` gates on `'Rescue' in DB.skills`). Our project currently has no such
  skill → currently **zero penalty while carrying**.

Evidence (trigger run, `evidence_triggers.json → q1_carry`):

- `starting_traveler` honored at level load: `rand.traveler == "tam"`, Tam off-map.
- With no `Rescue` skill in DB: movement unchanged while carrying (MOV 5, 30 valid
  moves).
- Engine `Drop` ability placed Tam on an adjacent traversable tile ((5,9)); carrier
  death also auto-drops the traveler (native `Die` action behavior, `action.py:2499`).
- **Softlock hazard confirmed**: after dropping, interactive re-rescue is blocked —
  `RescueAbility.targets(rand)` is empty because Rand's aid (CON 8 → 7) < Tam's weight
  (CON 11). Event `pair_up` bypasses the gate and re-attached Tam fine.
- Penalty prototype: with a `Rescue` skill added to the copy's `skills.json`
  (`hidden` + `stat_change [["MOV",-2]]` + `stat_multiplier SKL/SPD 0.5`), the engine
  applied it on rescue: MOV 5 → 3, valid moves 30 → 12. **Note:** the skill is applied
  by the Rescue *action*, not by `starting_traveler` at load (skills list was empty at
  load) — if C4 wants the penalty from turn 1, attach Tam via a `level_start`
  `pair_up` event instead of (or in addition to) `starting_traveler`.

Recommendation for wn04:

- Rand carries Tam from a `level_start` event (`pair_up`) so the movement penalty is
  live; keep `starting_traveler` unset.
- Add a project `Rescue` skill (MOV −2 is a good litter feel; SKL/SPD halving is
  optional since C4 has no combat objective).
- Either forbid Drop narratively (simplest: never needed — Tam stays attached the whole
  mission, and the mission ends at the exit region), or, if a drop/pick-up beat is
  wanted, tune the aid/weight so re-rescue is legal (e.g. a distinct level-local
  "tam_litter" unit spec with CON ≤ 7, or a level-scoped `RESCUE_WEIGHT` that reads a
  litter tag). Do **not** ship a state where the player can drop and never re-lift.
- An "escort inert adjacent unit" fake is unnecessary; native rescue is strictly
  better (one moving piece, no adjacency policing).

Compiler additions needed (all data-level):

- `MissionUnitSpec`: optional `carried_by`/`starting_traveler` plumbing in
  `campaign_lt_adapter` (the adapter already writes the field as `null` for every
  unit).
- `EventActionSpec`: new actions `pair_up` and `separate` (map 1:1 to the LT
  commands, like the existing `remove_unit` mapping in `event_compiler.compile_action`).
- Gameplay/skills: emit the `Rescue` skill (new small spec in `design/gameplay.yaml`
  or a fixed compiler-emitted skill).

## Q2 — Forced-hide beat ("column passes; stay off the road turns N..M")

**VERDICT: supported via compiler additions (regions + turn events + one new condition
form); the region/turn/lose machinery itself is already in our vocabulary.**

LT vocabulary used:

- `add_region;road_danger;1,6;7,2;normal;;;;none` on turn 3 (turn_change event),
  `remove_region;road_danger` on turn 7. Our existing `activate_region` /
  `deactivate_region` mission actions plus `RegionSpec.starts_active: false` already
  compile to exactly this (`campaign_lt_adapter` skips `starts_active: false` regions
  at bake; `activate_region` emits `add_region`).
- Telegraph the turn before: turn-2 `turn_change` event with `speak` dialogue — ran
  fine both skipped (trigger run) and interactively (real loop).
- Caught check: `turn_change` event, condition
  `4 <= game.turncount <= 6 and 'road_danger' in game.level.regions and
  game.level.regions.get('road_danger').contains(game.get_unit('rand').position)`,
  actions: caught dialogue, `level_var`, `lose_game`.

Evidence (`evidence_triggers.json → q2_q3_hide_and_lose`):

- Turn 2 telegraph fired; turn 3 spawn+region fired; region `contains()` true for road
  tile, false for Rand's hiding tile.
- Turn 4 with Rand off-road: **no** event matched (no false positive).
- Turn 5 with Rand teleported onto the road: caught event fired, `caught_on_road` and
  `_lose_game` both set.
- Real-loop confirmation in Q3 below (actual game_over screen).

**Engine gotcha (important for the compiler work):** `game.get_region(nid)` reads a
persistent registry and still returns the region object after `remove_region`
(verified at runtime). Conditions must test membership via `game.level.regions`,
not `game.get_region`.

Compiler additions needed:

- `EventConditionSpec`: `turn_at_most` (we only have `turn_at_least`) and a
  `unit_in_region: {unit, region}` clause emitting the `game.level.regions`-based
  expression above. Both are one-line emissions in `_compile_condition`.
- Nothing else — regions, turn triggers, `only_once`, `lose` action all exist.

Recommendation for wn04: model the hide window exactly as prototyped — danger region
over road tiles, activated the turn the column enters, telegraphed one turn earlier by
dialogue + (optionally) the region's `highlight`, checked by a repeating
`turn_start` event across the window, released with the region removal and a "move,
now" line. This is honest: the player who parks on the road at end of turn is caught at
the next turn change; there is no hidden state.

## Q3 — Detection / loss-condition vocabulary

**VERDICT: supported natively; both loss paths fire correctly in the runtime.**

Vocabulary that exists today:

- `failure_conditions` (mission schema) → `unit_death`-trigger events emitting
  `lose_game` (existing compiled pattern, e.g. `wn01 failure_0_rand`).
- Scripted lose: any event can emit `lose_game` (already in
  `EventActionSpec.type: lose`). `lose_game` sets `game.level_vars['_lose_game']`;
  the engine's turn/phase machinery then enters `game_over`.

Evidence:

- Trigger run: `UnitDeath(rand)` → `proto_failure_rand` executed → `_lose_game: true`
  (`evidence_triggers.json → q3_unit_death_lose`).
- Real input-driven loop (`evidence_column.json → run_b_caught`): Rand walked onto the
  road on turn 3 with real key input; at turn 4's turn change the caught event fired
  its dialogue, then `lose_game`, and the engine reached the real `game_over` state
  (`saw_game_over: true, game_over_turn: 4, caught_flag: true, lose_flag: true`,
  729 frames). This is the same game-over surface `verify_game_over_recovery`
  already exercises, so the recovery path (game over → title) is known-good.

Recommendation for wn04: keep `failure_conditions: [{type: unit_death, unit: rand}]`
(Tam is a traveler and cannot be attacked while carried), and express "caught" as the
scripted region lose from Q2. No new loss vocabulary is required beyond the two
condition clauses listed above.

## Q4 — Moving enemy column (spawn edge → march along road → despawn far edge)

**VERDICT: supported via compiler additions — real AI marching works in the pinned
engine with a Move_to-only AI preset; spawn/despawn are existing vocabulary.**

LT vocabulary used:

- AI preset with behaviours `[Move_to → Position (16,7), None, None]` (no Attack
  behaviour) — added as `road_column` to the copy's `ai.json`. This is the same
  `AIBehaviour("Move_to", "Position", ...)` shape the compiler already emits for the
  existing `patrol` profile (`campaign_lt_adapter.py`), minus the leading Attack
  behaviour.
- `add_group` (turn 3) and `remove_unit;<nid>;fade` ×3 + `remove_region` (turn 7) —
  both already in `EventActionSpec` (`spawn_group`, `remove_unit`).

Evidence (real input-driven loop, `evidence_column.json → run_a_march`, 1509 frames;
screenshot `column-march-turn5.png`):

- Turn 3: column spawns at west edge (1,7)/(1,6)/(2,7).
- Enemy phases march it east at full MOV each turn — x≈6 on turn 4, x≈11 on turn 5
  (pathfinding routed it honestly through the farmhouse corridor of the borrowed farm
  map), x≈14–15 on turn 6.
- Rand (parked adjacent to the corridor rows, HP 24) was never targeted — HP constant
  all run; no combat state ever entered.
- Turn 7 event despawned all three units (`position: null`) and removed the danger
  region; run completed with `lose_flag: null`.

Recommendation for wn04:

- Use real AI marching, not an event-scripted sweep: add a `march` AI behavior to
  `design/gameplay.yaml` / `models.AIProfileSpec` (Move_to destination, **no** Attack
  behaviour) alongside the existing `patrol`. The scripted-sweep fallback was not
  needed and reads worse (units teleport by leaps under `move_group`).
- On the westwood_road layout, make road tiles cost 1 and off-road forest ≥ 2 so the
  column visibly keeps to the road while Rand's off-road hiding is slower — the
  detection threat then comes from the Q2 region, which is cleaner and more legible
  than AI aggro. (If the design wants the column itself to punish adjacency, the
  existing `patrol` profile with `detection_radius: 1-2` already does that; both were
  exercised — `patrol_west`/`patrol_east` presets exist in the built project.)
- Keep the Myrddraal "rider returns and stops opposite the hiding place" beat as a
  second, single-unit pass of the same machinery: spawn, `march` AI to a road tile
  opposite Rand, hold N turns (change_ai to `do_nothing`), then march off and despawn.
  Every piece of that is covered by the evidence above plus the existing `change_ai`
  action.

## Compiler work list implied by this spike (all in-repo, no engine patches)

1. `MissionUnitSpec.carried_by` → adapter writes `starting_traveler` (Q1), and/or
   `pair_up`/`separate` event actions (Q1; `pair_up` preferred so the Rescue-skill
   penalty applies).
2. Emit a `Rescue` skill into `skills.json` (carry penalty, Q1).
3. `EventConditionSpec.turn_at_most` + `unit_in_region` condition; emit region checks
   against `game.level.regions`, never `game.get_region` (Q2 — stale-registry gotcha).
4. `AIProfileSpec` new behavior `march` = Move_to destination with no Attack
   behaviour (Q4).
5. Nothing needed for Q3.

Everything above is specification/adapter/data work under `src/` + `schemas/` +
`design/`; no `vendor/lt-maker` modification is required or proposed.
