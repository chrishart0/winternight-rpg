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


def _browser_frame_due(
    deadline: float, now: float, interval: float
) -> tuple[bool, float]:
    if now < deadline:
        return False, deadline
    next_deadline = deadline + interval
    if next_deadline <= now:
        next_deadline = now + interval
    return True, next_deadline


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


def _set_browser_cutscene_mode(enabled: bool, background_nid: str | None) -> None:
    if sys.platform != "emscripten":
        return
    try:
        from platform import window

        window.winternightSetCutsceneMode(enabled, background_nid)
    except Exception:
        logging.exception("Could not update browser cutscene presentation")


def _is_cutscene_state(state_machine: Any) -> bool:
    return "event" in state_machine.state_names()


def _browser_cutscene_background(state_machine: Any) -> str | None:
    for state in reversed(state_machine.state):
        if state.name != "event":
            continue
        event = getattr(state, "event", None)
        background = getattr(event, "background", None)
        panorama = getattr(background, "panorama", None)
        return getattr(panorama, "nid", None)
    return None


_overlay_clear_bridge_missing = False


def _browser_requested_overlay_clear() -> bool:
    """Consume the shell's request to drop LT's sticky map overlays.

    The shell raises this when the pointer leaves the game screen, releases
    outside it, the page loses focus, or full screen exits. Each of those ends
    the gesture that LT's toggles need in order to be switched back off.
    """
    global _overlay_clear_bridge_missing
    if sys.platform != "emscripten" or _overlay_clear_bridge_missing:
        return False
    try:
        from platform import window

        return bool(window.winternightTakeOverlayClear())
    except Exception:
        _overlay_clear_bridge_missing = True
        logging.exception("Browser overlay-clear bridge is unavailable")
        return False


def _clear_enemy_range_overlay(game: Any) -> None:
    """Erase LT's enemy attack-range display.

    Selecting an enemy adds it to `boundary.displaying_units`, and INFO adds
    every enemy at once. Both stay drawn until the identical input repeats, so a
    pointer that leaves the canvas used to strand the red danger tiles on the
    map for the rest of the round. `boundary` is None outside a level.
    """
    boundary = getattr(game, "boundary", None)
    if boundary is None:
        return
    if boundary.displaying_units:
        boundary.displaying_units.clear()
        boundary.reset_surf()
    if boundary.all_on_flag:
        boundary.clear_all_enemy_attacks()


def _overlay_clear_due(
    event: str | None, state_name: str, shell_requested: bool
) -> bool:
    """Whether this frame should erase the enemy attack-range display.

    Cancel and the phase change are LT's own moments for dropping a stale
    danger zone; `shell_requested` carries the browser-only ones.
    """
    return shell_requested or event == "BACK" or state_name == "phase_change"


def restore_browser_saves() -> None:
    # LT writes achievements and persistent records during New Game setup,
    # before it creates a chapter save. The in-memory browser filesystem starts
    # empty, so establish the directory even when localStorage has no payload.
    save_root = Path("saves")
    save_root.mkdir(exist_ok=True)
    storage = _browser_storage()
    if storage is None:
        return
    raw = storage.getItem(SAVE_STORAGE_KEY)
    if not raw:
        return
    try:
        payload = json.loads(str(raw))
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

def _silence_other_music_channels(channel: Any, channel_stack: Any) -> None:
    """Halt every channel pair except the one that is about to become audible.

    Pinned LT spreads music over four channel pairs and only ever fades the
    next pair in after the previous pair reports that its own fade-out
    finished. Any channel finishing any fade satisfies that report, so the
    controller can start the next track while an older pair is still audible
    mid-fade. On the desktop that older pair is a one-shot chunk, but the
    browser build below hands SDL an unbounded native loop, so a pair the
    controller stops tracking would keep looping underneath the new track with
    nothing left to end it. The browser build therefore keeps exactly one
    audible owner: the pair that is starting replaces every other pair
    outright.
    """
    for pair in channel_stack:
        if channel is pair.channel or channel is pair.battle:
            continue
        pair.stop()


def _fade_in_browser_music(
    channel: Any,
    original_fade_in: Callable[[Any], None],
    channel_stack: Callable[[], Any],
) -> None:
    """Take sole ownership of music playback, then run LT's own fade-in."""
    _silence_other_music_channels(channel, channel_stack())
    original_fade_in(channel)


def _play_browser_music(
    channel: Any,
    original_play: Callable[[Any], None],
    current_time: Callable[[], int],
) -> None:
    song = channel.current_song
    if channel.num_plays >= 0 or channel.name == "battle" or song.intro:
        original_play(channel)
        return

    channel.last_play = current_time()
    channel._channel.play(song.song, -1)
    channel.reset_volume()


def _touch_hits_active_menu(state: Any) -> bool | None:
    """Return whether the current pointer is over a hit-testable active menu."""
    if state is None:
        return None
    found_menu = False
    seen: set[int] = set()
    for attribute in ("menu", "current_menu", "selection"):
        menu = getattr(state, attribute, None)
        if menu is None or id(menu) in seen:
            continue
        seen.add(id(menu))
        handle_mouse = getattr(menu, "handle_mouse", None)
        if not callable(handle_mouse):
            continue
        try:
            hit = handle_mouse()
        except TypeError:
            continue
        found_menu = True
        if hit:
            return True
    return False if found_menu else None


def install_browser_compatibility() -> None:
    if sys.platform != "emscripten":
        return

    threading.Thread = InlineThread  # type: ignore[assignment]
    threading.Timer = BrowserTimer  # type: ignore[assignment]

    from app.engine import engine, game_state, save, sound
    from app.engine.input_manager import InputManager
    original_music_play = sound.Channel._play
    sound.Channel._play = lambda channel: _play_browser_music(
        channel, original_music_play, engine.get_time
    )
    original_music_fade_in = sound.Channel.fade_in
    sound.Channel.fade_in = lambda channel: _fade_in_browser_music(
        channel,
        original_music_fade_in,
        lambda: sound.get_sound_thread().channel_stack,
    )
    original_process_input = InputManager.process_input

    def browser_process_input(manager: Any, events: list[Any]) -> Any:
        left_click = any(
            event.type == engine.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1
            for event in events
        )
        result = original_process_input(manager, events)
        if result != "SELECT" or not left_click:
            return result
        state_machine = getattr(game_state.game, "state", None)
        state = state_machine.current_state() if state_machine else None
        menu_hit = _touch_hits_active_menu(state)
        return "BACK" if menu_hit is False else result

    InputManager.process_input = browser_process_input


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
    fps_records: collections.deque[int] = collections.deque(maxlen=FPS)
    inp = get_input_manager()

    error_mode = False
    error_msg = ""
    soft_reset_start: float | None = None
    soft_reset_seconds = 3
    frame_interval = 1.0 / FPS
    next_frame_at = time.perf_counter()
    cutscene_mode: bool | None = None
    cutscene_background: str | None = None

    while True:
        frame_due, next_frame_at = _browser_frame_due(
            next_frame_at, time.perf_counter(), frame_interval
        )
        if not frame_due:
            await asyncio.sleep(0)
            continue
        engine.update_time()
        fps_records.append(engine.get_delta())
        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break

        event = inp.process_input(raw_events)
        # A hidden engine key sequence can still request DebugState even when
        # the visible debug menu entry is disabled. Never leave a public web
        # session trapped in that developer-only state.
        if not cf.SETTINGS["debug"] and game.state.current() == "debug":
            game.state.back()
            game.state.process_temp_state()
        # LT's enemy attack-range display is a sticky toggle that only the same
        # input can switch off. Cancel, a phase change, and the shell's pointer
        # and focus reports are the exits a browser player actually reaches.
        if _overlay_clear_due(
            event, game.state.current(), _browser_requested_overlay_clear()
        ):
            _clear_enemy_range_overlay(game)
        next_cutscene_mode = _is_cutscene_state(game.state)
        next_cutscene_background = (
            _browser_cutscene_background(game.state) if next_cutscene_mode else None
        )
        if (
            next_cutscene_mode != cutscene_mode
            or next_cutscene_background != cutscene_background
        ):
            _set_browser_cutscene_mode(next_cutscene_mode, next_cutscene_background)
            cutscene_mode = next_cutscene_mode
            cutscene_background = next_cutscene_background
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
        game.playtime += engine.get_delta()

        # Pygbag resumes on browser VSYNC, which may be much faster than LT's
        # 60 Hz contract on high-refresh displays. The non-blocking deadline
        # above caps game work without starving SDL's WebAudio scheduler.
        await asyncio.sleep(0)

    persist_browser_saves()


async def main() -> None:
    from app import lt_log
    from app.data.database.database import DB
    from app.data.metadata import Metadata
    from app.data.resources.resources import RESOURCES
    from app.data.serialization.dataclass_serialization import dataclass_from_dict
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    from app.engine import config as cf
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
    # LT reloads developer settings in driver.start; public web builds must
    # override them afterward.
    cf.SETTINGS["debug"] = 0
    cf.SETTINGS["display_fps"] = 0
    game = game_state.start_game()
    await run_game(game)


asyncio.run(main())
