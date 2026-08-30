# Repeated level-playtest run contract

## Required inputs

- compiled project path and tree hash;
- pinned engine path and commit;
- target level ID;
- checkpoint/save path, hash, and provenance;
- trial count, default `20`;
- ordered profile/seed matrix;
- authored objective and expected terminal states;
- state and global frame deadlines.

## Checkpoint provenance


For `synthetic_level_start`, define the checkpoint SHA-256 over canonical, sorted JSON containing project tree hash, engine commit, level ID, mode/difficulty, roster, levels/HP, inventory/durability, money, convoy, campaign and level flags, turn, and positions at the first stable `free` state. Assert the same hash at the start of every trial.
Use one of:

- `campaign_chapter_save`: reached through normal public play and chapter transition;
- `user_save`: supplied save with matching project and engine metadata;
- `synthetic_level_start`: direct LT level initialization, permitted only for self-contained levels.

Every trial receives a fresh copy. Record player roster, levels, HP, inventory/durability, money, convoy, campaign flags, level flags, turn, and positions before input begins. Reject divergent copies.

## Trial profiles

| Profile | Route bias | Combat bias | Resource bias | Optional-content bias |
| --- | --- | --- | --- | --- |
| direct | shortest objective progress | only useful fights | ordinary use | low |
| cautious | safe tiles and formation | favorable engagements | preserve scarce items | low-medium |
| aggressive | tempo and forward pressure | initiate available fights | spend for speed | low |
| exploratory | plausible alternate routes | contextual | ordinary use | high |

Seeds change combat RNG and tie-breaking. Profiles change decisions. Neither may grant hidden information unavailable from current visible state, objective text, previously shown dialogue, or normal player inspection.

## Per-run JSON shape

```json
{
  "run_id": "direct-03",
  "seed": 5003,
  "profile": "direct",
  "project_tree_hash": "...",
  "engine_commit": "...",
  "level_id": "...",
  "checkpoint": {"kind": "campaign_chapter_save", "sha256": "..."},
  "result": "completed",
  "failure_kind": null,
  "turns": 7,
  "frames": 4120,
  "objective_timeline": [{"stage": "rescue", "turn": 3}],
  "units": {},
  "resources": {},
  "combats": {},
  "optional_actions": [],
  "route_summary": [],
  "diagnostic": {},
  "evidence": []
}
```

`result`: `completed`, `game_failure`, `soft_lock`, `harness_error`, or `environment_error`.

## Aggregate minimums

- completed/attempted counts overall and per profile;
- separate harness/environment errors from gameplay outcomes;
- median, minimum, maximum, and individual values for turns and damage;
- player-death and soft-lock counts;
- failure reason frequencies;
- objective-stage timing distributions;
- checkpoint-state equality across run starts;
- project/engine/checkpoint identity equality across every run.

## Stop rules

Stop before 20 only for:

- save or project corruption risk;
- engine crash repeated twice from the same minimal reproduction;
- deterministic blocking defect repeated in three seeds and profiles;
- invalid checkpoint metadata;
- harness inability to issue a required public action.

A stop is `blocked`, never a favorable playability conclusion.
