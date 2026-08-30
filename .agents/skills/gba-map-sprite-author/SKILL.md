---
name: gba-map-sprite-author
description: "Author and review original, legally clean GBA-era tactical-RPG map sprites with Fire Emblem: The Sacred Stones-like scale, silhouette, palette economy, directional consistency, and LT-compatible sheets. Use when creating, replacing, prompting, processing, or critiquing Winternight map-unit sprites; do not use for portraits, battle animations, or copied/ripped game assets."
---

# GBA Map Sprite Author

Read `design/visual_bible.yaml`, the relevant identity anchors, and [references/sacred-stones-map-sprite-guide.md](references/sacred-stones-map-sprite-guide.md) before generating or editing a sprite.

## Non-negotiable constraints

- Create original forms. Never supply, trace, splice, recolor, or ship Nintendo sprites or community sprites without separately verified permission.
- Treat official game graphics as reference-only evidence for scale, palette economy, silhouette, and animation grammar.
- Target the repository contract rather than a generic pixel-art illustration: four source facings ordered down, left, right, up; fixed baseline and scale; deterministic stand and move sheets; no text or interface.
- Ask for a 24–27-pixel subject inside each 32×32 source cell. The processed stand silhouette for an approved AI source must not exceed 27 pixels tall. Reject full-cell figures, fine costume rendering, and evenly distributed detail.
- Build the sprite from a few large color masses: dark contour/contact shadow, saturated team-color body, hair/head block, skin hint, and one exaggerated gear silhouette. Use hard clusters only—no antialiasing, semitransparent edges, subpixel texture, blur, gradients, or isolated noise.
- Ask the generator for 10–15 input colors. Processing maps the result to the pinned 16-value RGBA allowlist, including the LT colorkey; tests require 6–13 non-colorkey subject colors. For player units, make the saturated team-color mass materially dominant instead of reducing it to a belt or narrow tabard.
- Before any roster generation, pass the non-shipping Eirika recognizability benchmark at `.codex-image/fe8-calibration/`. This is a hard gate: if the newly composed calibration is not immediately recognizable at native scale from silhouette, palette, costume mass, and gear, reject the method rather than tuning roster outputs.

## Workflow

1. Define only the cues that survive at 1×: class/gear silhouette, build, hair/head block, team-color body mass, and at most one accent.
2. Draw the down-facing neutral silhouette first inside a 32×32 review cell. Keep the feet on a stable baseline and the complete subject within the prompt's 24–27-pixel height.
3. Place broad hue masses before internal detail: dark contour/contact shadow, saturated team-color midtone and highlight, then head/hair and gear. If brown or gray occupies nearly the whole sprite, stop and rebalance the palette.
4. Build left, right, and up views from the same measurements. Keep head height, shoulder width, foot line, gear size, and gear side consistent. Do not let the generator redesign the character per view.
5. Author only the four directional source poses. The direct-grid pipeline builds the three-column stand cycle and four-column move cycle with pinned offsets; do not add unsupported source animation columns.
6. Author a horizontal logical 128×32 RGB sheet: four 32×32 cells ordered down, left, right, up on exact magenta RGB `(255, 0, 255)`. Enlarge it once with 8× nearest-neighbor to exactly 1024×256, then let the repository pipeline map the pinned palette and assemble the engine sheets.
7. Review at native 1× first and nearest-neighbor zoom second. Reject any candidate that needs enlargement to identify the unit, merges into terrain, changes identity between facings, clips gear, or leaves chroma/alpha debris.
8. For approved assets, update prompt/model/source hash/output hashes/processing version/approval/license note in `design/asset_manifest.yaml`; hand `make check` and the pinned-engine map smoke/capture path to the build owner.

## Reproducible pipeline

Treat [references/pipeline-sop.md](references/pipeline-sop.md) as the normative generation-to-approval procedure.

1. Pass the Eirika calibration hard gate, then compare multiple complete four-facing visual directions for each character.
2. Generate with `skill://codex-imagegen`, provider `OpenAI Codex imagegen`, model `gpt-image-2`, and the SOP's exact prompt scaffold.
3. Land only an exact 1024×256 nearest-neighbor source, dry-process that single source into `/tmp`, compute all three SHA-256 values, and copy the complete manifest field set with `processing_version: lt-direct-grid-sprite-1`.
4. Review the processed roster contact sheet and animated engine-scale HTML before approval; the build owner closes with `make check`.

## Prompting image generators

Ask for a sprite construction sheet, not a character illustration. Use the exact prompt scaffold in the pipeline SOP: four logical 32×32 facings, a 24–27-pixel subject, 10–15 input colors, exact magenta RGB `(255, 0, 255)`, and exact 8× nearest-neighbor output. Explicitly forbid detailed clothing, facial rendering, realistic anatomy, brown-dominant palettes, full-cell figures, antialiasing, gradients, and dithering.

Generated raster art is a draft. Do not approve it merely because it looks pixelated at large scale. Downsample and inspect the actual engine-scale result before selection.
