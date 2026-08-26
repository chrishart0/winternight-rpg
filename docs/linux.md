# Linux bootstrap and launch

The pinned LT commit supports CPython 3.11 only. The repository uses `uv` to install and select that interpreter even when the system default is newer.

## Bootstrap

```bash
git submodule update --init --recursive
uv sync --python 3.11 --extra dev
uv pip install --python .venv/bin/python -r vendor/lt-maker/requirements_editor.txt
```

Equivalent: `make bootstrap`.

LT pins `pygame-ce==2.3.2`, `PyQt5==5.15.10`, `pyinstaller==6.2.0`, and `typing-extensions==4.8.0`. PyInstaller is installed because it is in the official editor requirements. The private package remains a source/runtime archive launched through `uv`, not a frozen executable.

## Build and verify

```bash
uv run --python 3.11 winternight validate
uv run --python 3.11 winternight compile
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run --python 3.11 winternight smoke
QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run --python 3.11 winternight editor-smoke
uv run --python 3.11 pytest
uv run --python 3.11 winternight determinism
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run --python 3.11 winternight input-playthrough
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run --python 3.11 winternight suspend-continue
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run --python 3.11 winternight game-over-recovery
```

Equivalent complete verification: `make check`.

## Interactive engine

```bash
uv run --python 3.11 winternight play
```

Equivalent: `make play`.

At the title screen, use the arrow keys, `Enter`/`Z` to confirm, and `X` to cancel. The first chapter opens with dialogue; advance it with `Enter`/`Z`.

On GNOME Wayland sessions where the launching terminal has `WAYLAND_DISPLAY`
but no `DISPLAY`, the launcher automatically selects the local Mutter
XWayland display. This avoids an SDL window that runs without appearing in
GNOME's window stack. An existing `DISPLAY` or explicit `SDL_VIDEODRIVER` is
always preserved.

## Editor

```bash
uv run --python 3.11 winternight editor
```

Equivalent: `make editor`. Close the editor before running `make compile`; LT's own documentation warns against external project edits while the editor is open.

For a display-less machine, use `make smoke` and `make editor-smoke`. Interactive use still requires a display or remote desktop.

## Private Linux package

```bash
make package
make package-smoke
tar -xzf dist/winternight-private-linux.tar.gz
cd winternight-private-linux
./run.sh
```

The archive contains the generated project, pinned LT runtime, launch wrapper, provenance record, notices, and checksum. It is for private technical evaluation only.
