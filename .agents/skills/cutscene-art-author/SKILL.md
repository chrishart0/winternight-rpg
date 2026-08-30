---
name: cutscene-art-author
description: "Author, replace, process, and review original Winternight cutscene portraits and scene backgrounds after the graybox art gate. Use when creating or replacing cutscene portraits or scene backgrounds after that gate; do not use for map sprites, title logos, or the local SDXL path."
---

# Cutscene Art Author

Use this skill only after the complete graybox campaign is playable and the art gate is recorded. Do not generate early (`AGENTS.md:3,12,28-35`).

## Authority boundary

- Generate future Winternight art only through this skill for cutscene portraits and scene backgrounds or through `skill://gba-map-sprite-author` for map-unit sprites. No other generated-art path is authorized.
- Do not use this skill for map sprites, battle animations, the title logo, or the title logo's local SDXL/Canny/LoRA process. A title *background* remains a background and follows this skill (`design/asset_manifest.yaml:47-68,75-91`).
- Read and invoke `skill://codex-imagegen` for every new model call. Keep candidates under `.codex-image/`; ship only the accepted immutable PNG under `assets/generated_sources/` (`assets/generated_sources/PROVENANCE.md:1-13,47-53`).

## Prompt contract

Bind every prompt to these anchors:

- GBA-era tactical-RPG pixel illustration; `perspective: eye_level`; readable silhouettes; restrained saturation and shading; rural medieval-fantasy materials; cool shadows; warm highlights; no photorealism, modern objects, copied Fire Emblem assets, or text in art (`design/visual_bible.yaml:2-11`).
- Preserve the subject's `identity_anchors` and the matching character description and constraints (`design/visual_bible.yaml:12-27`; `source/characters.yaml:2-150`).
- Judge the processed engine resource, not the model-resolution source. Bind `portrait_dimensions: [160, 112]`, `background_dimensions: [240, 160]`, and `palette_colors_max: 64` (`design/visual_bible.yaml:75-86`; `tests/test_assets.py:309-355`).

## Required procedure

- Follow [references/portrait-sop.md](references/portrait-sop.md) for identity sheets, single-cell busts, chroma removal, LT frame assembly, hashes, and approval.
- Follow [references/background-sop.md](references/background-sop.md) for scene composition, variants, deterministic reduction, hashes, scene wiring, and approval.
- Never mark an AI asset `approved` without prompt, provider, model, source hash, output hash, license note, immutable source, and human review at native `1x` and nearest-neighbor `4x` (`src/winternight_gen/models.py:701-757`; `tests/test_assets.py:309-367`).
- Never write `build/`. Dry-process one asset through the Python pipeline into `/tmp`; hand build-writing validation to the orchestrator (`src/winternight_gen/asset_pipeline.py:928-1090,2209-2300`).
