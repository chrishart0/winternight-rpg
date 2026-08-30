from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path


def configure_display() -> None:
    if os.environ.get("DISPLAY") or not os.environ.get("WAYLAND_DISPLAY"):
        return
    if os.environ.get("SDL_VIDEODRIVER") or not os.environ.get("XDG_RUNTIME_DIR"):
        return
    auth_files = sorted(Path(os.environ["XDG_RUNTIME_DIR"]).glob(".mutter-Xwaylandauth.*"))
    displays = []
    for socket in Path("/tmp/.X11-unix").glob("X*"):
        match = re.fullmatch(r"X(\d+)", socket.name)
        if match and int(match.group(1)) < 90:
            displays.append(int(match.group(1)))
    if len(auth_files) == 1 and displays:
        os.environ.update(
            DISPLAY=f":{min(displays)}",
            XAUTHORITY=str(auth_files[0]),
            SDL_VIDEODRIVER="x11",
        )


def main() -> None:
    root = Path(__file__).resolve().parent
    engine_root = root / "engine"
    (engine_root / "saves").mkdir(exist_ok=True)
    os.chdir(engine_root)
    sys.path.insert(0, str(engine_root))
    configure_display()
    from app.engine import config, driver
    from app.engine.codegen.source_generator import generate_all

    generate_all()
    config.SETTINGS["debug"] = 0
    config.SETTINGS["show_terrain"] = 0
    import run_engine

    smoke_mode = os.environ.get("WINTERNIGHT_PACKAGE_LAUNCH_SMOKE") == "1"
    original_frame_hook = driver.save_screenshot
    frame = 0

    def launch_smoke_hook(raw_events, surface):
        nonlocal frame
        import pygame

        frame += 1
        result = original_frame_hook(raw_events, surface)
        if frame == 30:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        if frame == 60:
            screenshot = root / "launch-smoke.png"
            pygame.image.save(surface, screenshot)
            payload = {
                "window_created": pygame.display.get_surface() is not None,
                "window_caption": pygame.display.get_caption()[0],
                "window_size": list(pygame.display.get_surface().get_size()),
                "sdl_video_driver": pygame.display.get_driver(),
                "screenshot_sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
            }
            (root / "launch-smoke.json").write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        return result

    if smoke_mode:
        driver.save_screenshot = launch_smoke_hook

    try:
        run_engine.main(str(root / "winternight"))
    finally:
        driver.save_screenshot = original_frame_hook


if __name__ == "__main__":
    main()
