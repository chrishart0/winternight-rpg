# Public workshop invite launch gate

Use this when reviewing a workshop/event site before invites go out. The failure mode is not only visual polish; it is accidentally publishing the production workspace.

## Inventory first

Before grading taste, inventory every routable static page, not just top nav. For VitePress/docs-style sites, every `docs/*.md` file may be public, searchable, and included in the client hash map even if it is not intentionally promoted.

Flag or hide pages that read like internal artifacts:
- presenter/facilitator guides
- agenda notes vs a polished public agenda
- working wiki / source material / workshop objective drafts
- flyer production briefs, Canva handoff docs, variant comparisons
- generation prompts, generated image asset notes, cache paths, implementation notes
- redacted internal business examples or speaker-only talk tracks

Public invite surface should normally be tiny:
- Overview / landing page
- Register CTA
- Pre-work / setup checklist
- Workshop outline or public agenda
- Official docs link

## Conversion gate

The homepage must answer, above the fold or very near it:
- What is this?
- Who is it for?
- When and where is it?
- What will I leave with?
- What do I click to register?

For invite traffic, `Register` should beat `Pre-work`, `Guide`, or `GitHub` as the primary CTA. Include date/time/location/food/laptop requirements near the hero, not buried in internal notes.

## Weird/internal copy smells

Treat these as public-readiness issues:
- framework chrome such as `Search Ctrl K` when the site is not primarily docs
- nav sections named `Source Material`
- public links named `Presenter Guide`, `Working Wiki`, `Agenda Notes`
- phrases like `source of truth` and `trust them over this page`
- raw token/env-var details in first-screen pre-work copy
- production statements like `Generated image asset`, `Canva handoff`, `Generation prompt used`

Prefer welcoming labels:
- `Official docs` instead of `Source of truth`
- `Workshop Agenda` instead of `Agenda Notes`
- `Workshop Outline` instead of planning/objective pages
- `Use the official docs if anything here has changed` instead of `trust them over this page`

## Link and leak checks

Run a focused crawler or script over all public routes before signoff:
- fetch every local link and report 404s
- scan rendered HTML for absolute machine paths, cache paths, old repo slugs, and internal-production phrases
- inspect generated output, not only source, because VitePress can expose links/page names through its hash map

Relative Markdown links to files outside the VitePress docs tree often become broken public routes. Convert them to GitHub URLs, copy the content into public docs, or remove them.

## Verdict rule

A visually good homepage is not enough. If internal docs are public or registration is not obvious, the site is not launch-ready for broad invites. For friendly technical insiders, the minimum viable fix is: register CTA + hide internal nav/pages + no broken links.