# Generated visual source provenance

These files are original visual sources for a technical proof of concept. They were created with OpenAI's built-in image generation tool on 2026-08-26. No actor likeness, television-adaptation likeness, Fire Emblem asset, or game screenshot was requested or supplied. The generated source PNGs are immutable compiler inputs; `design/asset_manifest.yaml` records their SHA-256 hashes and each processed engine resource's expected hash.

## Shared generation direction

All new-image calls used the same direction: handcrafted GBA-era tactical-RPG pixel illustration, readable silhouettes, restrained medieval-rural palette, cool shadows, warm highlights, no photorealism, no text, no logo, no UI, and no recognizable adaptation or actor likeness. Backgrounds were generated as 3:2 landscapes with a quiet lower third for dialogue overlays.

## Character sources

- `cast_identity_sheet-v1.png` — new-image mode. A strict 5×2 identity grid: Rand, Tam, Mat, Perrin, Egwene / Moiraine, Lan, Thom, Padan Fain, Trolloc. Character identity details came from `design/visual_bible.yaml` and `source/characters.yaml`.
- `rand_tam_variants-v1.png` — edit/reference mode using the cast sheet. Strict 3×2 grid: Rand neutral/frightened/determined; Tam neutral/battle-ready/wounded. The prompt required unchanged identity, clothes, lighting, rendering, and crop across expressions.
- `cast_identity_chroma-v1.png` and `rand_tam_chroma-v1.png` — precision edit/reference mode. The prompt required changing only each cell's slate backdrop to flat RGB `255,0,255`, preserving every portrait, expression, grid boundary, black gutter, and pixel-art detail.

### Book-accuracy portrait corrections

Five named-cast busts were regenerated through the authorized Codex
`gpt-image-2` edit workflow using `cast_identity_chroma-v1.png` as the identity
reference. The immutable selected sources are `mat-book-accurate-v1.png`
(red neckerchief and pouch strap), `perrin-book-accurate-v1.png` (smith apron
and square hammer), `egwene-book-accurate-v1.png` (long braid, pale apron, and
herb-pouch strap), `thom-patchwork-v1.png` (white hair and moustache over an
unmistakable many-colored gleeman's patchwork cloak), and
`fain-book-accurate-v1.png` (dark wool cap, pack straps, and walking staff).
`lt-ai-portrait-6` removes exact chroma before the high-resolution thumbnail
step so magenta cannot bleed into antialiased silhouettes. Native `96x80` face
review confirmed every named cue survives; the manifest locks all source and
processed hashes.

A sixth correction replaced `nynaeve_neutral`. Owner review rejected the Wave C
sheet cell as too young. `nynaeve-book-accurate-v1.png` is a direct single-cell
bust on exact hot-magenta chroma, generated locally with ComfyUI Krea 2 Turbo
NVFP4 after Codex imagegen hit a usage cap. It shows the Wisdom as an adult
woman in her mid twenties, glancing aside, with one fist closed around her
braid. It carries no `source_grid` or `source_cell` and processes under
`lt-ai-portrait-6`.

## Background sources

- `quarry_road_cold-v1.png` — cold early-spring mountain valley, muddy wagon road, old stone walls, remaining snow, no figures.
- `quarry_road_cold-v2.png` — Codex CLI (`gpt-image-2`) 2026-08-27. Same cold track with village roofs ahead and a distant hooded black rider, no face.
- `emonds_field_day-v1.png` — peaceful village green, dominant timber inn, spring festival greenery and carts, no figures.
- `winespring_inn-v1.png` — warm timber common room, hearth, tables, stairs, no figures.
- `winespring_inn_night-v1.png` — Codex CLI (`gpt-image-2`) 2026-08-27. Same inn as a night refuge, firelit, moon in the window, empty of people.
- `villager_woman-source-v1.png` and `villager_man-source-v1.png` — Codex CLI (`gpt-image-2`) 2026-08-27. Generic neighbor busts on magenta chroma; not named-cast likenesses.
- `farmhouse_evening-v1.png` — modest firelit farmhouse interior, closed door, old bow, gathering tension, no figures.
- `farm_night-v1.png` — moonlit isolated farm exterior during a breach, broken wall and restrained firelight, no figures or gore.
- `westwood_night-v1.png` — ancient moonlit forest clearing and narrow path, low fog, no figures.
- `emonds_burning-v1.png` — precision edit/reference mode from `emonds_field_day-v1.png`; preserve exact village geometry while changing only time, lighting, smoke, distant fires, and limited damage.
- `farm_ruined-v1.png` — precision edit/reference mode from `farm_night-v1.png`; preserve exact farm geometry while changing only elapsed-time damage, dead embers, smoke, fog, and debris.

`title_background` and `winternight_ending` are deterministic color grades of `westwood_night-v1.png`, not additional model outputs.

## Tactical map-sprite sources

The previous full-size turnaround sources were rejected and replaced in full.
The initial fourteen character sources were generated with Codex image generation
using `gpt-image-2`, then deterministically calibrated as exact 8× enlargements of
horizontal four-view `128×32` logical sheets. Each facing is authored within a
`32×32` target cell rather than derived by the compiler from a character
illustration.

A non-shipping, newly composed Eirika recognizability calibration established
the accepted 2004-era scale, cluster density, curved anatomy, palette depth, and
gear readability. It was not copied into project assets and no official sprite
was supplied, traced, or spliced. Character-specific prompts derive from
`design/visual_bible.yaml`; no adaptation image, actor likeness, or third-party
game sprite was supplied.

`design/asset_manifest.yaml` records every accepted prompt, model, source hash,
processed stand/move hash, approval, and provenance note. The provider does not
expose generation seeds, so no seed is recorded for these sources.

## Deterministic processing

`src/winternight_gen/asset_pipeline.py` verifies direct-grid sources are exact `1024×256` 8× pixel enlargements, recovers the four logical `32×32` facings without rescaling their authored clusters, removes flat chroma backdrops, maps source colors to the exact pinned LT team-recolor palette, assembles stand/move sheets, and rejects any source or processed-output hash mismatch. Portraits and backgrounds retain their separate deterministic reduction paths.

## Wave B tactical map-sprite sources

Nine additional sources were generated on 2026-08-27 through Codex image
generation, provider `OpenAI Codex imagegen`, model `gpt-image-2`, using the
same non-shipping Eirika calibration and exact direct-grid prompt scaffold.
Two complete four-facing directions were compared for every subject under
`.codex-image/wave-b-map-sprites/`. The accepted immutable sources are:

- `map_sprite_nynaeve-source-v1.png` — direction A: shoulder braid and round herb pouch.
- `map_sprite_bran-source-v1.png` — direction A: barrel-bodied mayor, apron, and key ring.
- `map_sprite_haral_luhhan-source-v1.png` — direction A: broad forge apron and shoulder hammer.
- `map_sprite_myrddraal-source-v1.png` — direction A: faceless mounted rider and gaunt horse; generated neutral horse highlights were deterministically palette-calibrated without changing the silhouette.
- `map_sprite_hunter-source-v1.png` — direction B: compact capped woodsman and broad recurved bow.
- `map_sprite_villager_axeman-source-v1.png` — direction B: stocky low two-hand felling-axe guard.
- `map_sprite_villager_spearman-source-v1.png` — direction B: wide low boar-spear guard.
- `map_sprite_tam_litter-source-v1.png` — direction B: wounded man in a hide sling with exposed head, boots, blanket, and projecting poles.
- `map_sprite_ewin-source-v1.png` — direction A: round news satchel and raised hand, normalized to a deliberate 22-pixel child silhouette as the guide's slight-youth exception.

Every source is RGB `1024×256`, has an exact magenta backdrop, reconstructs
byte-for-byte after the `128×32` nearest-neighbor round trip, and uses 10–15
non-chroma input colors. `/tmp` single-asset processing confirmed the pinned
stand/move geometry, 6–13 processed subject colors, at least 20 percent team
palette coverage, four distinct directional rows, no greater than 27-pixel
processed height, and a unique alpha-mask silhouette across all 24 active roster
sprites.

Automated vision review stood in for human review this pass. Native engine
scale and nearest-neighbor zoom were reviewed for silhouette, identity,
direction consistency, baseline, gear clipping, chroma residue, palette mass,
and roster collisions. `.codex-image/direct-grid-processed/roster-contact.png`
and `.codex-image/sprite-roster-review/index.html` contain the complete
24-sprite contact and animated review surfaces and are ready for owner
re-review.

## Raven tutorial assets

The playable raven tutorial added one active character after the Wave B roster.
Two portrait and two direct-grid candidates were generated through the authorized
Codex image workflow with `gpt-image-2`; native-scale review selected candidate A
for both. `raven-portrait-source-v1.png` preserves the alert left-facing bust on
exact magenta chroma. `map_sprite_raven-source-v1.png` is an RGB `1024x256`
source that reconstructs byte-for-byte from its logical `128x32` four-facing
grid. Authored blue feather clusters preserve the six-color and dominant-team-
palette native sprite contracts after deterministic mapping. The manifest locks
both source files and all three processed outputs.

## Wave C cutscene portraits and story backgrounds

Eleven cutscene resources were generated on 2026-08-28 through the authorized
Codex image-generation workflow with model `gpt-image-2`. The shared prompt
direction and deterministic portrait/background pipelines above were retained.
All drafts and rejected variants remain under
`.codex-image/wave-c-cutscene-art/`; only the accepted immutable sources were
copied here.

- `westwood_road_night-v1.png` — candidate A, a centered moonlit rutted road
  through bare late-winter trees with a quiet foreground dialogue area.
- `emonds_field_burned_dawn-v1.png` — lineage-preserving candidate C from
  `emonds_burning-v1.png`, preserving the village geometry while changing only
  first-light grading, collapsed roof state, smoke, embers, and damage.
- `wave_c_identity_sheet-v1.png` — strict `3x2` identity sheet ordered
  Nynaeve, Bran, Haral / Ewin, Black Rider, fevered Tam.
- `wave_c_identity_chroma-v1.png` — precision chroma derivative of that sheet.
  Built-in image edits reconstructed portrait pixels, so the accepted sheet
  uses exact connected-backdrop substitution to RGB `(255,0,255)` and preserves
  every non-backdrop pixel and black gutter byte-for-byte.
- `hunter-source-v1.png` — isolated capped hunter with recurved bow and quiver.
- `villager_axeman-source-v2.png` — accepted close-bust revision with the axe
  behind the shoulder; the full-torso v1 draft was rejected because its LT face
  and animation-source regions were too small.
- `villager_spearman-source-v1.png` — isolated tied-hair farmer with broad
  boar-spear blade.

The six grid portraits select explicit `source_cell` coordinates; `tam_litter`
alone uses `processing_profile: dark_wounded`. `/tmp` single-asset probes
computed every source and processed-output SHA-256 before manifest approval.
The two backgrounds reduce to `240x160`; all nine portraits assemble to exact
`160x112` LT sheets with at most 64 colors and no residual keyed magenta.

Automated vision review stood in for human review this pass. Every processed
resource was inspected at native `1x` before nearest-neighbor `4x`, checking
identity, silhouette, crop, blink/mouth source regions, chroma edges, palette
noise, and scene readability. Backgrounds were also reviewed with a lower-third
dialogue box and the burned-dawn edit beside its parent. The review surfaces are
`.codex-image/roster-a-style/cutscene-portrait-contact.png` and
`.codex-image/isolated-roster-review/cutscene-background-contact.png`, ready for
owner re-review.
