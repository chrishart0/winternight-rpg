# Cutscene portrait SOP

Follow these steps in order. Do not edit `build/`. The executable contract is `src/winternight_gen/asset_pipeline.py:612-646,928-981,1022-1090`, `src/winternight_gen/models.py:701-757`, and `tests/test_assets.py:64-77,282-375`.

## 1. Load identity and style anchors

Confirm the graybox art gate. Read the subject's `identity_anchors` in `design/visual_bible.yaml:12-27` and its description, portrait ID, and narrative constraints in `source/characters.yaml:2-150`. Preserve build, hair, clothing, carried cues, age, and established likeness across expressions. Apply the global eye-level, restrained-saturation, cool-shadow, warm-highlight, non-photorealistic GBA-era style (`design/visual_bible.yaml:2-11`).

## 2. Choose one source path

Use an identity sheet for named cast, repeated expressions, or any character whose likeness must remain stable across assets. Generate one strict grid, then generate expression variants by edit/reference while preserving identity, clothes, lighting, rendering, crop, cell boundaries, and gutters. The accepted sheets are `5x2` and `3x2`; the recorded process is in `assets/generated_sources/PROVENANCE.md:9-13`.

Use a single-cell bust for a new isolated civilian or one-off subject. Generate the final bust directly on chroma. Omit both `source_grid` and `source_cell`; the accepted villager entries demonstrate this at `design/asset_manifest.yaml:381-414`.

For a grid, set `source_grid: [columns, rows]` and zero-based `source_cell: [column, row]` together. Never set only one or select an out-of-bounds cell; `AssetManifestEntry.validate_provenance` rejects either error (`src/winternight_gen/models.py:720-737`). `_grid_cell` crops the selected cell with `max(4 px, 4%)` left and vertical insets and `max(4 px, 6%)` right inset (`src/winternight_gen/asset_pipeline.py:1022-1035`).

## 3. Generate only through the authorized tool

Read and invoke `skill://codex-imagegen`; direct it to `.codex-image/<topic>/`. The accepted records contain these exact tool strings:

- Identity-sheet and edit lineage: `provider: OpenAI built-in imagegen`; `model: built-in imagegen (model-managed)` (`design/asset_manifest.yaml:3-17,93-379`).
- Direct single-cell generation: `provider: Codex CLI`; `model: gpt-image-2`; `seed: null` (`design/asset_manifest.yaml:381-414`; `assets/generated_sources/PROVENANCE.md:18-22`).

For new calls through Codex, record the actual `Codex CLI` / `gpt-image-2` route. Do not relabel new work as the historical model-managed route. Do not use the title logo's SDXL/Canny/LoRA path (`design/asset_manifest.yaml:47-68`).

Start from this recorded shared direction verbatim, then append the subject anchors, expression, bust crop, grid placement if any, and chroma requirement:

```text
handcrafted GBA-era tactical-RPG pixel illustration, readable silhouettes, restrained medieval-rural palette, cool shadows, warm highlights, no photorealism, no text, no logo, no UI, and no recognizable adaptation or actor likeness.
```

This is the accepted direct-bust prompt verbatim; copy its structure, not its identity:

```text
Adult village neighbor woman, practical braid, pale apron, frightened Winternight bust on hot magenta chroma, original GBA-era pixel illustration.
```

The sources are `assets/generated_sources/PROVENANCE.md:5-13` and `design/asset_manifest.yaml:381-397`. Record the final prompt exactly in the manifest; approved AI assets require it (`src/winternight_gen/models.py:738-757`).

## 4. Make and inspect the chroma source

For a sheet, perform a precision edit that changes only every cell backdrop to flat RGB `(255, 0, 255)` and preserves portrait pixels, expressions, grid boundaries, black gutters, crop, and pixel detail. For a single cell, request that backdrop in the original call. This reproduces `assets/generated_sources/PROVENANCE.md:11-13,22`.

Reject chroma-colored subject pixels. `_remove_chroma_backdrop` first thumbnails an image whose maximum dimension exceeds `420` to fit within `420x420` using LANCZOS, then makes a pixel transparent when `red >= 110`, `blue >= 90`, and `min(red, blue) - green >= 35`. It deliberately keys directly instead of sampling corners (`src/winternight_gen/asset_pipeline.py:1038-1054`). The source magenta is not the LT sheet colorkey `(128, 160, 128, 255)` (`design/visual_bible.yaml:75-86`).

## 5. Land and name the immutable source

Keep drafts under `.codex-image/<topic>/`. Copy only the selected source to one of these established forms:

```text
assets/generated_sources/{subject_or_group}-source-v{N}.png
assets/generated_sources/{subject_or_group}_chroma-v{N}.png
```

Increment `{N}`; never overwrite an accepted source. Set `processed_path: resources/portraits/{asset_id}.png`. The manifest and pipeline route portraits by stable ID (`design/asset_manifest.yaml:93-414`; `src/winternight_gen/asset_pipeline.py:2238-2247`).

## 6. Dry-process and compute hashes before editing the manifest

Run the single-asset pipeline into `/tmp` before adding or changing a manifest entry. For a grid source, set both grid variables, for example `SOURCE_GRID=3,2 SOURCE_CELL=1,0`; for a single cell, leave both empty. Substitute all values and run from the repository root:

```bash
ASSET_ID=rand_frightened SUBJECT_ID=rand VARIANT=frightened \
SOURCE_PATH=assets/generated_sources/rand_tam_chroma-v1.png \
SOURCE_GRID=3,2 SOURCE_CELL=1,0 PROFILE=standard \
uv run --python 3.11 python - <<'PY'
import hashlib
import os
from pathlib import Path

from winternight_gen.asset_pipeline import _ai_portrait
from winternight_gen.models import AssetManifestEntry

root = Path.cwd()
asset_id = os.environ["ASSET_ID"]
source_path = os.environ["SOURCE_PATH"]
source_hash = hashlib.sha256((root / source_path).read_bytes()).hexdigest()

def pair(name):
    value = os.environ.get(name, "")
    return tuple(int(part) for part in value.split(",")) if value else None

asset = AssetManifestEntry(
    id=asset_id,
    type="portrait",
    subject_id=os.environ["SUBJECT_ID"],
    variant=os.environ["VARIANT"],
    provenance="ai_generated",
    source_path=source_path,
    processed_path=f"resources/portraits/{asset_id}.png",
    source_hash=source_hash,
    source_grid=pair("SOURCE_GRID"),
    source_cell=pair("SOURCE_CELL"),
    processing_profile=os.environ.get("PROFILE", "standard"),
    processing_version="lt-ai-portrait-6",
    approval_status="pending",
    license_note="Temporary single-source hash probe.",
)
out = Path("/tmp") / f"winternight-{asset_id}-hash-probe"
out.mkdir(parents=True, exist_ok=True)
processed = out / f"{asset_id}.png"
_ai_portrait(processed, asset, root)
print(f"source_hash: {source_hash}")
print(f"output_hash: {hashlib.sha256(processed.read_bytes()).hexdigest()}")
print(f"output: {processed}")
PY
```

This uses `_ai_portrait` directly and never writes the repository build (`src/winternight_gen/asset_pipeline.py:1057-1080`). `_source_image` rejects a source outside the repository or a mismatched source hash; `_verify_processed_hash` later rejects output drift (`src/winternight_gen/asset_pipeline.py:928-943,1083-1090`).

## 7. Verify the exact deterministic portrait chain

Inspect the `/tmp` PNG. Require this implemented chain:

1. Select the grid cell, if present, then remove chroma (`src/winternight_gen/asset_pipeline.py:1022-1059`).
2. When `processing_profile: dark_wounded` is narratively applicable, apply brightness `0.78`, then alpha-composite tint RGBA `(84, 20, 20, 48)` over nontransparent pixels. Otherwise keep `standard` (`src/winternight_gen/models.py:722`; `src/winternight_gen/asset_pipeline.py:1060-1064`).
3. LANCZOS-fit the transparent subject to `192x160` with centering `(0.5, 0.34)`, resize to `96x80` with NEAREST, and quantize the main image to `64` colors without dithering (`src/winternight_gen/asset_pipeline.py:946-959,1066-1072`).
4. Mirror the main face and place it at `(32, 0)` on a `160x112` LT-colorkey sheet. Fit the minimug to `32x32` with NEAREST centering `(0.5, 0.28)` and place it at `(128, 80)` (`src/winternight_gen/asset_pipeline.py:612-625`).
5. Crop the blink source at `(30, 31, 62, 47)`. Place the open frame at `(128, 48)` and the closed frame at `(128, 64)` (`src/winternight_gen/asset_pipeline.py:619-631`).
6. Crop the mouth source at `(30, 48, 62, 64)`. Place the base mouth at `(96, 80)`; place the three generated frames at x `(64, 32, 0)` on y `80` and `96` (`src/winternight_gen/asset_pipeline.py:620,633-645`).
7. Finalize the whole sheet to `63` quantized colors plus exact LT colorkey `(128, 160, 128, 255)`, for at most `64` colors (`src/winternight_gen/asset_pipeline.py:962-981`). LT registers blink offset `[30, 31]` and smile offset `[30, 48]` (`src/winternight_gen/campaign_lt_adapter.py:551-557`).

## 8. Copy the approved manifest shape

After processing and review, copy this approved `rand_frightened` entry as the field template. Replace every identity, path, prompt, lineage, cell, provider/model, and hash value; never reuse the sample hashes. New portrait sources use `processing_version: lt-ai-portrait-6`, which keys chroma before high-resolution reduction to prevent magenta edge bleed.

```yaml
  - id: rand_frightened
    type: portrait
    subject_id: rand
    variant: frightened
    provenance: ai_generated
    source_path: assets/generated_sources/rand_tam_chroma-v1.png
    processed_path: resources/portraits/rand_frightened.png
    prompt: Rand frightened expression, identity-preserving portrait variant from the original cast sheet.
    reference_ids: [rand_neutral, cast_identity_sheet]
    provider: OpenAI built-in imagegen
    model: built-in imagegen (model-managed)
    seed: null
    source_hash: 3a2f8c86131746a553aec987721f51fecbfe8689a44f67fc0ae225cb18d26033
    output_hash: a1e942ef60a3497b817c8545e74062eaad64b40f0e08b30c19889677aba7656d
    source_grid: [3, 2]
    source_cell: [1, 0]
    processing_version: lt-ai-portrait-6
    approval_status: approved
    license_note: Original AI-generated character design; no actor or adaptation likeness requested.
```

This is `design/asset_manifest.yaml:112-130`. Point identity-derived portraits to their reference sheet and expression variants to both the neutral portrait and sheet. Reference IDs must resolve (`tests/test_assets.py:358-367`). Add `processing_profile: dark_wounded` only for that deterministic treatment; the accepted example is `design/asset_manifest.yaml:360-379`.

## 9. Run the native-scale review loop

Create portrait contact pages beside the established review artifacts under `.codex-image/roster-a-style/` and `.codex-image/isolated-roster-review/`. Show every new processed sheet and the existing cast roster at native `1x` and nearest-neighbor `4x`; include the portrait over its intended scene background and dialogue area. Do not overwrite the existing map-sprite contact page.

Review `1x` first. Reject identity drift, incorrect expression, weak silhouette, lost eyes or mouth, chroma holes or halo, clipping, palette noise, inconsistent crop, and any portrait recognizable only at `4x`. Review `4x` only to diagnose clusters. The native dimensions and palette are enforced by `test_approved_ai_assets_are_source_and_output_hash_locked` (`tests/test_assets.py:309-355`); the approval field is enforced by `AssetManifestEntry` (`src/winternight_gen/models.py:701-757`).

Mark `approval_status: approved` only after human acceptance of both contact pages. If the source changes, increment `{N}` and repeat dry-processing, hashes, and review.

## 10. Hand scoped checks to the build owner

Do not run a build-writing command. Ask the orchestrator to run the repository gate. Use these exact tests to diagnose portrait failures:

- `test_placeholder_sprite_sheets_use_pinned_engine_colorkey` checks every campaign portrait's LT colorkey (`tests/test_assets.py:64-77`).
- `test_campaign_portrait_sheets_match_pinned_lt_frame_layout` checks face placement, empty top-left space, side colorkey, blink, and mouth source frames (`tests/test_assets.py:282-299`).
- `test_campaign_civilian_portraits_have_textured_pixel_detail` requires accepted villager portraits to contain `24-64` colors (`tests/test_assets.py:301-307`).
- `test_approved_ai_assets_are_source_and_output_hash_locked` checks the approved inventory count, source and output hashes, `160x112` dimensions, at most `64` colors, and no residual keyed magenta (`tests/test_assets.py:309-355`). Update its explicit inventory count when a new approved AI asset changes that count (`tests/test_assets.py:311-318`).
- `test_asset_reference_lineage_resolves_and_is_source_hash_locked` checks all lineage IDs and reference-source hashes (`tests/test_assets.py:358-367`).
- `test_campaign_content_hash_includes_ai_source_images` guards inclusion of AI source inputs in deterministic build identity (`tests/test_assets.py:370-375`).

Prompt wording, candidate selection, contact pages, and human taste remain review gates rather than automated assertions. Required provenance fields and grid pairing are schema-enforced by `AssetManifestEntry.validate_provenance` (`src/winternight_gen/models.py:727-757`).
