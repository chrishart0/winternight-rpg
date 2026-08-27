# Execution plan

## Current phase

Phase 5 — balance and packaging: **automated gate passed on 2026-08-26; human timing remains**. The full four-chapter build, AI visual assets, original music and sound effects, real-input completion route, suspend/continue, game-over recovery, deterministic private package, and fresh visual review pass. The initial Phase 6 portability extraction is also complete through an original second content pack. Human playtesting is still required to confirm the 45–75 minute duration and tune subjective difficulty and audio balance.

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
- [x] All 32 scenes load and execute through the pinned LT event runtime.
- [x] Per-chapter victory commands and objective truth tables pass.
- [x] Tam's chapter-specific `TrueMiracle` survives an actual lethal LT combat-solver strike at 1 HP.
- [x] Real `S`, `X`, `X` input drives title screen → New Game → Chapter 0.
- [x] Public LT triggers/actions execute Talk, Visit, Rescue, reinforcement, Search, equipment, escape, and ending chains.
- [x] Twenty-five native 240×160 title/intro/map/milestone frames captured, hash-bound, and visually inspected.
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
- [x] Three original, procedurally synthesized music tracks are hash-locked, assigned, decoded, and packaged through the pinned runtime.
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
- Engine patches: none. The launcher disables the optional terrain-info overlay as a narrowly scoped compatibility workaround for a pinned-engine suspend/continue restoration crash.

## Gate evidence

Successful commands on Ubuntu 24.04 / CPython 3.11.13:

- `make bootstrap` — installed the pinned project and official LT editor requirements.
- `make check` — validation, compilation, Ruff, 53 tests, four-level engine smoke, real title input, full mission action traversal, lethal Tam combat, chapter journey, editor smoke, determinism, full real-input completion, suspend/continue, game-over recovery, 25-frame capture, isolated package smoke, and final report all passed from a fresh detached checkout of `3ac9846a00571198f87ab4419fd5357c34bb9d5d`.
- `make portability` — the unrelated Signal Lantern pack compiles deterministically, contains no Winternight-specific database IDs, initializes through the pinned engine, and enters its declared first chapter through real title input.
- `make smoke` — all four levels initialize; 32 scenes execute; every intro/outro and win/loss path resolves; all four victory commands execute; and mission truth tables pass in LT's evaluator.
- `make editor-smoke` — LT-Maker constructed offscreen, loaded the fresh-checkout `build/winternight.ltproj`, and exited with status 0.
- `make capture` — captured a fresh set of 25 native-resolution title/intro/map/milestone frames, including secondary cast, combat quotes, village consequences, Tam's wound, and the ending card, and wrote a project-hash-bound `build/evidence/screenshot_manifest.json`.
- `make title-flow` — real pygame inputs reached Chapter 0 from the title screen.
- `make mechanics` — all authored non-combat mission chains executed through LT's public trigger and action runtime.
- `make tam-survival` — a real 8-damage Trolloc strike at 8 HP invoked `story_guardian` and left Tam alive at 1 HP.
- `make input-playthrough` — 11,767 real-game-loop frames completed Chapters 0–3 in 16, 4, 7, and 11 turns; opened the tutorial inventory and equipped Rand's bow through the Item menu; exercised every required conversation, optional archery, Lan and Moiraine combat, all rescues, the farmhouse-approach stage, every search, patrol AI, Rand's lone-Trolloc fight, and chapter saves; captured a real chapter-start/save-selection frame; and reached the ending card.
- `make suspend-continue` — suspended Chapter 3 on turn 1 and restored Rand at the same `[1, 7]` position through the real title-menu Continue flow.
- `make game-over-recovery` — triggered a real Chapter 2 failure, captured a readable Game Over frame, and returned to the title screen.
- `make package-smoke` — extracted the deterministic private Linux archive in isolation; every level and scene initialized, the packaged `run.sh` created the correctly titled engine window, and its real driver loop exited cleanly.
- `make music` — regenerated three original Ogg/Vorbis tracks byte-identically; the pinned LT sound controller decoded and began playback of each, and the generated project assigned them to title/tutorial, Winternight combat, and the return/ending.
- `make sfx` plus the SFX test lane — regenerated four original Ogg/Vorbis cues byte-identically; the pinned LT sound controller decoded, started, and stopped each; and compiled scene events resolve real `sound` commands rather than visual captions.
- `uv run --python 3.11 winternight determinism` — two clean campaign builds produced identical project tree hashes.
- Six invocations of the official skill quick validator — all skill packages passed.
- `make play` — the GNOME Wayland launch path selected Mutter's XWayland display `:1`, created a 480×320 X11 window titled `Winternight: A Tactical RPG Vertical Slice - v2026.02.17a`, and wrote a hash-bound live title capture. The final capture was inspected with vision and matches the generated-project title frame.

The authoritative clean-check build contains 162 generated files with content hash `7b03565be6b53dd9280aaff44b8de1fb58c06273f71cd2b431ec1541cfb340f8`, project tree hash `e477d6392e20301be5ce8fbac1bbb4dd188cd36a79871685c83a7313771fd679`, project-manifest hash `3d8cac77d81275afe231e7c77d3fdcf3e0e3fe9ac11f97d2d4fc0ed5e757d2d3`, and private-package hash `4bbfe6b7ade9a77c2b47f49210d8477e436e16e17a328f61bbb8203e0caff9ce`. Its report contains no stale verification entries. The root checkout's generated build was intentionally not replaced while a user-launched game process remained open.

## Blockers and risks

- The automated playthrough uses the real game loop, keyboard events, pathfinding, menus, combat, saves, and dialogue, but it does not establish human completion time or subjective difficulty. Three timed human runs remain the Phase 5 exit gate.
- Automated audio checks prove catalog registration, decode/start behavior, deterministic delivery, and packaged availability; final perceived loudness and loop quality still benefit from a human listening pass.
- The LT engine repository contains bundled sample projects and engine UI assets with mixed provenance. This project does not copy sample-project data/resources; a later distribution review must separately audit any upstream runtime asset provenance.
- LT's serializer imports editor settings when saving resources, so compiler bootstrap includes the pinned editor dependency set rather than engine-only dependencies.
- Upstream engine PNGs emit benign `libpng` iCCP warnings during headless launch; repository-generated PNGs are not the source of those warnings.

## Independent visual gate decision

PASS on 2026-08-26. Independent review plus the final main-agent vision pass inspected the 25 hash-bound gallery frames and the separate chapter-transition and game-over flow captures. The final gallery is bound to project tree `e477d6392e20301be5ce8fbac1bbb4dd188cd36a79871685c83a7313771fd679`; the chapter-transition, game-over, and visible wounded-Trolloc frames have hashes `98b963e5354d86bb7545ba5019ddadbfc7b2184aef3cb7d3fea7e9f4ef6e3ca9`, `03f650d1a38e7dc40e7686479408b73292b6ddc342b477482eb5b1a3e687f2f9`, and `d8a6b75b777db9c2c6d69a443df8e055867c9e5fa88d4c89e0cae615a31c3dcb`. Review found no clipping, unreadable text, wrong named portraits, broken maps, chroma defects, identity drift, or blocking defects. The transition still proves the chapter-start/save-selection state while the input timeline separately proves all three chapter-to-chapter handoffs. Intentional polish notes are limited to graybox generic villagers, the Trolloc portrait touching the top edge without obscuring its face, and a few evidence frames captured mid-dialogue page. Human duration, balance, and listening checks remain mandatory Phase 5 work.

## Next bounded action

Follow `docs/playtesting.md` for three timed human playthroughs, record chapter durations and usability/audio findings, and adjust only mission balance or objective clarity where the evidence warrants it.
