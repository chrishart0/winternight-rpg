# Workshop Site Bateman Loop Notes

Use these notes when applying Bateman review to a public workshop/static site, especially a VitePress site with a branded homepage and docs pages.

## Lessons from Hermes workshop site

- Do not accept “build passes” or implementer self-review as visual signoff. Treat screenshot review, fresh re-review, and independent signoff as the gate.
- If the user says the site is ugly/tasteless, stop incremental CSS flailing. Re-anchor on the actual brand source, official assets, and the page’s public job-to-be-done.
- For public sites, information architecture is part of taste. A repo dump of internal agenda/flyer/planning docs can fail the visual surface even when each page renders.
- For homepage marketing pages, use explicit layout classes/components instead of relying on generic VitePress home cards.
- For mobile reviews, hero-only screenshots matter. A code block or card that is technically scrollable can still fail if it visually reads cropped in the first viewport.
- Vision/OCR reviews can hallucinate text errors. When screenshots imply typos or truncation, verify with DOM text and layout metrics before changing copy.
- Before grading taste, confirm the screenshot is actually the target page. If it shows browser error chrome such as `ERR_CONNECTION_REFUSED`, restart the dev server and recapture. A connection-refused screenshot is mechanical failure evidence, not design evidence.

## Recommended evidence loop

1. Capture desktop and mobile screenshots for every public page.
2. Review each page and viewport against: Bone Structure, Restraint, Texture & Materiality, Typographic Confidence, Color Discipline, Breathing Room, Craft Details.
3. Record grades and ranked blockers in a markdown review under the project QA folder.
4. Implement only ranked fixes, preserving already-passing pages.
5. Rebuild and recapture screenshots.
6. Use independent review or fresh-context critique; do not accept the implementing agent’s signoff alone.
7. For suspected mobile clipping/overflow, add DOM checks: `scrollWidth === clientWidth`, element bounds relative to viewport, code block scroll width/client width, and exact body text presence.
8. Only declare signoff when every public page has A-level evidence or the user explicitly narrows the gate.

## Common blockers

- Generic docs theme pretending to be a marketing site.
- Exposed internal/research/flyer-production pages in public nav.
- Mobile terminal/code blocks with clipped commands.
- Footer links or repeated org/social labels reading as duplicates on mobile.
- Self-review reports without independent screenshot inspection.
- A “library” implemented as oversized marketing cards. If the user needs to browse many titles, grade against library affordances: dense rows/cards, search, live count, type/status chips, side filters with counts on desktop, clear active states, and mobile ordering that surfaces search/results before secondary filter rails.
- Result-row metadata colliding with descriptions or being forced into a too-narrow third column. Put metadata under the description or use compact badges; overlap is a craft blocker, not a minor spacing nit.
- VitePress child pages missing the same `pageClass` as their index page. This can make a component look good on the library/index page while individual item pages silently render unstyled.
- Raw HTML blocks immediately followed by Markdown headings without a blank line. In VitePress this can render `## Heading` as literal text or visually jam section headings into metadata blocks.
- Markdown tables used for small metadata summaries on mobile. They pass mechanical checks but often read as default docs chrome; a compact styled metadata strip is usually more polished.
