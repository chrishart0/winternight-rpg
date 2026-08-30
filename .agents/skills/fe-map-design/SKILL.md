---
name: fe-map-design
description: Design or repair the tactical layer of a Fire Emblem-style chapter — map dimensions, chokepoints, terrain, enemy placement, objective choice, reinforcement timing, and turn budget — so the mission is decision-dense and fair rather than large, sparse, or punishing. Use when drafting a new mission map, when a chapter plays as sparse, samey, unwinnable, or unfair, or when an objective type is being chosen; do not author narrative source data, compile LT files, or edit `build/`.
---

# Fire Emblem Map Design

A Fire Emblem map is not scenery. It is a set of forced decisions, one per player unit per turn. Your job is to guarantee that on every turn of the target window the player faces a choice whose wrong answer costs something and whose right answer is discoverable from information on screen.

This skill produces or corrects the tactical half of a mission specification under `design/missions/` and the layout it references under `design/maps/`. It does not write scenes, beats, or characters. It never edits `build/` or `vendor/lt-maker`. Follow `AGENTS.md` and the current phase in `EXEC_PLAN.md`; every mission must still reference source beat IDs and label gameplay inventions.

## When to use

Use this skill when any of the following is true:

- A new mission needs a map layout, enemy roster, or objective.
- A chapter is reported as boring, sparse, "just end-turn at a chokepoint", or trivially safe.
- A chapter is reported as unfair: a unit died to something the player could not see or plan against.
- A reviewer flags map size, enemy count, turn count, reinforcement timing, or fog.
- An objective type is being selected or changed.

Do not use it to fix a *comprehension* failure (player does not know what to do, cannot find the target, gets no feedback). That is `mission-coherence`. Do not use it to invent story. That is `narrative-adapter` and `tactical-mission-designer`, which own beat linkage and objective intent; this skill supplies the numbers and the geometry those specifications carry.

## Core loop of map design

Work in this order. Do not place a single enemy before step 4.

1. **Fix the objective and the failure condition.** One sentence, in player verbs. If the objective cannot be stated without "and also", split the chapter or make one clause optional.
2. **Fix the turn window.** Choose `target_play.minimum_turns` and `maximum_turns`. Everything downstream is sized to fit that window.
3. **Draw the route skeleton.** Mark the start tiles, the required destination(s), and the two-to-four chokepoints the player must pass. Compute the shortest path length in movement cost, not tiles. Required turns ≥ ceil(path_cost / lowest player MOV on the mandatory unit). Repo player MOV is 5–6 (`source/characters.yaml`), enemy Trolloc MOV is 5 and the wounded variant is 3.
4. **Assign a location to each turn.** Write "on turn N the player should be near X" for every turn in the window. This is RandomWizard's method: decide where the player is meant to be, then place enemies so each turn has something engaging but not overwhelming to fight.
5. **Place starting enemies against that timeline.** Count movement out by hand. An enemy the player will never meet inside the turn window is filler; delete it or move it onto the timeline.
6. **Place reinforcements only where the timeline has a gap** the player would otherwise coast through, and only under the fairness rules below.
7. **Add an anti-turtle incentive** if the objective does not already supply one: a pursuing wave from behind, a burning building, an NPC who dies on a known turn, a hard `maximum_turns`.
8. **Sanity-check terrain.** Every non-default tile must change a decision. Delete decoration that does not.
9. **Run the review checklist.** Fix every failing line before handing off.

## Quantitative heuristics

All ratios below come from two calibration sets. **Sourced**: Fire Emblem Wiki chapter data for *The Sacred Stones* prologue through Chapter 6, and RandomWizard's rule that starting enemies should be roughly 2–3× the number of player units (target ≈2.5×), under 2× reading as empty and over 3× as too dense. **Repo-local target**: the columns marked as such are this project's chosen values for the Winternight four-chapter slice, derived by scaling the sourced numbers down for a 1–5 unit party and a first-time player.

Sacred Stones calibration (sourced, Fire Emblem Wiki):

| FE8 chapter | Dimensions | Total tiles | Player units | Starting enemies | Enemy:player | Objective |
| --- | --- | --- | --- | --- | --- | --- |
| Prologue | 15×10 | 150 | 2 | 3 | 1.5 | Defeat boss |
| 1 Escape! | 15×10 | 150 | 2 (→4 turn 2) | 7 (+3) | 1.8–3.5 | Seize |
| 2 The Protected | 15×15 | 225 | 6 (→8) | 6 (+2) | 0.8–1.0 | Rout |
| 3 Bandits of Borgo | 17×16 | 272 | 9 | 10 | 1.1 | Seize |
| 4 Ancient Horrors | 15×15 | 225 | 2–9 | 15 (+7) | 1.7–7.5 | Rout |
| 5 Empire's Reach | 15×21 | 315 | 2–9 | 16 (+7) | 1.8–8.0 | Defeat boss |

Read three things off that table. Early chapters are small (150–272 tiles). Early chapters run *below* the 2.5× hack-design rule, because the rule is calibrated for mid-game maps with a trained player. Map area per starting enemy in FE8 chapters 1–4 sits between 15 and 37 tiles.

Repo-local targets for the four-chapter slice:

| Chapter index | Function | Layout (w×h) | Walkable tiles | Player units on map | Starting combat enemies | Enemy:player | Reinforcement waves | Turn window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Tutorial, no combat | 20×16 (`emonds_field`) | 274 | 1 | 0 | — | 0 | 3–8 |
| 1 | First combat, escape | 18×14 (`althor_farm`) | 169 | 2 | 3–5 | 1.5–2.5 | 1 wave, ≤2 units | 4–8 |
| 2 | Defend and rescue | 20×16 (`emonds_field`) | 274 | 4–6 | 7–9 | 1.5–2.0 | 2 waves, ≤2 units each | 6–8 |
| 3 | Solo search and escape | 18×14 (`althor_farm`) | 169 | 1–2 | 1–3 | 1.0–2.0 | ≤1 wave, ≤1 unit | 6–12 |

Derive the numbers in this order. The two density rules interact, and the order matters:

1. **Enemy count comes from the party, not the map.** Multiply player units on the map by the chapter's enemy:player range above. With 2 deployed units you get 3–5 enemies; you may not add a sixth just to fill space.
2. **Map size then comes from the enemy count.** Target **18–35 walkable tiles per starting enemy**. Above 35 the map reads as empty; below 18 a 5-MOV party cannot manoeuvre. Walkable tiles are the count of legend cells whose symbol lacks `blocks_movement`.
3. **If those two disagree, shrink the playable area — never inflate the roster.** Reduce dimensions, or add `blocks_movement` terrain and off-route walls so the *walkable* count drops into range. A 2-unit chapter on a 169-tile map wants roughly 5 enemies or roughly 100 walkable tiles; pick one.

Further repo-local targets:

- **Map area ceiling: 320 tiles** for this slice. Do not add a third layout larger than `emonds_field` without a stated reason; oversized maps in this genre are criticised specifically for empty wasted space.
- **`maximum_turns` ≤ 1.6 × `minimum_turns`** for movement-objective chapters, so the limit bites a stalling player without punishing a careful one. For a fixed-duration defence, set `minimum_turns == maximum_turns` (Chapter 2 uses 6 = 6).
- **`expected_minutes`**: 4–8 for a tutorial, 10–22 for a combat chapter. Widen only with playtest evidence.
- **Chokepoint width 1–2 tiles.** Manhattan distance is the engine's metric (`vendor/lt-maker/app/utilities/utils.py:60`), so a 1-wide gap exposes the holder to at most 3 melee attackers and a 2-wide gap to at most 4. Give every chokepoint exactly one bypass that costs 2–4 extra movement, so holding the line is a choice rather than the only option.
- **At least one decision per player unit per turn.** With 5 units and a 6-turn window that is 30 decisions. If half the turns are "move forward, no enemy in range", cut turns or add pressure.
- **Enemy overlap: at least one third of starting enemies must have overlapping threat ranges** with another enemy, so attacking one puts the attacker in a second one's reach. Non-overlapping enemies get killed one at a time and teach nothing.

### What the shipped slice currently measures

Measured from `design/missions/*.yaml` and `design/maps/*.yaml` as of this writing. Starting enemies exclude units with `starts_on_map: false`; `reinf` is the total across all waves.

| Chapter | Layout | Walkable | Players | Starting enemies | Enemy:player | Walkable per enemy | Reinf | Turn window | max/min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 tutorial | 20×16 | 274 | 1 | 0 | — | — | 0 | 3–8 | 2.67 |
| 1 escape | 18×14 | 169 | 2 | 3 | 1.5 | 56.3 | 2 | 4–8 | 2.00 |
| 2 defend_rescue | 20×16 | 274 | 5 | 5 | 1.0 | 54.8 | 4 | 6–6 | 1.00 |
| 3 search_escape | 18×14 | 174 | 1 | 0 | — | — | 1 | 6–12 | 2.00 |

Read this as the known deviation, not as permission. Three facts follow, and any redesign of these chapters should fix them:

- **Both combat maps are roughly 60% larger than their rosters justify** (55–56 walkable tiles per enemy against a 18–35 target). The remedy is to bound the playable area with blocking terrain or smaller dimensions, not to add enemies to a 2-unit party.
- **Chapter 2 runs at 1.0 enemy:player against a 1.5–2.0 target,** which is where a "defend for 6 turns" objective becomes satisfiable by blobbing.
- **Chapters 1 and 3 exceed the 1.6 max/min turn ratio** (both 2.00), and Chapter 0 is at 2.67. For a tutorial that is acceptable; for Chapter 1 it means a stalling player is never punished.

When you change a chapter, recompute this table for that chapter and state the new row. Do not leave a deviation unmeasured.

## Playtest-earned fun rules

Use the labels **[Repo-earned]** for rules proven by Winternight runs and **[Imported]** for outside patterns adapted to this repo. Full ledgers, cases, calculations, and sources live in [the fun-review reference](references/fun-review-learnings.md); the primary evidence is [`docs/qa/fun-review.md`](../../../docs/qa/fun-review.md).

### Decision density and text concentration

**[Repo-earned]** Count a **dead turn** when the player has one credible action and no risk, reward, ordering, route, or resource tradeoff. Count whole player turns from control to natural victory. Count a sole-safe-action destination turn; exclude QA-only menu checks and probes, and report raw completion separately. Use `dead turns / natural turns` as a diagnostic, not a universal pass line:

| Mission archetype | Intended ratio | Weak or mandatory-only ratio |
| --- | ---: | ---: |
| Tutorial talk/carry | 7/13 (54%) | 7/7 (100%) |
| Escape | 2/4 (50%) | 3/8 (38%), all in the stall tail |
| Defend/rescue | 0/6 (0%) | 0/6 (0%) lazy formation |
| Search/escape | 7/11 (64%) | Bad choice caused a prompt loss, not a soft wait |
| Stealth/carry | 4/9 (44%) | Exposed route lost on turn 7 |
| Zero-pressure denouement | 2/5 (40%) | 10/10 (100%) stall |

Treat placement as decisive: the `wn01` weak route has a lower aggregate ratio than its golden run but invalidates **escape** with a three-turn dead tail.

**[Repo-earned]** Record mandatory A-press pages before first control beside natural mission turns. For a short chapter, treat more than **4 pre-control pages per natural turn** as over budget until play earns an exception. `wn01`'s 22 pages before four turns (5.5/turn) failed; the bounded target was 16/4. Cut redundant pages and dead travel before cutting story beats. See [Text-concentration budget](references/fun-review-learnings.md#text-concentration-budget).

### Consequence, tension, and release

- **[Repo-earned] Optional content must change the next tactical state.** Use the campaign's six payoff patterns: route-efficient Prologue Talks; Chapter 1 Cloth as speed versus preparation; Chapter 2 home-saving as reduced flank pressure plus a green-survivor callback; Chapter 3 sheep pen as increased planning information; Chapter 4 shelter choice as the next safe state; Chapter 5 Luhhan Talk as a litter refresh. Do not add optional texture that changes no route, resource, action, information, pressure, or later callback. See [the payoff table](references/fun-review-learnings.md#optional-content-must-change-the-next-tactical-state).
- **[Repo-earned] Never let a mercy timeout erase the objective verb.** A stall path that wins without performing the displayed verb makes that verb optional; `wn01` awarded turn-8 victory from `[7,7]` after all enemies died. Lose, change to another explicit playable objective, or remove the timeout.
- **[Repo-earned] Stage set pieces agent-first.** Show and focus the threat agent on screen before highlighting the danger zone it creates: `spawn/show agent → focus → scene → highlight zone → control`. `wn04` showed the watched road while its rider remained off-screen.
- **[Repo-earned + Imported] Place tension peaks by verb.** Escape peaks near the playable midpoint, not at the opening breach; defend/rescue builds late; search/care peaks at the reveal and then shortens the resolved tail; stealth/carry peaks at its detection set piece; a denouement peaks emotionally near its final consequence. See [Objective verbs and tension peaks](references/fun-review-learnings.md#objective-verbs-and-tension-peaks).
- **[Repo-earned + Imported] Keep a zero-pressure denouement nonlethal.** Never add enemies or a hard timer. Escalate stalls with condition barks, objective changes, repeated highlights, environmental progression, or optional-action callbacks, then end soon after the emotional peak.

## Objective-type selection

The repo compiler currently accepts exactly four objective types (`src/winternight_gen/models.py`, `ObjectiveSpec`): `tutorial`, `escape`, `defend_rescue`, `search_escape`. Anything else requires extending the model, the compiler, and the schema; do not fake a fifth type with display text.

| Type | Player question it asks | Use when | Dominant failure mode | Required mitigation |
| --- | --- | --- | --- | --- |
| `tutorial` | "What are the controls?" | Chapter 0 only | Combat-free maps become a walking simulator | Gate progress on one named interaction; keep the map under 8 turns; give optional talks so exploration is rewarded, not required |
| `escape` | "Can I get out before it closes?" | Story requires flight, party is outmatched | Difficulty peaks in the middle and the last turns are a foregone conclusion | Put the hardest fight at the mid-point chokepoint, then make the final approach a real race with a pursuing wave rather than empty tiles |
| `defend_rescue` | "Can I hold and still save them?" | Story requires a siege with civilians | Turtling: the player blobs units on one tile and mashes End Turn | Add rescue targets that must be reached *outward* from the defended point, so holding alone loses. Attack the defended point from two directions on different turns |
| `search_escape` | "Where is it, and can I leave?" | Story requires a solitary sweep of a known place | Aimless wandering; fog makes it a guessing game | Cap required search targets at 3–5, make each visually cued, and require only the exit for victory |

Objective types this pipeline does **not** support, and the reason each is a poor fit even if added: `rout` (defeat all) makes filler enemies mandatory and rewards no positioning; `seize` needs a boss with a throne and a distinct Seize action the compiler does not emit. If a chapter's shape genuinely demands one, say so and stop — do not approximate it.

Never require deliberate player failure for a story outcome. Where the story says a unit is wounded, use `survival_floor: 1` (a floor of 1 HP, compiled via `campaign_lt_adapter.py` protected units) or a scripted event; never rely on the player losing a fight.

## Reinforcement fairness

The genre's single most-cited unfairness is the *ambush spawn*: a reinforcement that appears and acts in the same phase, killing a unit the player had no turn to react to. Fire Emblem Wiki's per-game timing table records *The Sacred Stones* as spawning reinforcements "at the start of a turn, before player phase" — never same-turn — while *The Binding Blade* spawns at the start of enemy phase and can act immediately, which is exactly the behaviour reviewers single out as frustrating.

This repo is structurally on the fair side and must stay there. `event_compiler.py:211-213` maps mission `turn_start` triggers to LT's `turn_change`, which fires at the start of a turn before player phase. `ReinforcementSpec.turn` is constrained to ≥ 2 (`src/winternight_gen/models.py`), so nothing spawns before the player has moved once.

Rules:

1. **Never spawn on enemy phase.** Use `turn_start` (→ `turn_change`) or a `region_interact` trigger. Do not introduce an `enemy_turn_change` path.
2. **Telegraph the source.** Before the wave lands, the player must have seen the spawn edge named or shown: a line of dialogue that names the direction, a highlighted region, or a visible road leading off-map at that edge. A wave from an edge the player has never been told about is an ambush even if it does not act immediately.
3. **Cap wave size at 2 units for this slice, and cap the total across all waves at the starting enemy count.** Once reinforcements outnumber the initial placement, the starting placement no longer matters and the map is a spawn treadmill. A chapter with zero starting enemies (Chapter 3 as shipped) is the one exception: its opponents are scripted encounters gated on a region or flag, and one such spawn is permitted — but it must still satisfy rules 1, 2 and 4.
4. **Never spawn inside the player's cluster.** Spawn tiles must be ≥ enemy MOV + 1 (i.e. ≥ 6 tiles) from the nearest player unit at the moment of spawn, measured in Manhattan distance, so the player gets one full turn of warning.
5. **Reinforcements have a job.** Each wave is either an anti-turtle pursuer (spawns behind, charges) or a flank that opens a second front on a defence. A wave that just adds bodies is filler.
6. **Bound the total.** Once the objective is achievable, stop spawning. Infinite waves convert a tactical map into an endurance test. State the last spawning turn explicitly in the specification.
7. **Announce the wave in the same frame it lands** via `play_scene` or `change_objective`, so the player attributes the new units to a cause.

## Terrain as verb

In this pipeline terrain currently affects **movement cost and passability only**. `campaign_lt_adapter.py:202-214` constructs `Terrain(nid, name, color, minimap, platform, None, terrain_id)`, leaving LT's `status` field `None` and `opaque` at its `False` default (`vendor/lt-maker/app/data/database/terrain.py:6-19`). There are therefore no forest avoid bonuses, no fort healing, and no vision-blocking tiles. Additionally `db.mcost.unit_types = ["Foot"]` (`campaign_lt_adapter.py:200`) means one movement group: terrain cannot differentiate unit classes. Design within that, or state the adapter change you need.

Each terrain choice must answer "which decision does this change?":

| Verb | Legend pattern | Cost | Decision it creates |
| --- | --- | --- | --- |
| Advance | `grass` | 1 | Baseline. Open ground is where the player gets punished for spreading out. |
| Commit | `road` | 1 | A fast lane. Make it the exposed route so speed trades against safety. |
| Delay | `forest`, `rubble` | 2 | A one-turn tax. Use it to make the safe route slower than the risky one, not as decoration. Without a `status` bonus it does not reward standing still. |
| Channel | `house`, `inn_wall`, `fire` (`blocks_movement`) | 99 | The only chokepoint tool available. Two blocking tiles with a 1-tile gap is a real tactical object. |
| Signpost | `inn_step`, `inn_door` (`visual_style: doorstep`/`doorway`) | 1 | Marks an interactive tile so the objective target is identifiable at native resolution. |
| Enclose | `inn_floor` behind walls | 1 | An interior pocket the player must enter through a known door — the "behind doors and walls" formation, where enemies sit just inside a gap the player can close in one turn. |

Ban list: no maze corridors wider than the party is deep; no terrain band that is uniformly cost-2 across the whole route (that is a flat turn tax, not a decision); no blocking tile that creates a dead end with nothing in it.

## Tutorial ladder: one mechanic per chapter

Teach exactly one new mechanic per chapter and require it. Sacred Stones' prologue is a fully scripted, unlosable tutorial; the mechanics arrive one at a time afterwards. Mirror that shape.

| Chapter index | New mechanic taught | Made mandatory by | Deliberately absent |
| --- | --- | --- | --- |
| 0 | Move, adjacency, Talk, step-on-region | Victory requires one named Talk and one region entry; no enemies exist | Combat, items, terrain cost, reinforcements, fog |
| 1 | Attack, enemy threat range, terrain movement cost, escape region | 3–5 enemies stand between start and exit; the cheap route is exposed and the safe route costs 2/tile | Fog, rescue, defence timers, healing pressure |
| 2 | Multi-unit turn order, chokepoint holding, protecting a non-combatant, a turn timer | Defend N turns *and* escort 3 civilians to a region; holding alone fails the rescue clause | Fog, item management |
| 3 | Fog-limited vision, search, solo resource discipline | Required items are on distinct regions inside fog; a single wounded enemy punishes careless approach | New unit types, new objective structures |

Ladder rules:

- A mechanic introduced in chapter N must be *used* in chapter N+1, or it was a gimmick.
- Never introduce two mechanics in the same chapter. If a beat demands it, move one.
- The first time a mechanic appears, its failure must be survivable: on chapter 1 the enemy must not be able to one-round the mandatory unit from full HP.
- Difficulty across the slice must be monotonic in *pressure*, not in enemy count. Chapter 3 has the fewest enemies and the highest pressure, because the party is one unit and vision is limited.

## Imported healer and escort patterns

Keep imports subordinate to this repo's played evidence. Detailed examples and URLs are in [the research section](references/fun-review-learnings.md#imported-research-translated-for-this-repo).

### Introduce a healer

- **[Imported] Create immediate role demand.** Put the new healer within one move of a pre-injured ally and outside immediate lethal threat. Guide exactly one valid heal, show the HP and any staff-EXP change, then release control.
- **[Imported] Continue the lesson through choices.** Later turns must ask heal versus move, target, or unit-order questions; do not reduce the healer to one scripted action.
- **[Imported] Keep support bounded.** A weak heal preserves attrition and formation decisions. A dedicated healer stays fragile and player-controlled, not an AI liability.
- **[Imported, lore-bounded] Separate combat HP from story illness.** Ordinary village care must not imply that it can cure a condition reserved for Moiraine's later Healing.

The source patterns are Serra's forced first heal of injured Erk, Natasha's automatic join with Mend and guided support Talk, Lissa's Prologue join with Heal and repeated early role demand, and staff-use EXP without kills. See [Introduce healers through an immediate safe heal](references/fun-review-learnings.md#introduce-healers-through-an-immediate-safe-heal).

### Design escort and carry

- **[Imported] Give the player deterministic control of pace.** Control the carrier or escorted unit directly; never hinge success on follower pathfinding.
- **[Imported] Charge a visible tactical cost.** Carrying must change movement, action economy, route, exposure, or handoff options on the next turn. Cargo that only adds a loss condition is not a mechanic.
- **[Imported] Keep pressure finite and fair.** Telegraph threats and time them to actual progress; never use infinite waves to force movement.
- **[Imported] Protect the traveler without erasing the carrier's decisions.** Prefer Fire Emblem's inactive traveler plus carrier tradeoff over autonomous babysitting. See [Make escort/carry a controlled tradeoff](references/fun-review-learnings.md#make-escortcarry-a-controlled-tradeoff-not-ai-babysitting).

## Named anti-patterns

Each of these is a rejection, not a note.

- **Ambush spawn.** A reinforcement that acts before the player gets a turn, or arrives from an untelegraphed edge. Reject.
- **Filler enemy.** An enemy the mapped turn timeline never brings into contact, or one that dies in a single hit with no positional consequence. Delete.
- **Empty acreage.** Walkable tiles per starting enemy above 35, or a region of the map with no objective, no enemy, and no reward. Shrink the map.
- **End-turn chokepoint.** A single 1-wide gap with charging enemies and no bypass, no timer, and no side objective. The optimal play is to park one unit and mash End Turn. Add a bypass, a timer, or a flank.
- **Bait-and-switch sprawl.** Every enemy has attack-in-range behaviour and non-overlapping threat ranges, so the player kills them one at a time at leisure. Overlap ranges or add pressure.
- **Turtle blob.** A defence objective whose only requirement is survival, satisfied by stacking every unit on one tile. Add an outward requirement.
- **Mercy-timeout victory.** A stall path wins without performing the displayed verb, converting that verb into optional flavor. Replace the mercy win with a stated loss or another objective that still requires play; never apply this fix to a zero-pressure denouement.
- **Fog abuse.** Fog covering the mandatory route, or fog plus escort, or fog with enemy vision advantage. Fog is criticised precisely because the AI is not blinded symmetrically and the player is given no reaction window. In this pipeline `set_fog` compiles to `enable_fog_of_war;True` + `set_fog_of_war;gba;R;R` (`event_compiler.py:184-185`), which sets the same radius for player and AI, so it is symmetric — but the player still has less information than the AI's pathing. Restrict fog to optional search areas with radius ≥ 3, never to the required path, and never in the same chapter as an escort.
- **RNG blowout.** A single enemy whose hit or crit can kill a mandatory unit outright. Check the worst case against the mandatory unit's HP and defence in `source/characters.yaml`; if maximum damage across one enemy phase ≥ its HP, cut the roster or lower the might.
- **Unwinnable seed.** A layout where the required region is not 4-connected to the start over non-blocking tiles. `semantic_validation.py` already runs this BFS; do not make it fail.
- **Objective drift.** Display text that names a goal the win event does not check, or a win event the display text never mentions.
- **Decoration terrain.** Any non-`grass` tile that changes no decision.
- **Silent difficulty spike.** A chapter whose enemy:player ratio jumps more than 0.7 above the previous chapter's without a new tool given to the player.

## Review checklist

Run every line against the draft mission and map specifications. Each is binary. Any `no` blocks handoff.

### Fun review method

**[Repo-earned]** Review for fun only after correctness is established. Run the intended all-content route and one deliberately weak route using public inputs only. Use `FUN`, `MOSTLY FUN`, `FLAT`, or `NOT FUN`; do not average the result into a score. Cite the compiled report-tree hash, engine pin, both run artifacts, natural and raw turn counts, dead-turn rationale, a native-resolution peak frame, weak-route evidence, causal source lines, tension curve, core verb, and contracts the fix must preserve. See [Fun review method](references/fun-review-learnings.md#fun-review-method).

1. Objective type is one of the four the compiler accepts, and `display_text` names the same target the win event checks.
2. A `win` action and a `lose` action both exist somewhere in the chapter's events (`static_analysis.py` enforces this per level), and no victory condition is left implied by `survive_turns` or `rescue_count` alone — both fields are inert metadata, so the counter and the `win` action are written out as events.
3. `target_play.minimum_turns` ≥ ceil(shortest required path cost / mandatory unit MOV), computed and recorded.
4. `maximum_turns` ≤ 1.6 × `minimum_turns`; exempt only a fixed-duration defence with the two equal, or a `tutorial` chapter, where a wide window is a courtesy rather than a stall.
5. Map dimensions are within 320 total tiles, and walkable tiles per starting enemy fall in 18–35. If not, the recorded remedy is a smaller playable area, not a larger roster. A chapter with zero starting enemies is exempt from the density half and must state why it has none.
6. Starting enemy:player ratio falls in this chapter's row of the repo-local table, or the chapter has zero starting enemies by documented intent.
7. Every starting enemy appears on the written turn-by-turn timeline; none is unreachable within `maximum_turns`.
8. At least one third of starting enemies share an overlapping threat range with another enemy.
9. The map has 2–4 chokepoints of width 1–2, and each has exactly one bypass costing 2–4 extra movement.
10. Every reinforcement has `turn` ≥ 2 or a `region_interact` trigger, and no reinforcement uses an enemy-phase trigger.
11. Every reinforcement spawn tile is ≥ 6 tiles (Manhattan) from the nearest player unit at spawn time, and its edge or direction was telegraphed earlier in the chapter.
12. Per-wave reinforcement size ≤ 2, total reinforcement units ≤ starting enemy count (or the chapter is the documented zero-starting-enemy scripted-encounter case), and the last spawning turn is stated.
13. The chapter has at least one anti-turtle incentive: a hard turn limit, a pursuing wave, or a timed loss condition.
14. Exactly one new mechanic is introduced relative to the previous chapter index, and the objective cannot be completed without using it.
15. Worst-case single-enemy-phase damage against the mandatory unit is less than its HP, computed from `source/characters.yaml` and `design/gameplay.yaml`.
16. Every non-`grass` terrain symbol used in the variant is justified by one entry in the terrain-as-verb table.
17. The required destination region is 4-connected to every player start position over non-blocking tiles.
18. Fog, if present, covers only optional area, has radius ≥ 3, and does not coexist with an escort or rescue clause in the same chapter.
19. Every failure condition is either a mandatory unit's death or a stated turn limit; none requires deliberate player failure.
20. Every mission-level invention not traceable to a source beat is labelled per `AGENTS.md` rule 5.
21. The natural route has a dead-turn ledger; QA probes are excluded and weak-route stall turns are annotated separately.
22. Every optional objective changes the next tactical state or earns a later visible callback without becoming required.
23. The planned tension peak fits the objective verb; any set-piece threat agent is shown before its danger zone.
24. Mandatory pre-control pages are recorded beside natural gameplay turns and meet the 4:1 short-chapter budget or cite played evidence for an exception.
25. A healer introduction, escort/carry objective, or zero-pressure denouement follows its labelled pattern above.

## LT-Maker implementability notes

Verify every recommendation against the pinned engine before proposing it.

- **There is no built-in victory evaluation.** LT stores only display strings: `LevelPrefab.objective` is a dict over `OBJECTIVE_KEYS = ['simple', 'win', 'loss']` (`vendor/lt-maker/app/data/database/levels.py:11,22`), rewritten at runtime by the `change_objective_simple` / `change_objective_win` / `change_objective_loss` commands (`vendor/lt-maker/app/events/event_commands.py:2740-2766`). Winning and losing are event side effects: the `win_game` and `lose_game` commands (`vendor/lt-maker/app/events/event_commands.py:1058-1068`) resolve to functions that set `game.level_vars['_win_game']` / `_lose_game` (`vendor/lt-maker/app/events/event_functions.py:750-754`), consumed in `vendor/lt-maker/app/events/event_state.py:120-137`. Consequently *every* objective in this project is authored logic, and "rout", "seize", or a turn-limit victory would have to be written as events, not selected.
- **`ObjectiveSpec` is mostly declarative, and two of its fields are inert.** Only `display_text` reaches the engine: `campaign_lt_adapter.py:401-406` copies it into the `simple` and `win` slots and synthesizes the `loss` slot from `failure_conditions`. `type`, `unit`, and `region` are read only by `semantic_validation.py:183-200` for reachability checks. **`survive_turns` and `rescue_count` are consumed by nothing** — declaring `survive_turns: 6` does not create a turn-6 victory. Chapter 2's six-turn defence is hand-authored as a chain of `turn_start` events. Treat both fields as review metadata, and write the counter and the `win` action out explicitly.
- **Repo objective compilation** flows through `src/winternight_gen/event_compiler.py:188-191` (`win` → `win_game`, `lose` → `lose_game`). Unit-death failure conditions additionally compile to a synthesized `unit_death`-triggered `lose_game` event in `src/winternight_gen/campaign_lt_adapter.py:474-483`. `src/winternight_gen/static_analysis.py:92-95` fails the build if any level lacks either command.
- **Fair reinforcement timing is already wired.** `src/winternight_gen/event_compiler.py:211-213` maps `turn_start` to LT's `turn_change` trigger, whose engine docstring reads "Occurs immediately before turn changes to Player Phase. Useful for dialogue or reinforcements" (`vendor/lt-maker/app/events/triggers.py:94-99`). The engine also exposes `enemy_turn_change`, documented as "Useful for 'same turn reinforcements' and other evil deeds" (`vendor/lt-maker/app/events/triggers.py:101-107`). The repo compiler deliberately does not expose it. Keep it that way.
- **Available mission event triggers** (`schemas/mission.schema.json`, `EventTriggerSpec`): `level_start`, `level_end`, `turn_start`, `unit_wait`, `unit_death`, `combat_start`, `region_interact`, `talk`, `call`. Available actions include `spawn_group`, `change_ai`, `activate_region`, `deactivate_region`, `highlight_target`, `change_objective`, `set_fog`, `win`, `lose`. The `change_objective` action's `target` selects the objective slot: `event_compiler.py:181-182` emits `change_objective_{target};{value}`, so `target` must be `simple`, `win`, or `loss`.
- **AI vocabulary is the current bottleneck.** `AIProfileSpec.behavior` accepts only `pursue`, `do_nothing`, and `patrol` (`src/winternight_gen/models.py`), and `design/gameplay.yaml` defines only `pursue` and `do_nothing`. The engine supports far more: `AI_ActionTypes = ['None', 'Attack', 'Support', 'Steal', 'Interact', 'Move_to', 'Move_away_from', 'Wait']` with view-range semantics documented in `vendor/lt-maker/app/data/database/ai.py:4-8`, where `view_range` of `-1` is guard, `-3`/`-4` widen the search. Attack-in-range and attack-in-2-range behaviour — the two AI types most responsible for interesting placement — require adding profiles there and mapping them in the adapter. Say this explicitly rather than approximating them with `pursue`.
- **Group aggro exists in the engine, not in the repo schema.** LT's `AIGroup` carries a `trigger_threshold` (`vendor/lt-maker/app/data/database/ai_groups.py`) so a whole group charges once that many members could attack (`vendor/lt-maker/app/data/database/ai.py`, `vendor/lt-maker/app/engine/ai_controller.py:282-342`, documented in `vendor/lt-maker/docs/source/editors/Level-Editor.md:24-31`). This is the clean implementation of "linked AI" formations. It is not currently reachable from a mission specification.
- **Deployment count** is controlled by formation regions or the `_prep_slots` / `_minimum_deployment` level variables (`vendor/lt-maker/docs/source/editors/Level-Editor.md:20-22`, `vendor/lt-maker/docs/source/appendix/Special-Variables.md:87-89`). This slice places units explicitly instead; a variable-deployment chapter needs those variables.
- **Fog variables**: `_fog_of_war`, `_fog_of_war_type`, `_fog_of_war_radius`, `_ai_fog_of_war_radius`, `_other_fog_of_war_radius` (`vendor/lt-maker/docs/source/appendix/Special-Variables.md:71-83`, read in `vendor/lt-maker/app/engine/game_state.py:1293-1301`). Type 0/1 is GBA-style masking of enemy positions only. Map variants also carry `fog` and `fog_radius` (`src/winternight_gen/models.py`, `MapVariantSpec`).
- **Region idioms** the engine documents for villages, shops, seize, escape, switches, and chests are in `vendor/lt-maker/docs/source/events/Region-Events.md`; the escape idiom there (`remove_unit` then win when no player unit remains positioned) is the model for a multi-unit escape if this project ever needs one.
- **Reinforcement groups**: LT's `spawn_group` / `add_group` / `move_group` commands and their cardinal-direction spawning are documented in `vendor/lt-maker/docs/source/guides/eventing_tutorials/Unit-Groups.md`; the repo surfaces this as the `spawn_group` mission event action.
- **Distance is Manhattan** (`vendor/lt-maker/app/utilities/utils.py:60`). All range, chokepoint, and spawn-distance arithmetic above uses that metric.
- **Terrain limits** are stated in the terrain-as-verb section: no `status`, no `opaque`, one movement group. Changing any of those means editing `src/winternight_gen/campaign_lt_adapter.py:194-214` and the map schema, which is a compiler change, not a content change.

## Sources

Repository playtest evidence and research synthesis:

- [Fun-review learnings](references/fun-review-learnings.md), derived from [`docs/qa/fun-review.md`](../../../docs/qa/fun-review.md), with the dual-run ledger, dead-turn metrics, mission cases, healer/escort/denouement research, and external URLs.

Community design analysis:

- RandomWizard, "RandomWizard's Enemy Placement Guide", Fire Emblem Universe — AI-type taxonomy (charge, attack-in-range, guard tile, attack-in-2-range, linked, escape), formations, the turn-by-turn placement method, anti-turtle incentives, and the 2–3× (≈2.5×) enemy-to-player ratio rule. <https://feuniverse.us/t/randomwizards-enemy-placement-guide/14888>
- Same thread, reply 11 — escape maps peak toward the centre with the final turns a foregone conclusion, whereas well-designed defence maps peak later. <https://feuniverse.us/t/randomwizards-enemy-placement-guide/14888/11>
- "Ten Tips to Improve Fire Emblem #3: Map Design" and "Map Design (Continued)", The Crusader Grant — thoughtful enemy positioning so attacking one enemy puts you in another's range; chokepoints, anti-turtling and side objectives; terrain placement as strategy; elevated ledges in defence chapters; "ambush spawns are terrible for the strategy of a game" and the recommendation that reinforcement locations be hinted in advance; big maps' reputation for empty wasted space. <http://thecrusadergrant.blogspot.com/2015/11/ten-tips-to-improve-fire-emblem-3-map.html>, <http://thecrusadergrant.blogspot.com/2015/11/map-design-continued.html>
- "Mapping Advice", Fire Emblem Universe. <https://feuniverse.us/t/mapping-advice/25184>
- Primefusion, "[ARCHIVED] Primefusion's Mapping Tutorial", Fire Emblem Universe. <https://feuniverse.us/t/archived-primefusions-mapping-tutorial/7868>

Series reference data:

- Fire Emblem Wiki, "Objectives" — taxonomy of Seize, Rout, Defeat boss, Defend/Survive (defensive objectives typically 7–15 turns, emphasis on maintaining defences rather than attacking), and Escape (maps typically feature enemies much stronger than or greatly outnumbering the player). <https://fireemblemwiki.org/wiki/Objectives>
- Fire Emblem Wiki, "Reinforcement" — per-game timing table; *The Sacred Stones* spawns "at the start of a turn, before player phase", *The Binding Blade* at the start of enemy phase and can act the turn it appears; fan terminology "same-turn"/"ambush" reinforcements. <https://fireemblemwiki.org/wiki/Reinforcement>
- Fire Emblem Wiki chapter data pages used for the calibration table: <https://fireemblemwiki.org/wiki/The_Fall_of_Renais>, <https://fireemblemwiki.org/wiki/Escape!>, <https://fireemblemwiki.org/wiki/The_Protected>, <https://fireemblemwiki.org/wiki/The_Bandits_of_Borgo>, <https://fireemblemwiki.org/wiki/Ancient_Horrors>, <https://fireemblemwiki.org/wiki/The_Empire%27s_Reach>
- RPGFan, *The Binding Blade* review — enemy reinforcements that move as soon as they spawn named as a frustrating mechanic. <https://www.rpgfan.com/review/fire-emblem-the-binding-blade/>
- CBR, "12 Worst Fire Emblem Maps In The Series" — fog of war forcing reliance on limited visibility while enemies ignore it; "Arcadia" as fog plus escort plus desert. <https://www.cbr.com/fire-emblem-worst-maps-series/>
- Fire Emblem Wiki (Fandom), "Fog of War" — the Thracia 776 AI imbalance and later corrections. <https://fireemblem.fandom.com/wiki/Fog_of_War>

Engine and repository:

- `vendor/lt-maker/docs/source/events/Region-Events.md`, `vendor/lt-maker/docs/source/editors/Level-Editor.md`, `vendor/lt-maker/docs/source/appendix/Special-Variables.md`, `vendor/lt-maker/docs/source/guides/eventing_tutorials/Unit-Groups.md`
- `vendor/lt-maker/app/data/database/levels.py`, `ai.py`, `ai_groups.py`, `terrain.py`; `vendor/lt-maker/app/events/triggers.py`, `event_commands.py`, `event_functions.py`, `event_state.py`, `regions.py`; `vendor/lt-maker/app/engine/ai_controller.py`, `game_state.py`; `vendor/lt-maker/app/utilities/utils.py`
- `src/winternight_gen/models.py`, `event_compiler.py`, `campaign_lt_adapter.py`, `semantic_validation.py`, `static_analysis.py`; `schemas/mission.schema.json`; `design/missions/*.yaml`, `design/maps/*.yaml`, `design/gameplay.yaml`; `source/characters.yaml`
