# Browser build

Live POC: <https://wot-game.arcadian.cloud/>

The browser target is a repository-local compatibility layer over the pinned Lex
Talionis runtime. It does not modify the engine submodule. Pygbag packages the staged
Python and `pygame-ce` application as CPython WebAssembly for static hosting.
The desktop compiler/runtime tests remain pinned to Python 3.11; Pygbag 0.9.3's
published WebAssembly runtime is CPython 3.12.

## Build and test locally

```bash
make web-build
make web-serve
```

`make web-build` writes the static site under `build/web-app/build/web/`. The web
application contains the already compiled `winternight.ltproj`; the compiler, editor,
Pillow, and Pydantic do not run in the browser. Finalization writes the web-only
`cutscene-wide/` rail images and manifest beside the Pygbag payload from the approved,
hash-locked source paintings.

The adapter changes only runtime concerns that differ in a browser:

- the desktop driver loop yields to the browser once per VSYNC and uses a non-blocking 60 Hz
  deadline, preventing high-refresh focused tabs from running LT work at 120–240 Hz and starving
  SDL's WebAudio scheduler;
- LT's short music-loading and save threads run inline;
- save files are mirrored to browser `localStorage` and restored on startup;
- the 240×160 logical game frame uses a whole-number scale capped at 4× logical
  size (960×640) on desktop, avoiding both Pygbag's fractional full-window stretch
  and oversized pixel blocks;
- portrait mobile uses the responsive handheld shell and a dismissible bottom prompt
  recommending landscape; Full screen and Log/Start occupy separate bottom thumb
  zones above that prompt, while portrait play mode hides the redundant prompt;
- landscape mobile and Full screen mode center map, title, and menu play at the
  largest fitting whole-number backing-canvas scale. The native 3:2 frame is never
  stretched; unused viewport space remains as bars;
- for approved 16:9 cutscene paintings, the browser matches LT's current panorama ID
  to deterministic left/right web rails made from the source area outside LT's 3:2
  center crop. The rails fill the landscape columns behind the controls; the centered
  canvas, portraits, dialogue, sprites, and engine-native 240×160 panorama remain
  unstretched and unchanged;
- landscape cutscenes use the same round A/B buttons, GBA-style D-pad chrome,
  compact Log/Start buttons, and pill-shaped Full screen control as title and map
  play;
- holding the touch directional pad repeats movement without requiring a tap per tile;
- the visible **Log** button (keyboard `C`) opens LT's dialogue history during
  cutscenes, where the D-pad or arrow keys scroll missed text;
- taps on the game screen use LT's mouse-input path, so map tiles and menu options
  can be selected directly while the D-pad and A/B controls remain available;
- tapping outside an active hit-testable menu sends Back, matching mobile modal
  dismissal conventions without changing map taps when no menu is open;
- LT's enemy attack-range display is a sticky toggle that only the identical
  select can switch off. The browser clears it on cancel, on the phase change,
  and when the shell reports that the mouse left the game screen, that a press
  was released outside it, that the page lost focus, or that Full screen exited;
  touch pointers, which stop existing after every tap, are not treated as
  leaving;
- the browser smooths the final presentation so LT's very small bitmap text and
  generated portraits remain readable;
- browser audio follows the browser's autoplay policy and begins after interaction
  when the browser requires it.

Pygbag 0.9.3 currently emits a dead BrowserFS script URL. The finalization step
downloads the archived script, verifies its pinned SHA-256 hash, vendors it into the
site, and removes the unused debug terminal from the production page.

The first load downloads the Pygbag CPython/pygame WebAssembly runtime from its pinned
0.9.3 CDN. The application code and assets are served from the selected static host.

## Production deployment boundary

Only the contents of `build/web-app/build/web/` belong in the hosting bucket. Never
upload the repository, `source/private/`, desktop saves, logs, `dist/`, or AWS
credentials. The public bucket grants anonymous `s3:GetObject` only; writes remain
authenticated.

The versioned `winternight-rpg-poc-chrishart0` bucket in `us-east-1` is the origin for
CloudFront distribution `E1V1AX0S4NBYGI`. Route 53 zone `arcadian.cloud` aliases
`wot-game.arcadian.cloud` to that distribution; an ACM certificate in `us-east-1`
provides TLS. Every S3 deployment must invalidate `/*` on the distribution before
live verification so the custom domain cannot retain the previous game archives.

The current production responsive proofs are
[`docs/qa/map-no-stretch-2026-08-28-844x390.webp`](qa/map-no-stretch-2026-08-28-844x390.webp)
and
[`docs/qa/portrait-fullscreen-bottom-2026-08-28-390x844.webp`](qa/portrait-fullscreen-bottom-2026-08-28-390x844.webp).
The landscape map canvas is `480×320`, centered at `(182, 35)` with its native
3:2 ratio. In portrait, Full screen is a `116×44` bottom-left target above the
orientation hint; measured intersection with the canvas, D-pad, A/B, Log/Start,
and hint is zero.

This is an unofficial adaptation POC. Public distribution still requires the legal
and provenance review recorded in `EXEC_PLAN.md`.
