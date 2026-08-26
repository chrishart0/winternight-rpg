# Winternight RPG generation harness

Private technical proof of concept for compiling structured story and mission specifications into a deterministic Lex Talionis project. The current build contains a complete four-chapter campaign generated from versioned story, mission, scene, map, gameplay, and asset specifications, with processed AI portrait and story-background assets recorded in a provenance manifest.

## Linux quick start

Requirements: Git, `uv`, Python 3.11 (installed automatically by `uv`), and common SDL/X11 runtime libraries. On Ubuntu 24.04, the pinned PyPI wheels work without a system PyQt package.

```bash
git submodule update --init --recursive
make bootstrap
make compile
make check
make play
```

`make compile` recreates `build/winternight.ltproj` from structured specifications and validated assets. `make smoke` loads all four chapters through the pinned engine and evaluates its objective scenarios. `make check` runs the complete verification portfolio and writes `build/report.json` plus `build/REPORT.md`. `make play` launches the generated campaign interactively.

The official upstream is hosted at GitLab, despite older plans and links naming GitHub: `https://gitlab.com/rainlash/lt-maker.git`. The exact commit is recorded in [`engine.lock`](engine.lock).

## Command surface

- `make bootstrap`: install Python 3.11 dependencies and initialize the pinned submodule.
- `make validate`: validate the source specification and internal references.
- `make compile`: replace `build/winternight.ltproj` with deterministic output.
- `make smoke`: verify engine loading, event parsing/execution, level initialization, and a clean timed game-loop exit.
- `make capture`: render a fresh, hash-bound set of title, intro, map, milestone, and ending-card evidence.
- `make title-flow`: drive the real title menu into Chapter 0 with pygame input.
- `make mechanics`: execute every mission's Talk/Visit/Rescue/Search/reinforcement/equipment/escape chain through LT's public runtime.
- `make tam-survival`: prove Tam's story protection using the real LT combat solver.
- `make input-playthrough`: complete all four chapters using only real pygame keyboard input.
- `make suspend-continue`: suspend during Chapter 3, return through the title menu, and verify the restored unit state.
- `make game-over-recovery`: trigger a real loss and verify recovery to the title screen.
- `make package`: create the deterministic private Linux archive in `dist/`.
- `make package-smoke`: extract that archive in isolation and exercise its packaged engine and project.
- `make play`: launch the generated project with the pinned engine.
- `make report`: regenerate the build report from the current output.
- `make check`: run every validation lane above plus engine/editor smoke, the chapter journey, capture, report, and a clean-tree determinism comparison.
- `make clean`: remove generated build and test cache files.

## Editor launch

Do not run the compiler while the editor is open.

```bash
make editor
```

The editor opens `build/winternight.ltproj`. Close it before compiling again. See [`docs/linux.md`](docs/linux.md) for exact direct commands and headless notes.

## Legal/provenance boundary

The project does not copy either bundled sample game's data or resources. Repository-created placeholder resources and processed visual assets carry hashes and provenance records; dialogue is original paraphrase. LT-Maker, Pillow, and other dependencies remain governed by their upstream licenses. This private adaptation build is not intended for distribution.
