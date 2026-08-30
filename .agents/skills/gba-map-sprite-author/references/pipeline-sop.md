# Direct-grid map-sprite pipeline SOP

Follow these steps in order. Keep generated candidates and review files under `.codex-image/`; ship only the accepted immutable source PNG and its manifest entry. The implemented contract is in `assets/generated_sources/PROVENANCE.md:31-53`, `src/winternight_gen/asset_pipeline.py:1994-2136`, and `tests/test_assets.py:64-173,309-367`.

## 1. Load anchors and pass the calibration gate

Read `design/visual_bible.yaml`, the subject's entry in `source/characters.yaml`, this skill, and `references/sacred-stones-map-sprite-guide.md`.

Before any roster generation, author a newly composed, non-shipping Eirika recognizability calibration directly on the logical grid. Store it in `.codex-image/fe8-calibration/` (the established artifact is `eirika-recognition-calibration.png`). Do not supply, trace, splice, or ship an official sprite. Treat this as a hard gate: stop unless Eirika is immediately recognizable at native scale from silhouette, palette, costume mass, and gear. See `assets/generated_sources/PROVENANCE.md:40-45`.

## 2. Explore candidates before selecting a direction

Generate multiple genuinely different visual directions for every character before making a final source. Make each candidate a complete four-facing construction sheet, not a single illustration. Compare the candidates at native scale; select one direction with a human reviewer before proceeding. The existing five-direction Rand review demonstrates the required comparison in `.codex-image/rand-map-sprite-restart/index.html:34-44`.

Keep head height, shoulder width, baseline, gear side, and dominant team-color mass consistent across down, left, right, and up. Reject identity drift, a full-cell body, weak team color, clipped gear, and candidates readable only when enlarged.

## 3. Generate with the pinned tool and prompt

Read and follow `skill://codex-imagegen`. Use Codex image generation with provider `OpenAI Codex imagegen` and model `gpt-image-2`; request the destination filename separately as required by that skill. `assets/generated_sources/PROVENANCE.md:33-38` and `design/asset_manifest.yaml:615-617` pin the working tool and model.

Use this exact two-part prompt scaffold. Keep the first sentence verbatim. Replace the bracketed second part with a concise character-specific tail naming the build, hair, clothing with a dominant team-color mass, and one exaggerated gear silhouette.

```text
Original target-grid GBA-2004 tactical map sprite; four newly composed logical 32x32 views ordered down, left, right, up; 24-27 pixel subject; 10-15 colors; deliberate one-pixel clusters; curved anatomy; selective dark-purple outline; exact magenta background; exact 8x nearest-neighbor enlargement; no copied sprites, text, scenery, antialiasing, gradients, dithering, or actor likeness. [character-specific tail: build, hair, clothing, team-color mass, one exaggerated gear silhouette]
```

The prompt's `10-15 colors` is an input direction, not the output limit. The processed subject must use `6-13` colors from the output allowlist in step 8. See `design/asset_manifest.yaml:615` and `tests/test_assets.py:147-153`.

## 4. Normalize and name the immutable source

Author the decision surface as one horizontal logical `128x32` RGB sheet: exactly four `32x32` cells ordered down, left, right, up. Set every background pixel to exact magenta RGB `(255, 0, 255)`. Upscale once with nearest-neighbor by exactly `8x` to an RGB `1024x256` PNG. Save it as:

```text
assets/generated_sources/map_sprite_{subject_id}-source-v{N}.png
```

Increment `{N}`; never overwrite an accepted source. The pipeline converts the source to RGB, downsamples it with nearest-neighbor to `128x32`, re-enlarges it to `1024x256`, and requires the reconstructed RGB pixel bytes to match exactly. A visually similar resize is not sufficient. See `assets/generated_sources/PROVENANCE.md:33-38,47-53` and `src/winternight_gen/asset_pipeline.py:1994-2021`.

## 5. Dry-process one source and compute all hashes

Do not touch `build/`. Process only the new source through the same single-asset Python function into `/tmp`, then compute SHA-256 over the source file and the two saved PNG files. From the repository root, substitute the four shell values and run:

```bash
SUBJECT_ID=rand ASSET_ID=rand_map_sprite VARIANT=rand_archer VERSION=3 \
uv run --python 3.11 python - <<'PY'
import hashlib
import os
from pathlib import Path

from winternight_gen.asset_pipeline import _ai_map_sprite
from winternight_gen.models import AssetManifestEntry

root = Path.cwd()
subject_id = os.environ["SUBJECT_ID"]
asset_id = os.environ["ASSET_ID"]
variant = os.environ["VARIANT"]
version = os.environ["VERSION"]
source_path = f"assets/generated_sources/map_sprite_{subject_id}-source-v{version}.png"
source_hash = hashlib.sha256((root / source_path).read_bytes()).hexdigest()
asset = AssetManifestEntry(
    id=asset_id,
    type="map_sprite",
    subject_id=subject_id,
    variant=variant,
    provenance="ai_generated",
    source_path=source_path,
    source_hash=source_hash,
    processing_version="lt-direct-grid-sprite-1",
    approval_status="pending",
    license_note="Temporary single-source hash probe.",
)
out = Path("/tmp") / f"winternight-{asset_id}-hash-probe"
out.mkdir(parents=True, exist_ok=True)
stand = out / f"{asset_id}-stand.png"
move = out / f"{asset_id}-move.png"
_ai_map_sprite(stand, move, asset, root)
print(f"source_hash: {source_hash}")
print(f"stand_output_hash: {hashlib.sha256(stand.read_bytes()).hexdigest()}")
print(f"move_output_hash: {hashlib.sha256(move.read_bytes()).hexdigest()}")
print(f"outputs: {out}")
PY
```

This deliberately uses the pipeline's single-asset `_ai_map_sprite` implementation (`src/winternight_gen/asset_pipeline.py:2079-2118`) with an in-memory `pending` entry so output hashes can exist before an `approved` manifest entry requires them (`src/winternight_gen/models.py:701-757`). The compiler later verifies the recorded hashes with `_verify_map_sprite_hashes` (`src/winternight_gen/asset_pipeline.py:2121-2136`).

## 6. Copy the manifest field set and record the hashes

Copy this `rand_map_sprite` field set verbatim, then replace every subject-specific value and all three hashes. Keep `processing_version: lt-direct-grid-sprite-1`, the provider, and the model exact. Do not mark the entry `approved` until the review in step 9 passes.

```yaml
  - id: rand_map_sprite
    type: map_sprite
    subject_id: rand
    variant: rand_archer
    provenance: ai_generated
    source_path: assets/generated_sources/map_sprite_rand-source-v3.png
    stand_processed_path: resources/map_sprites/rand_map_sprite-stand.png
    move_processed_path: resources/map_sprites/rand_map_sprite-move.png
    prompt: 'Original target-grid GBA-2004 tactical map sprite; four newly composed logical 32x32 views ordered down, left, right, up; 24-27 pixel subject; 10-15 colors; deliberate one-pixel clusters; curved anatomy; selective dark-purple outline; exact magenta background; exact 8x nearest-neighbor enlargement; no copied sprites, text, scenery, antialiasing, gradients, dithering, or actor likeness. very tall lean young rural archer, tousled reddish-brown hair, brown wool, blue tabard, shortbow and quiver'
    provider: OpenAI Codex imagegen
    model: gpt-image-2
    source_hash: b8386baa4ae8c535358e0cb9041b7110a0d01d1e6df6fda5118214b5db8e4028
    stand_output_hash: 46e85ae381fd95dbbb3ec26c3e4e5f4aec6988d12e738c5e4d97653764d67b50
    move_output_hash: f6370b5b8136f4850566316550c2962441dbf1241a5cbf5654ad3089e65e2abf
    processing_version: lt-direct-grid-sprite-1
    approval_status: approved
    license_note: Original AI-assisted target-grid sprite source; Eirika calibration used only for scale and cluster-density review; no official sprite, adaptation image, actor likeness, or third-party game asset supplied.
```

This is the repository entry at `design/asset_manifest.yaml:607-623`. Preserve its field set; do not add a seed because the provider exposes none (`assets/generated_sources/PROVENANCE.md:47-49`).

## 7. Verify the assembled sheet geometry

Inspect the `/tmp` outputs, not only the source art.

- Stand: exactly `192x144`, a `3x3` layout of `64x48` cells. Every cell uses the down-facing source. Column offsets are `(-1, 0)`, `(0, -1)`, `(1, 0)` in rows zero and one; the implementation's active-row adjustment makes row two `(-1, -1)`, `(0, -2)`, `(1, -1)`.
- Move: exactly `192x160`, a `4x4` layout of `48x40` cells. Rows are down, left, right, up. Every row uses column offsets `(-1, 0)`, `(0, -1)`, `(1, 0)`, `(0, 0)`.
- Placement: center each subject horizontally and anchor its bottom two pixels above the cell bottom before applying the listed offset.

These are executable facts from `src/winternight_gen/asset_pipeline.py:2063-2118`; dimensions are independently asserted at `tests/test_assets.py:114-128,329-349`.

## 8. Enforce the palette, colorkey, and scale

Require every output pixel to be in this exact 16-value RGBA allowlist, including the LT colorkey:

```text
(128, 160, 128, 255)  colorkey
(88, 72, 120, 255)
(144, 184, 232, 255)
(216, 232, 240, 255)
(112, 96, 96, 255)
(176, 144, 88, 255)
(248, 248, 208, 255)
(56, 56, 144, 255)    team dark
(56, 80, 224, 255)    team mid
(40, 160, 248, 255)   team light
(24, 240, 248, 255)   team glow
(232, 16, 24, 255)
(248, 248, 64, 255)
(248, 248, 248, 255)
(64, 56, 56, 255)
(128, 136, 112, 255)
```

The direct-grid mapper's named colors are pinned at `src/winternight_gen/asset_pipeline.py:1403-1435`; the complete output allowlist and four-value team ramp are enforced at `tests/test_assets.py:82-105`. For an approved AI sprite, require a processed subject height no greater than `27` pixels, `6-13` subject colors, four distinct directional rows, and team-ramp coverage of at least `0.2` of subject pixels. See `tests/test_assets.py:124-153`.

## 9. Run the roster review loop

Add the processed stand and move sheets to both review artifacts:

- contact sheet: `.codex-image/direct-grid-processed/roster-contact.png`
- animated engine-scale review: `.codex-image/sprite-roster-review/index.html`

In the HTML, animate all three stand columns and all four move columns, expose down/left/right/up switching, and include a synchronized native `1x` roster view. Review native scale first and nearest-neighbor zoom second. Reject palette residue, baseline jitter, direction drift, duplicate silhouettes, weak team-color mass, terrain loss, or clipped gear. The established review contract is visible at `.codex-image/sprite-roster-review/index.html:70-75,95-134,184-219`.

Only after the human accepts both artifacts, set `approval_status: approved` and retain the exact hashes from step 5. If the source changes, increment `{N}` and repeat processing, hashing, and review.

## 10. Hand verification to the build owner

Do not run a build-writing command as the sprite author. Hand the accepted source and manifest change to the build owner, who runs `make check`. Its 18 prerequisites are `validate`, `compile`, `lint`, `test`, `smoke`, `title-flow`, `mechanics`, `tam-survival`, `journey`, `editor-smoke`, `determinism`, `input-playthrough`, `suspend-continue`, `gui-navigation`, `game-over-recovery`, `capture`, `package-smoke`, and `report` (`Makefile:96`).

Use these exact tests to identify failures:

- `test_approved_ai_assets_are_source_and_output_hash_locked` catches source/output hash drift and processed dimensions; its `compiled_campaign` setup also exercises the `1024x256` and byte-exact `8x` pipeline guards (`tests/test_assets.py:309-355`; `src/winternight_gen/asset_pipeline.py:1994-2008`). It also pins the current approved-AI inventory count at `tests/test_assets.py:311-318`; the build owner must update that explicit count when an accepted sprite replaces a placeholder.
- `test_campaign_map_sprites_use_pinned_layout_palette_and_distinct_facings` catches missing sheets, wrong stand/move dimensions, out-of-palette pixels, duplicate facings, AI height over `27`, subject color count outside `6-13`, and team-color share below `0.2` (`tests/test_assets.py:79-153`).
- `test_placeholder_sprite_sheets_use_pinned_engine_colorkey` catches a wrong LT colorkey in campaign sheets (`tests/test_assets.py:64-76`).
- `test_campaign_map_sprite_archetypes_have_distinct_silhouettes` catches roster silhouette duplication (`tests/test_assets.py:156-165`).
- `test_campaign_characters_have_individual_map_sprites` catches shared character assignments (`tests/test_assets.py:168-173`).
- `test_asset_reference_lineage_resolves_and_is_source_hash_locked` catches unresolved or changed shipping reference sources (`tests/test_assets.py:358-367`). The Eirika calibration is non-shipping and must not be added as a project asset.

The exact prompt wording, provider/model strings, source naming, exact source magenta, calibration gate, candidate exploration, and review artifacts remain mandatory human-review gates; no current test checks those strings or artifacts. Missing required approved-AI provenance fields are rejected by `AssetManifestEntry.validate_provenance` (`src/winternight_gen/models.py:727-757`).
