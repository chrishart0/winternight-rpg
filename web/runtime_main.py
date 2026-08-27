"""Browser entry point for the pinned Lex Talionis runtime.

This file is copied to the root of the generated Pygbag application. It deliberately
keeps all browser compatibility behavior outside the pinned engine submodule.
"""

# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///

from __future__ import annotations

import asyncio
import base64
import collections
import json
import logging
import math
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_NAME = "winternight"
SAVE_STORAGE_KEY = "winternight-rpg:saves:v1"


class InlineThread:
    """Run LT's short asset/save jobs inline when browser threads are unavailable."""

    def __init__(
        self,
        group: object | None = None,
        target: Callable[..., Any] | None = None,
        name: str | None = None,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        daemon: bool | None = None,
    ) -> None:
        del group, name, daemon
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}
        self._alive = False

    def start(self) -> None:
        self._alive = True
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        finally:
            self._alive = False

    def is_alive(self) -> bool:
        return self._alive

    def join(self, timeout: float | None = None) -> None:
        del timeout


class BrowserTimer:
    """Ignore LT's housekeeping timers in the single-threaded browser runtime."""

    daemon = True

    def __init__(
        self,
        interval: float,
        function: Callable[..., Any],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        del interval, function, args, kwargs

    def start(self) -> None:
        pass

    def cancel(self) -> None:
        pass


def _browser_storage() -> Any | None:
    if sys.platform != "emscripten":
        return None
    try:
        from platform import window

        return window.localStorage
    except Exception:
        logging.exception("Browser localStorage is unavailable")
        return None


def restore_browser_saves() -> None:
    storage = _browser_storage()
    if storage is None:
        return
    raw = storage.getItem(SAVE_STORAGE_KEY)
    if not raw:
        return
    try:
        payload = json.loads(str(raw))
        save_root = Path("saves")
        save_root.mkdir(exist_ok=True)
        for name, encoded in payload.items():
            safe_name = Path(name).name
            if safe_name != name:
                continue
            (save_root / safe_name).write_bytes(base64.b64decode(encoded))
    except Exception:
        logging.exception("Could not restore browser saves")


def persist_browser_saves() -> None:
    storage = _browser_storage()
    if storage is None:
        return
    try:
        save_root = Path("saves")
        payload = {
            path.name: base64.b64encode(path.read_bytes()).decode("ascii")
            for path in sorted(save_root.iterdir())
            if path.is_file() and path.stat().st_size <= 5_000_000
        }
        storage.setItem(SAVE_STORAGE_KEY, json.dumps(payload, sort_keys=True))
    except Exception:
        logging.exception("Could not persist browser saves")


def install_browser_compatibility() -> None:
    if sys.platform != "emscripten":
        return

    threading.Thread = InlineThread  # type: ignore[assignment]
    threading.Timer = BrowserTimer  # type: ignore[assignment]

    from app.engine import save

    original_save_io = save.save_io

    def browser_save_io(*args: Any, **kwargs: Any) -> None:
        original_save_io(*args, **kwargs)
        persist_browser_saves()

    save.save_io = browser_save_io


async def run_game(game: Any) -> None:
    """Async-aware form of the pinned engine's desktop driver loop."""

    from app import lt_log
    from app.constants import FPS, WINHEIGHT, WINWIDTH
    from app.engine import config as cf
    from app.engine import driver, engine
    from app.engine.game_counters import ANIMATION_COUNTERS
    from app.engine.input_manager import get_input_manager
    from app.engine.sound import get_sound_thread

    ANIMATION_COUNTERS.reset()
    get_sound_thread().reset()
    get_sound_thread().set_music_volume(cf.SETTINGS["music_volume"])
    get_sound_thread().set_sfx_volume(cf.SETTINGS["sound_volume"])

    surf = engine.create_surface((WINWIDTH, WINHEIGHT))
    clock = engine.Clock()
    fps_records: collections.deque[int] = collections.deque(maxlen=FPS)
    inp = get_input_manager()

    error_mode = False
    error_msg = ""
    soft_reset_start: float | None = None
    soft_reset_seconds = 3

    while True:
        engine.update_time()
        fps_records.append(engine.get_delta())
        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break

        event = inp.process_input(raw_events)
        if driver.check_soft_reset(game, inp):
            if soft_reset_start is None:
                soft_reset_start = time.time()
            if time.time() - soft_reset_seconds >= soft_reset_start:
                soft_reset_start = None
                error_mode = False
                game.memory.clear()
                game.state.change("title_start")
                game.state.update([], surf)
                await asyncio.sleep(0)
                continue
        else:
            soft_reset_start = None

        if error_mode:
            surf = engine.write_system_msg(surf, error_msg)
        else:
            try:
                surf, repeat = game.state.update(event, surf)
                while repeat:
                    surf, repeat = game.state.update([], surf)
                if cf.SETTINGS["display_fps"]:
                    driver.draw_fps(surf, fps_records)
                if soft_reset_start is not None:
                    remaining = math.ceil(soft_reset_seconds - (time.time() - soft_reset_start))
                    driver.draw_soft_reset(surf, remaining)
            except Exception as exc:
                logging.exception("Game crashed in browser runtime")
                log_dir = lt_log.get_log_dir() or "browser console"
                error_msg = (
                    f"Game crashed with exception:\n{str(exc).strip()}\n"
                    f"Logs can be found in {log_dir}"
                )
                error_mode = True
                if cf.SETTINGS["debug"]:
                    raise

        get_sound_thread().update(raw_events)
        engine.push_display(surf, engine.get_screensize(), engine.DISPLAYSURF)
        engine.update_display()
        game.playtime += clock.tick()

        # Pygbag requires the game to yield to the browser once per frame.
        await asyncio.sleep(0)

    persist_browser_saves()


async def main() -> None:
    from app import lt_log
    from app.data.database.database import DB
    from app.data.metadata import Metadata
    from app.data.resources.resources import RESOURCES
    from app.data.serialization.dataclass_serialization import dataclass_from_dict
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    from app.engine import driver, game_state

    project = Path(f"{PROJECT_NAME}.ltproj")
    if not project.exists():
        raise RuntimeError(f"Could not locate browser project: {project}")

    # LT uses a handful of short-lived threads for loading and saves. Install the
    # browser shims before constructing game states that import those modules.
    install_browser_compatibility()
    restore_browser_saves()
    lt_log.create_logger()

    metadata = dataclass_from_dict(Metadata, json.loads((project / "metadata.json").read_text()))
    if metadata.has_fatal_errors:
        raise RuntimeError("Fatal errors were recorded in project metadata")

    RESOURCES.load(str(project), CURRENT_SERIALIZATION_VERSION)
    DB.load(str(project), CURRENT_SERIALIZATION_VERSION)
    title = DB.constants.value("title")
    driver.start(title)
    game = game_state.start_game()
    await run_game(game)


asyncio.run(main())
