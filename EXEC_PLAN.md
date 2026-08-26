# Execution plan

## Current phase

Phase 5 — balance and packaging: **automated gate passed on 2026-08-26; human timing remains**. The full four-chapter build, AI visual assets, real-input completion route, suspend/continue, game-over recovery, deterministic private package, and visual review pass. Human playtesting is still required to confirm the 45–75 minute duration and tune subjective difficulty.

## Deliverables

### Completed Phase 1

- [x] Versioned campaign, gameplay, map, mission, scene, and asset models with exported schemas.
- [x] Provenance-safe canon, character, location, beat, and adaptation specifications.
- [x] Multi-level LT adapter with ordered chapter progression and typed event lowering.
- [x] Cross-reference, reachability, narrative-boundary, asset, event, and determinism checks.
- [x] LT-backed contracts for movement costs, story-critical survival, and resource formats.

### Phase 2 graybox gate

- [x] Four compiled chapters using two shared layouts and four narrative variants.
- [x] Tutorial, escape, defense/rescue, and fog/search/escape objective structures.
- [x] All 18 scenes load and execute through the pinned LT event runtime.
- [x] Per-chapter victory commands and objective truth tables pass.
- [x] Tam's chapter-specific `TrueMiracle` survives an actual lethal LT combat-solver strike at 1 HP.
- [x] Real `S`, `X`, `X` input drives title screen → New Game → Chapter 0.
- [x] Public LT triggers/actions execute Talk, Visit, Rescue, reinforcement, Search, equipment, escape, and ending chains.
- [x] Sixteen native 240×160 title/intro/map/milestone frames captured, hash-bound, and visually inspected.
- [x] Independent graybox gate review has no blocking findings.

### Phase 4 visual gate

- [x] Approved portrait sources and variants are generated from the visual bible.
- [x] Approved story backgrounds are generated from the visual bible.
- [x] Deterministic processing produces LT-compatible registered assets.
- [x] All processed assets pass dimension, hash, provenance, and reference checks.
- [x] Fresh in-engine screenshots show consistent identities, readable text, and no clipping or color-key defects.

### Phase 5 balance/package gate

- [x] One complete automated input-driven playthrough reaches the ending card without a soft lock using only real pygame key events.
- [ ] Three human playthroughs pass after final balance changes.
- [ ] The slice duration is verified against the 45–75 minute target.
- [x] Save/resume, game-over recovery, and packaging are verified with the pinned runtime.
- [ ] Human difficulty and tutorial-clarity review is complete.

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
- Engine patches: none. The launcher disables the optional terrain-info overlay as a narrowly scoped compatibility workaround for a pinned-engine suspend/continue restoration crash.

## Gate evidence

Successful commands on Ubuntu 24.04 / CPython 3.11.13:

- `make bootstrap` — installed the pinned project and official LT editor requirements.
- `make check` — validation, compilation, Ruff, 25 tests, four-level engine smoke, real title input, full mission action traversal, lethal Tam combat, chapter journey, editor smoke, determinism, full real-input completion, suspend/continue, game-over recovery, 17-frame capture, isolated package smoke, and final report all passed.
- `make smoke` — all four levels initialize; 18 scenes execute; every intro/outro and win/loss path resolves; all four victory commands execute; and mission truth tables pass in LT's evaluator.
- `make editor-smoke` — LT-Maker constructed offscreen, loaded `/home/chris/git/wot-game/build/winternight.ltproj`, and exited with status 0.
- `make capture` — captured a fresh set of 17 native-resolution title/intro/map/milestone frames, including secondary cast, Tam's wound, and the ending card, and wrote a project-hash-bound `build/evidence/screenshot_manifest.json`.
- `make title-flow` — real pygame inputs reached Chapter 0 from the title screen.
- `make mechanics` — all authored non-combat mission chains executed through LT's public trigger and action runtime.
- `make tam-survival` — a real 8-damage Trolloc strike at 8 HP invoked `story_guardian` and left Tam alive at 1 HP.
- `make input-playthrough` — real pygame inputs completed Chapters 0–3 in 5, 4, 7, and 9 turns and reached the ending card through the chapter save screens.
- `make suspend-continue` — suspended Chapter 3 on turn 1 and restored Rand at the same `[1, 7]` position through the real title-menu Continue flow.
- `make game-over-recovery` — triggered a real Chapter 2 failure, displayed Game Over, and returned to the title screen.
- `make package-smoke` — extracted the deterministic private Linux archive in isolation; every level and scene initialized and its real driver loop exited cleanly.
- `uv run --python 3.11 winternight determinism` — two clean campaign builds produced identical project tree hashes.
- Six invocations of the official skill quick validator — all skill packages passed.
- `make play` — the GNOME Wayland launch path selected Mutter's XWayland display and registered `Winternight: A Tactical RPG Vertical Slice - v2026.02.17a`. A visual capture exposed and drove fixes for missing movement costs and the incorrect LT sprite color key.

Generated evidence: `build/report.json`, `build/REPORT.md`, and `build/evidence/`. Every runtime JSON and screenshot manifest records the pinned engine commit and current project hashes.

## Blockers and risks

- The automated playthrough uses the real game loop, keyboard events, pathfinding, menus, combat, saves, and dialogue, but it does not establish human completion time or subjective difficulty. Three timed human runs remain the Phase 5 exit gate.
- The LT engine repository contains bundled sample projects and engine UI assets with mixed provenance. This project does not copy sample-project data/resources; a later distribution review must separately audit any upstream runtime asset provenance.
- LT's serializer imports editor settings when saving resources, so compiler bootstrap includes the pinned editor dependency set rather than engine-only dependencies.
- Upstream engine PNGs emit benign `libpng` iCCP warnings during headless launch; repository-generated PNGs are not the source of those warnings.

## Independent visual gate decision

PASS on 2026-08-26. The reviewer independently recomputed all 17 screenshot hashes, inspected every processed portrait and captured frame with vision, matched engine/content/project hashes, and verified all 38 provenance entries and 23 reference edges. No visual or asset blocker remains. Human duration and balance checks remain mandatory Phase 5 work.

## Next bounded action

Run three timed human playthroughs, record chapter durations and usability findings, and adjust only mission balance or objective clarity where the evidence warrants it.
