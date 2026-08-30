---
name: level-playtester
description: Repeatedly play one LT level from a representative checkpoint through real public inputs, vary plausible player strategies across about twenty seeded trials, and report completion reliability, difficulty spread, dominant strategies, resource pressure, soft locks, and player-facing friction. Use when balancing or validating one playable level; do not infer subjective fun or first-time clarity from automation alone.
---

# Level Playtester

Read `AGENTS.md`, `EXEC_PLAN.md`, the target mission/map/scenes, `design/gameplay.yaml`, and [references/run-contract.md](references/run-contract.md). Reuse the real-input state driver in `src/winternight_gen/input_playthrough.py` and the checkpoint/input-flow patterns in `src/winternight_gen/interactive_flows.py` rather than mutating LT flags, firing events directly, or patching generated output.

## Mission

Play one requested level repeatedly from the same representative starting state. Discover whether legal but meaningfully different play styles finish reliably, expose soft locks or dominant routes, and produce evidence useful for balance decisions.

This is automated tactical exploration, not a claim that the level is fun. Human timing, discoverability, emotional pacing, and subjective difficulty remain human playtest questions.

## Establish a trustworthy checkpoint

1. Bind the run to the current project tree hash, engine commit, level ID, difficulty/mode, and checkpoint hash.
2. Prefer a chapter-start save reached through public campaign input and created after the previous chapter's normal transition. Clone it for every trial so runs are independent.
3. A user-supplied save is acceptable only when its project/engine metadata match and its state is documented.
4. Use `game_state.start_level(level_id)` only after proving from mission/unit/item/event specifications that prior campaign inventory, flags, HP, money, convoy, and party state cannot affect the level. Record that proof and label the checkpoint `synthetic_level_start`.
5. Never begin from a debug-only state that grants hidden knowledge, items, flags, positions, or healed units unavailable to a normal player.

## Execute through the public interface

When the browser tool is available, prefer the browser build and drive its visible
controls through Playwright:

1. Run `make web-build`.
2. Serve `build/web-app/build/web/` on a local port through the supervised process
   tool.
3. Open the local `index.html` in an owned browser tab.
4. Use the rendered Select, Confirm, Back, Start, and directional controls or normal
   keyboard input. Observe and screenshot the actual screen after every material
   transition.

The browser target contains the compiled `.ltproj` and accepts the same public game
inputs as the desktop runtime. Never navigate by writing browser `localStorage`,
calling game internals from page JavaScript, mutating flags, editing HP or positions,
teleporting units, or forcing events or victory.

Use the desktop `_run_input_flow` harness only when browser UI automation is
unavailable. It must post public pygame key events; direct action calls, trigger
execution, event skipping APIs, flag mutation, unit teleportation, HP edits, and
forced victory remain prohibited.

For either surface, treat an unavailable intended action, unknown menu state, missing
checkpoint, or state with no legal public input as `harness_error`. Never silently
replace it with Wait or Back and count the run. Write per-run JSON and screenshots
under `build/evidence/level-playtests/<level-id>/`; generated evidence is not authored
project input.

## Build the trial portfolio

Default to 20 deterministic, independently seeded runs:

- 5 `direct`: pursue the stated objective efficiently with ordinary combat risk.
- 5 `cautious`: protect units, preserve HP/resources, and prefer safer routes.
- 5 `aggressive`: seek combat tempo and shorter completion at higher exposure.
- 5 `exploratory`: take plausible detours, optional interactions, and imperfect routes without deliberately sabotaging the run.

The strategies must differ in target selection, route scoring, risk tolerance, optional actions, resource use, or timing—not merely RNG seed. Keep the strategy contract fixed across a comparison so balance changes remain measurable.

Use posted pygame key events and semantic menu labels. Reading LT state for planning and metrics is allowed. Direct action calls, direct trigger execution, event skipping APIs, flag mutation, unit teleportation, HP edits, and forced victory are prohibited.

## Run and observe

For each trial, record:

- seed, profile, checkpoint hash, project tree hash, engine commit;
- completion/failure, terminal state, turns, frames, and wall-clock runtime;
- objective stages reached and the turn each changed;
- player deaths, ending HP, damage taken, combats initiated/received;
- consumables/items used or gained and important durability deltas;
- enemies defeated/remaining, optional interactions completed, and route summary;
- state deadlines, repeated state loops, unavailable required actions, and soft-lock diagnostics;
- screenshots at start, first material divergence, failure, and completion when relevant.

A run fails as `harness_error` when the planner cannot express an intended legal action or the environment/build is invalid. Do not count it as player failure. A run fails as `game_failure` when public play reaches authored defeat. A `soft_lock` requires a stable state with no legal route to progress or a repeated state/input loop beyond the declared deadline.

Run all 20 unless continuing would corrupt data, repeatedly crash the environment, or the same deterministic blocking defect makes later trials non-informative. If stopped early, report the exact stop rule and completed count.

## Judge the level

Aggregate by profile and overall:

- completion rate and confidence limits;
- median and range for turns, damage, deaths, resource use, and objective timing;
- failure/soft-lock clusters with minimal reproductions;
- strategy dominance: one profile or route strictly outperforming alternatives without a meaningful tradeoff;
- sensitivity: outcomes hinging on one seed, one unit, one tile, or one hidden prerequisite;
- pacing: long no-decision stretches, repeated cleanup turns, or abrupt objective transitions;
- checkpoint fairness: whether inherited HP/items/state create unavoidable failure or trivialize the mission.

Use the mission's authored target ranges as oracles when present. Otherwise report distributions without inventing pass thresholds. Never claim statistical certainty from 20 runs; this is a high-signal exploratory sample.

## Report

Write one aggregate JSON report plus per-run JSON under `build/evidence/level-playtests/<level-id>/` through the disposable wrapper described above. Include:

1. `stable`, `unstable`, or `blocked`, with the earliest material reason;
2. checkpoint provenance and trial matrix;
3. aggregate distributions and profile comparison;
4. findings ranked blocking/major/minor with run IDs and evidence paths;
5. the smallest source-level balance or flow adjustment for each material finding;
6. durable regression checks worth adding;
7. remaining human playtest questions.

Do not rebalance missions, change content, or bless a phase gate unless the user separately requests those actions.
