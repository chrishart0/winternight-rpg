# Browser build

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
Pillow, and Pydantic do not run in the browser.

The adapter changes only runtime concerns that differ in a browser:

- the desktop driver loop yields to the browser once per frame;
- LT's short music-loading and save threads run inline;
- save files are mirrored to browser `localStorage` and restored on startup;
- browser audio follows the browser's autoplay policy and begins after interaction
  when the browser requires it.

Pygbag 0.9.3 currently emits a dead BrowserFS script URL. The finalization step
downloads the archived script, verifies its pinned SHA-256 hash, vendors it into the
site, and removes the unused debug terminal from the production page.

The first load downloads the Pygbag CPython/pygame WebAssembly runtime from its pinned
0.9.3 CDN. The application code and assets are served from the selected static host.

## S3 deployment boundary

Only the contents of `build/web-app/build/web/` belong in the hosting bucket. Never
upload the repository, `source/private/`, desktop saves, logs, `dist/`, or AWS
credentials. A public host should grant anonymous `s3:GetObject` only; writes remain
authenticated.

This is an unofficial adaptation POC. Publicly hosting the Winternight content should
be treated separately from proving the browser exporter with original content.
