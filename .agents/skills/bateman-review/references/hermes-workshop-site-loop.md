# Hermes Workshop Static Site Bateman Loop — Session Lessons

Use this as a concrete calibration case for public static-site/homepage work where the user says the page is ugly or not tasteful enough.

## Key corrections from the session

- **Do not equate verification with design quality.** `npm run docs:build`, screenshots, no console errors, and no overflow are prerequisites only. They are not aesthetic approval.
- **Do not accept implementer self-signoff as independent A.** Claude Code or Codex may produce a useful self-review, but the orchestrator must inspect screenshots and/or dispatch an independent reviewer before telling the user a page has passed.
- **When the user says every public page needs independent A signoff, inventory the actual public routes.** A static site may expose internal planning/flyer/source docs even if they are not in top nav. Either run the Bateman loop on them or explicitly decide they should be hidden/internal.
- **Homepage-only A is not site A.** Track per-route status: homepage, pre-work, guide/outline, presenter/internal pages, flyer pages, etc.
- **Use DOM/text checks to resolve OCR hallucinations.** Vision/OCR may misread `MIT` as `KIT`, `NOUS` as `MOUS`, or `ENGRAVING` as another word. Do not patch correct copy because OCR hallucinated it; verify `document.body.innerText`, computed layout, and screenshot evidence.
- **Mobile screenshots need segment capture when full-page capture artifacts appear.** Chrome/Puppeteer full-page under device emulation may tile/repeat content. Capture sequential viewport segments and pair them with DOM checks.
- **Hero code/terminal blocks are craft hazards.** A command that technically scrolls horizontally may still read as clipped in a hero screenshot. For A-level mobile: wrap the command fully, move it out of the first viewport, or replace it with a compact chip and keep the full command on the setup page.
- **Footer/link twins can fail craft.** On mobile, adjacent `Nous Research` and `@NousResearch` can read as a duplicate. Stack or separate them clearly.
- **Public copy rules are quality gates.** If the user says no em dashes, remove them from all public site source before deploy. Scan source and generated output after build; ignore only third-party cache/vendor artifacts, not routable pages.
- **Preserve docs readability while styling the homepage.** Scope strong marketing CSS under explicit homepage classes (`.hw`, `.hw-page`, etc.) and separately regression-check pre-work/docs pages.

## Recommended loop for Hermes/static workshop sites

1. Load `hermes-brand-visual-identity` for the brand target and `bateman-review` for the gate.
2. Capture desktop and mobile screenshots for every public route.
3. Run a strict A–F scorecard per route/viewport against the 7 Bateman criteria.
4. Implement with a coding agent, giving explicit route, brand, and exit-bar instructions.
5. Build and capture fresh screenshots.
6. Independently re-review. If a single viewport/section is below the required grade, re-dispatch a narrow loop for that blocker.
7. Use DOM assertions for mechanical claims: overflow, expected text, terminal wrapping, footer link layout, visible asset URLs.
8. Only deploy after the required routes have independent signoff at the requested grade.

## Example DOM checks worth reusing

- `document.documentElement.scrollWidth === document.documentElement.clientWidth` for no horizontal overflow.
- `document.body.innerText.includes('MIT')`, `includes('CLASSICAL ENGRAVING')`, etc. to reject OCR false positives.
- Code block: `scrollWidth === clientWidth`, `getComputedStyle(code).whiteSpace`, and full command text present.
- Footer links: collect `.textContent` and top positions to ensure social handle and org link are visually distinct on mobile.
