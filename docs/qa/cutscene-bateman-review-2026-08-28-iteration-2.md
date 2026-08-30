# Winternight mobile-landscape cutscene — Bateman iteration 2 re-review

**Mode:** UI / web, fresh independent cutscene-presentation review
**Reviewed surface:** locally built cutscene at `http://127.0.0.1:39793/`
**Scope:** cutscene presentation only. Map play is unchanged and outside this review.
**Viewport evidence:** 844×390 and 812×375, both with the cutscene class active.
**Verdict:** **A− — PASS. Iteration 2 may ship.**

## 1. Evidence and capture report

### Durable evidence

| Viewport | Screenshot | Canvas measurement | Layout result |
|---|---|---|---|
| 844×390 | [`docs/qa/cutscene-bateman-2026-08-28-iteration-2-844x390.webp`](cutscene-bateman-2026-08-28-iteration-2-844x390.webp) | `x=182`, `y=35`, `480×320` | No overflow; every control has `0 px²` intersection with the canvas |
| 812×375 | [`docs/qa/cutscene-bateman-2026-08-28-iteration-2-812x375.webp`](cutscene-bateman-2026-08-28-iteration-2-812x375.webp) | `x=166`, `y=27.5`, `480×320` | No overflow; every control has `0 px²` intersection with the canvas |

The complete surfaces were re-graded from these captures. The assessment is not a defect-only comparison and does not carry forward an earlier grade.

### Mechanical findings

The mechanics pass independently of the aesthetic judgment:

- The cutscene state is active at both viewports.
- The canvas remains exactly `480×320` in both captures. Its aspect and pixel geometry are preserved rather than stretched to fill the viewport.
- At 844×390, the canvas is centered at `x=182`, `y=35`; at 812×375, it is centered at `x=166`, `y=27.5`.
- There is no horizontal or vertical overflow in either measurement set.
- D-pad buttons are `44×44`, meeting the 44 px minimum.
- A and B are `64×64`, comfortably exceeding the minimum.
- Log and Start are `48×48`, meeting the preferred 48 px size.
- Full Screen is `118.48×48`, meeting the preferred 48 px height with ample horizontal label room.
- Every measured control/canvas intersection area is exactly `0 px²` at both viewports.
- The scene background, dialogue frame, dialogue text, prompt marker, and all controls are visibly present; neither screenshot shows a missing asset, broken-image treatment, clipped primary control, or obvious local-build mismatch.
- Focus and pressed CSS exists. Static captures do not demonstrate its rendered appearance, so this report does not pretend that those interaction states were visually exercised.
- No console transcript was part of the supplied evidence. There is no visible error state or broken asset in either capture, but silent console diagnostics are outside what these screenshots and measurements can prove.

### Visual-taste findings

The visual result also passes; this is not merely a geometrically correct layout. The unscaled pixel-art scene is the unmistakable protagonist, while the controls recede into a quiet charcoal shell. The dialogue frame has strong period-appropriate contrast, the two-line composition scans immediately, and the cool prompt marker supplies the only saturated accent. The left and right control rails balance the centered canvas without touching it or competing with its narrative content.

The sole visible polish concern is microtypography on **Log** and **Start**: the 48 px targets are excellent, but their labels rasterize notably smaller and lighter than the rest of the control language. They remain identifiable in both captures, so this is not a readability blocker; it is the one detail preventing an unqualified A.

## 2. Shipping-blocker checks

### 844×390

| Check | Result | Evidence |
|---|---|---|
| Overflow or clipped content | **PASS** | No overflow. The `480×320` canvas fits at `x=182`, `y=35`; all controls remain fully inside the viewport. |
| Tap targets below 44 px | **PASS** | D-pad `44×44`; A/B `64×64`; Log/Start `48×48`; Full Screen `118.48×48`. |
| Control occlusion of cutscene | **PASS** | Every control has `0 px²` intersection with the canvas. |
| Unreadable body/dialogue text | **PASS** | Both dialogue lines are fully visible, high contrast, and cleanly separated inside the frame. Log/Start microtype is a polish issue, not body text and not an unidentified target. |
| Hidden or dead-ended primary action | **PASS** | A and B are prominent, separated, and visibly available in the right rail; the D-pad and utility actions are also exposed. |
| Missing asset or obvious deploy mismatch | **PASS** | Scene art, dialogue chrome, prompt marker, and controls all render coherently. No visible broken state. |
| Relevant interaction-state evidence | **PASS WITH EVIDENCE LIMIT** | Focus/pressed CSS is present, but this static screenshot does not prove the rendered states. No static-state blocker is visible. |

**Shipping blockers at 844×390: 0.**

### 812×375

| Check | Result | Evidence |
|---|---|---|
| Overflow or clipped content | **PASS** | No overflow. The `480×320` canvas fits at `x=166`, `y=27.5`; the tighter height does not crop the scene or dialogue. |
| Tap targets below 44 px | **PASS** | Same passing dimensions: D-pad `44×44`; A/B `64×64`; Log/Start `48×48`; Full Screen `118.48×48`. |
| Control occlusion of cutscene | **PASS** | Every control has `0 px²` intersection with the canvas. |
| Unreadable body/dialogue text | **PASS** | The complete two-line sentence and prompt marker remain legible; no line or glyph is clipped. |
| Hidden or dead-ended primary action | **PASS** | A/B, D-pad, Log, Start, and Full Screen are visible and spatially distinct despite the narrower viewport. |
| Missing asset or obvious deploy mismatch | **PASS** | The complete scene and interface render with no visible broken asset or mismatched shell. |
| Relevant interaction-state evidence | **PASS WITH EVIDENCE LIMIT** | Focus/pressed CSS is present, but the static capture does not visually exercise those states. No static-state blocker is visible. |

**Shipping blockers at 812×375: 0.**

## 3. Seven-criterion scorecards

### Screen A — 844×390 cutscene

**Screen grade: A−**

| Criterion | Grade | Assessment | Exact A-tier delta, if any |
|---|---:|---|---|
| 1. Bone Structure | **A** | The centered `480×320` stage establishes a rigid primary grid. The left D-pad and right action rail occupy separate lanes, with measured zero canvas intersection and comfortable outer margins. | None. Preserve the centered canvas and independent control rails. |
| 2. Restraint | **A** | The surface contains only scene, dialogue, and necessary controls. Charcoal controls yield to the art; no decorative panel, redundant legend, or competing callout dilutes the cutscene. | None. Do not add chrome around the canvas. |
| 3. Texture & Materiality | **A** | Pixel art, graphite controls, cool borders, and the dark shell speak one restrained material language. The dialogue frame feels native to the game rather than pasted on top of a web template. | None. The current low-sheen control treatment is coherent. |
| 4. Typographic Confidence | **A−** | Dialogue typography is decisive, highly contrasted, and comfortably fitted into two lines. Full Screen and A/B scan cleanly, but Log/Start appear undersized relative to their `48×48` surfaces. | Set the computed Log/Start label size to at least `10px` with `line-height: 1`; keep both targets exactly `48×48` and centered. |
| 5. Color Discipline | **A** | Near-black and charcoal carry the shell; warm off-white identifies action labels; the cyan-violet prompt marker is a precise semantic accent. Nothing competes chromatically with the mountain scene. | None. Keep saturated color reserved for game feedback. |
| 6. Breathing Room | **A** | The 35 px top and bottom staging and the separated control lanes make the composition feel framed, not packed. Empty space is functional: it isolates play controls from narrative content. | None. Do not enlarge the canvas into the controls. |
| 7. Craft Details | **A−** | Target sizing, consistent borders, crisp canvas geometry, complete line wrapping, and zero intersection are all excellent. The remaining uncertainty is evidentiary: focus and pressed styles exist but are not visible in this static capture. | For an A-grade evidence packet, add one 844×390 capture with a keyboard focus ring visible and one with A or B visibly pressed; do not change the passing geometry. |

### Screen B — 812×375 cutscene

**Screen grade: A−**

| Criterion | Grade | Assessment | Exact A-tier delta, if any |
|---|---:|---|---|
| 1. Bone Structure | **A** | The canvas remains exactly centered at `x=166` and retains `480×320`; the 812 px width compresses the side lanes without collapsing them. Zero intersections prove that the apparent closeness is controlled rather than accidental. | None. The half-pixel vertical centering does not produce visible softness in the supplied capture; no speculative nudge is warranted. |
| 2. Restraint | **A** | Every object is functional, and the narrower view does not trigger a fallback panel, duplicated action, or explanatory clutter. The stage remains visually singular. | None. Keep the current one-stage composition. |
| 3. Texture & Materiality | **A** | The same dark control material and pixel-art frame survive the reduced viewport without looking like a separate responsive theme. Borders, fills, and label colors remain coherent. | None. Preserve material parity across both widths. |
| 4. Typographic Confidence | **A−** | The dialogue retains its intended two-line rhythm and the prompt marker remains attached to the sentence. As at 844×390, Log/Start are the only labels whose raster presence feels too timid for their targets. | Set Log/Start to at least `10px` computed size with `line-height: 1`; retain `48×48` targets and current centering. |
| 5. Color Discipline | **A** | The scene owns the chromatic range while controls remain neutral and action labels warm. The single prompt accent is enough to direct the eye without creating UI noise. | None. No new accent color is needed. |
| 6. Breathing Room | **A** | Even with only 55 px of total vertical surplus, the canvas is evenly staged at `y=27.5`; the dialogue and controls have room to read as separate systems. No area feels pinched or stranded. | None. Preserve the even vertical centering. |
| 7. Craft Details | **A−** | The hardest viewport retains exact canvas dimensions, minimum-or-better targets, full labels, and zero overlap. Static evidence still cannot show whether focus and pressed treatments are as polished as the resting state. | Add focused and pressed 812×375 captures to a future evidence packet; retain current dimensions and non-intersection guarantees. |

## 4. Top five strengths

1. **Aspect-ratio integrity:** the `480×320` canvas is identical at both widths. Pixel geometry is treated as authored artwork, not responsive filler, so the landscape and dialogue frame remain crisp and credible.
2. **Measured separation:** every control/canvas intersection is `0 px²` in both measurement sets. This is stronger than “looks clear”; it proves the game image and input surfaces have distinct spatial ownership.
3. **Touch-first sizing:** the smallest controls are the `44×44` D-pad buttons, while frequent and utility actions reach `64×64` and `48×48`. The hierarchy is both accessible and visually intelligible.
4. **Disciplined narrative hierarchy:** the eye lands on the landscape, then the dialogue, then the prompt marker. The shell and controls support the scene instead of becoming a competing dashboard.
5. **Responsive continuity:** 844×390 and 812×375 feel like the same designed object. The tighter viewport preserves art scale, materials, control order, and dialogue rhythm rather than invoking an visibly improvised breakpoint.

## 5. Ranked top fixes

There is **one visible refinement** and **two evidence refinements**. No shipping fix is required; manufacturing a longer list would violate the restraint that makes this surface successful.

1. **Raise Log/Start microtype one step — visual polish, low risk.** In both screenshots the labels occupy only a small fraction of their `48×48` targets and are the least confident type on the surface. Set their computed `font-size` to at least `10px`, use `line-height: 1`, preserve the exact target size, and verify optical centering. This closes the only visible A-tier gap without adding weight or changing hierarchy.
2. **Capture focus-visible appearance — evidence completion, not a discovered defect.** At each viewport, record a screenshot with keyboard focus on Full Screen or Start. The ring should be fully visible, remain outside the glyph, avoid canvas intersection, and cause no layout shift. CSS presence is mechanical evidence; a rendered capture is taste evidence.
3. **Capture the pressed state — evidence completion, not a discovered defect.** At each viewport, record A or B in its active/pressed treatment. Confirm that feedback is obvious without shrinking the target, moving neighboring controls, or introducing a saturated accent that competes with the scene.

**Do not change:** canvas scale, centered stage coordinates, control target dimensions, side-rail separation, or the quiet charcoal palette. Those are already passing decisions, not areas for another redesign pass.

## 6. Overall verdict and exit bar

**Overall grade: A−.** The complete mobile-landscape cutscene is compositionally disciplined, mechanically sound, and aesthetically coherent at both reviewed viewports. Its strongest decision is the refusal to trade authored pixel geometry for screen fill: the fixed `480×320` stage stays centered while full-size controls live in measured, non-overlapping rails. The sole visible imperfection is the timid Log/Start microtype; increasing it to a `10px` minimum would have the highest remaining aesthetic impact. Focus/pressed styling exists but remains a static-evidence limitation rather than an observed defect.

| Exit condition | Decision |
|---|---|
| Overall grade A− or better | **PASS — A−** |
| Zero shipping blockers | **PASS — 0 at 844×390; 0 at 812×375** |
| No screen below B+ | **PASS — 844×390 is A−; 812×375 is A−** |
| Iteration 2 ship decision | **PASS — may ship the reviewed cutscene presentation** |

**Exit-bar decision:** **MET.** Iteration 2 may ship within the reviewed cutscene-presentation scope. Map play is not included in this decision.
