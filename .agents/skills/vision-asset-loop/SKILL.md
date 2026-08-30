---
name: vision-asset-loop
description: "Run a reference-controlled local image-generation, visual-review, and refinement loop for repository visual assets. Use when a licensed or original reference must retain its geometry while adopting the project's art direction, especially logos, UI emblems, icons, portraits, backgrounds, or sprite source art; do not use before the visual-art phase gate or to disguise unlicensed copying."
---

# Vision Asset Loop

Read `design/visual_bible.yaml`, `design/asset_manifest.yaml`, and the relevant engine dimensions before generation. Use the repository's `visual-asset-director` contract for approval and provenance.

## Constraints

- Verify the graybox/visual-art phase gate first.
- Start from an original, public-domain, or explicitly licensed reference. Record its URL, local source path, hash, attribution, and license before using it. A model transformation does not erase copyright or ShareAlike obligations.
- Use image-to-image or structural control for required geometry. Do not prompt-engineer around a generator's refusal or ask text-only generation to rediscover a known logo.
- Generated pixels are source art, not engine art. Deterministic crop, mask, palette reduction, layout, and nearest-neighbor scaling remain repository code.
- Never approve at model resolution. The actual runtime surface at native resolution is authoritative.

## Loop

1. **Define the contract.** Write down output dimensions, alpha/chroma behavior, palette ceiling, composition, identity/shape anchors, and what must remain readable at 1×.
2. **Prepare the reference.** Rasterize to the generation canvas, isolate the relevant silhouette, and build a clean Canny control image. Remove text, walls, checkerboards, and unrelated edges before generation. For exact licensed marks, retain the clean reference as the final geometry mask.
3. **Generate a bounded batch.** Use four deterministic seeds with SDXL, Canny ControlNet, and the Pixel Art XL LoRA via `scripts/generate_sdxl_controlnet.py`. Keep the positive prompt below CLIP's 77-token limit. State subject, target style, palette, background, and native-readability goal. Negative-prompt text, watermarks, scenery, blur, broken geometry, and known failure colors.
4. **Make a review sheet.** Label the candidates and inspect them together. Reject text contamination, background leakage, broken loops/limbs, malformed spokes, style drift, and candidates whose apparent detail will vanish when reduced.
5. **Review in context.** Deterministically process each plausible candidate to the exact runtime dimensions and composite it into a real capture. Inspect native 1× first, then nearest-neighbor 4× for pixel defects. A good isolated image can still fail through overlap, weak contrast, wrong scale, or unreadable silhouette.
6. **Diagnose one layer at a time.** Geometry defect → clean or strengthen ControlNet. Palette/style defect → adjust LoRA weight and color prompt. Background/text defect → clean the control image and strengthen negative constraints. Layout defect → change deterministic composition code, not the generator.
7. **Refine.** Generate another four-seed batch only after naming the previous batch's failure. Preserve the best seed and settings. Stop when one candidate passes geometry, palette, native readability, and runtime composition.
8. **Lock geometry and provenance.** When exact licensed geometry matters, apply the clean reference mask to the chosen generated color/texture source. Record reference lineage, model IDs, LoRA, ControlNet, seed, prompt, source hash, output hash, processing version, approval, and license note.
9. **Verify the shipped surface.** Rebuild from source, capture or launch the exact runtime screen, run the focused changed-contract tests, then run the repository-required full check.

## Operational guardrails

- Inspect GPU occupancy before loading SDXL. Do not kill unrelated processes. Ask before pausing a user service; restart it after generation.
- Prefer already-cached compatible models over downloading a second stack. On this workstation the proven path is SDXL 1.0 + `nerijs/pixel-art-xl` + `diffusers/controlnet-canny-sdxl-1.0` + the fp16-fixed SDXL VAE.
- Keep candidates and review sheets outside the repository until selection. Commit only licensed references, the selected source, deterministic processor changes, provenance, and required evidence.
- Generated text is never accepted. Compose lettering deterministically from repository fonts or pixel glyphs.
