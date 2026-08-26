# Generated visual source provenance

These files are original visual sources for a private technical prototype. They were created with OpenAI's built-in image generation tool on 2026-08-26. No actor likeness, television-adaptation likeness, Fire Emblem asset, or game screenshot was requested or supplied. The generated source PNGs are immutable compiler inputs; `design/asset_manifest.yaml` records their SHA-256 hashes and each processed engine resource's expected hash.

## Shared generation direction

All new-image calls used the same direction: handcrafted GBA-era tactical-RPG pixel illustration, readable silhouettes, restrained medieval-rural palette, cool shadows, warm highlights, no photorealism, no text, no logo, no UI, and no recognizable adaptation or actor likeness. Backgrounds were generated as 3:2 landscapes with a quiet lower third for dialogue overlays.

## Character sources

- `cast_identity_sheet-v1.png` — new-image mode. A strict 5×2 identity grid: Rand, Tam, Mat, Perrin, Egwene / Moiraine, Lan, Thom, Padan Fain, Trolloc. Character identity details came from `design/visual_bible.yaml` and `source/characters.yaml`.
- `rand_tam_variants-v1.png` — edit/reference mode using the cast sheet. Strict 3×2 grid: Rand neutral/frightened/determined; Tam neutral/battle-ready/wounded. The prompt required unchanged identity, clothes, lighting, rendering, and crop across expressions.
- `cast_identity_chroma-v1.png` and `rand_tam_chroma-v1.png` — precision edit/reference mode. The prompt required changing only each cell's slate backdrop to flat RGB `255,0,255`, preserving every portrait, expression, grid boundary, black gutter, and pixel-art detail.

## Background sources

- `quarry_road_cold-v1.png` — cold early-spring mountain valley, muddy wagon road, old stone walls, remaining snow, no figures.
- `emonds_field_day-v1.png` — peaceful village green, dominant timber inn, spring festival greenery and carts, no figures.
- `winespring_inn-v1.png` — warm timber common room, hearth, tables, stairs, no figures.
- `farmhouse_evening-v1.png` — modest firelit farmhouse interior, closed door, old bow, gathering tension, no figures.
- `farm_night-v1.png` — moonlit isolated farm exterior during a breach, broken wall and restrained firelight, no figures or gore.
- `westwood_night-v1.png` — ancient moonlit forest clearing and narrow path, low fog, no figures.
- `emonds_burning-v1.png` — precision edit/reference mode from `emonds_field_day-v1.png`; preserve exact village geometry while changing only time, lighting, smoke, distant fires, and limited damage.
- `farm_ruined-v1.png` — precision edit/reference mode from `farm_night-v1.png`; preserve exact farm geometry while changing only elapsed-time damage, dead embers, smoke, fog, and debris.

`title_background` and `winternight_ending` are deterministic color grades of `westwood_night-v1.png`, not additional model outputs.

## Deterministic processing

`src/winternight_gen/asset_pipeline.py` crops registered grid cells, removes the flat chroma backdrop, assembles the pinned LT 160×112 portrait regions, reduces portrait sheets to at most 64 colors including the exact LT color key, crops backgrounds to 3:2, reduces them to 240×160 and at most 64 colors, and rejects any source or output hash mismatch.
