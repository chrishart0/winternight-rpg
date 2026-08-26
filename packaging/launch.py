from __future__ import annotations

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
    os.chdir(engine_root)
    sys.path.insert(0, str(engine_root))
    configure_display()
    from app.engine import config
    from app.engine.codegen.source_generator import generate_all

    generate_all()
    config.SETTINGS["show_terrain"] = 0
    import run_engine

    run_engine.main(str(root / "winternight"))


if __name__ == "__main__":
    main()
