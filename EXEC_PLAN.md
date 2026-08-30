# Execution plan

## Current phase

Phase 3/5 — **story-plan v2 is fully implemented and QA-passed as of 2026-08-28.**
All six chapters carry the book-text narrative pass (direct beats quote trimmed
source dialogue; contract tests verify every direct line is a contiguous source
subsequence). The Long Road compiler worklist landed (pair_up/separate, Rescue
carry skill, turn_at_most + unit_in_region conditions, non-attacking march AI,
region_condition for gated activations, failure_scene cause scenes,
change_objective target both). The full cast has approved hash-locked AI art:
24 map sprites, all portraits, and dedicated wn04/wn05 backgrounds, generated
only through `gba-map-sprite-author` (references/pipeline-sop.md) and the new
`cutscene-art-author` skill. Systemic UI fixes are measured and test-enforced:
56-character settled dialogue budget (216 boxes fixed, zero remaining across
644), 30-character banner and 16-character persistent objective budgets with
compile-time diagnostics, deduplicated loss text.

QA ran as agent playtest loops with real pygame input and native-frame vision
review (`docs/qa/round1-*` → fix waves → `round2-*` → wn03 objective fix →
`round3-wn03*`): final verdicts PASS on all six chapters. Round-1 defects fixed
include the wn00 early-inn soft-lock and auto-win door, the wn02 mandatory-unit
balance failure (worst-case one-phase math now passes for every mandatory unit;
two real-input golden formations verified), the wn04 hold-still contradiction,
and stale Objective screens campaign-wide. Known accepted note: the wn01
pre-control opening is 22 settled boxes (down from 28) — pacing judgment, no
player-facing defect; wn05 has no public-input loss path by design (zero-enemy
denouement).

Final gate: `make check` green end-to-end (146 tests, six-level pinned-engine
smoke with per-chapter truth tables, full-campaign real-input playthrough,
suspend/continue, Game Over recovery, deterministic packaging) at report tree
`a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a`.
Remaining Phase 5 exit gates are the human ones: three timed human playthroughs,
60–110 minute duration check, and human difficulty/tutorial-clarity review.

**Fun-improvement plan implemented and playtested (2026-08-28,
`docs/fun-improvement-plan.md` + owner directives).** Healing landed: items can
target allies (self-use preserved via 0..1 ranges), the `healing_spell` kind
gives Moiraine her `mending_weave` (runtime-verified through the Spells menu),
and Nynaeve joins the redesigned wn02 with a guided tutorial-style first heal
of wounded Haral. wn02 was rebuilt to the owner's epic brief per
`docs/design/wn02-epic-redesign.md`: dedicated 22x18 layout (cap raised to 5),
eight-turn hold, FE8-style four-house race (enemy at an open door ruins it,
player Visit spawns an escortable resident; 3-of-4 return quota with
quota-aware loss semantics), progressive burn layers via new source-authored
tilemap layers, Mat/Egwene/Nynaeve as green Talk recruits (survival-floored;
Haral remains mortal with death=loss per standing owner rule), march
torchbearers and anchored green patrols, and cause scenes on every loss path.
New compiler vocabulary: map layers, triggering-unit region conditions,
level_var_compare, set_current_hp, scripted-forecast lessons. FE8
movement-through-enemies blocking was verified already-native (probe: 1 valid
tile past an enemy blocker vs 6 past an ally). All other chapters received
their fun-review improvements (wn01 mercy-win became a real loss; wn03 12-turn
fever clock + Narg quick-exit + sheep-pen intel; wn04 real hide shelters +
visible rider + earlier sweepers; wn05 Luhhan litter assist + fever barks +
both-talks callback + restored ending card after a foreign CTA was removed;
wn00 evolved with the external tutorial agent's two-thrower forced-move lesson,
post-throw pacing cut 63->20 mandatory boxes). Every mission was playtested by
QA agents with real pygame input and vision-inspected native frames across
three rounds (`docs/qa/fun2-*`, `fun3-*`): final verdicts wn00 FUN, wn01 FUN,
wn02 FUN, wn03 MOSTLY FUN (target met), wn04 FUN, wn05 MOSTLY FUN (target met,
by-design zero-pressure denouement). Closing gate: `make check` green at report
tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403`.


**Village-defense human playtest pass shipped (2026-08-29).** This supersedes
the earlier wn02 details where they differ. `herb_pouch` now displays as
**Healing Herbs**, targets one adjacent ally, heals a fixed 8 HP, spends one of
three uses, and grants 11 EXP; the full real-input campaign used it through
Items on Haral, raised him 28→36 HP, left two uses, and gave Nynaeve 11 EXP.
`mending_weave` heals 12 at range 1–2, preserving Moiraine's stronger One
Power care. Nynaeve now starts blue inside the inn beside green Egwene; the
mandatory Nynaeve→Egwene→Mat Talk chain teaches Talk, gives Mat his compatible
Hunting Bow, and points him at the south house before releasing the four
door-bound torchbearers. Residents return automatically on their first step
onto the inn floor; no Return menu is exposed. Haral remains mortal but no
longer causes Game Over. Bran and Thom are visible, talkable, phase-inert inn
NPCs with invented placement/dialogue and no loss conditions. Reaching the
three-resident quota changes the objective to the inn hold, plays Lan's
fall-back order, and spawns two fair two-unit groups from opposite roads using
an inn-directed attack/move AI; their 12–14-tile spawn distances preserve a
reaction turn and total reinforcements remain bounded by the ten starting
enemies. Original programmatic house tiles now compose 3×2/4×2 roof masses,
deep eaves, timber facades, real apertures/steps, warm occupied windows,
boarded empty windows, and existing fire/rubble ruins; FE8 tiles were
reference-only and no Nintendo pixels were copied, traced, recolored, or
shipped.

**WN02 house doors welded to the redrawn facades (2026-08-29).** The FE-grammar
house redraw left `house_door`/`closed_door` drawing their own free-standing
door over the road base, so at native 1× the gold read as a box pasted in front
of the wall: bare road showed through the 2px corner-post columns, the eave and
sill bands stopped at the tile edge, and the "threshold" floated across the
middle of the tile at y9–11. `asset_pipeline.py` now has one facade grammar,
`_house_palette` + `_draw_house_ground_floor`, shared by the wall-row house
tiles and both door states; `_draw_house_door` cuts the doorway into that shell
and puts the gold on the bottom three rows where a threshold belongs. Hearth
light is emissive (never dimmed by `_lit_color`) so the Visit markers carry at
night. `house_door` and `closed_door` now declare the house colour
`[118, 82, 57]`, which removes the last seam in the firelit top-row glint.
Occupied/empty house tiles are byte-identical to before the refactor. Door
coordinates were already correct and are unchanged: west `[3, 7]`, north
`[10, 2]`, east `[18, 7]`, south `[12, 16]` — each in its house's wall row, and
each the only tile of that facade with a walkable neighbour, so the map,
`house_*_saved`/`house_*_ruined` layers, `house_*_door` regions, and resident
spawns in `design/missions/village_defense.yaml` all still key off the same
four tiles. Rescue rules untouched. Evidence:
`docs/qa/wn02-house-{west,north,east,south}-door-native-1x.png` and the new
`-saved-` captures beside them, plus
`test_battle_house_doors_are_cut_into_the_facade_they_stand_in`, which locks the
shared eave/post/sill columns, the bottom-row gold, and the absence of gold
above the threshold or on a shut door.

**WN02 objective clarity, one-move Talk, east-house direction, counted inn
hold, and armed Bran (2026-08-29).** Owner playtest notes on the village night,
all measured against the pinned engine rather than assumed:

- *Objective clarity.* LT stores objective slots as display strings and redraws
  the persistent panel every frame from `game.level.objective['simple']`
  (`vendor/lt-maker/app/engine/ui_view.py`), and `change_objective_*` arguments
  are `EvaluableString`, which `convert_parse` deliberately does not
  pre-evaluate (`app/events/event_validators.py:24-27`). Saving the east house
  now sets the banner to `{v:residents_returned}/3 villagers saved`, so the
  panel reads the true live count — `0/3` before any return, `2/3` mid-rescue —
  with no per-count event variants. Because the map HUD is hidden during
  events, no content-only trick can animate that panel, so the emphasis is a
  new opt-in engine behavior: the `flash_objective` action lowers to
  `level_var;_objective_flash;True`, and the patched `UIView` consumes that var
  once and blinks the panel three times at `1.4x` before easing back to `1x`
  over 900 ms. Measured at native `240x160`: the settled panel is `136x27` and
  the grown panel `190x37`, so the enlarged right-anchored draw still fits
  (`4 + 190 < 240`). The redundant `change_objective` inside
  `nynaeve_guided_heal` was removed; it was a no-op that would now overwrite the
  quota banner. `_objective_length_warnings` now measures the drawn line, so the
  30/16-character budgets apply to `0/3 villagers saved` (19) rather than to the
  raw expression (40).
- *Inn hold at three saved.* `begin_inn_hold` was expressed as
  `residents_returned >= 2` on the same `Return` region trigger as the counting
  events. LT evaluates every candidate condition for a trigger before running
  any of them (`app/events/event_manager.py:45-57`), so that condition could
  only ever see the pre-increment count, and the Lan scene played before the
  third villager was counted or removed. The hold now triggers on `unit_wait`
  with an honest `residents_returned >= 3`, which fires on the first wait after
  the third villager is counted, so the panel, the removal, and Lan's cut agree.
  `sc_c2_inn_hold_begins` is rewritten in Lan's authored voice — "Three inside.
  They want the inn now." / "Nothing gets through that door." — and adds
  `c2_homes_threatened`, the beat that carries the three-of-four quota. The
  existing inn-directed spawn/AI is unchanged.
- *One-move Talk.* Mat moved from `[7, 8]` to `[11, 7]`. The old position sat
  behind the inn's west wall (`x=8` is `inn_wall` on `y=6..8`), so Egwene's only
  route was out the threshold and around: six tiles against her five movement,
  a two-turn Talk. He is now one step from her `[10, 8]` start, does not stack
  on Nynaeve `[11, 8]` or Moiraine `[12, 8]`, and is 13 tiles from the east door
  instead of 16. The real-input run performs the Talk on turn 1 with a single
  `[10, 8] -> [10, 7]` move.
- *East, not south.* `recruit_mat_egwene` highlights `house_east_door`
  `[18, 7]`, its tutorial line reads "Visit the east door. Walk its resident
  into the inn.", and both recruit scenes say east. Rescue rules, quotas, and
  loss semantics are untouched.
- *Torch clock decoupled.* The four door-bound torchbearers were released by
  the Talk chain, so making that chain one turn faster also started the door
  race a turn earlier and made the south house unwinnable (the first real-input
  run lost on a second ruin at turn 3). They now advance on `turn_start turn: 2`
  in `torchbearers_advance`, which reproduces the previous effective timing —
  the change lands before the turn-2 enemy phase either way — while making the
  race clock independent of how fast the player learns Talk.
- *Armed Bran.* `bran` carried `weapon_type: Utility` and no items, so his
  `patrol_bran_west` profile's `Attack` behavior never had a valid action and he
  stood in the fight unable to swing. He now carries the existing `boar_spear`
  with `weapon_type: Lance` and `additional_weapon_types: [Utility]`. He stays a
  green, non-`Tile` inn NPC on `patrol_bran_west` with no loss condition; no
  class pass was made.

Evidence: `make check` green end-to-end (175 tests, six-level pinned-engine
smoke, public mechanics with the two new WN02 checks
`east_house_lesson_flashes_live_quota` and
`hold_waits_for_the_counted_third_villager`, editor smoke, deterministic
rebuild, the 22,237-frame full real-input campaign, suspend/continue, Game Over
recovery, captures, isolated packaging, reporting) at content hash
`67ebef2606ecca8a3e1ffcc05d014cadab26b5ffc8a962a12e4d95a884c1e75a`, tree
`fe05453d37de1e1e3f4c92a137ae34c2eb15645ddfbcf8043302ccd0f54f6f38`, manifest
`82f5a7e17a842435357b461abb8ae8c9ce03f4f95ddd540169463caa46c1d962`. Native
`240x160` frames: `docs/qa/wn02-objective-flash-{blink-out,grown,easing,settled}-native-1x.png`
plus captured `build/evidence/screenshots/wn02_village_defense-{map,sc_c2_recruit_mat,sc_c2_recruit_egwene,sc_c2_inn_hold_begins}.png`.
Observation for the owner, not a harness failure: the automated "direct"
playthrough parks Mat on the saved east door for the remaining turns and he was
killed there in the enemy phase, so the run exercised the Mat permadeath
`Continue` path and still finished all six chapters. A human should walk him
back with Lan's fall-back order.

**WN02 clarity production deploy (2026-08-29).** `make web-build` staged
project tree `fe05453d37de1e1e3f4c92a137ae34c2eb15645ddfbcf8043302ccd0f54f6f38`
with project manifest
`82f5a7e17a842435357b461abb8ae8c9ce03f4f95ddd540169463caa46c1d962` and web
adapter `1.0`. AWS profile `personal` resolved to account `933784155053`; the
exact static payload in `build/web-app/build/web/` was synchronized with
`--delete` to `s3://winternight-rpg-poc-chrishart0/` in `us-east-1`.
`web-app.tar.gz` is 4,677,149 bytes, version
`6eehHj8GG22E8sgpshhGB.KIXEUgY2fu`, with S3 ETag and local MD5
`2ffc8e1335deafab638f0b027f3ea036`. CloudFront distribution `E1V1AX0S4NBYGI`
completed invalidation `I8CCMT6JX54TN80TYJB7C44JBJ`. Fresh headless Chromium at
`https://wot-game.arcadian.cloud/` observed a secure context, zero failed
requests, `web-app.tar.gz` decoded at 4,677,149 bytes, document title
`Eye of the World - v2026.02.17a`, service-worker scope
`https://wot-game.arcadian.cloud/sw.js`, the native `480x320` canvas, and the
Eye of the World `PRESS START` frame. Evidence:
`docs/qa/wn02-clarity-deploy-2026-08-29-live-title.webp`. No live gameplay
smoke beyond the title frame was performed in the browser; the WN02 behavior
evidence above comes from the pinned engine locally.

**Stuck enemy-range overlay and Ruined Farm search order (2026-08-30).** Two
owner playtest defects from the live browser POC, both reproduced against the
pinned engine before any change.

- *Sticky red danger zone.* `FreeState` answers `SELECT` on an enemy with
  `game.boundary.toggle_unit` (`vendor/lt-maker/app/engine/general_states.py:406-409`),
  which adds that unit to `BoundaryInterface.displaying_units` and draws
  `boundary_red` over every tile it can reach and attack. Nothing in LT clears
  that set except the identical select, `reset_unit` on the unit's death, or the
  turnwheel — `FreeState`'s `BACK` branch is `pass`, and `boundary.reset()`
  rebuilds the grids while keeping the displayed set. A headless free-state probe
  on `wn02_village_defense` selected `torch_west` at `[1, 2]`, drew 46 red tiles
  with `draw_flag: true`, and still reported
  `displaying_units == {'torch_west'}` after `BACK`, after the cursor moved to
  `[0, 0]`, and after a real `turn_change`/`status_endstep` phase change. On the
  web that overlay was unreachable: `InputManager.process_input` only maps mouse
  buttons 1/2/3 to `SELECT`/`INFO`/`BACK`, and the shell dispatches button 0
  only, so a pointer that left the canvas had no second select and no cancel.
  Fixed in the browser adapter alone — `vendor/lt-maker` and
  `patches/lt-maker-winternight-runtime.patch` are untouched. `web/runtime_main.py`
  erases `boundary.displaying_units` (and the `INFO` `all_on_flag`) when the
  frame's input is `BACK`, when the state machine is in `phase_change`, or when
  the shell reports a browser-only exit through the new
  `window.winternightTakeOverlayClear()` bridge. `WEB_SHELL_SCRIPT` raises that
  report on mouse `pointerleave` of the game canvas, on a press released outside
  the canvas rect, on window `blur`, and on `fullscreenchange`; touch and pen
  `pointerleave` are ignored because those pointers are destroyed after every
  tap, which would otherwise cancel the overlay on the same tap that opened it.
  Move-range and hover highlights are untouched, and the danger toggle itself
  still works — it is now escapable.
- *Ruined Farm search order.* `design/missions/return_to_farm.yaml` gated the
  water, bandages, and blankets Search regions on
  `required_flags: [farmhouse_reached]`, which compiled to region condition
  `game.level_vars.get('farmhouse_reached', False)` plus the same clause on each
  `find_*` event. A trigger probe at level start with `farmhouse_reached: false`
  fired zero Search events for all three regions, so a player who walked to the
  supplies instead of the gold `farmhouse_approach` tile at `[6, 7]` spent the
  12-turn fever clock on inputs that did nothing, and lost the chapter. The three
  supply regions and their events are now ungated (region condition `True`), and
  the opening objective states the real goal, `Find Tam's needs,By turn 12`,
  instead of `Reach farmhouse,By turn 12`; the then-duplicate `change_objective`
  inside `reach_farmhouse` was removed. The gold tile keeps
  `sc_c3_farmhouse_approach`, its `farmhouse_reached` flag, and the sheep-pen fog
  payoff for a player who walks it. Tam's sword still requires all three
  supplies, and both escape gates are unchanged.

Evidence: `make check` green end-to-end (179 tests, six-level pinned-engine
smoke, public mechanics, editor smoke, deterministic rebuild, full real-input
campaign, suspend/continue, Game Over recovery, captures, isolated packaging,
reporting) at content hash
`a9482b50a1744b3ed28214ad0fa4ace4ad5e00473429574a985117a73a7196ca`, tree
`976640584fe63ae1002889da51a524b754e745be24db703c8e5a76a2e06ce0ce`, manifest
`da49f0636b193a7d2982ab243f7be9813b4367a2677d14b85ed3f5b726d032ea`. The public
mechanics run now searches the three supplies before the optional Visit and
records `supplies_searchable_before_farmhouse_visit: true` alongside the
unchanged `farmhouse_stage_reached`, sword, Narg, and quick-exit checks
(`build/evidence/mechanics.json`). New tests: `test_web_export.py` locks the
clear predicate, the boundary clear itself, the four shell exits, and a
pinned-engine regression that selects a live enemy in `free` state, confirms LT
keeps the red range through `BACK`, and confirms the adapter helper empties it;
`test_campaign_specs.py` locks the ungated supply regions, the still-gated sword,
and the new opening objective.

**Red-box and farm-order production deploy (2026-08-30).** `make web-build`
staged project tree
`976640584fe63ae1002889da51a524b754e745be24db703c8e5a76a2e06ce0ce` with project
manifest `da49f0636b193a7d2982ab243f7be9813b4367a2677d14b85ed3f5b726d032ea` and
web adapter `1.0`. AWS profile `personal` resolved to account `933784155053`;
`build/web-app/build/web/` was synchronized with `--delete` to
`s3://winternight-rpg-poc-chrishart0/` in `us-east-1`. `web-app.tar.gz` is
4,678,069 bytes, version `ZFfolZmHOGOaoXAGZRzc_n2HPEl_W9zp`, with S3 ETag and
local MD5 `3f537b7dca0179c7e67d796d4c7c920f`. CloudFront distribution
`E1V1AX0S4NBYGI` completed invalidation `IA97IL5443HZ7MJ1MXSE998BCP`. Headless
Chromium at `https://wot-game.arcadian.cloud/` observed a secure context, zero
failed requests, `web-app.tar.gz` refetched at 4,678,069 bytes, document title
`Eye of the World - v2026.02.17a`, service-worker scope
`https://wot-game.arcadian.cloud/`, an unstretched native `480x320` canvas at
aspect `1.5`, and the Eye of the World title menu. The overlay-clear bridge was
exercised live with real trusted mouse input: zero clears while hovering the
screen, then one each as the mouse left the canvas, as a press was released
outside it, on `blur`, and on `fullscreenchange`, every one of them consumed by
the Python frame loop. Evidence:
`docs/qa/redbox-farm-order-deploy-2026-08-30-live-title.webp`. No live gameplay
smoke past the title menu was performed in the browser; the danger-overlay and
WN03 state evidence above comes from the pinned engine locally.

## Deliverables

### Completed Phase 1

- [x] Versioned campaign, gameplay, map, mission, scene, and asset models with exported schemas.
- [x] Canon, character, location, beat, and adaptation specifications.
- [x] Multi-level LT adapter with ordered chapter progression and typed event lowering.
- [x] Cross-reference, reachability, narrative-boundary, asset, event, and determinism checks.
- [x] LT-backed contracts for movement costs, story-critical survival, and resource formats.

### Phase 2 graybox gate

- [x] Four compiled chapters using two shared layouts and four narrative variants.
- [x] Tutorial, escape, defense/rescue, and fog/search/escape objective structures.
- [x] All 36 current scenes load and execute through the pinned LT event runtime.
- [x] Per-chapter victory commands and objective truth tables pass.
- [x] Tam's chapter-specific `TrueMiracle` survives an actual lethal LT combat-solver strike at 1 HP.
- [x] Real `S`, `X`, `X` input drives title screen → New Game → Chapter 0.
- [x] Public LT triggers/actions execute Talk, Visit, Rescue, reinforcement, Search, equipment, escape, and ending chains.
- [x] All 36 current authored scenes plus title, intro, and map states are captured in 45 native 240×160 frames, hash-bound, and visually inspected.
- [x] Independent graybox gate review has no blocking findings.

### Phase 3 narrative gate

- [x] A Grok CLI-owned fresh story pass establishes home, friendship, festival anticipation, intrusion, rupture, communal cost, solitary responsibility, and reunion.
- [x] Character voices are concise and distinct; UI instructions are presented as tutorial narration rather than character dialogue.
- [x] All missions and scenes reference stable source beat IDs with direct, inferred, or gameplay-invention status.
- [x] The Emond's Field defense remains explicitly inferred in metadata and the adaptation ledger without breaking diegetic presentation.
- [x] The final scene stops before all Chapter 6 material.
- [x] A later book-grounded pass realigns talk to private EotW chapter 1-5 locators (unmoving cloak, shared rider fear, Ghealdan news, Tam's hidden sword, Narg).
- [x] A `playable-scene-writer` skill owns first-time-player talk separately from beat extraction. Opening is arrival (father, cider, festival, rider, Find Mat); Egwene and Fain no longer assume the book; pickups and combat quotes carry care or pressure instead of captions.
- [x] A source-grounded story pass restores the book's throughline: wolves and the rider's hatred, Mat's shared scare, gleeman as wonder, Fain staining the festival, stew then hidden sword then the door, Winternight as ruined visiting-night, Tam still calling the wound a scratch at the fade.
- [x] Three story assets generated with Codex (`gpt-image-2`): arrival road with village roofs and a faceless hooded rider, two neighbor portraits replacing graybox civilians, and the inn as a night refuge. Chapter 2 rescue talk uses the night inn.

### Phase 4 visual gate

- [x] Approved portrait sources and variants are generated from the visual bible.
- [x] Approved story backgrounds are generated from the visual bible.
- [x] Deterministic processing produces LT-compatible registered assets.
- [x] All processed assets pass dimension, hash, provenance, and reference checks.
- [x] Fresh in-engine screenshots show consistent identities, readable text, and no clipping or color-key defects across all authored scenes and 27 distinct GUI/gameplay flow states.
- [x] The two reusable map layouts render with original semantic terrain variants across day, moonlit, and firelit states without changing topology.
- [x] Twenty-four locally AI-generated four-view map-sprite sources replace the rejected programmatic character art; deterministic processing supplies passive/active sheets, directional movement, LT team recoloring, identity-specific silhouettes/gear, exact dimensions, and source/stand/move hash locks.
- [x] Approved pinned-engine patch: phase-inert character units retain the `Tile` tag that suppresses empty team phases, while the map HUD resolves their portrait-backed hover panel directly from the board. Purpose: every visible character receives the same nameplate without making inert villagers selectable or adding an NPC phase. A real-input pinned-engine run hovered phase-inert Egwene and captured her portrait, name, and HP panel at native `240x160`; review evidence is `.codex-image/asset-completeness-review/phase-inert-hover.png`.
- [x] Book-accuracy portrait correction replaced five generic cast-sheet busts with hash-locked identity edits whose native LT faces retain their canonical cues: Mat's red neckerchief, Perrin's smith apron and square hammer, Egwene's braid and pale apron, Thom Merrilin's many-colored patchwork cloak, and Padan Fain's cap, pack straps, and staff. Review evidence is `.codex-image/book-accuracy-portraits/processed-contact.png`.

### Phase 5 balance/package gate

- [x] One complete automated input-driven playthrough reaches the ending card without a soft lock using only real pygame key events.
- [x] A repository-local mission-coherence skill defines a full-level, first-time-player review across narrative setup, visible cues, available actions, objective gates, feedback, and terminal outcomes.
- [ ] Three human playthroughs pass after final balance changes.
- [ ] The slice duration is verified against the 45–75 minute target.
- [x] Save/resume, game-over recovery, and packaging are verified with the pinned runtime.
- [x] Six original procedurally synthesized tracks plus the declared title arrangement are hash-locked, assigned to title/phase/Game Over slots, decoded, and packaged through the pinned runtime.
- [x] Four original, procedurally synthesized sound effects are hash-locked, referenced by real LT `sound` commands, decoded, and packaged through the pinned runtime.
- [ ] Human difficulty and tutorial-clarity review is complete.

### Initial Phase 6 portability gate

- [x] Campaign party, leader, title art, story protection, unit roles, resource provenance, item placement, smoke checks, and title entry are data-driven rather than Winternight-ID driven.
- [x] The original one-chapter Signal Lantern fixture compiles twice to the same hash without Winternight, Rand, Tam, or Trolloc identifiers.
- [x] Signal Lantern initializes through the pinned engine and reaches its declared entry chapter through real title input.
- [x] The repository exposes the story-neutral `storygen compile-pack --content-root ... --output ...` command.

### Completed Phase 0

- [x] Empty repository initialized with a pinned LT-Maker submodule.
- [x] Repository constitution and bounded command surface defined.
- [x] Six repository-local skill skeletons completed and validated.
- [x] Legally clean placeholder assets and minimal structured specification added.
- [x] Deterministic compiler, validator, smoke check, and report CLI implemented.
- [x] `build/minimal.ltproj` loads and initializes through the pinned LT engine.
- [x] Start dialogue, victory trigger, and end dialogue verified structurally and at runtime.
- [x] Determinism and reference tests pass.
- [x] Linux bootstrap, editor, and engine launch commands documented.

## Engine decision record

- Requested upstream `https://github.com/rainlash/lt-maker.git` returned “repository not found” on 2026-08-26.
- Canonical documentation points to `https://gitlab.com/rainlash/lt-maker.git`; that official repository is used instead.
- Pinned commit: `1820e585450f6f47605aebd686b2a3f13af181f0` (2026-08-20, engine version `2026.02.17a`).
- Pinned runtime: CPython 3.11, matching the engine's supported-version guard and CI documentation.
- Adapter strategy: construct database/resource prefabs with LT's own models, serialize them using LT catalogs, and test output with LT's own loaders and event parser. Direct JSON is limited to deterministic metadata/report manifests and is isolated in the adapter.
- Engine patch: `patches/lt-maker-winternight-runtime.patch` (SHA-256 `01904392e35d532c69da879bafd1dec74c6446e6b9707eeb34d56148de0faf83`, superseding `d4287fb8238def29bd0ecdefd35095a40dc6549eb63b8eeccda79cb592b9c46f`) is the approved, reproducible patch over pinned LT commit `1820e585450f6f47605aebd686b2a3f13af181f0`. `make bootstrap` applies it; every CLI engine check verifies the patch bytes. It adds generic level-var-driven forced tutorial movement, count-aware manual-End confirmation, the pre-existing Tile-unit hover treatment, and the opt-in objective-panel emphasis pulse. Purpose of the pulse: LT redraws the persistent objective panel every frame and hides the whole map HUD during events, so a changed objective cannot be made unmissable from content alone. `UIView` consumes the `_objective_flash` level var once inside a legal map state and then blinks the panel three times at `1.4x` before easing back to `1x` over 900 ms; nothing about the settled panel's styling, position, or text changes, and no serialized engine format changes. Verification: `test_objective_panel_blinks_then_settles_after_a_flash_request` pins the blink/grow/settle windows and the native-width bound, `test_engine_patch_matches_tracked_patch` pins the patch bytes, and native `240x160` frames `docs/qa/wn02-objective-flash-{blink-out,grown,easing,settled}-native-1x.png` were rendered from the pinned engine after a real east-house `Visit` and visually inspected.

## Gate evidence

Successful commands on Ubuntu 24.04 / CPython 3.11.13:

- `make bootstrap` — installed the pinned project and official LT editor requirements.
- `make check` — validation, compilation, Ruff, 84 tests, four-level engine smoke, real title input, full mission action traversal, lethal Tam combat, chapter journey, editor smoke, determinism, full real-input completion, suspend/continue, expanded GUI navigation, game-over recovery, exhaustive authored-scene capture, isolated package smoke, and final report all pass on the current build.
- `make portability` — the unrelated Signal Lantern pack compiles deterministically, contains no Winternight-specific database IDs, initializes through the pinned engine, and enters its declared first chapter through real title input.
- `make smoke` — all four levels initialize; 36 scenes execute; every intro/outro and win/loss path resolves; all four victory commands execute; and mission truth tables pass in LT's evaluator, including Chapter 0's early-inn redirect and post-Mat entrance unlock.
- `make editor-smoke` — LT-Maker constructed offscreen, loaded the fresh-checkout `build/winternight.ltproj`, and exited with status 0.
- `make capture` — captured all 36 current authored scenes plus the title and each chapter's intro/map state in 45 native-resolution frames and wrote a project-hash-bound `build/evidence/screenshot_manifest.json`.
- `make gui-navigation` — real keyboard input captured the minimap; map menu and help; unit roster; objective; full settings and controls lists; all three unit-info pages; Extras; and all three Sound Room track selections. The audit asserts that visible descriptions and control names cannot fall back to raw localization IDs.
- `make title-flow` — real pygame inputs reached Chapter 0 from the title screen.
- `make mechanics` — all authored non-combat mission chains executed through LT's public trigger and action runtime.
- `make tam-survival` — a real 8-damage Trolloc strike at 8 HP invoked `story_guardian` and left Tam alive at 1 HP.
- `make input-playthrough` — the current contention-free `make check` run used 6,921 real-game-loop frames and completed Chapters 0–3 in 3, 4, 7, and 10 turns. Chapter 0 set `talked_to_mat`, revealed the gold Winespring entrance, set `entered_inn`, and completed without a fetch, inventory, greeting-checklist, combat requirement, enemy unit, or empty AI phase. The journey also exercised Lan and Moiraine combat, all rescues, the farmhouse-approach stage, every search, Rand's lone-Trolloc encounter and fight, chapter saves, and the ending card.
- `make suspend-continue` — suspended Chapter 3 on turn 1 and restored Rand at the same `[1, 7]` position through the real title-menu Continue flow.
- `make game-over-recovery` — triggered a real Chapter 2 failure, captured a readable Game Over frame, and returned to the title screen.
- `make package-smoke` — extracted the deterministic private Linux archive in isolation; every level and scene initialized, the packaged `run.sh` created the correctly titled engine window, and its real driver loop exited cleanly.
- `make music` — seven Ogg/Vorbis tracks from the `2.0` sectional score: `wn_wheel_of_time` is `music_main`, `wn_broken_wheel` is `music_game_over`, Chapter 0 is `wn_hearthlight` on both phases, Chapters 1-2 alternate `wn_black_wind` and `wn_shadow_advance`, Chapter 3 alternates `wn_embers_on_snow` and `wn_last_light`.
- `make sfx` plus the SFX test lane — regenerated four original Ogg/Vorbis cues byte-identically; the pinned LT sound controller decoded, started, and stopped each; and compiled scene events resolve real `sound` commands rather than visual captions.
- `uv run --python 3.11 winternight determinism` — two clean campaign builds produced identical project tree hashes.
- Six invocations of the official skill quick validator — all skill packages passed.
- The official skill quick validator passed the new repository-local `mission-coherence` skill; an independent forward test reviewed Chapter 0 without receiving the known diagnosis.
- `make play` — the GNOME Wayland launch path was previously verified through Mutter's XWayland display `:1`; the exact current launcher was refreshed headlessly and created the correctly titled 480×320 window with a title-frame hash matching the generated and packaged projects.
- `make web-build` plus a headless Chromium probe — Pygbag 0.9.3 loaded the pinned project through CPython 3.12 WebAssembly, initialized music, and rendered the native 480×320 LT title screen without failed requests or page errors. The same probe passed against the public, HTTPS S3 object URL.
- 2026-08-27 browser-audio repair — removed the blocking `pygame.time.Clock.tick(FPS)` call from the Pygbag loop so browser VSYNC can drive frames without starving WebAudio, and made browser music with unbounded play counts use SDL's native `loops=-1` instead of depending on end events. The focused Chromium smoke reached the native title menu from the rebuilt web bundle; the regression test and all 79 tests passed, and the complete `make check` runtime/determinism sequence passed at project tree `36ffa29b51e1acf513e1a137ba564d89012b4cbca544773d289d0bf0c8dacbeb`.
- `make check` after the book-grounded story, semantic-map, directional-sprite, Fire Emblem-style dialogue, pinned portrait-sheet, and static inward-facing portrait passes — the combined four-chapter project passed validation, Ruff, the full automated suite, pinned-engine smoke, real-input completion and recovery flows, deterministic rebuild, all 46 visual captures, isolated packaging, and final report generation at project tree `ca0fdc54793a47b9a4d77ea2b7328abd80e3aab4f8f061425663f9df04e1746f`.
- AI sprite replacement and image review on 2026-08-27 rejected the programmatic campaign art, generated 15 local SDXL/Pixel Art XL four-view sources, and rejected then regenerated identity-drifting Rand, Tam, and Thom candidates. Enlarged source/processed sheets and three native LT map frames were inspected for identity, gear, direction, scale, clipping, chroma, and team recoloring. All 16 asset contracts passed; the full 80-test suite and Ruff passed; and an isolated pinned-engine build produced 182 files, registered all 15 sprites, initialized every level, executed every scene, and exited cleanly at project tree `bf4cd4c638cfd162e40cd734f4c424bbec6b28b2eede01ccaf432e28aa7652dc`.
- 2026-08-27 title-entry pass — original programmatic `WINTERNIGHT` wordmark, 8-frame `PRESS START`, graded Westwood night panorama, attribution `original work`, and original GBA-style title fanfare `Lanterns in First Frost`. No Blind Guardian, Fire Emblem, or LT-default quotation. `make check` passed at project tree `f36c46c090979597888aba31de8cb9cda72663e2f9f2e356ae9934b344cc0058`.
- 2026-08-27 computer-use screen review — the live web build plus 74 current evidence PNGs were reviewed at native and 2× presentation. The pass removed web-only Debug/FPS exposure; replaced the single-color bitmap font with deterministic two-layer outlined glyphs and higher-contrast palettes; corrected map HUD, settings, roster, objective, inventory, action, and combat text; added player-facing weapon-type icons; kept UI portraits inward-facing; and added textured civilian portrait treatment. The published web bundle was reloaded and inspected after rebuilding.
- 2026-08-27 title-score swap (user-directed) — replaced the title fanfare with a GBA-style chiptune arrangement of the main theme from Blind Guardian's "Wheel of Time" (`wn_wheel_of_time`, displayed as "Wheel of Time" in the Sound Room). The user removed the "no Wheel of Time adaptation music" constraint from `design/music.yaml`; the arrangement is now declared `third_party_arrangement` in the design, `assets/music/PROVENANCE.md`, `docs/music.md`, and the music tests, and the legal-distribution risk is recorded under Blockers and risks. The full `make check` lane passed, which also unblocked two pre-existing in-flight font-feature breaks: the Signal Lantern fixture was missing `assets/fonts/DepartureMono-Regular.otf` (copied with its OFL license), and `campaign_lt_adapter.py` now emits descriptions only for custom region commands declared by the campaign.
- 2026-08-27 Codex imagegen sprite restart — the user selected clean-heroic Rand candidate 2 from five original directions; that source and fourteen separately generated `gpt-image-2` four-view sheets replaced the full map-sprite roster. All 15 source hashes and 30 deterministic LT stand/move hashes passed, `make validate`, compilation, Ruff, all 83 tests, pinned-engine smoke, title flow, mechanics, Tam survival, and `make capture` passed. Four fresh native LT map frames were inspected for scale, silhouette, gear, palette, chroma, and clipping. The user then reviewed and approved all 15 compiled standing and four-direction movement animations at native and enlarged scale in the LAN animation gallery. The complete `make check` lane stopped at `make journey`; a focused rerun reproduced the pre-final-chapter transition failure after Chapter 0.
- 2026-08-28 Chapter 0 FE8-informed attack tutorial (user-directed) — reduced the cider errand to one cart-to-cellar trip, then makes Mat player-controlled and spawns an inert enemy raven. FE8U `bmpatharrowdisp.c` and shipped Easy Mode video at 02:58-03:02 informed thin static cyan two-tone 16x16 route glyphs below units; only the required destination tile remains gold. Rand is locked to `[10,7]`, Mat to `[11,10]`; other units, cancel, and wrong-tile commits are rejected, while manual End warns with the exact remaining-unit count. Both real Attack flows use a range-2 `StoneThrow` projectile and the systemic unboxed ivory `MapMiss` badge; `set_combat_script;miss1,end` leaves the raven at 22/22 HP. After both misses, enemy phase moves the raven no-follow to `[19,8]`, visibly crossing the right edge before removal and Moiraine. Temporary stones are removed and Rand's bow is restored. Native captures cover both routes, throw, MISS badge, End confirmation, and edge flight.
- 2026-08-28 pinned-engine tutorial-control patch verification — the approved patch reads `_forced_move_{unit,position,layer}`, gates unit/destination commits, hides the route before locomotion, resets an interrupt-finished forced unit, and safely clears an unreachable lock. Manual End counts unfinished selectable player units and asks `You still have X unit(s) to move. Are you sure you want to end your turn?`. The tracked patch is applied by bootstrap and verified byte-for-byte. The real-input run completed all six chapters at project tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403` / manifest `0ee30b7357266494c6efe5ec2a7d708eb0631ae334ffe6712dbf7f5d279ccab7`, traversed menu -> weapon -> target -> combat for both throws, and captured every feedback state.
- 2026-08-27 selected-A map-sprite cutover — the user selected the compact A study after Sacred Stones reference measurement and Hermes/Twyla Tharp spine refinement. All 15 approved sources now pass through deterministic `lt-ai-map-sprite-3`: 18-pixel human and 20-pixel Trolloc bodies, five-to-eight functional colors, broad pinned team-color masses, retained directional silhouettes, and simplified identity/gear cues. The processing pass now deterministically preserves team colors while capping each tiny subject at eight colors; this corrected over-budget Thom and Trolloc-spear outputs without weakening the contract. The 17 focused asset tests and complete 84-test suite passed; Ruff, validation, pinned-engine smoke, title input, mechanics, Tam survival, campaign journey, editor loading, determinism, real-input playthrough and recovery lanes, 45-frame capture, isolated package smoke, and final report generation passed. Fifteen compiled four-direction animations were published to the LAN gallery and four isolated native 240×160 map frames were inspected for scale, terrain contrast, team recoloring, silhouettes, and clipping at project tree `65165619bdb92e53ecdd39ad7ad810b5905ecd1272aae2aa8d36a505e9d8efd2`.
- 2026-08-27 music arrangement rewrite (user-directed) — the previous score format applied one 8-step motif, one static pad, one 4-step bass, and one of two drum patterns to every bar of a track, which is what made the set sound basic. `design/music.yaml` is now a `2.0` tracker-style score: named harmony blocks with per-chord durations, sixteenth-grid phrases with real note lengths and rests, chord-relative bass, chord-tone arpeggios, accompaniment and multi-bar drum patterns with end-of-section fills, and an ordered `form` assigning five instrument roles plus drums and a `dynamic` scalar per section. `music_pipeline.py` was rewritten to match: band-limited additive wavetables (no more aliased pulse leads at 22.05 kHz), ADSR plus vibrato, detune and brightness-decay per voice, seven percussion lanes with high-pass and low-pass shaping, a GBA-style feedback delay bus, and an RMS-plus-soft-knee master stage that replaced the old peak-only normalization. Every track is now a 45–70 s multi-section arrangement instead of a 24–39 s loop: Wheel of Time (intro/verse/prechorus/hook, 58.8 s), Hearthlight Before Snow (opening/verse/bridge/outro, 64.0 s), Black Wind at the Palisade (approach/drive/surge/breach/tag, 61.0 s), and Embers Under Snow (lament/drift/rest, 68.6 s). Measured section RMS now arcs 4.9–10.5 dB across each form. A harmony audit against every chord removed three unintended clashes and kept the deliberate Phrygian flat-second, tritone, and major-seventh colours. Delivered peaks sit at -7.7 to -6.4 dBFS with RMS inside 0.2 dB across all four tracks, and the loop-boundary ramp went from 8 ms to 20 ms because Vorbis ringing at the file boundary scales with the surrounding energy. The complete `make check` lane passed at project tree `8bd3f078d30034fc21688375cfe606e254d59471101fed4030218374b70a2fd7`.
- 2026-08-27 level-playtester subagent design — added a repository-local specialist that runs one level across a default 20-trial matrix (`direct`, `cautious`, `aggressive`, and `exploratory`), requires hash-bound checkpoint provenance, uses only posted pygame inputs and visible planning state, separates game failures/soft locks from harness and environment errors, records per-run and aggregate balance evidence, and preserves human-only judgments. The reusable `_run_input_flow` now accepts and reports an explicit RNG seed, frame deadline, and start level. The official skill validator passed; a Chapter 2 forward test initially found the contract non-executable, then passed after the design added a disposable target-level planner/writer, strict unavailable-action failures, synthetic-start dependency proof, canonical checkpoint hashing, and the exact reusable harness call. Existing suspend/continue and game-over recovery flows passed with the new evidence fields. The complete `make check` lane passed with 91 tests at project tree `994516904cf414e57909f9e9a283a0c5855fee6b55c44629a1d3fdc98560fe9d`. No 20-run level sample was executed because the user has not selected the target level.
- 2026-08-27 phase-music and failure-cue expansion (user-directed) — web research into the published *Sacred Stones* Sound Room inventory established the GBA-era functional taxonomy: six player-phase map themes, six enemy-phase map themes, an NPC-phase theme, and a Game Over cue across 69 tracks. Measured against that, the slice had two concrete gaps, both now closed. First, every chapter named the same track for `player_phase` and `enemy_phase`, so pinned LT's phase helper never crossfaded and the engine's horizontal re-sequencing was dead code. Two enemy-phase themes were composed as passacaglias — a fixed ground bass and chord cycle with variation supplied only by the upper voices, which reads as sustained pressure rather than a journey: `wn_shadow_advance` ("Shadow on the Snow", 53.3 s, A Phrygian/126 BPM to match Black Wind) and `wn_last_light` ("The Last Light", 54.9 s, C-sharp/70 BPM to match Embers Under Snow). Key and tempo are matched deliberately because LT crossfades phase music over 400 ms with no beat matching; a test now locks that pairing. Second, `music_game_over` was hardcoded to `None`, so the Game Over screen was silent even though `app/engine/game_over.py` resolves that constant. `assignments.special` was added to the design schema, mapped onto LT's `music_game_over`, `music_promotion`, and `music_class_change` constants, and bound to a new 13.7 s failure cue `wn_broken_wheel` ("The Wheel Turns Away") in the tutorial's key, sized to the 5-15 s sting convention rather than as a map loop. Phase keys are now validated against the four teams LT actually resolves. A harmony audit of all three new tracks found no unintended clashes; delivered peaks sit at -7.8 to -6.4 dBFS with RMS inside 0.21 dB across all seven. A pinned-runtime probe drove `DefaultSoundController` with the engine clock advancing and observed the real state machine: Chapter 0 skips the fade, Chapters 1-2 cross into Shadow on the Snow, Chapter 3 crosses into The Last Light, and the Game Over slot resolves and decodes at 13.71 s. Two committed decode probes were rewritten to compare each decoded length against its authored bar count instead of asserting a fixed 20 s floor, which was an assumption that only held while every track was a long loop. The complete `make check` lane passed at project tree `96bd3a35712d3038e8a0412404fd1418e9a4dba9371309762d2ecd1e049ca544`, with `saw_game_over` true in the recovery lane and all seven tracks registered in the compiled project.
- 2026-08-27 direct-grid map-sprite rebuild — the user rejected every illustration-reduction roster and approved a newly composed, non-shipping Eirika recognizability calibration as the production gate. All 15 prior source designs were discarded and replaced with character-specific horizontal four-view sheets authored as exact 8× enlargements of logical `128×32` strips. `lt-direct-grid-sprite-1` verifies the `1024×256` source geometry and exact pixel enlargement, recovers each `32×32` facing without rescaling its clusters, maps colors to the pinned LT team palette, and assembles the existing stand/move contracts. No official sprite was supplied, traced, spliced, or shipped. All 15 source hashes and 30 processed hashes pass; the 17 focused asset tests, 92-test suite, Ruff, validation, pinned-engine smoke, title input, mechanics, Tam survival, campaign journey, editor loading, determinism, real-input completion/recovery flows, 45-frame capture, package smoke, and report passed. The complete compiled roster and four-direction animations are live in the LAN gallery; four native `240×160` map frames were inspected for scale, identity, terrain contrast, team recoloring, gear, chroma, and clipping at project tree `09832cf53c9154b1a1598eaa4704a2a04b859f3a474b8bfb810f4644ef63890c`.
- 2026-08-27 production web deploy — after the direct-grid roster rebuild passed the complete `make check` lane, `make web-build` staged project tree `09832cf53c9154b1a1598eaa4704a2a04b859f3a474b8bfb810f4644ef63890c` and project manifest `e960e796bbaf3ccd3d53710f8cde188d199899adfe49998be1daea304dd7bccf`. The five-file static payload was synchronized with `--delete` to `s3://winternight-rpg-poc-chrishart0/` in `us-east-1` using AWS profile `personal` and account `933784155053`. The deployed `web-app.tar.gz` version `2ku6GgsLJrJle.iKJiJHyu3cfvVT70Uf` has ETag `268aec2b290f1f807a4431d2833fae57`, matching the local MD5. A fresh Chromium load of `https://winternight-rpg-poc-chrishart0.s3.amazonaws.com/index.html` downloaded the 4,044,030-byte archive without failed app resources, initialized the native `480×320` canvas, updated the document title to the pinned `v2026.02.17a`, and visibly rendered the Winternight `PRESS START` screen. The new repository-local `winternight-web-deploy` skill records the exact build, `--profile personal` S3 sync, checksum, browser-smoke, and evidence workflow; the official skill validator passed.
- 2026-08-27 reference-controlled title-logo pass — replaced the programmatic wordmark-only treatment with a side-by-side Great Serpent/Wheel emblem and deterministic `WINTERNIGHT` lettering. Four local SDXL + Pixel Art XL + Canny batches (16 candidates) were reviewed at source scale and in the native 240×160 LT title frame; the selected seed `47293` uses the licensed Tor Books Wheel SVG as an exact alpha-geometry mask, a 16-color 32px logical reduction, and 2× nearest-neighbor delivery. Source, reference, and output hashes plus CC BY-SA 3.0/Open RAIL-M provenance are locked in `design/asset_manifest.yaml`. The 17 focused asset tests, all 92 tests, Ruff, pinned-engine smoke, real title input, journey/input/suspend flows, isolated GUI navigation, 67-frame capture, package smoke, and report lanes passed. The repository-local `vision-asset-loop` skill and its deterministic-seed local generator passed the official skill validator. Aggregate `make check` was invoked in parallel and serialized forms but concurrent external compiles replaced individual generated resources during long runtime lanes; GUI navigation and capture passed when rerun alone, while a later game-over retry encountered the same external build-directory race.
- 2026-08-27 browser page-load splash — web adapter `0.3` copies the hash-locked selected seed-`47293` Dragon Wheel source beside the generated Pygbag page, precaches it in service-worker cache `v3`, and renders it with `WINTERNIGHT` / `TURNING THE WHEEL` inside the handheld screen before the game archive finishes loading. A canvas-dimension observer removes the splash after Pygame establishes the real 480×320 surface. `make web-build`, all six focused web-export tests, all 94 tests, and Ruff passed. A throttled Chromium run observed the splash with a 1×1 pre-runtime canvas, then the splash removed and the native title screen rendered on the 480×320 canvas with document title `Winternight: A Tactical RPG Vertical Slice - v2026.02.17a`. The serialized aggregate check later reached the input playthrough but encountered the already-recorded concurrent-compile race when `farm_ruined.png` disappeared from the generated project.
- 2026-08-27 fullscreen PWA and mobile deploy — the responsive shell now occupies the full `390×844` phone viewport with no overflow, uses `viewport-fit=cover` and safe-area spacing, requests browser fullscreen from the first game-control gesture where supported, and installs with a fullscreen/standalone web manifest, 192px/512px icons, and activated service-worker cache `winternight-pwa-v4`. Desktop retains the handheld presentation and now shows the explicit key legend `Move Arrow keys · A X · B Z · Start S · Select Backspace`. The complete `make check` lane passed all 94 tests and runtime, determinism, capture, package, and report checks. `make web-build` staged project tree `249735c914ef12441e491e16646d7cd895601148021154559e0b7092c81903de` and project manifest `e04d6834a65a1ef719a4949437531e4c5968568803f23eb1c90973f78fdd1fc9`; the ten-file payload was synchronized with `--delete` to `s3://winternight-rpg-poc-chrishart0/` using AWS account `933784155053`. Deployed `web-app.tar.gz` version `riJoUcPkjMO3HcOAIIJtjltfr84aM4gc` has ETag `0cef93ccb8223cf299ca4b7a00c66e98`, matching the local MD5. Fresh production Chromium checks at `https://winternight-rpg-poc-chrishart0.s3.amazonaws.com/index.html` observed the activated service worker, fullscreen manifest, native `480×320` canvas, `4,092,478`-byte game archive, complete phone-viewport shell, visible desktop key legend, and title `Winternight: A Tactical RPG Vertical Slice - v2026.02.17a`; the mobile screenshot is `/tmp/omp-sshots-1568d6553f0d18bc.webp`.
- 2026-08-27 mobile tap-input deploy — direct taps and drags on the visible game canvas now flow through Pygbag's DOM mouse bridge into LT's existing menu hit-testing and map cursor path; the on-screen Start, Select, D-pad, A, and B controls use the browser keyboard bridge, directional holds repeat, system buttons are 44px tall, and the mobile bezel explicitly says `TAP SCREEN TO CHOOSE`. The fix also scopes presentation CSS to `canvas#canvas`, leaving Pygbag's hidden `canvas3d` hidden instead of letting it intercept every control tap. The complete `make check` lane passed all 100 tests and every runtime, deterministic-build, capture, package, and report check. `make web-build` staged project tree `97cab368e263dd9335e9904e76dc41d17181a8381596240de4d0e22b3b9f3761` and project manifest `7aa39621849bebe9e0d437dbebb6209de5530fdf02f04c587823df7b577888b1`; the production payload was synchronized with `--delete`. Deployed `web-app.tar.gz` version `puTgy4.3OBHCk5OK.kxnmj9L50KeNY8z` has ETag `e8c6956baf5ba2c1247ded1a0cc87639`, matching the local MD5, and is `4,101,926` bytes. Fresh production Chromium at `390×844` verified a full-window shell with no overflow, a tappable Start button, direct-tap New Game menu selection, B returning to the prior menu, D-pad selection movement, and A confirmation into Extras; screenshots are `/tmp/omp-sshots-1568e73bd06aebf5.webp`, `/tmp/omp-sshots-1568e74add6aebf6.webp`, and `/tmp/omp-sshots-1568e75fdc6aebf7.webp`.
- 2026-08-28 scrollable cutscene history — the browser shell's nonfunctional `Select`/`Backspace` control is now a visible `Log` button mapped to LT's native `INFO` input (`C` on keyboard/controller X). During an active cutscene it opens LT's dialogue history; D-pad/arrow input scrolls earlier lines. A real Chromium run entered Chapter 0, advanced six boxes, opened the log through the rendered button, and visibly scrolled from “I wouldn't doubt your word” back to “A rider. A stranger.” All eight web-export tests, the serialized `Dialogue Log` control-label contract, Ruff, compilation, and the six-level pinned-engine smoke pass. The aggregate `make check` reached 111/112 tests before the unrelated music-assignment test failed while looking up a level-qualified intro event by its bare scene ID.
- 2026-08-28 FE8 audio-system audit — compared the pinned LT paths with FE8U's song catalog, Prologue/Chapter 1 event cues, menu navigation, help, and minimap sound calls. The campaign now uses LT's native intro-event `music`, phase, battle, title, promotion/class-change, and Game Over slots; dialogue uses LT's normal talk-blip path. Twenty-four original procedural effects expand to 57 exact LT runtime IDs covering title/menu navigation, save, info/minimap, dialogue, phases, combat, progression, items, healing, movement, and stage clear; no LT/FE8 sample audio was copied. An isolated 276-file compile passed the 41 focused audio/event/web tests and a full real-input campaign playthrough. An isolated Pygbag 0.9.3 Chromium run reached the Chapter 0 Quarry Road cutscene at native 480×320 with WebAudio `running` and a nonzero 512-sample output buffer (RMS 0.041, peak 0.081). The browser loop now non-blockingly caps LT work at 60 Hz on high-refresh focused tabs. Aggregate `make check` could not produce stable evidence while other active sessions repeatedly rewrote Chapter 0 content and replaced the shared build during verification; use the isolated evidence until those sessions settle.
- 2026-08-28 fullscreen mobile gameplay deploy — web adapter `0.5` adds an explicit mobile `Full screen` mode and automatically enters it from the rendered Start control. The mode removes the handheld chassis, preserves the native 3:2 game image without distortion, requests browser fullscreen plus landscape orientation where supported, and overlays every touch control above gameplay without shrinking the canvas. Direct taps select LT menu items and map positions; taps outside active hit-testable menus now route to LT Back and dismiss them without changing map-click behavior. The complete aggregate `make check` passed all 123 tests plus smoke, title, mechanics, Tam survival, journey, deterministic rebuild, full input playthrough, suspend/continue, GUI navigation, Game Over recovery, capture, package smoke, and report lanes at deployed project tree `a84b023b9a35adc6eaeef402d876fce0e28c942a769b0910b77e25b2b6c6a4de` and manifest `23362989a0f748c16f20bc5335342b8b36efbbc6fa67ab7fb80fe61c853f8e9d`. The ten-file PWA payload, with activated cache `winternight-pwa-v6`, was synchronized with `--delete` to the production S3 bucket. Deployed `web-app.tar.gz` version `9TEkjtmuncw1XEhOIzLqBi09KU6ujcy_` is `4,446,558` bytes and has ETag `60184993ae6e528de6da8e210b5094a8`, matching the local MD5. Fresh production Chromium at `844×390` verified a `585×390` undistorted canvas, all five control groups as topmost hit targets, Start navigation, direct menu selection, outside-tap dismissal, active service worker, no overflow, and clean exit from fullscreen; selected/dismissed evidence is `/tmp/omp-sshots-1569b4b0db7b023a.webp` and `/tmp/omp-sshots-1569b4b1a9fb023b.webp`.
- 2026-08-28 mobile orientation refinement deploy — landscape mobile now removes the residual shell border and stretches gameplay to the complete `844×390` viewport; the D-pad and A/B controls remain topmost touch targets over gameplay. Fullscreen landscape moves the small `Log` and `Start` controls together at the bottom-right as `46×22` buttons instead of covering the game center. Portrait mobile retains the handheld layout and shows a bottom `Rotate your phone for a wider view` prompt only in portrait; Dismiss hides it immediately and persists the choice in `localStorage`. The focused eight-test web-export lane and Ruff passed, and the complete repository verification passed all 132 tests plus smoke, title, mechanics, Tam survival, journey, deterministic rebuild, full input playthrough, suspend/continue, GUI navigation, Game Over recovery, capture, package smoke, and report lanes at deployed project tree `9a431aa5106129951db522e037fab935b0f0f2b6798fcb061d9a7925472a6fa4` and manifest `07389a6a8a62f0615564067d347a4b9daf9bac6b5495e730aeff7f3ce7792ee6`. The production S3 payload was synchronized with `--delete`; `web-app.tar.gz` version `9jRdETKvzQowuvLm6CHvuf0cvzmcegqG` is `4,446,958` bytes with ETag `3523ae4423e704e7ab6da9293874c288`, matching the local MD5. Fresh production Chromium verified the portrait prompt and persistent dismissal at `390×844`, then a borderless `844×390` canvas with every overlay control tappable, no overflow, the prompt hidden, and an activated service worker. Evidence is `/tmp/omp-sshots-1569ccb8fe6bc6ea.webp` and `/tmp/omp-sshots-1569ccdfd03f42f7.webp`.
- 2026-08-28 player-facing title and ending copy (user-directed) — renamed the game from **Winternight** to **Eye of the World** across LT metadata, the generated title wordmark, Pygbag document metadata, PWA install metadata, loading splash, handheld shell, and web-build title. The final ending card now reads `Want more? Ping me on X(@X_) with feedback.` A native pinned-engine capture verified the complete CTA on the ending background; a fresh Chromium load verified the `480×320` game canvas, `Eye of the World - v2026.02.17a` document title, renamed shell, and unclipped title art. `make web-build` staged project tree `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a` with project manifest `e20d63d4cceb81952f5cf2db587fc4cfe8e7cfcf90349554b09576a5b9485601`; all 40 focused campaign/web tests passed. The required aggregate `make check` passed validation, compilation, Ruff, all 146 tests, six-level pinned-engine smoke, and real-input title flow, then stopped in the separately in-flight Chapter 2 redesign because the mechanics driver found no matching `Visit` event for Egwene.
- 2026-08-28 Enter confirm alias deploy — the web keyboard bridge now intercepts physical `Enter` keydown/keyup events and forwards them as LT's existing `X`/A confirm input without changing any player-facing key legend. The focused eight-test exporter lane and Ruff passed; the complete `make check` lane passed all 146 tests plus every runtime, deterministic-build, playthrough, capture, package, and report check at project tree `a93c94652eda1f24d61e03231661797e701d4ed7526c74d57ca2b9999113db3a` and manifest `e20d63d4cceb81952f5cf2db587fc4cfe8e7cfcf90349554b09576a5b9485601`. The production S3 payload was synchronized with `--delete`; deployed `web-app.tar.gz` version `IPsO7r_A2RMz4WiTWZR54fsZs4IiBDFE` is `4,446,956` bytes with ETag `5c56b223b76e1281691c9c4fb4d91e73`, matching the local MD5. Fresh production Chromium focused the canvas, entered the title menu with Start, selected a menu entry, and used physical Enter to open the New Game save screen; evidence is `/tmp/omp-sshots-1569d3e8eebd46c9.webp`.
- 2026-08-28 custom production domain — AWS profile `personal` resolved to account `933784155053`. ACM issued certificate `50f3ff09-6201-41e5-af9e-9bb96c04e84c` for `wot-game.arcadian.cloud` through DNS validation in Route 53 zone `ZPUEIPB6QNCF`. CloudFront distribution `E1V1AX0S4NBYGI` (`d1t6pnc0m8ia3g.cloudfront.net`) serves the existing versioned S3 bucket over TLS 1.2+, redirects HTTP to HTTPS, enables HTTP/2 and HTTP/3, and is targeted by Route 53 A and AAAA aliases. Invalidation `I4SILCX9L01TO22PTEGWA832VW` completed after provisioning. `curl` observed HTTP/2 200 with `Miss from cloudfront`; fresh Chromium at `https://wot-game.arcadian.cloud/` observed a secure context, title `Eye of the World - v2026.02.17a`, native `480×320` canvas rendered at the full `844×390` mobile viewport, activated service worker scoped to the custom origin, the complete `4,446,956`-byte game archive, and no document overflow. Evidence is `/tmp/omp-sshots-1569df88d1dc5af5.webp`. Future S3 deploys must invalidate `/*` on this distribution before live verification.
- 2026-08-28 mobile-landscape cutscene aspect repair and production deploy — web adapter `0.6` leaves widescreen map play unchanged but detects LT's active `event` state stack and renders cutscenes at the largest fitting whole-number backing-canvas scale. At the reviewed `844×390` and `812×375` viewports, the `480×320` canvas is centered in black bars; every D-pad/A/B/Log/Start/Full screen target has zero intersection with the canvas, with 44×44 D-pad, 64×64 A/B, 48×48 Log/Start, and 48px-high Full screen targets. The initial Bateman review graded the stretched/occluded production surface D; iteration 2 independently graded both repaired viewports A− with zero blockers (`docs/qa/cutscene-bateman-review-2026-08-28-iteration-{1,2}.md`). The focused nine-test web lane and complete `make check` lane passed all 153 tests plus validation, Ruff, smoke, real-input, deterministic-build, capture, package, and report checks. `make web-build` staged project tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403` and project manifest `0ee30b7357266494c6efe5ec2a7d708eb0631ae334ffe6712dbf7f5d279ccab7`. AWS profile `personal` resolved to account `933784155053`; the ten-file payload was synchronized with `--delete` to `s3://winternight-rpg-poc-chrishart0/`. Deployed `web-app.tar.gz` version `OnKe7H4NUonvZVrKEBUBU0V3ojkqP3H3` is 4,448,273 bytes with ETag `3423017d0aa4ccf03082abb2c34bf17e`, matching the local MD5. CloudFront distribution `E1V1AX0S4NBYGI` invalidation `ICZ3V5394HIU28LW6WPMCTA1GQ` completed. Fresh Chromium at `https://wot-game.arcadian.cloud/` observed the correct TLS origin, `Eye of the World - v2026.02.17a`, a native `480×320` canvas, visible title/`PRESS START`, service-worker scope at the production origin, a 200 response for the nonzero 4,448,273-byte archive, and no failed requests. The same live session entered the Chapter 0 cutscene at `844×390`, measured an unstretched `480×320` frame at `[182,35]`, confirmed zero control/canvas intersections, and exercised the rendered Log control. Evidence: `docs/qa/web-production-title-2026-08-28-844x390.webp` and `docs/qa/cutscene-production-2026-08-28-844x390.webp`.
- 2026-08-28 unified original-control production deploy — web adapter `0.7` removes the complete landscape `.is-cutscene` descendant-control block, including the square charcoal D-pad, A/B, Log/Start, Full screen, focus, and pressed-state overrides; only the cutscene canvas retains class-specific presentation, so title, map, and cutscene reuse one overlay markup and the original GBA-style control skin. The focused nine-test web lane passed, and the complete `make check` lane passed all 153 tests plus validation, Ruff, pinned-engine smoke, real-input flows, deterministic rebuild, capture, package, and report checks. `make web-build` staged project tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403` and project manifest `0ee30b7357266494c6efe5ec2a7d708eb0631ae334ffe6712dbf7f5d279ccab7`. AWS profile `personal` resolved to account `933784155053`; the ten-file static payload was synchronized with `--delete` to `s3://winternight-rpg-poc-chrishart0/`. Deployed `web-app.tar.gz` version `DtiY8HJYoWIocnpOTNSn4.dB4zVwUe_S` is 4,448,243 bytes with ETag `fbde6e60a2c32fcfda14ce30b5853892`, matching the local MD5. CloudFront distribution `E1V1AX0S4NBYGI` invalidation `IEUHCT8FRQANXKJC9GB685EAG4` completed. Fresh Chromium at `https://wot-game.arcadian.cloud/` observed a secure context, title `Eye of the World - v2026.02.17a`, service-worker scope at the production origin, a 200 response for the nonzero 4,448,243-byte archive, and no failed requests. Public rendered controls started a new game and reached the Chapter 0 cutscene at `844×390`: the native `480×320` canvas remained centered at `[182,35]` in black bars with zero overflow and zero control intersections; one shared shell/control tree remained; no cutscene-specific descendant control rule was present; computed controls retained the original gradient D-pad chrome, round 70px A/B, compact gradient `46×22` Log/Start, and pill-shaped Full screen styling. Thirty-five further rendered A inputs reached map play, where the canvas still filled `844×390` and the same 70px round A/B styling remained. Evidence: `docs/qa/web-production-old-controls-title-2026-08-28-844x390.webp`, `docs/qa/cutscene-production-old-controls-2026-08-28-844x390.webp`, and `docs/qa/map-production-old-controls-2026-08-28-844x390.webp`.
- 2026-08-28 wide landscape cutscene production deploy — web adapter `0.8` keeps LT's centered `480×320` cutscene canvas unchanged and matches the active event panorama ID to deterministic web-only left/right rails cut from the approved 16:9 source painting outside LT's existing 3:2 center crop. Map presentation and the single original D-pad/A/B/Log/Start/Full screen overlay are unchanged. The focused nine-test web lane passed, followed by the complete `make check` lane with all 153 tests, validation, Ruff, pinned-engine smoke, real-input flows, deterministic rebuild, capture, package, and report checks. `make web-build` staged project tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403`, project manifest `0ee30b7357266494c6efe5ec2a7d708eb0631ae334ffe6712dbf7f5d279ccab7`, and two wide panorama pairs under backdrop manifest hash `9587004ef039adfe3c2f64762439877c7f943fac150d3fe5758bdb82b0f9440f`. AWS profile `personal` resolved to account `933784155053`; the exact static payload was synchronized with `--delete`. Deployed `web-app.tar.gz` version `rYcMgiSx.LEfQi66xKqUmh2WnlI.VqGs` is `4,448,497` bytes with ETag `0432df5c3f1d331c74a161dfb0b5a812`, matching the local MD5. CloudFront invalidation `IF4T2HV8G7A0R8K5UCVHQDLDSP` completed on distribution `E1V1AX0S4NBYGI`. Fresh Chromium at `https://wot-game.arcadian.cloud/` observed a secure context, title `Eye of the World - v2026.02.17a`, service-worker scope at the production origin, a nonzero `4,448,497`-byte game archive, and the Chapter 0 Quarry Road cutscene at `844×390`: the native canvas remained `480×320` at `[182,35]`, both `22×160` source rails loaded and filled the side columns, and the original D-pad/A/B/Log/Start/Full screen controls remained visible. Evidence: `docs/qa/chapter-0-wide-cutscene-production-2026-08-28-844x390.png`.
- 2026-08-29 landscape map aspect and portrait Full screen production deploy — web adapter `0.9` removes the `100vw × 100dvh` canvas stretch from landscape and `.is-play-mode`: title, menus, maps, and cutscenes now share the largest fitting whole-number `480×320` backing-canvas scale with centered bars. The original D-pad, round A/B, compact Log/Start, and pill Full screen skin remains. Portrait places Full screen bottom-left and Log/Start bottom-right above the orientation hint; portrait play mode hides that hint and keeps the same controls in nonintersecting bottom rows. Wide cutscene rails now resolve to the canvas height, and Full screen/Dismiss use keyboard-accessible click activation. The focused 11-test exporter lane and Ruff passed. A complete `make check` earlier in the session passed all 155 tests plus validation, pinned-engine smoke, runtime flows, deterministic rebuild, captures, package smoke, and report generation for the deployed project hashes; a final aggregate rerun stopped during validation on a concurrent unpublished `design/missions/village_defense.yaml` edit with empty `failure_conditions`, before reaching this web code. The static release therefore deliberately restaged the last verified 279-file project: project tree `808b96ed89281554bf326af676346fc7aa7d600ddbf921614a12f7c267578403`, project manifest `0ee30b7357266494c6efe5ec2a7d708eb0631ae334ffe6712dbf7f5d279ccab7`, and content hash `a24fd696b02159a00b506915c64150ce295875294fce11465a77b2a23fd4f1cc`. AWS profile `personal` resolved to account `933784155053`; the exact 15-file static payload was synchronized with `--delete`. Deployed `web-app.tar.gz` version `9LrdmRCA37YMW0.dmMng1vtJToLe_iwj` is `4,448,499` bytes with ETag `46e49ab977d471d3fba9cbc17c46b47f`, matching the local MD5. CloudFront invalidation `I1QTZ8DWFRGWBB72KD4DOCV1LR` completed on distribution `E1V1AX0S4NBYGI`. Fresh Chromium at `https://wot-game.arcadian.cloud/` observed a secure context, title `Eye of the World - v2026.02.17a`, native `480×320` canvas backing, service-worker scope at the production origin, a 200 response for the nonzero archive, and no failed game-archive resources. The live `844×390` map in Full screen measured `480×320` at `[182,35]` with exact 3:2 ratio and zero control intersections. The live `390×844` portrait Full screen target measured `116×44` at `[10,712]` with zero intersection against canvas, D-pad, A/B, Log/Start, or orientation hint. Evidence: `docs/qa/map-no-stretch-2026-08-28-844x390.webp` and `docs/qa/portrait-fullscreen-bottom-2026-08-28-390x844.webp`.
- 2026-08-29 village-defense human-note verification — FE8U `src/bmitemuse.c`,
  `src/bmtarget.c`, `src/data_items.c`, `src/bmitem.c`, and
  `src/bmbattle.c` establish that Heal is a staff inventory action with an
  adjacent wounded allied target, encoded range 1, `10 + caster power` healing,
  and staff-use EXP (`10 + cost/use / 20`, 11 for Heal). Winternight copies the
  adjacent ally, consumed-use, and 11-EXP behavior for ordinary herbs while
  deliberately keeping their heal fixed and below Moiraine's; FE8U
  `graphics/map/ObjectType1.png` informed only multi-tile roof/facade/door/shadow
  grammar. The pinned-engine Mat combat contract fired `hunting_bow` through
  the real solver. The interrupt-region runtime test returned a resident
  without a Return command. Native `240×160` captures
  `build/evidence/screenshots/wn02_village_defense-map.png`,
  `-sc_c2_recruit_egwene.png`, `-sc_c2_recruit_mat.png`, and
  `-sc_c2_inn_hold_begins.png` were inspected; the original occupied, empty,
  and fire/rubble tile contacts remain distinct at 1×. Final `make check`
  passed validation, Ruff, all 160 tests, six-level engine smoke, public
  mechanics, deterministic rebuild, the 21,546-frame full real-input campaign,
  suspend/recovery, captures, packaging, and reporting at content hash
  `9f2f5135c8f211c8881f76a117fd716dfbf203b9470df3b9c35293d0d9660dd5`,
  tree `388cac54b7f7703ff21ab290eb78f99469ec969735fa77d62d553f4223a02081`,
  and manifest
  `9c463c3a971510d19d7e32a5a6f1daeb923612b46d470cdc691a0cc2e5eec334`.
- 2026-08-29 village-defense production deploy — `make web-build` staged the
  same tree/manifest. AWS profile `personal` resolved to account
  `933784155053`; the exact static payload was synchronized with `--delete`.
  `web-app.tar.gz` is 4,451,007 bytes, version
  `FcMOAqWk_BX5uuQpDIK7OKarvH7qyQjO`, with S3 ETag/local MD5
  `fea1c677458db663c87e854a1f65f0c9`. CloudFront distribution
  `E1V1AX0S4NBYGI` completed invalidation
  `IBOB17EOEUMWYXKH86Q6PSDITX`. Fresh Chromium at
  `https://wot-game.arcadian.cloud/` observed a secure context, HTTP 200 and
  4,451,007-byte archive, document title
  `Eye of the World - v2026.02.17a`, service-worker scope at the production
  origin, native `480×320` canvas, and the visible Eye of the World
  `PRESS START` frame.
- 2026-08-29 mobile audio-unlock and portrait Full screen production deploy — web adapter `1.0`. Root cause, measured not guessed: Pygbag's Emscripten runtime opens its audio device during LT start-up, before any gesture, so the browser creates that `AudioContext` `suspended`, and the only unlock in the whole stack is Emscripten's `autoResumeAudioContext`. A headful Chromium probe with `--autoplay-policy=document-user-activation-required`, mobile metrics, touch emulation, and `Runtime.evaluate` `userGesture: false` (so the probe itself grants no activation) captured its exact registrations — `{once: true}` `keydown`/`mousedown`/`touchstart` on `document` and `#canvas` from `cpython312/main.js:1:342309` — and resume stack traces proving this shell spent them itself: `resume ← main.js:1:342616 ← dispatchGamePointer ← canvas pointerdown handler`. The touch controls synthesize untrusted `MouseEvent`/`KeyboardEvent` objects, and a real `touchstart` is not an activation-triggering input event, so all six one-shot listeners are consumed with no user activation and nothing can start audio again; a tap on the plain `Full screen` button still produced a genuine compatibility `mousedown` after `touchend`, which is why music arrived only after fullscreen. The shell now owns the unlock: it wraps `AudioContext`/`webkitAudioContext` before the runtime module loads, keeps a registry of every context, ignores untrusted events, and resumes any suspended context from `pointerup`/`touchend`/`mousedown`/`click`/`keydown` on `window` in the capture phase, never `{once: true}`. Fullscreen keeps `requestFullscreen` and has no audio responsibility, which is test-enforced. Verified A/B against the deployed `0.9` build and the rebuilt `1.0` build under one emulated mobile autoplay policy (`resume()` is a no-op until a trusted activation event, because desktop Chromium permits `resume()` without activation and therefore cannot reproduce the phone refusal): `0.9` refused all six attempts and then stayed `suspended` with `currentTime` 0 and analyser RMS 0 through five canvas taps and three A taps; `1.0` refused the same six untrusted attempts and then went `running` on the first ordinary tap, `currentTime` advancing, analyser RMS 0.88–4.29 with peaks 3–13, in regular landscape `844×390` and portrait `390×664`, with `document.fullscreenElement` null and `.is-play-mode` absent throughout. Portrait Full screen moved off the left thumb's D-pad arc: it was `left: 10px; bottom: 88px`, measured 0–33px under the D-pad column and overlapping the down key outright at `360×600`; it is now centred on the bottom edge below the Log/Start row, measuring no overlap and 67–212px of D-pad clearance, 36px of Log/Start clearance, and 309–455px of canvas clearance at `360×600`, `390×664`, `412×780`, and `430×700`, with `elementFromPoint` returning the pill at its own centre. The dismissible rotate hint moved to the top edge because portrait has no third row that clears the D-pad; play-mode portrait puts the pill in the empty letterbox band above the canvas and play-mode landscape keeps it top-right. The single original D-pad/A/B/Log/Start/Full screen skin is unchanged and the canvas still reports backing `480×320` at CSS `480×320`, ratio 1.5000, integer scale 1 in landscape and play mode. `make check` passed the complete lane at project tree `ac6bcf6048cd03add1b109e8440cd59e391834eb052f1f7dfd13c0c99fe504e9` / project manifest `37825b2528404e4cd2aacd735d9d6cc95a1b8d125c587b16faa681634e519f73`, `make web-build` staged that same tree, and the payload synchronized with `--delete` to `s3://winternight-rpg-poc-chrishart0/` in `us-east-1` using AWS profile `personal` and account `933784155053`. Deployed `web-app.tar.gz` version `G8GS00HZChWS0HUgWR_bs6061L35HgJs` has ETag `8072624cfbb1ab340e52e6acc7154a8e` and `index.html` has ETag `3589b015c4b31d50af2c7036d12ae896`, both matching the local MD5s. CloudFront invalidation `IAYS1OAYDA186B4R30QVJ78R0V` on distribution `E1V1AX0S4NBYGI` completed, and a fresh load of `https://wot-game.arcadian.cloud/` served document title `Eye of the World - v2026.02.17a`, service-worker scope `https://wot-game.arcadian.cloud/sw.js`, the native `480×320` canvas and title menu, with zero failed requests and zero page errors.
  Evidence: `docs/qa/audio-unlock-landscape-2026-08-29-844x390.webp` and
  `docs/qa/portrait-fullscreen-bottom-center-2026-08-29-390x664.webp`.
- 2026-08-29 Nynaeve cutscene bust correction — owner playtest rejected `nynaeve_neutral` as "too young, not the book woman" and specified Jordan's Nynaeve: about 25, the youngest Wisdom the Two Rivers ever accepted, a pouty angry set to the face, and a hand tugging her braid, keeping the braid, blue wool dress, pale apron, and herb pouch. `design/visual_bible.yaml` now reads `nynaeve: [mid_twenties_wisdom, braid_tugging_scowl, long_dark_braid, blue_wool_dress, pale_apron, herb_pouch]`; the removed `young_village_wisdom` anchor is the documented instruction that produced the aging-down, surviving verbatim into the shipped prompt at `design/asset_manifest.yaml:432` as "young village Wisdom". This is a specification correction, not a mechanism fix: nothing parses `identity_anchors` programmatically — `src/winternight_gen/campaign_compiler.py:80` lists the file only as a content-hash input — and the anchors are consumed by prompt authoring per `cutscene-art-author` SKILL.md:21 and references/portrait-sop.md:7. `tests/test_assets.py` passes with the edit and the shipped asset stays valid because its manifest entry still points at the unchanged `wave_c_identity_chroma-v1.png` with its original hashes. The replacement bust itself is **blocked**: `skill://cutscene-art-author` authorizes only `skill://codex-imagegen` for cutscene portraits, and both the codex plugin and the `codex exec` fallback return "You've hit your usage limit ... try again at Sep 3rd, 2026 12:24 PM" for the sole `chatgpt`-mode credential (`~/.codex/auth.json`, `OPENAI_API_KEY: null`, no alternate profile). Zero candidates were generated and the local SDXL path was deliberately not substituted. `docs/nynaeve-portrait-regen.md` holds the ready-to-run prompts, the exact codex invocation, the `/tmp` dry-process harness — proven against `egwene-book-accurate-v1.png`, reproducing its recorded `source_hash`/`output_hash` pair with `size: (160, 112)`, 63 colours, no residual chroma — and the exact `design/asset_manifest.yaml` and `PROVENANCE.md` diffs. Evidence: `docs/KNOWN_ISSUES.md` records the open defect.
- 2026-08-29 Nynaeve book-accurate bust production deploy — owner picked
  glance-aside variant 3 from local Krea 2 Turbo NVFP4. Source landed as
  `assets/generated_sources/nynaeve-book-accurate-v1.png`, processed
  `160x112` / 63 colours under `lt-ai-portrait-6`, hashes locked in
  `design/asset_manifest.yaml`. `tests/test_assets.py` 18 passed.
  `make web-build` staged project tree
  `6bdedd8fd75bf73c901ec64326bda3a609872b4b001672e21ce017cf57590d4a` /
  manifest `3eadff3ff0533d781ed905169dbcc8522bc4dd6b36a5d06a26f5b0794e6d62a2`.
  S3 sync `--delete` to `s3://winternight-rpg-poc-chrishart0/` account
  `933784155053`. `web-app.tar.gz` ETag `01ea2a0398721e50edd34aecf1b41f52`
  matches local MD5. CloudFront invalidation `I2ZAIYQ5E8EM30QLKYXTSE67YP`
  completed on `E1V1AX0S4NBYGI`. Live
  `https://wot-game.arcadian.cloud/web-app.tar.gz` served that ETag.
- 2026-08-29 FE8 movement-occupancy audit — FE8U commit
  `ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb` keeps occupancy in
  [`gBmMapUnit`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/bmmap.c#L33-L35)
  separately from `gBmMapMovement`. Unit movement-map generation supplies the
  unit's terrain costs, movement stat, and unit index through
  [`GenerateUnitMovementMap`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/bmidoten.c#L24-L30).
  [`GenerateMovementMap`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/bmidoten.c#L79-L111)
  records that unit filter and invokes the ARM fill. Its flood step adds only
  terrain cost
  ([executed instructions](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/asm/arm.s#L595-L605)),
  then refuses to enqueue a tile occupied by the opposing faction
  ([C reference](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/bmidoten.c#L113-L143),
  [executed instructions](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/asm/arm.s#L606-L618)).
  The player destination check separately rejects every occupied endpoint
  ([`CanMoveActiveUnitTo`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/playerphase.c#L1033-L1046)).
  Thus enemy tiles are impassable, allied tiles may be crossed but not ended
  on, and adjacency has no extra cost. The current decomp has no
  `MapMovementFill` symbol; the path is `GenerateMovementMap` →
  `CallARM_FillMovementMap` → `MapFloodCoreStep`, while `bmmind.c` owns action
  execution rather than movement-map filling. Pinned LT already matches this:
  `Board.can_move_through` admits empty/allied tiles and rejects visible enemy
  tiles, and its Dijkstra/A* pathfinders call that predicate while adding only
  terrain cost. LT's move state separately rejects every visible occupied
  destination. The focused compiled-village traversal test places Lan at
  `[2,11]`, a Trolloc at `[3,11]`, and targets `[4,11]`: enemy occupancy forces a
  four-point detour that excludes `[3,11]`; changing the Trolloc to an ally
  restores the two-point direct path. The same probe executed inside the live
  Pygbag Python runtime at `https://wot-game.arcadian.cloud/` with identical
  results (`enemy_can_pass=false`, cost 4; `ally_can_pass=true`, cost 2).
  Chromium also retained the `480×320` 3:2 backing canvas and the existing
  D-pad/A/B/Log/Start controls. The focused contract passed again after its
  final simplification; full `make check` completed with 160 tests and wrote
  the report for tree
  `73d1b3f4bdda6480ad7badd83990e98f02aea75d2c68a3acb0bfacfd3a98a87d`
  / manifest
  `93c866ecc21a6770361a4cde41d9e57b72df3b469d3083c8679c924da4192869`.
  No compiler, adapter, vendor patch, generated project, or web payload changed;
  no deployment is required.
- 2026-08-29 full-synthesizer Wheel of Time production deploy — rebuilt
  `wn_wheel_of_time` natively in the schema-2.0 `winternight-music-2` score
  from Songsterr transcription s410588 revision 927374: 48 bars and eight
  sections use all five orchestration roles, eight harmony blocks, 20
  phrase/bass patterns, three arpeggios, five accompaniment patterns, six
  drum kits, sectional dynamics, and deterministic synthesis. The 117.551 s
  Ogg SHA-256 is
  `2751e334aa90510be9236acf08fdc148f05865d381749b263cd1e82bd23bbd5a`;
  title assignment and Sound Room index 1 are unchanged. `make check` passed
  all 167 tests plus the six-level pinned-engine/runtime, deterministic,
  real-input, capture, package, and report lanes at content hash
  `c79db5c43b2ab6397c9b52b4ef091e4988e97e9f2bc707037124fc77f09dea3f`,
  tree `2a47a22ecd873e3e8539f3988a9eb6e6ec867455289cf6eb077e034e40dc5231`,
  and manifest
  `7055fa2597ebfd4c2451209d6c84309f89d8a34961169e02bd65621e2bd3ad43`.
  AWS account `933784155053` received the exact static payload via S3 sync
  `--delete`; `web-app.tar.gz` version
  `kOEGh8P5m_g.icPa9EFNjKVUC1yerV5U` is 4,676,100 bytes with matching
  local-MD5/S3-ETag `2e5949c5e2505a84e6804148f12f9d99`. CloudFront
  invalidation `ICEBQBKNSJZJMUD0JO3QK7N0FK` completed. Fresh Chromium at
  `https://wot-game.arcadian.cloud/` observed HTTP 200 for that archive,
  service-worker scope on the production origin, title
  `Eye of the World - v2026.02.17a`, native `480x320` canvas, and the visible
  Eye of the World `PRESS START` frame.
- 2026-08-29 farm-lad class lines (owner-directed) — Rand, Mat, and Perrin now
  wear three distinct FE8-grounded classes with original names instead of
  `farmer_archer`/`villager`/`villager_sturdy`. FE8U commit
  `ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb` is the cited source: `gClassData`
  in
  [`src/data_classes.c`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/data_classes.c#L1054-L1111)
  supplies Myrmidon `16/4/9/9/2/0`, CON 8, MOV 5, Sword D and growths
  `70/35/40/40/15/20/30`;
  [Thief](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/data_classes.c#L712-L769)
  supplies `16/3/1/9/2/0`, CON 6, MOV 6, Sword E and growths
  `50/5/45/40/5/20/40`;
  [Fighter](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/data_classes.c#L3609-L3664)
  supplies `20/5/2/4/2/0`, CON 11, MOV 5, Axe D and growths
  `85/55/35/30/15/15/15`.
  [`gPromoJidLut`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/classchg-data.c#L5-L29)
  supplies the branches, and the tier-2 entries own the gains
  [`ApplyUnitPromotion`](https://github.com/FireEmblemUniverse/fireemblem8u/blob/ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb/src/bmbattle.c#L1414-L1459)
  adds. Adapted lines, per the owner's mapping: **Swordsman → Blademark**
  (Myrmidon → Swordmaster, gains `+5 HP/+2 Str/+2 Def/+1 Res` plus CON 8→9 and
  MOV 5→6), **Trickster → Nightblade or Highwayman** (Thief → Assassin or
  Rogue, Assassin gains `+3/+1/+2/+2` with CON 6→8, Rogue gains
  `+2/+1/+1 Skl/+2/+2` with CON 6→7), and **Apprentice → Hammerhand** (Fighter
  → Warrior, gains `+3 HP/+1 Str/+2 Skl/+3 Def/+3 Res` plus CON 11→13, MOV
  5→6, and the Warrior bow rank). Names are original; FE8's other Myrmidon
  branch (Assassin) and Fighter branch (Hero) are deliberately not adapted, and
  no art changed — promoted classes reuse the character's existing hash-locked
  map sprite, so no Nintendo pixels enter the tree. Rand's bases move only where
  FE8 defines the class (SKL/SPD 7→9, already-matching CON 8/MOV 5) and keep his
  personal HP/STR/DEF/RES deltas so Chapter 1 and the mandatory Narg exchange
  survive unchanged; Mat takes FE8 Thief SPD 9, CON 6, MOV 6 at unchanged HP 20
  and DEF 3, so the wn02 worst-case one-phase math is untouched; Perrin's
  existing CON 11/MOV 5/SPD 4 already matched FE8 Fighter, so only his weapon
  lock, growths, and class line changed. Mat and Perrin previously had zero
  growths and now progress. Weapon locks are FE8's, with one declared exception
  recorded as `farmboy_class_lines` in `source/adaptation_rules.yaml`: Rand and
  Mat keep Bow and Utility beside Sword so the Chapter 0 stone throws and the
  tutorial Hunting Bow still work; Perrin is axe-locked and Hammerhand adds
  Bow. Compiler surface: `PromotionSpec` plus `CombatSpec.promotions`, a
  `PROMOTION_STAT_NIDS` set that lets promotion gains address CON/MOV (growths
  and mission stat bonuses still cannot), catalog validation that promoted class
  IDs never collide or repeat, and adapter emission of tier-2 `Klass` rows with
  `promotes_from`, `turns_into`, and LT promotion gains. Evidence: an isolated
  279-file compile outside `build/` loaded through LT's own `Database` resolves
  `promotion_options` to `['blademark']`, `['nightblade', 'highwayman']`, and
  `['hammerhand']`, and its six-level pinned-engine smoke passed every level,
  scene, victory command, and loss path with a clean game-loop exit. Real
  pygame input opened the native unit-info pages
  `docs/qa/farmboy-classes-2026-08-29-rand-swordsman-native-1x.png` (Rand,
  **Swordsman**, Skill 9 / Spd 9 / Con 8 / Move 5, unclipped) and
  `docs/qa/farmboy-classes-2026-08-29-mat-trickster-native-1x.png` (Mat,
  **Trickster**, Str 4 / Skill 5 / Spd 9 / Luck 9 / Con 6 / Move 6). Perrin
  stays a phase-inert `Tile` villager with no selectable info page, so his class
  is verified in serialized data and through the engine loader only. `make
  validate`, `make lint`, and the full 175-test pytest suite pass, and a
  complete real-input campaign playthrough on the same isolated build reached
  the ending through all six chapters in order in 22,230 frames. A transient
  wn02 quota loss seen mid-pass came from a parallel session's in-flight
  village-defense edits, not the class pass: an isolated build whose only
  difference was the three original combat blocks failed identically one turn
  earlier, and both cleared once those edits settled. Not run by owner
  directive: `make check`, `make web-build`, and any deploy.
- 2026-08-30 browser music KISS pass, one audible owner — web adapter `1.1`.
  The owner reported two songs at once on the first mission. Root cause,
  measured not guessed, in two independent parts.
  First, the engine part. Pinned LT spreads music over four channel pairs and
  only fades the next pair in when `DefaultSoundController.update` sees *any*
  channel report a finished fade, so the next track can start while an older
  pair is still audible mid-fade. A virtual-clock probe over LT's real
  controller with the browser adapter installed found this in a four-call
  sequence the campaign actually issues — `fade_in(player_battle,
  from_start=True)`, `fade_in(enemy_phase)`, `fade_back()`,
  `fade_in(enemy_phase)` — leaving `Black Wind at the Palisade` and `Shadow on
  the Snow` both audible; 12 of 1,500 randomized transition sequences hit it.
  The browser build hands SDL an unbounded native loop, so such a pair has
  nothing left to end it and keeps looping underneath the new track.
  Second, the page part, reproduced on the deployed artifact: two live
  instances of `https://wot-game.arcadian.cloud/` each played their own track
  with no arbitration — tab A `Shadow on the Snow` in WN01 at output RMS
  0.0357, tab B `Wheel of Time` at the title at RMS 0.0290, both `AudioContext`
  `running`. A background tab, a duplicate tab, and an installed window are all
  reachable by ordinary use, and the older instance cannot be reached from the
  newer one.
  Ruled out by measurement rather than argument: the live build plays exactly
  one track through title to New Game to Chapter 0, soft reset back to title,
  Restart Level, a scripted replay of every phase/battle transition, and 140
  seconds across three loop boundaries; muting LT's 16 mixer channels from the
  live page silenced it completely (output RMS 0.0), so the engine owns all
  page audio; the desktop full-campaign real-input playthrough with the browser
  adapter installed recorded 140 audibility transitions and zero overlap.
  Pygbag resolves `pygame.mixer` to a real wasm SDL2_mixer, not Emscripten's
  JS SDL1 audio emulation whose `Mix_*` exports are present but unused, and
  channel end events do arrive (measured: `USEREVENT+7` delivered after a
  0.133 s one-shot), so the native `loops=-1` replay was kept as the single
  replay owner rather than traded back for event-driven replay.
  Intentionally simplified playback contract for the browser build: one active
  song, explicit replacement on transitions, and the visible page as the only
  audio owner. `web/runtime_main.py` now owns music ownership in
  `_fade_in_browser_music`, which stops every channel pair except the one about
  to become audible before running LT's own fade-in, so pause/resume of the
  same track and LT's within-pair battle crossfade are untouched while a stale
  pair is cut instead of left looping. The generated shell suspends the page's
  audio device on `visibilitychange` while `document.hidden` and resumes it on
  return, reusing the same helper as the trusted-gesture unlock; that unlock is
  still never spent, so the mobile tap-to-unlock fix is preserved.
  Tests: `test_browser_music_keeps_one_audible_track_through_real_transitions`
  drives the pinned controller through the shipped adapter with SDL pause state
  tracked and asserts at most one audible channel per frame plus the expected
  track after each of five real phase/battle transitions — it fails on the
  pre-fix adapter with `(112, [(0, 'Black Wind at the Palisade'), (2, 'Shadow
  on the Snow')])` and passes on the fixed one.
  `test_browser_music_fade_in_replaces_every_other_channel_pair` and
  `test_hidden_page_gives_up_audio_ownership` pin the ownership rule and the
  shell contract.
  Verification: focused 41-test music and web-export lane, `make lint`, and
  every `make check` lane except `input-playthrough` pass, including the full
  pytest suite, pinned-engine six-level smoke, title flow, mechanics, Tam
  survival, journey, editor smoke, deterministic rebuild, suspend/continue,
  GUI navigation, game-over recovery, capture, package smoke, and report at
  project tree `cb75a20015e20cd8d785409466f0c89ac3f5552bb8c91cd6e0220037059ecdf2`.
  `make web-build` staged that project and the fixed adapter into
  `build/web-app/build/web/`. A real Chromium run of that local build reached
  the Chapter 0 Quarry Road cutscene from a fresh New Game with one audible
  channel, replayed the four-call overlap sequence with a peak of exactly one
  audible channel, and showed the device moving `running` to `suspended` to
  `running` across a hidden and re-shown page.
  Not deployed. `make input-playthrough` fails inside `wn02_village_defense`
  with `global frame deadline exceeded`, stuck in an item menu, because that
  chapter is mid-redesign in this working tree — `design/missions/
  village_defense.yaml` was rewritten onto the new untracked
  `design/maps/emonds_field_battle.yaml` template while
  `src/winternight_gen/input_playthrough.py` still carries the migrating
  hardcoded plan. The same harness completed all six chapters earlier in this
  pass against the previously compiled project tree
  `976640584fe63ae1002889da51a524b754e745be24db703c8e5a76a2e06ce0ce`, and no
  file this pass touched is imported by that lane, so the failure is the
  in-flight WN02 work, not the music fix. Deploy once that lane is green again.

- 2026-08-30 combined music/gameplay production deploy — the settled tree passed
  the complete `make check` gate after restoring the tested Chapter 5 optional
  Luhhan/Egwene callback and actionable two-line objectives. `make web-build`
  staged 280 files at project tree
  `3737b2e782598eb77537c81a69ff2234cd3d763158146404dc365e8508a4634f`,
  content hash `6ce3aef58979281d14c15d86ddca0b8f8d45a01c85adc689aff3e2cb56a761fe`,
  project manifest `d28b0a46a79ad5f80a9ca3c1fa4539114ee7ddfdd047cb7e4a89802681b1ac4d`,
  and web adapter `1.1`. The static payload was synchronized with `--delete` to
  `s3://winternight-rpg-poc-chrishart0/` using AWS account `933784155053` and
  CloudFront invalidation `I7Q088IJMIPITQYLM0AOEF9WKA` completed. The deployed
  `web-app.tar.gz` is 4,678,072 bytes, version
  `CuroUNRtG5JHOsxuzPl6nWS0GC3PiPiY`, with matching local MD5/S3 ETag
  `e3e5196832644bcb7ac4e8edbe76ffb1`. Fresh Chromium at the production URL
  loaded `Eye of the World - v2026.02.17a`, registered the production service
  worker, fetched the archive with HTTP 200 and matching length, and visibly
  rendered the Eye of the World title screen at the native 480x320 canvas.
  This deploy also carries Moiraine's three-weave kit, Healing Herbs through
  Item, infinite-durability Tam/Lan blades, and the inert-until-attacked
  top-left Myrddraal in WN02. Human phone listening remains the final check for
  the reported two-song symptom; no post-title live gameplay was claimed.



The authoritative deployed compiled project contains 280 generated files with content hash `6ce3aef58979281d14c15d86ddca0b8f8d45a01c85adc689aff3e2cb56a761fe`, project tree hash `3737b2e782598eb77537c81a69ff2234cd3d763158146404dc365e8508a4634f`, and project-manifest hash `d28b0a46a79ad5f80a9ca3c1fa4539114ee7ddfdd047cb7e4a89802681b1ac4d`.

## Blockers and risks


- The automated playthrough uses the real game loop, keyboard events, pathfinding, menus, combat, saves, and dialogue, but it does not establish human completion time or subjective difficulty. Three timed human runs remain the Phase 5 exit gate.
- Chapter 0's automated route, combat, inventory restoration, raven flight, layer lifecycle, and native Rand/Mat drawn-guide captures pass, but a blind first-time human still needs to confirm that the one-cask handoff, destination arrows, and Rand-then-Mat order are immediately understandable without coaching.
- Automated audio checks prove catalog registration, decode/start behavior, authored-duration agreement, player/enemy phase crossfade through LT's real sound-controller state machine, deterministic delivery, packaged availability, and browser infinite-loop configuration. Headless Chromium has no audible output device, so final focused-tab listening, perceived loudness, enemy-phase transition feel in play, and loop quality remain part of the human listening pass.
- The LT engine repository contains bundled sample projects and engine UI assets with mixed provenance. This project does not copy sample-project data/resources; a later distribution review must separately audit any upstream runtime asset provenance.
- LT's serializer imports editor settings when saving resources, so compiler bootstrap includes the pinned editor dependency set rather than engine-only dependencies.
- Upstream engine PNGs emit benign `libpng` iCCP warnings during headless launch; repository-generated PNGs are not the source of those warnings.
- The title track is a third-party arrangement of copyrighted music (Blind Guardian, "Wheel of Time", released on *At the Edge of Time*, Nuclear Blast, 2010). The user directed the swap and the removal of the prior constraint; any public distribution of this repository would include that derivative work and needs a separate license/legal review before publication.
- The title emblem is a restyled derivative of Tor Books' Wheel title-page/chapter icon, distributed with permission by `jcsalomon/wot-chapter-icons` under CC BY-SA 3.0. Public distribution must retain attribution and ShareAlike terms.
- Concurrent compiles replace `build/winternight.ltproj` atomically but runtime verification reads that directory in place. During this pass, unrelated compiles repeatedly removed a single portrait, icon sheet, or panorama beneath long-running checks; isolated reruns passed. Run the aggregate lane only when no other compiler session is active.
- Desktop Chromium permits `AudioContext.resume()` without user activation, so it cannot reproduce the Android/iOS refusal that caused the silent-until-fullscreen defect. The `1.0` unlock was proved against an explicitly emulated mobile policy plus a real trusted touch tap; a human tap on Christian's phone in regular landscape and portrait is still the confirming check.
- The `nynaeve_neutral` cutscene bust remains the owner-rejected too-young art until the Codex weekly limit resets on 2026-09-03 12:24. `skill://cutscene-art-author` authorizes no alternate generator for cutscene portraits, so no substitute path was taken.

## Screen-by-screen GUI gate decision

PASS on 2026-08-27. The main-agent computer-use pass inspected the live published web build across title, save, Extras, Sound Room, settings, controls, dialogue, map HUD, tactical menus, minimap, objective, roster, and unit-info screens. The current evidence set contains 75 native PNGs: 45 hash-bound authored-scene/title/map frames, 18 GUI-navigation frames, four Mission 1 clarity frames, six full-playthrough menu/combat frames, the chapter transition, and Game Over. Fixes include developer-only Debug/FPS exposure; low-contrast and single-layer text; unreadable HUD and menu values; missing weapon-rank labels; flat civilian portrait treatment; top-anchored, outward-facing, duplicated, or animated portrait defects; clipped labels; internal IDs; and inconsistent player/capture settings.

No release-blocking GUI defect remains in the inspected paths. The current runtime evidence, four Mission 1 clarity captures, and the early-inn recovery capture are bound to project tree `65165619bdb92e53ecdd39ad7ad810b5905ecd1272aae2aa8d36a505e9d8efd2`; the report contains no stale verification. The remaining intentional launcher limitation disables the optional terrain HUD to avoid the documented pinned-engine Continue crash. Human duration, blind first-time confirmation of the revised objective, difficulty, and listening checks remain mandatory Phase 5 work.

## Next bounded action

The stuck enemy-range overlay and the Ruined Farm search-order loss are fixed,
verified, and live (2026-08-30). Two earlier owner browser defects also remain
fixed and live: mobile audio unlocks from an ordinary tap in regular landscape
and portrait without fullscreen, and the portrait Full screen control is clear
of the D-pad. The next bounded action for this report is one human pass on the
live build: select an enemy on a real map, leave the screen, and confirm the red
range is gone, then play WN03 without touching the gold farmhouse tile and
confirm the three supplies and the sword still complete the chapter.
The browser music KISS pass and the settled gameplay tree are verified and live
with web adapter `1.1`. The human check that automation cannot give is one
listening pass on the deployed build: enter
the first mission, force a phase change and a combat, and confirm a single
track at every handoff, then background the tab, reopen the game, and confirm
only the visible instance is audible.
The remaining bounded action from the earlier reports is the book-accurate
`nynaeve_neutral` bust: on or after 2026-09-03 12:24, run
`docs/nynaeve-portrait-regen.md` end to end, judge the processed `160×112`
engine bust at `1×` for adult age, the pouty angry set, and the braid tug, then
land the source, manifest entry, and `PROVENANCE.md` note and redeploy. In
parallel, resume the deferred Phase 5 human exit gates against project tree
`ac6bcf6048cd03add1b109e8440cd59e391834eb052f1f7dfd13c0c99fe504e9`: one blind
first-time Chapter 0 playtest with no coaching, then the three timed human
campaign playthroughs per `docs/playtesting.md`, recording duration,
difficulty, tutorial clarity, and the listening pass. Owner review artifacts
for generated art are staged under `.codex-image/` (roster contact sheets,
animated sprite review, portrait and background contact pages); automated
vision review stood in for human approval and is flagged in
`assets/generated_sources/PROVENANCE.md`.
