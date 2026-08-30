# Nynaeve book-accurate portrait — regen recipe

Blocked 2026-08-29: Codex weekly usage limit, resets **2026-09-03 12:24**.
Zero candidates were generated. Everything below is ready to run unchanged once
credits return. Run from the repository root `/home/chris/git/wot-game`.

Target read (book + owner call): Nynaeve al'Meara, ~25, the youngest Wisdom the
Two Rivers ever accepted — an adult woman with a long face, defined jaw and
cheekbones, adult neck and shoulders; habitually cross, with a pouty/angry set
to mouth and brows; one fist closed around the thick dark braid in a deliberate
tug. Identity anchors retained: long dark braid, blue wool dress, pale apron,
herb pouch.

---

## 1. Exact imagegen prompt text (primary direction, candidates A/B)

```text
handcrafted GBA-era tactical-RPG pixel illustration, readable silhouettes, restrained medieval-rural palette, cool shadows, warm highlights, no photorealism, no text, no logo, no UI, and no recognizable adaptation or actor likeness. Subject: Nynaeve, the village Wisdom of a small rural medieval-fantasy hamlet. She is a grown woman of about twenty-five, the youngest Wisdom her village ever accepted: NOT a teenager, NOT a girl. Adult facial proportions - long oval face, clearly defined jawline and cheekbones, hollowed cheeks rather than round ones, narrowed dark eyes, an adult neck and broad adult shoulders. Her expression is habitually cross and she does not hide it: brows drawn low and hard together, mouth set in a stubborn angry pout, chin lifted in irritation. One hand is raised to her collarbone and grips her thick dark braid in a closed fist, pulling it sharply downward in a deliberate angry tug; the fingers must visibly close around the braid rather than rest beside it. The heavy dark brown braid falls forward over her shoulder and down across her chest. She wears a plain dark blue wool dress with a pale undyed linen apron over it, and a small brown leather herb pouch on a strap at her chest with dried green herbs showing at its mouth. Eye-level three-quarter bust: head, shoulders and upper chest only, filling the frame, head in the upper third. The entire background is one flat field of exact hot magenta RGB 255,0,255, with no gradient, vignette, border, drop shadow or texture, and no magenta anywhere on the figure or her clothing. Portrait aspect roughly 4:5, about 1120x1400. Generate 2 variants and save them as nynaeve-a.png and nynaeve-b.png.
```

Second direction (candidates C/D), if A/B still read young — harder on age,
weathering, and the tug as the point of the pose:

```text
handcrafted GBA-era tactical-RPG pixel illustration, readable silhouettes, restrained medieval-rural palette, cool shadows, warm highlights, no photorealism, no text, no logo, no UI, and no recognizable adaptation or actor likeness. Subject: a stern rural village healer woman named Nynaeve, aged twenty-five, mature and adult - visibly a woman in her mid twenties, never a teenager. Give her the face of an adult working woman: long face, strong jaw, high cheekbones, faint weather lines at the brow and mouth corners, deep-set dark eyes under heavy lowered brows, a firm angry set to a full pouting mouth. She glares straight at the viewer, plainly annoyed. Her left hand is up at her chest, fist closed hard around a thick dark brown braid that hangs forward over her shoulder, and she is yanking it downward - the tug is the point of the pose and the knuckles and gripping fingers must read clearly. Costume: dark blue wool dress, pale linen apron, brown leather herb pouch on a shoulder strap with sprigs of dried herbs. Eye-level bust framing, head and shoulders and upper chest, head high in the frame, strong readable silhouette. Background: one perfectly flat field of pure hot magenta RGB 255,0,255 behind her, edge to edge, no gradient, no border, no vignette, no cast shadow; nothing on the figure may be magenta or pink. Portrait aspect roughly 4:5, about 1120x1400. Generate 2 variants and save them as nynaeve-c.png and nynaeve-d.png.
```

Framing note for candidate selection: `_ai_portrait` fits the whole keyed
subject into `192x160` at centering `(0.5, 0.34)` and then hard-downsamples to
`96x80`, so the gripping fist must sit near the collarbone/jaw. A hand held low
at the waist is cropped away or reduced to noise and the tug will not read.

## 2. Exact codex invocation

```bash
bash /home/chris/.claude/skills/codex-imagegen/scripts/codex-imagegen.sh \
  --dest ".codex-image/nynaeve-book-accurate" \
  "<prompt text from section 1, single argument, double-quoted>"
```

Notes: run from the repository root; allow ~10 min; the script prepends
`$imagegen` itself, so the token must never appear in the prompt string. It
prints `GENERATED_FILES:` with the landed paths. Verify auth first with
`codex exec --skip-git-repo-check --sandbox read-only "say OK"` — while the
weekly limit is active this returns
`ERROR: You've hit your usage limit ... try again at Sep 3rd, 2026 12:24 PM.`

## 3. Exact /tmp dry-process snippet

Judge the **processed** `160x112` sheet at `1x` first, `4x` only to diagnose.
The script below writes only under `/tmp`, never `build/`.

```bash
ASSET_ID=nynaeve_neutral SUBJECT_ID=nynaeve VARIANT=neutral \
SOURCE_PATH=.codex-image/nynaeve-book-accurate/nynaeve-a.png \
STEM=nynaeve-a \
uv run --python 3.11 python - <<'PY'
import os
import sys
from pathlib import Path

from PIL import Image

from winternight_gen.asset_pipeline import _ai_portrait
from winternight_gen.build_report import sha256
from winternight_gen.models import AssetManifestEntry

root = Path.cwd()
asset_id = os.environ["ASSET_ID"]
source_path = os.environ["SOURCE_PATH"]
source_hash = sha256(root / source_path)

asset = AssetManifestEntry(
    id=asset_id,
    type="portrait",
    subject_id=os.environ["SUBJECT_ID"],
    variant=os.environ["VARIANT"],
    provenance="ai_generated",
    source_path=source_path,
    processed_path=f"resources/portraits/{asset_id}.png",
    source_hash=source_hash,
    processing_profile=os.environ.get("PROFILE", "standard"),
    processing_version="lt-ai-portrait-6",
    approval_status="pending",
    license_note="Temporary single-source hash probe.",
)

out = Path("/tmp") / f"winternight-{asset_id}-hash-probe"
out.mkdir(parents=True, exist_ok=True)
stem = os.environ.get("STEM", asset_id)
processed = out / f"{stem}.png"
_ai_portrait(processed, asset, root)

with Image.open(processed) as sheet:
    rgba = sheet.convert("RGBA")
    size = rgba.size
    colors = rgba.getcolors(maxcolors=1 << 20) or []
    keyed_magenta = [
        (r, g, b, a)
        for _, (r, g, b, a) in colors
        if a == 255 and r >= 110 and b >= 90 and min(r, b) - g >= 35
    ]
    face = rgba.crop((32, 0, 128, 80))
    face.save(out / f"{stem}-face-1x.png")
    face.resize((face.width * 4, face.height * 4), Image.Resampling.NEAREST).save(
        out / f"{stem}-face-4x.png"
    )
    rgba.resize((size[0] * 4, size[1] * 4), Image.Resampling.NEAREST).save(
        out / f"{stem}-sheet-4x.png"
    )

print(f"source_hash: {source_hash}")
print(f"output_hash: {sha256(processed)}")
print(f"output: {processed}")
print(f"size: {size}  colors: {len(colors)}  keyed_magenta: {keyed_magenta}")
if size != (160, 112):
    print("FAIL: dimensions", file=sys.stderr)
if len(colors) > 64:
    print("FAIL: palette", file=sys.stderr)
PY
```

Harness correctness is already proven: run verbatim against
`assets/generated_sources/egwene-book-accurate-v1.png` with
`ASSET_ID=egwene_neutral SUBJECT_ID=egwene VARIANT=neutral` and it reproduces
the manifest's recorded pair exactly —
`source_hash: 4be08913f2d62cb89cb2636f74ad2ff8496b8e427d380ad255edf5438f50e231`,
`output_hash: 1b059761be48d332571ed360e5692d1def5b15aa81351940f34dcad11ee30da6`,
`size: (160, 112)  colors: 63  keyed_magenta: []`.

Accept a candidate only when the `1x` processed face reads as a cross woman of
about twenty-five tugging her braid: exactly `160x112`, at most 64 colours,
`keyed_magenta: []`, silhouette intact at `1x`, adult age at `1x`, angry/pouty
expression legible at `1x`, braid-tug gesture legible at `1x`.

## 4. Promote the accepted candidate

```bash
cp .codex-image/nynaeve-book-accurate/nynaeve-<accepted>.png \
   assets/generated_sources/nynaeve-book-accurate-v1.png
```

Then recompute both hashes against the **landed** source path (the manifest
`source_hash` must be the hash of `assets/generated_sources/...`, and the
`output_hash` must come from a probe run whose `SOURCE_PATH` is that same landed
path — the bytes are identical to the `.codex-image/` copy, but re-run to be
certain):

```bash
ASSET_ID=nynaeve_neutral SUBJECT_ID=nynaeve VARIANT=neutral \
SOURCE_PATH=assets/generated_sources/nynaeve-book-accurate-v1.png \
STEM=nynaeve-accepted \
uv run --python 3.11 python - <<'PY'
... (identical snippet from section 3) ...
PY
```

Standalone hash of either file, using the repository's own helper:

```bash
uv run --python 3.11 python -c \
  "from pathlib import Path; from winternight_gen.build_report import sha256; \
   print(sha256(Path('assets/generated_sources/nynaeve-book-accurate-v1.png')))"
```

## 5. Exact `design/asset_manifest.yaml` diff

Replace the whole `nynaeve_neutral` entry (currently lines 425-443). Note the
deleted `source_grid` / `source_cell` pair — the new source is a single bust,
not a `3x2` sheet cell — and `processing_version` moving `lt-ai-portrait-5` ->
`lt-ai-portrait-6`. `id`, `type`, `subject_id`, `variant`, `provenance`,
`processed_path`, `provider`, `model`, `seed`, `approval_status`, and
`license_note` are unchanged.

```diff
   - id: nynaeve_neutral
     type: portrait
     subject_id: nynaeve
     variant: neutral
     provenance: ai_generated
-    source_path: assets/generated_sources/wave_c_identity_chroma-v1.png
+    source_path: assets/generated_sources/nynaeve-book-accurate-v1.png
     processed_path: resources/portraits/nynaeve_neutral.png
-    prompt: Nynaeve identity portrait from the Wave C six-character visual reference sheet; young village Wisdom with long shoulder braid, pale apron, blue wool dress, and herb pouch.
+    prompt: Identity-preserving Nynaeve portrait regenerated for book accuracy; the village Wisdom as a grown woman of about twenty-five with adult facial proportions, a cross pouting set to brows and mouth, and one fist closed around her thick dark braid in a deliberate tug, over a blue wool dress, pale apron, and herb pouch on exact hot-magenta chroma.
     reference_ids: [wave_c_identity_sheet]
     provider: Codex CLI
     model: gpt-image-2
     seed: null
-    source_hash: 17e0f6b65a08b99eac3e240805b9719bb60fab433b6abaa3f9dc054f656253ea
-    output_hash: 7aa335052319fbc8fcc1e58c165e953a957d9344cb039a0ec19f7fa8cae9b7a1
-    source_grid: [3, 2]
-    source_cell: [0, 0]
-    processing_version: lt-ai-portrait-5
+    source_hash: TODO_SOURCE_SHA256
+    output_hash: TODO_OUTPUT_SHA256
+    processing_version: lt-ai-portrait-6
     approval_status: approved
     license_note: Original AI-generated character design; no actor or adaptation likeness requested.
```

`TODO_SOURCE_SHA256` / `TODO_OUTPUT_SHA256` come from the section-4 probe run
(`source_hash:` / `output_hash:` lines). This matches the `egwene_neutral`
precedent at `design/asset_manifest.yaml:262-278` field for field.

## 6. `assets/generated_sources/PROVENANCE.md`

Extend the existing `### Book-accuracy portrait corrections` block (currently
"Five named-cast busts were regenerated ..."). Same form as its neighbours:

> A sixth correction replaced `nynaeve_neutral`. Owner review rejected the Wave C
> sheet cell as too young for the character; `nynaeve-book-accurate-v1.png` is a
> direct single-cell bust on exact hot-magenta chroma showing the Wisdom as an
> adult woman in her mid twenties with a cross, pouting set to the face and one
> fist closed around her braid in a deliberate tug. It carries no `source_grid`
> or `source_cell` and processes under `lt-ai-portrait-6`.

## 7. Already landed (do not redo)

`design/visual_bible.yaml:17` nynaeve identity anchors:

```
- nynaeve: [young_village_wisdom, long_dark_braid, blue_wool_dress, pale_apron, herb_pouch]
+ nynaeve: [mid_twenties_wisdom, braid_tugging_scowl, long_dark_braid, blue_wool_dress, pale_apron, herb_pouch]
```
