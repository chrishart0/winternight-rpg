from __future__ import annotations

import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from .build_report import sha256, tree_hash
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
        import pygame
        import run_engine
        from app.engine import config, driver

        config.SETTINGS["debug"] = 0

        # Pinned LT 2026.02.17a can render the terrain HUD before its restored
        # cursor tile is initialized after Continue. Hide that optional panel in
        # this launcher so Suspend/Continue remains stable without an engine fork.
        config.SETTINGS["show_terrain"] = 0

        evidence_root = project.parent / "evidence"
        screenshot = evidence_root / "live-launch-title.png"
        manifest = evidence_root / "live_launch.json"
        original_frame_hook = driver.save_screenshot
        frame = 0
        recorded = False

        def record_visible_window(raw_events, surface):
            nonlocal frame, recorded
            frame += 1
            result = original_frame_hook(raw_events, surface)
            if not recorded and frame >= 60 and pygame.display.get_surface() is not None:
                recorded = True
                evidence_root.mkdir(parents=True, exist_ok=True)
                pygame.image.save(surface, screenshot)
                payload = {
                    "verification_kind": "exact_interactive_launcher_window",
                    "window_created": True,
                    "window_caption": pygame.display.get_caption()[0],
                    "window_size": list(pygame.display.get_surface().get_size()),
                    "sdl_video_driver": pygame.display.get_driver(),
                    "display": os.environ.get("DISPLAY"),
                    "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
                    "project_tree_hash": tree_hash(project),
                    "project_manifest_sha256": sha256(project / "build_manifest.json"),
                    "screenshot": screenshot.name,
                    "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                }
                manifest.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            return result

        driver.save_screenshot = record_visible_window
        try:
            run_engine.main(project_name)
        finally:
            driver.save_screenshot = original_frame_hook
