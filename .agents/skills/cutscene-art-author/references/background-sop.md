# Cutscene background SOP

Follow these steps in order. Do not edit `build/`. The executable contract is `src/winternight_gen/asset_pipeline.py:928-1020,1083-1090`, `src/winternight_gen/models.py:701-757,921-930`, `src/winternight_gen/event_compiler.py:57-101`, and `tests/test_assets.py:309-375`.

## 1. Load scene and style anchors

Confirm the graybox art gate. Read the target scene, location identity, time, weather, damage state, and dialogue needs. Apply an eye-level GBA-era tactical-RPG pixel illustration with restrained saturation and shading, rural medieval-fantasy materials, cool shadows, warm highlights, readable forms, and no photorealism, modern objects, copied Fire Emblem assets, or text (`design/visual_bible.yaml:2-11`).

Compose a `3:2` landscape with a quiet lower third for dialogue overlays. Omit figures unless the scene specification requires a distant story cue; never add incidental cast. The accepted direction and exceptions are recorded at `assets/generated_sources/PROVENANCE.md:5-29`.

## 2. Choose a new composition or lineage-preserving variant

For a new location, describe the stable geometry first, then time/state, lighting, atmosphere, readable focal point, quiet lower third, and absence or required placement of figures.

For another state of an existing location, use edit/reference mode. Begin with `Same ... composition`; preserve geometry and camera while changing only the named time, light, weather, smoke, fire, damage, or debris. Set `reference_ids: [parent_background_id]`. The accepted edits are documented at `assets/generated_sources/PROVENANCE.md:26-29` and `design/asset_manifest.yaml:486-502,537-570,588-604`.

Use this approved prompt verbatim as the template; replace location-specific content without weakening the style or composition lineage:

```text
Same timber inn common room at night as a refuge, firelit, moon in the window, empty of people, original GBA-era tactical-RPG pixel painting.
```

This is `design/asset_manifest.yaml:486-502`. Record the exact final prompt; `AssetManifestEntry.validate_provenance` requires a prompt for approved AI art (`src/winternight_gen/models.py:738-757`).

## 3. Generate only through the authorized tool

Read and invoke `skill://codex-imagegen`; direct candidates to `.codex-image/<topic>/`. Accepted backgrounds record either:

- `provider: OpenAI built-in imagegen`; `model: built-in imagegen (model-managed)`; `seed: null`.
- `provider: Codex CLI`; `model: gpt-image-2`; `seed: null`.

The exact records are `design/asset_manifest.yaml:435-604` and `assets/generated_sources/PROVENANCE.md:15-29`. For new calls through Codex, record `Codex CLI` and `gpt-image-2`; do not relabel them as historical model-managed calls. Do not use the title logo's local SDXL/Canny/LoRA path (`design/asset_manifest.yaml:47-68`).

Generate genuinely different candidates for a new location. For a lineage variant, compare the edited candidate against its parent and reject camera, geometry, or focal-point drift. Preserve the prompt and selected source exactly; approved provenance is schema-enforced (`src/winternight_gen/models.py:701-757`).

## 4. Land and name the immutable source

Keep drafts under `.codex-image/<topic>/`. Copy only the selected source to:

```text
assets/generated_sources/{background_id}-v{N}.png
```

Increment `{N}`; never overwrite an accepted source. Set `processed_path: resources/panoramas/{background_id}.png`. The manifest and asset pipeline route stable background IDs to panorama resources (`design/asset_manifest.yaml:435-604`; `src/winternight_gen/asset_pipeline.py:2230-2237`; `src/winternight_gen/campaign_lt_adapter.py:551-552`).

## 5. Dry-process and compute hashes before editing the manifest

Run the single-asset pipeline into `/tmp` before adding or changing a manifest entry. Set `PROCESSING_VERSION=lt-ai-bg-title-3` only for `VARIANT=title`; use `lt-ai-bg-1` for ordinary and `ending_card` backgrounds. Substitute values and run from the repository root:

```bash
ASSET_ID=winespring_inn_night SUBJECT_ID=winespring_inn VARIANT=night_refuge \
SOURCE_PATH=assets/generated_sources/winespring_inn_night-v1.png \
PROCESSING_VERSION=lt-ai-bg-1 \
uv run --python 3.11 python - <<'PY'
import hashlib
import os
from pathlib import Path

from winternight_gen.asset_pipeline import _ai_background
from winternight_gen.models import AssetManifestEntry

root = Path.cwd()
asset_id = os.environ["ASSET_ID"]
source_path = os.environ["SOURCE_PATH"]
source_hash = hashlib.sha256((root / source_path).read_bytes()).hexdigest()
asset = AssetManifestEntry(
    id=asset_id,
    type="background",
    subject_id=os.environ["SUBJECT_ID"],
    variant=os.environ["VARIANT"],
    provenance="ai_generated",
    source_path=source_path,
    processed_path=f"resources/panoramas/{asset_id}.png",
    source_hash=source_hash,
    processing_version=os.environ["PROCESSING_VERSION"],
    approval_status="pending",
    license_note="Temporary single-source hash probe.",
)
out = Path("/tmp") / f"winternight-{asset_id}-hash-probe"
out.mkdir(parents=True, exist_ok=True)
processed = out / f"{asset_id}.png"
_ai_background(processed, asset, root)
print(f"source_hash: {source_hash}")
print(f"output_hash: {hashlib.sha256(processed.read_bytes()).hexdigest()}")
print(f"output: {processed}")
PY
```

This uses `_ai_background` directly and never writes the repository build (`src/winternight_gen/asset_pipeline.py:984-1019`). `_source_image` rejects a source outside the repository or a mismatched source hash; `_verify_processed_hash` later rejects output drift (`src/winternight_gen/asset_pipeline.py:928-943,1083-1090`).

## 6. Verify the exact deterministic background chain

Inspect the `/tmp` PNG. Require this implemented chain:

1. Convert the source to RGB. LANCZOS-fit it to `480x320` with centering `(0.5, 0.44)` (`src/winternight_gen/asset_pipeline.py:984-994`).
2. For `variant: title`, blend the image `0.45` toward RGB `(7, 12, 24)`. Add a top `48`-row and bottom `72`-row alpha gradient, each reaching alpha `90` (`src/winternight_gen/asset_pipeline.py:995-1007`). Keep `processing_version: lt-ai-bg-title-3`, as pinned by `design/asset_manifest.yaml:75-91`.
3. For `variant: ending_card`, add RGBA `(8, 14, 24, 76)` over rectangle `(0, 212, 479, 319)` (`src/winternight_gen/asset_pipeline.py:1008-1012`). Keep `processing_version: lt-ai-bg-1`, as pinned by `design/asset_manifest.yaml:588-604`.
4. Quantize to `64` colors with MEDIANCUT and no dithering, then resize to `240x160` with NEAREST (`src/winternight_gen/asset_pipeline.py:1013-1019`).

Do not pre-grade a source to mimic deterministic title or ending overlays; preserve one immutable source and let `variant` select the implemented grade. `title_background` and `winternight_ending` both derive from `westwood_night-v1.png` (`assets/generated_sources/PROVENANCE.md:29`; `design/asset_manifest.yaml:75-91,571-604`).

## 7. Copy the approved manifest shape

After processing and review, copy this approved `winespring_inn_night` entry verbatim as the field template. Replace every ID, state, path, prompt, lineage, provider/model, and hash value; never reuse the sample hashes.

```yaml
  - id: winespring_inn_night
    type: background
    subject_id: winespring_inn
    variant: night_refuge
    provenance: ai_generated
    source_path: assets/generated_sources/winespring_inn_night-v1.png
    processed_path: resources/panoramas/winespring_inn_night.png
    prompt: Same timber inn common room at night as a refuge, firelit, moon in the window, empty of people, original GBA-era tactical-RPG pixel painting.
    reference_ids: [winespring_inn]
    provider: Codex CLI
    model: gpt-image-2
    seed: null
    source_hash: 3099920ff4d5674b08751afff13d387ac818785771964c722ca7dc79ef24c79c
    output_hash: 8823db8c9a81a620dcfebc8bedcc7ecf51120f7e2d5893dd9a92be2d6a366e52
    processing_version: lt-ai-bg-1
    approval_status: approved
    license_note: Original AI-generated environment; no adaptation screenshot or copyrighted game asset used.
```

This is `design/asset_manifest.yaml:486-502`. Use `processing_version: lt-ai-bg-1` for ordinary and `ending_card` resources, and `lt-ai-bg-title-3` only for `variant: title` (`design/asset_manifest.yaml:75-91,435-604`). Reference IDs must resolve (`tests/test_assets.py:358-367`).

## 8. Wire the background to scenes

Set each intended scene's `background` to the stable manifest ID. `CampaignBundle` rejects missing IDs and non-background assets; it also validates cast portraits (`src/winternight_gen/models.py:921-930`). `compile_scene_v2` emits `change_background;{scene.background}` first and clears it last (`src/winternight_gen/event_compiler.py:57-60,99-101`).

For an `ending_card` action, set its `asset` to the approved ending background ID. The compiler removes visible portraits and emits another `change_background;{asset}` before the card text (`src/winternight_gen/event_compiler.py:90-98`). Do not point a scene at a source filename or `processed_path`; use the manifest ID.

## 9. Run the native-scale review loop

Create background contact pages beside the established review artifacts under `.codex-image/roster-a-style/` and `.codex-image/isolated-roster-review/`. Show each processed background at native `1x` and nearest-neighbor `4x`, with its parent variant beside it when applicable. Include a native scene mock with the actual dialogue box over the lower third. Do not overwrite the existing map-sprite contact page.

Review `1x` first. Reject unreadable focal geometry, a busy dialogue area, cast-like incidental figures, inconsistent location geometry, palette banding that obscures action, title text competition, or a state readable only at `4x`. Review `4x` only to diagnose clusters. The native dimensions and palette ceiling are enforced by `test_approved_ai_assets_are_source_and_output_hash_locked` (`tests/test_assets.py:309-355`); `AssetManifestEntry` enforces approval and provenance fields (`src/winternight_gen/models.py:701-757`).

Mark `approval_status: approved` only after human acceptance of both contact pages and the wired scene mock. If the source changes, increment `{N}` and repeat dry-processing, hashes, scene review, and lineage comparison.

## 10. Hand scoped checks to the build owner

Do not run a build-writing command. Ask the orchestrator to run the repository gate. Use these exact checks to diagnose background failures:

- `test_approved_ai_assets_are_source_and_output_hash_locked` checks the approved inventory count, source and output hashes, `240x160` dimensions, and at most `64` colors (`tests/test_assets.py:309-355`). Update its explicit inventory count when a new approved AI asset changes that count (`tests/test_assets.py:311-318`).
- `test_asset_reference_lineage_resolves_and_is_source_hash_locked` checks every parent/reference ID and reference-source hash (`tests/test_assets.py:358-367`).
- `test_campaign_content_hash_includes_ai_source_images` guards inclusion of AI source images in deterministic build identity (`tests/test_assets.py:370-375`).
- `uv run --python 3.11 winternight validate` exercises manifest provenance and scene-to-background validation without writing `build/` (`src/winternight_gen/models.py:727-757,921-930`).
- Engine-load static analysis rejects panoramas other than `240x160` (`src/winternight_gen/static_analysis.py:124-140`).

Prompt wording, candidate selection, composition matching, contact pages, and human taste remain review gates rather than automated assertions. The pipeline enforces deterministic processing and hashes (`src/winternight_gen/asset_pipeline.py:984-1019,1083-1090`).
