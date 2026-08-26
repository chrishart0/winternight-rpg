from __future__ import annotations

from pathlib import Path

from winternight_gen.display import configure_sdl_display


def test_wayland_only_environment_uses_visible_xwayland_display(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    socket_dir = tmp_path / "sockets"
    runtime_dir.mkdir()
    socket_dir.mkdir()
    (runtime_dir / ".mutter-Xwaylandauth.test").touch()
    (socket_dir / "X1").touch()
    (socket_dir / "X99").touch()
    environ = {
        "WAYLAND_DISPLAY": "wayland-0",
        "XDG_RUNTIME_DIR": str(runtime_dir),
    }

    selected = configure_sdl_display(environ, x11_socket_dir=socket_dir)

    assert selected == ":1"
    assert environ["DISPLAY"] == ":1"
    assert environ["SDL_VIDEODRIVER"] == "x11"
    assert environ["XAUTHORITY"] == str(runtime_dir / ".mutter-Xwaylandauth.test")


def test_existing_display_selection_is_preserved(tmp_path: Path):
    environ = {
        "DISPLAY": ":7",
        "WAYLAND_DISPLAY": "wayland-0",
        "SDL_VIDEODRIVER": "wayland",
    }

    selected = configure_sdl_display(environ, x11_socket_dir=tmp_path)

    assert selected is None
    assert environ == {
        "DISPLAY": ":7",
        "WAYLAND_DISPLAY": "wayland-0",
        "SDL_VIDEODRIVER": "wayland",
    }
