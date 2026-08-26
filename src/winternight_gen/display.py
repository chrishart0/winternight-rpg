from __future__ import annotations

import re
from collections.abc import MutableMapping
from pathlib import Path


def configure_sdl_display(
    environ: MutableMapping[str, str],
    *,
    x11_socket_dir: Path = Path("/tmp/.X11-unix"),
) -> str | None:
    """Select XWayland when a Wayland-only launch environment cannot show SDL."""
    if environ.get("DISPLAY") or not environ.get("WAYLAND_DISPLAY"):
        return None
    if environ.get("SDL_VIDEODRIVER"):
        return None

    runtime_dir = environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        return None
    auth_files = sorted(Path(runtime_dir).glob(".mutter-Xwaylandauth.*"))
    if len(auth_files) != 1:
        return None

    display_numbers: list[int] = []
    for socket in x11_socket_dir.glob("X*"):
        match = re.fullmatch(r"X(\d+)", socket.name)
        if match:
            display_number = int(match.group(1))
            # High-numbered displays are commonly headless Xvfb instances.
            if display_number < 90:
                display_numbers.append(display_number)
    if not display_numbers:
        return None

    display = f":{min(display_numbers)}"
    environ["DISPLAY"] = display
    environ["XAUTHORITY"] = str(auth_files[0])
    environ["SDL_VIDEODRIVER"] = "x11"
    return display
