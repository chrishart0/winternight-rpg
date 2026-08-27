# Winternight RPG Repository Constitution

This repository is a portable, public-source, repository-local story-to-tactics-game generation harness. The approved scope is the complete **Winternight vertical slice** described in `EXEC_PLAN.md`: four connected chapters generated from structured specifications, followed by verified visual assets, balancing, and local packaging. The generated adaptation build is not published as a game release. Respect phase gates; do not generate AI art before the complete graybox campaign is playable and recorded as such.

## Permanent rules

1. Do not edit generated files under `build/`; change specifications, templates, assets, or compiler code and rebuild.
2. Do not modify `vendor/lt-maker` unless an approved engine patch is documented in `EXEC_PLAN.md` with its purpose and verification evidence.
3. Pin the LT-Maker commit in `engine.lock` and record it in every build manifest.
4. Never commit full novel text, private source excerpts, or material copied from a protected source. Keep private notes under `source/private/`, which is gitignored.
5. Write original paraphrased dialogue only.
6. Every future mission and scene must reference one or more source beat IDs.
7. Label inferred, gameplay-invented, and altered material explicitly.
8. Do not begin AI art generation until the complete graybox campaign is playable and that phase gate is recorded in `EXEC_PLAN.md`.
9. Run `make check` after every content or compiler change. Run the engine smoke check for changes that affect LT serialization or runtime behavior.
10. A successful command is not proof of a successful game. Produce a build report and launch or smoke-test the generated project with the pinned engine.
11. Compiler output must be deterministic for identical versioned inputs. Build timestamps and machine paths do not belong in deterministic project output.
12. Never edit a `.ltproj` while LT-Maker is open. The compiler always replaces a fresh build directory and refuses to run when the repository's editor lock is present.

## Working contract

- The LLM authors structured specifications. Deterministic Python code writes engine files.
- Keep the compiler story-agnostic. Phase-specific content belongs under `source/`, `design/`, `assets/`, or `template/`.
- Treat `template/minimal.ltproj` as source material: it may be changed deliberately, but never by patching `build/` after compilation.
- Preserve the exact command surface: `make bootstrap`, `make validate`, `make compile`, `make smoke`, `make play`, `make report`, `make clean`, and `make check`.
- Keep `EXEC_PLAN.md` current with phase, deliverables, blockers, evidence, and the next bounded action.
- Prefer LT's own data objects, parsers, and loaders at the adapter boundary. Isolate any direct serialized-format knowledge in `lt_adapter.py` and contract tests.

## Phase boundaries

Phase 0 remains the original one-chapter engine fixture and regression test. Phase 1 adds story-agnostic schemas and compiler support. Phase 2 adds the four-chapter campaign using programmatic placeholders. Phase 3 adds original narrative content. Phase 4 may add approved AI-generated source art only after the Phase 2 graybox gate. Phase 5 balances and packages the game. Phase 6 extracts reusable generator assumptions only after the playable slice is complete.
