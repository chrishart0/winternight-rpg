# Winternight mobile-landscape cutscene — Bateman review, iteration 1

**Review date:** 2026-08-28
**Mode:** UI/web, independent pre-fix review
**Surface:** Live cutscene presentation only; map play and map presentation are outside this review
**Live URL recorded for the surface:** <https://wot-game.arcadian.cloud/>
**Overall grade:** **D — do not ship**

## Evidence and capture report

### Evidence key

- **[Observed]** Visible directly in one or both supplied screenshots.
- **[Measured]** Supplied DOM/layout measurement.
- **[Derived]** Arithmetic from supplied measurements, not a new DOM measurement.
- **[Inference]** A likely interaction or implementation consequence that the static captures cannot prove.

### Reviewed captures

| Viewport | Screenshot | Evidence summary |
|---|---|---|
| 844 × 390 | `docs/qa/cutscene-bateman-2026-08-28-iteration-1-844x390.webp` | **[Measured]** A 480 × 320 backing canvas is displayed at 844 × 390. The displayed ratio is 2.164:1 rather than the native 1.5:1, producing 44.3% horizontal aspect distortion. There is no document overflow. Directional targets measure 46–48px, A/B targets 83px, and Log/Start targets only 46 × 22px. Controls overlap both dialogue and scene art. |
| 812 × 375 | `docs/qa/cutscene-bateman-2026-08-28-iteration-1-812x375.webp` | **[Measured]** The canvas displays at 812 × 375 and there is no document overflow. **[Derived, using the supplied 480 × 320 backing size]** The displayed ratio is 2.165:1; horizontal scaling is about 44.4% greater than vertical scaling. **[Observed]** The same control arrangement obscures dialogue and scene art, and Log/Start retain the same visibly undersized treatment. |

### What the captures establish

- **[Observed]** The cutscene background is present in both captures; there is no visible missing-image placeholder or broken asset icon.
- **[Observed]** The dialogue panel is present and high-contrast, but the D-pad covers the beginning of both visible lines and the B button covers text on the first line. The controls therefore obscure authored dialogue, not merely decorative pixels.
- **[Observed]** A, B, the D-pad, Full Screen, Log, and Start are all visually present.
- **[Measured]** Neither viewport has document-level overflow. This is a pass, but it does not offset the canvas distortion or occlusion.
- **[Measured]** At 844 × 390, the 480 × 320 canvas has width scale $844/480 = 1.758$ and height scale $390/320 = 1.219$. The unequal scales are the source of the supplied 44.3% horizontal distortion.
- **[Derived]** At 812 × 375, the equivalent scales are $812/480 = 1.692$ and $375/320 = 1.172$, or about 44.4% excess horizontal scaling.
- **[Inference]** The static screenshots do not prove click behavior, focus-visible treatment, pressed states, audio, progression, or whether every asset request and script completed without a console error.

### Evidence limitations

This review intentionally uses the two supplied durable screenshots and supplied DOM evidence. No fresh browser session, console log, network trace, or interaction-state capture was supplied. Therefore:

- **Console errors:** not established; no pass is claimed.
- **Broken network assets:** not established; only the absence of an obvious broken visual asset in the screenshots is observed.
- **Computed dialogue font size:** not supplied. The glyphs are visibly substantial, but readable sizing cannot receive a mechanical pass because the text is distorted and occluded.
- **812 × 375 target boxes:** no separate DOM target dimensions were supplied. The 812 screenshot visibly preserves the same undersized Log/Start geometry; applying the 844 × 390 measurement to that viewport is explicitly an inference about the shared layout, not a second measurement.

## Shipping-blocker checks

### 844 × 390

| Check | Result | Evidence and ruling |
|---|---|---|
| Horizontal overflow / clipped document | **Pass** | **[Measured]** No document overflow. |
| Native aspect and undistorted authored image | **FAIL — shipping blocker** | **[Measured]** 480 × 320 is stretched to 844 × 390: 2.164:1 versus 1.5:1, with 44.3% horizontal aspect distortion. Pixel art, dialogue glyphs, frame thicknesses, and the entire scene are visibly widened. |
| Minimum 44px tap targets | **FAIL — shipping blocker** | **[Measured]** Log and Start are 46 × 22px; the 22px height is exactly half the 44px minimum. Directional targets at 46–48px clear the minimum, although 46px misses the preferred 48px. A/B at 83px clear both thresholds. |
| Dialogue remains unobscured | **FAIL — shipping blocker** | **[Observed + Measured]** The supplied evidence states that controls overlap dialogue and scene art. The D-pad masks line openings, while B masks first-line characters. |
| Primary controls visually discoverable | **Pass, visibility only** | **[Observed]** A, B, D-pad, Full Screen, Log, and Start are visible. **[Inference]** Their operability is not established by a static capture. |
| Readability | **Fail** | **[Observed]** The text is large enough to recognize, but a readable-size pass is irrelevant while glyphs are non-uniformly stretched and words are hidden under controls. |
| Broken assets / console / deploy mismatch | **Not established** | **[Observed]** No obvious broken visual asset. No console or network evidence was supplied. |

### 812 × 375

| Check | Result | Evidence and ruling |
|---|---|---|
| Horizontal overflow / clipped document | **Pass** | **[Measured]** No document overflow. |
| Native aspect and undistorted authored image | **FAIL — shipping blocker** | **[Measured + Derived]** The canvas displays at 812 × 375. Against the supplied 480 × 320 backing size, this is 2.165:1 versus 1.5:1 and about 44.4% excess horizontal scaling. |
| Minimum 44px tap targets | **FAIL — shipping blocker** | **[Observed + Inference]** Log/Start visibly retain the same shallow control treatment as the measured 46 × 22px controls at 844 × 390. Because separate 812 DOM boxes were not supplied, the exact repeated value is not claimed as a second measurement; this viewport fails until both controls are proven at least 44 × 44px. |
| Dialogue remains unobscured | **FAIL — shipping blocker** | **[Observed]** The D-pad covers the start of both dialogue lines and B covers the first line. The narrower viewport does not create a collision-free composition. |
| Primary controls visually discoverable | **Pass, visibility only** | **[Observed]** All named controls are visible. **[Inference]** Operability and interaction feedback are not established. |
| Readability | **Fail** | **[Observed]** The text remains recognizable but not continuously readable because controls hide characters and the canvas is non-uniformly stretched. |
| Broken assets / console / deploy mismatch | **Not established** | **[Observed]** No obvious broken visual asset. No console or network evidence was supplied. |

## Seven-criterion scorecards

### Viewport: 844 × 390

**Screen description:** landscape cutscene scene, dialogue panel at the bottom, Full Screen at upper right, D-pad at lower left, A/B at lower right, and Log/Start along the lower edge.

| Criterion | Grade | Assessment and exact correction |
|---|---:|---|
| 1. Bone Structure | **D** | **[Measured]** The root geometry violates the authored 3:2 canvas: a 480 × 320 surface is forced into 844 × 390. **Fix:** preserve 480 × 320 at 1× in this viewport, centered, yielding 182px side rails and 35px total vertical remainder; place touch controls in the rails rather than over the canvas. |
| 2. Restraint | **C-** | **[Observed]** Every control is simultaneously asserted over the authored scene, and A/B at 83px become dominant visual objects rather than quiet input affordances. **Fix:** use 64 × 64px A/B targets, 48 × 48px directional cells, and move utility controls out of the dialogue layer. |
| 3. Texture & Materiality | **C** | **[Observed]** The atmospheric pixel-art scene and framed charcoal dialogue panel speak one material language; glossy translucent violet circles, blur-like shadows, and the modern black Full Screen pill speak another. **Fix:** use one opaque pixel-compatible control treatment with a 2px keyline, 4px radius, and no soft shadow blur or glossy gradient. |
| 4. Typographic Confidence | **C-** | **[Observed + Measured]** The pixel face is stylistically decisive, but its letterforms are widened by the 44.3% aspect error and entire characters are hidden. **Fix:** render the canvas uniformly at 1× here, keep all controls outside the dialogue rectangle, and preserve at least 16 backing-canvas pixels of text inset on all sides. |
| 5. Color Discipline | **B-** | **[Observed]** Scene neutrals and the charcoal dialogue surface are coherent, while violet controls introduce a saturated competing system without a semantic reason visible in the cutscene. **Fix:** derive controls from the existing dialogue-frame neutral palette and reserve the existing dialogue advance accent as the only saturated signal. |
| 6. Breathing Room | **D** | **[Observed]** There is abundant scene area but effectively no protected interface space: D-pad, A/B, Log/Start, and the dialogue panel occupy the same lower band. **Fix:** allocate 182px side rails around a centered 480px canvas and require zero bounding-box intersection between any control and the canvas/dialogue panel. |
| 7. Craft Details | **D** | **[Measured]** Log/Start are 46 × 22px, directional cells vary from 46–48px, and control scales range from 22px high to 83px. **Fix:** set every utility target to at least 48 × 48px, each directional cell to exactly 48 × 48px, and A/B to exactly 64 × 64px, with a common focus/pressed-state vocabulary verified in a fresh capture. |

**Viewport grade: D.** The screen is mechanically present but compositionally broken: authored pixels are deformed, dialogue is obscured, and two controls fail the minimum target-height gate.

### Viewport: 812 × 375

**Screen description:** the same landscape cutscene arrangement at the narrower supplied mobile-landscape viewport.

| Criterion | Grade | Assessment and exact correction |
|---|---:|---|
| 1. Bone Structure | **D** | **[Measured + Derived]** The canvas is forced to 812 × 375, approximately 2.165:1 against its native 1.5:1. **Fix:** preserve the 480 × 320 canvas at 1×, centered, yielding 166px side rails and 55px total vertical remainder. |
| 2. Restraint | **C-** | **[Observed]** The narrower capture makes the control competition worse: D-pad and B consume the dialogue line while A floats over the scene. **Fix:** keep A/B at 64 × 64px, directional cells at 48 × 48px, and utility controls at 48 × 48px inside the 166px rails, never over authored content. |
| 3. Texture & Materiality | **C** | **[Observed]** The scene and dialogue frame remain coherent; the glossy purple controller skin and black pill still feel composited from a different product. **Fix:** use the same 2px-keyline, 4px-radius, no-soft-shadow control material as the 844px layout. |
| 4. Typographic Confidence | **D+** | **[Observed]** The first characters of both visible lines are masked, first-line text is masked at the right, and non-uniform scaling widens the glyphs. **Fix:** keep controls wholly outside the dialogue rectangle and preserve a uniform 16px backing-canvas text inset after native-ratio rendering. |
| 5. Color Discipline | **B-** | **[Observed]** The neutral scene/dialogue palette still works, but violet controls remain the loudest color family despite being secondary chrome. **Fix:** return controls to the dialogue-frame neutrals and retain one saturated advance/status accent only. |
| 6. Breathing Room | **D** | **[Observed]** The lower portion is collision, not density: controls, dialogue, and bottom-edge utilities stack into the same visual band. **Fix:** use the 166px side rails and maintain a 12px minimum outer safe inset, increased with `env(safe-area-inset-*)` where required. |
| 7. Craft Details | **D** | **[Observed + Inference]** Log/Start remain visibly half-height relative to acceptable touch controls, the D-pad scale is not normalized, and the lower controls crowd the viewport edge. **Fix:** prove 48 × 48px minimum boxes for Log/Start in 812px DOM evidence, normalize directional cells to 48px, and keep every control at least 12px from the physical edge or safe-area boundary. |

**Viewport grade: D.** The smaller screen reproduces every structural defect and gives the dialogue even less visual protection.

## Top five strengths

1. **The cutscene establishes place immediately.** **[Observed]** The distant mountains, fortified foreground, and broad tonal depth create a clear cinematic establishing shot without ornamental UI competing in the upper center. This is strong visual hierarchy in the authored scene.
2. **The dialogue panel has decisive contrast.** **[Observed]** White pixel type on a dark framed surface separates dialogue from the detailed background. The panel material belongs to the scene's pixel-art vocabulary even though the controls do not.
3. **The dialogue-advance cue is economical.** **[Observed]** A single small colored marker at the end of the second line communicates progression without another text label. This is disciplined semantic accent use.
4. **Core controller semantics are recognizable.** **[Observed]** The cross-shaped D-pad and large A/B labels are immediately legible as game inputs. Discoverability is not the problem; scale and placement are.
5. **The document itself does not overflow.** **[Measured]** Both 844 × 390 and 812 × 375 remain within the viewport. The responsive shell has basic containment even though the contained canvas is distorted.

## Top ten fixes, ranked by impact

### 1. Restore the authored 3:2 canvas without non-uniform scaling

- **Wrong:** **[Measured]** 480 × 320 becomes 844 × 390, changing 1.5:1 to 2.164:1 and producing 44.3% horizontal distortion. **[Derived]** 812 × 375 produces about 44.4% horizontal distortion.
- **Make it:** At both reviewed viewports, render the backing canvas at exactly 480 × 320 CSS px, centered and unwarped. Do not independently force width and height to `100%`.
- **Why:** Aspect fidelity is foundational craft; every authored shape, glyph, and border is otherwise wrong before any polish begins.
- **Affected:** Both reviewed cutscene viewports.

### 2. Give controls dedicated side rails instead of overlaying authored content

- **Wrong:** **[Observed + Measured]** Controls intersect both dialogue and scene art.
- **Make it:** With a centered 480px canvas, use the remaining horizontal space as two dedicated rails: 182px each at 844px and 166px each at 812px. Require `intersection(controlRect, canvasRect) = 0` for every touch control.
- **Why:** Functional chrome must frame cinematic content, not erase it.
- **Affected:** D-pad, A, B, Full Screen, Log, and Start at both viewports.

### 3. Raise Log and Start to accessible touch size

- **Wrong:** **[Measured at 844]** Each is 46 × 22px; the height is 22px below the 44px minimum and 26px below the preferred 48px.
- **Make it:** Use 48 × 48px boxes for both controls at both viewports, with the visual label centered inside the full interactive box. Re-measure the 812px viewport separately.
- **Why:** A visible label is not an operable mobile target. This is a hard shipping gate, not polish.
- **Affected:** Log and Start.

### 4. Guarantee a zero-occlusion dialogue safe area

- **Wrong:** **[Observed]** D-pad hides the openings of both visible lines; B hides first-line characters.
- **Make it:** Keep every control outside the dialogue rectangle and preserve a 16px inset in backing-canvas coordinates between glyphs and the panel frame. Add a DOM assertion that no control rectangle intersects the dialogue rectangle.
- **Why:** Dialogue is the primary cutscene content. Hiding words is equivalent to clipping the primary action on a product screen.
- **Affected:** Both lines of dialogue at both viewports.

### 5. Normalize control hierarchy

- **Wrong:** **[Measured]** The screen mixes 46–48px directional targets, 83px A/B controls, and 22px-high utility controls. The nearly 4:1 height range makes hierarchy look accidental.
- **Make it:** Directional cells: 48 × 48px. A/B: 64 × 64px. Log/Start: 48 × 48px. Full Screen: at least 48px high. Keep all target dimensions on this 16px/48px/64px system.
- **Why:** Hierarchy should reflect action importance without sacrificing target consistency or content area.
- **Affected:** All touch controls.

### 6. Replace the glossy controller skin with the cutscene's material language

- **Wrong:** **[Observed]** Soft violet gradients, large circular highlights, and blurred depth effects conflict with the crisp pixel scene and dialogue frame.
- **Make it:** Use an opaque neutral fill derived from the dialogue panel, a 2px keyline, a 4px radius, and no glossy gradient or soft shadow blur. Keep directional and action controls in one material family.
- **Why:** A premium surface has one coherent physical logic; this currently looks like a controller overlay pasted onto a different game.
- **Affected:** D-pad, A, and B at both viewports.

### 7. Preserve pixel-letterform geometry

- **Wrong:** **[Observed + Measured]** Dialogue glyphs are visibly widened by the unequal canvas scales.
- **Make it:** Render at the proposed 480 × 320 1× CSS size in these viewports and use one uniform scale factor at any other breakpoint. Never scale width and height independently.
- **Why:** Pixel typography depends on exact geometry; distortion makes deliberate letterforms look counterfeit.
- **Affected:** Dialogue type, advance marker, frame, and all scene pixels.

### 8. Establish a real safe-area rule at the physical edges

- **Wrong:** **[Observed]** Log/Start sit against the lower edge and A/B crowd the right edge; the captures leave no convincing device-safe margin.
- **Make it:** Keep controls at least 12px from the viewport edge, using `max(12px, env(safe-area-inset-left/right/top/bottom))` on the relevant side.
- **Why:** Edge crowding reads unfinished and risks collision with browser or device affordances.
- **Affected:** Full Screen, A/B, Log/Start, and D-pad.

### 9. Demote and integrate Full Screen

- **Wrong:** **[Observed]** The black rounded pill floats over the brightest part of the scene and uses a third material system distinct from both dialogue and controller chrome.
- **Make it:** Place Full Screen in the right control rail, keep it at least 48px high, and apply the same neutral keyline material as the other utility controls.
- **Why:** A utility action should remain findable without becoming a foreign object inside the cinematic frame.
- **Affected:** Full Screen at both viewports.

### 10. Prove interaction craft in the next capture set

- **Wrong:** **[Inference]** Static screenshots provide no evidence for focus-visible, pressed, disabled, or touch-active feedback; these states cannot be awarded a pass.
- **Make it:** Define and capture one consistent pressed state and one keyboard focus-visible state for D-pad, A/B, Full Screen, Log, and Start. Keep state changes within the same geometry so controls do not shift.
- **Why:** Interaction feedback is part of craft, and a visually repaired still is not sufficient shipping evidence for an input surface.
- **Affected:** All cutscene controls; no map behavior is implicated.

## Overall verdict

**D — do not ship.** The authored scene and dialogue-panel foundation are promising, but the responsive presentation fails at the skeletal level. Both reviewed mobile-landscape viewports non-uniformly stretch a 3:2 canvas by roughly 44%, both allow controls to cover dialogue and scene art, and the measured 46 × 22px Log/Start controls fail the 44px mobile target minimum. The single highest-impact correction is to restore a centered, undistorted 480 × 320 canvas and use the resulting 166–182px side rails for controls; that one structural move removes the stretch, creates breathing room, and makes zero dialogue occlusion achievable.

## Exit-bar status

**Not met.** The Bateman exit bar requires **overall A−, zero shipping blockers, and no screen below B+**.

- Overall grade: **D**, below A−.
- 844 × 390 viewport: **D**, below B+.
- 812 × 375 viewport: **D**, below B+.
- Shipping blockers remain at both viewports: **canvas stretch**, **dialogue/art occlusion**, and **undersized 22px-high Log/Start targets**.

Iteration 1 is therefore a failed gate. A fresh independent re-review is required after structural fixes; mechanical no-overflow evidence alone cannot satisfy the exit bar.
