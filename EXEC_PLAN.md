# Execution plan

## Current phase

Phase 5 — balance and packaging: **the fresh story pass plus automated and screen-by-screen GUI gates passed on 2026-08-27; human timing remains**. The full four-chapter build now carries a deliberate ordinary-life-to-Winternight emotional arc, AI visual assets, original music and sound effects, real-input completion route, suspend/continue, game-over recovery, deterministic private package, exhaustive authored-scene gallery, and expanded GUI-navigation review pass. The initial Phase 6 portability extraction is also complete through an original second content pack. Human playtesting is still required to confirm the 45–75 minute duration and tune subjective difficulty and audio balance.

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
- [x] All 37 scenes load and execute through the pinned LT event runtime.
- [x] Per-chapter victory commands and objective truth tables pass.
- [x] Tam's chapter-specific `TrueMiracle` survives an actual lethal LT combat-solver strike at 1 HP.
- [x] Real `S`, `X`, `X` input drives title screen → New Game → Chapter 0.
- [x] Public LT triggers/actions execute Talk, Visit, Rescue, reinforcement, Search, equipment, escape, and ending chains.
- [x] All 37 authored scenes plus title, intro, and map states are captured in 46 native 240×160 frames, hash-bound, and visually inspected.
- [x] Independent graybox gate review has no blocking findings.

### Phase 3 narrative gate

- [x] A Grok CLI-owned fresh story pass establishes home, friendship, festival anticipation, intrusion, rupture, communal cost, solitary responsibility, and reunion.
- [x] Character voices are concise and distinct; UI instructions are presented as tutorial narration rather than character dialogue.
- [x] All missions and scenes reference stable source beat IDs with direct, inferred, or gameplay-invention status.
- [x] The Emond's Field defense remains explicitly inferred in metadata and the adaptation ledger without breaking diegetic presentation.
- [x] Playable dialogue is original paraphrase and the final scene stops before all Chapter 6 material.
- [x] A later book-grounded paraphrase pass realigns talk to private EotW chapter 1-5 locators (unmoving cloak, shared rider fear, Ghealdan news, Tam's hidden sword, Narg) without quoting novel prose.

### Phase 4 visual gate

- [x] Approved portrait sources and variants are generated from the visual bible.
- [x] Approved story backgrounds are generated from the visual bible.
- [x] Deterministic processing produces LT-compatible registered assets.
- [x] All processed assets pass dimension, hash, provenance, and reference checks.
- [x] Fresh in-engine screenshots show consistent identities, readable text, and no clipping or color-key defects across all authored scenes and 26 distinct GUI/gameplay flow states.
- [x] The two reusable map layouts render with original semantic terrain variants across day, moonlit, and firelit states without changing topology.
- [x] Six original map-sprite archetypes provide passive/active poses, four-direction movement, LT team recoloring, and exact pinned-engine sheet dimensions.

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
- `make check` — validation, compilation, Ruff, 60 tests, four-level engine smoke, real title input, full mission action traversal, lethal Tam combat, chapter journey, editor smoke, determinism, full real-input completion, suspend/continue, expanded GUI navigation, game-over recovery, exhaustive 46-frame authored-scene capture, isolated package smoke, and final report all passed in the current workspace.
- `make portability` — the unrelated Signal Lantern pack compiles deterministically, contains no Winternight-specific database IDs, initializes through the pinned engine, and enters its declared first chapter through real title input.
- `make smoke` — all four levels initialize; 37 scenes execute; every intro/outro and win/loss path resolves; all four victory commands execute; and mission truth tables pass in LT's evaluator.
- `make editor-smoke` — LT-Maker constructed offscreen, loaded the fresh-checkout `build/winternight.ltproj`, and exited with status 0.
- `make capture` — captured all 37 authored scenes plus the title and each chapter's intro/map state in 46 native-resolution frames and wrote a project-hash-bound `build/evidence/screenshot_manifest.json`.
- `make gui-navigation` — real keyboard input captured the minimap; map menu and help; unit roster; objective; full settings and controls lists; all three unit-info pages; Extras; and all three Sound Room track selections. The audit asserts that visible descriptions and control names cannot fall back to raw localization IDs.
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
- `make play` — the GNOME Wayland launch path was previously verified through Mutter's XWayland display `:1`; the exact current launcher was refreshed headlessly and created the correctly titled 480×320 window with a title-frame hash matching the generated and packaged projects.
- `make web-build` plus a headless Chromium probe — Pygbag 0.9.3 loaded the pinned project through CPython 3.12 WebAssembly, initialized music, and rendered the native 480×320 LT title screen without failed requests or page errors. The same probe passed against the public, HTTPS S3 object URL.
- `make check` after the book-grounded story, semantic-map, and directional-sprite passes — the combined four-chapter project passed validation, Ruff, the full automated suite, pinned-engine smoke, real-input completion and recovery flows, deterministic rebuild, all 46 visual captures, isolated packaging, and final report generation at project tree `f24c65d9ea03ada85389a7edcd90686d80f65bb3c55647c5b3f238ba0d3cfebe`.

The authoritative current build contains 162 generated files with content hash `f4c513ba563ba2e3afd414e448e553e0e560d2950b0a2cf7add4e68f759e8ca6`, project tree hash `52b5a29d560af2c880ef3bbb24b9d0e4b86297e7543c5b1d91afbc6352ed04b6`, project-manifest hash `e627fdb072e22b7c216dc96482181576074ecfd465ce675fae3de0136660c3dc`, and private-package hash `6e50be148afd6d3d6ee40013c07b2bf12987f1433cb5e2d325a6994020f2d184`. Its report contains no stale verification entries.

## Blockers and risks

- The automated playthrough uses the real game loop, keyboard events, pathfinding, menus, combat, saves, and dialogue, but it does not establish human completion time or subjective difficulty. Three timed human runs remain the Phase 5 exit gate.
- Automated audio checks prove catalog registration, decode/start behavior, deterministic delivery, and packaged availability; final perceived loudness and loop quality still benefit from a human listening pass.
- The LT engine repository contains bundled sample projects and engine UI assets with mixed provenance. This project does not copy sample-project data/resources; a later distribution review must separately audit any upstream runtime asset provenance.
- LT's serializer imports editor settings when saving resources, so compiler bootstrap includes the pinned editor dependency set rather than engine-only dependencies.
- Upstream engine PNGs emit benign `libpng` iCCP warnings during headless launch; repository-generated PNGs are not the source of those warnings.

## Screen-by-screen GUI gate decision

PASS on 2026-08-27. The main-agent vision pass inspected all 46 hash-bound authored-scene/title/map frames, 18 real-input GUI-navigation frames, eight full-playthrough menu/combat frames, the chapter transition, and Game Over. Fixes made during the audit include the minimap crash from unsupported terrain GUI keys; clipped terrain/class/forecast labels; developer-only Debug exposure; internal objective and localization IDs; empty Credits; internal Sound Room IDs; partial dialogue evidence; an overly crude villager placeholder; inconsistent player/capture settings; a UI instruction spoken by Rand; and an adaptation label shown as diegetic prose. The final review covers title, save slots, Extras, all three Sound Room tracks, settings and controls from top to bottom, minimap, map options/help, objectives, roster, all three unit-info pages, action/item/equip/weapon/forecast menus, every authored scene, all four map states, chapter transition, Game Over, and the ending card.

No release-blocking GUI defect remains in those inspected paths. The gallery and runtime evidence are bound to project tree `52b5a29d560af2c880ef3bbb24b9d0e4b86297e7543c5b1d91afbc6352ed04b6`; the report contains no stale verification. Intentional limitations are the graybox generic villagers, the Trolloc portrait touching the top edge without obscuring its face, and the launcher disabling the optional terrain HUD to avoid the documented pinned-engine Continue crash. Human duration, difficulty, tutorial clarity, and listening checks remain mandatory Phase 5 work.

## Next bounded action

Follow `docs/playtesting.md` for three timed human playthroughs, record chapter durations and usability/audio findings, and adjust only mission balance or objective clarity where the evidence warrants it.
