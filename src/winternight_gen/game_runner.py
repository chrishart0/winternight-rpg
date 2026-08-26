from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from .display import configure_sdl_display
from .lt_runtime import generated_component_system
from .runtime import prepare_engine_runtime


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def play_project(project: Path, engine_root: Path) -> None:
    x11_display = configure_sdl_display(os.environ)
    if x11_display:
        print(f"Wayland window fallback: using XWayland display {x11_display}")
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    project_name = str(project.resolve().with_suffix(""))
    runtime_root = prepare_engine_runtime(project.parent / "runtime", engine_root)
    with _working_directory(runtime_root), generated_component_system(engine_root):
        import run_engine
        from app.engine import config

        # Pinned LT 2026.02.17a can render the terrain HUD before its restored
        # cursor tile is initialized after Continue. Hide that optional panel in
        # this launcher so Suspend/Continue remains stable without an engine fork.
        config.SETTINGS["show_terrain"] = 0

        run_engine.main(project_name)
