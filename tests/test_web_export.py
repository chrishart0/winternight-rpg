from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.mechanics import _working_directory
from winternight_gen.runtime import isolated_engine_runtime
from winternight_gen.web_export import (
    BROKEN_BROWSERFS_SCRIPT,
    DEBUG_TERMINAL_CONFIG,
    PWA_CACHE_NAME,
    WEB_ADAPTER_VERSION,
    WEB_SHELL_SCRIPT,
    WEB_SHELL_STYLE,
    finalize_pygbag_build,
    stage_web_application,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


def test_web_runtime_is_async_and_browser_yielding() -> None:
    runtime = (ROOT / "web" / "runtime_main.py").read_text(encoding="utf-8")
    assert "async def main()" in runtime
    assert "await asyncio.sleep(0)" in runtime
    assert "_browser_frame_due" in runtime
    assert "clock.tick(" not in runtime
    assert "SAVE_STORAGE_KEY" in runtime
    assert 'save_root = Path("saves")' in runtime
    assert "save_root.mkdir(exist_ok=True)" in runtime
    assert "InlineThread" in runtime
    assert "BrowserTimer" in runtime
    assert runtime.index("driver.start(title)") < runtime.index('cf.SETTINGS["debug"] = 0')
    assert 'cf.SETTINGS["display_fps"] = 0' in runtime
    assert 'game.state.current() == "debug"' in runtime
    assert "game.state.process_temp_state()" in runtime


def test_browser_frame_limiter_caps_high_refresh_without_catch_up() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    frame_due = runtime["_browser_frame_due"]
    interval = 1 / 60

    assert frame_due(10.0, 10.0, interval) == (True, 10.0 + interval)
    assert frame_due(10.0 + interval, 10.0 + 1 / 240, interval) == (
        False,
        10.0 + interval,
    )
    due, deadline = frame_due(10.0 + interval, 11.0, interval)
    assert due is True
    assert deadline == 11.0 + interval


def test_browser_cutscene_mode_tracks_event_state_without_affecting_map_play() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    is_cutscene_state = runtime["_is_cutscene_state"]
    cutscene_background = runtime["_browser_cutscene_background"]

    def state_stack(*states: SimpleNamespace) -> SimpleNamespace:
        return SimpleNamespace(
            state=list(states),
            state_names=lambda: [state.name for state in states],
        )

    free = SimpleNamespace(name="free")
    event = SimpleNamespace(
        name="event",
        event=SimpleNamespace(
            background=SimpleNamespace(
                panorama=SimpleNamespace(nid="winespring_inn_night")
            )
        ),
    )
    dialog_log = SimpleNamespace(name="dialog_log")

    assert is_cutscene_state(state_stack(free)) is False
    assert is_cutscene_state(state_stack(free, event)) is True
    assert is_cutscene_state(state_stack(free, event, dialog_log)) is True
    assert cutscene_background(state_stack(free, event, dialog_log)) == (
        "winespring_inn_night"
    )
    assert cutscene_background(state_stack(free)) is None


def test_browser_music_uses_native_infinite_looping() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    play_browser_music = runtime["_play_browser_music"]

    plays: list[tuple[object, int]] = []
    resets: list[bool] = []
    song = SimpleNamespace(song=object(), intro=None)
    channel = SimpleNamespace(
        current_song=song,
        last_play=0,
        name="music",
        num_plays=-1,
        _channel=SimpleNamespace(play=lambda sound, loops: plays.append((sound, loops))),
        reset_volume=lambda: resets.append(True),
    )

    play_browser_music(channel, lambda _: pytest.fail("used event-driven replay"), lambda: 42)

    assert plays == [(song.song, -1)]
    assert resets == [True]
    assert channel.last_play == 42


def test_browser_music_fade_in_replaces_every_other_channel_pair() -> None:
    """A track may only start once no other pair can still be heard.

    Pinned LT starts the next track as soon as any channel reports a finished
    fade, so an older pair can still be mid-fade when the next one begins. The
    browser build loops natively, so that older pair would keep playing
    underneath forever.
    """
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    fade_in_browser_music = runtime["_fade_in_browser_music"]

    stopped: list[str] = []

    def make_pair(name: str) -> SimpleNamespace:
        return SimpleNamespace(
            channel=SimpleNamespace(label=f"{name}-music"),
            battle=SimpleNamespace(label=f"{name}-battle"),
            stop=lambda name=name: stopped.append(name),
        )

    older, owner, unused = make_pair("older"), make_pair("owner"), make_pair("unused")
    stack = [older, owner, unused]
    faded: list[object] = []

    fade_in_browser_music(owner.channel, faded.append, lambda: stack)
    assert stopped == ["older", "unused"]
    assert faded == [owner.channel]

    # The battle half of the owning pair is LT's crossfade partner, so owning
    # the pair must never silence it.
    stopped.clear()
    fade_in_browser_music(owner.battle, faded.append, lambda: stack)
    assert stopped == ["older", "unused"]
    assert faded == [owner.channel, owner.battle]


def test_touch_menu_hit_testing_distinguishes_inside_outside_and_map() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    touch_hits_active_menu = runtime["_touch_hits_active_menu"]

    inside = SimpleNamespace(menu=SimpleNamespace(handle_mouse=lambda: True))
    outside = SimpleNamespace(menu=SimpleNamespace(handle_mouse=lambda: False))
    map_state = SimpleNamespace()

    assert touch_hits_active_menu(inside) is True
    assert touch_hits_active_menu(outside) is False
    assert touch_hits_active_menu(map_state) is None


def test_overlay_clear_is_due_on_cancel_phase_change_and_shell_report() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    overlay_clear_due = runtime["_overlay_clear_due"]

    assert overlay_clear_due("BACK", "free", False) is True
    assert overlay_clear_due(None, "phase_change", False) is True
    assert overlay_clear_due(None, "free", True) is True
    assert overlay_clear_due("SELECT", "free", False) is False
    assert overlay_clear_due(None, "free", False) is False


def test_clear_enemy_range_overlay_drops_single_and_all_enemy_displays() -> None:
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    clear_overlay = runtime["_clear_enemy_range_overlay"]

    resets: list[bool] = []
    boundary = SimpleNamespace(
        displaying_units={"torch_west"},
        all_on_flag=True,
        reset_surf=lambda: resets.append(True),
        clear_all_enemy_attacks=lambda: setattr(boundary, "all_on_flag", False),
    )

    clear_overlay(SimpleNamespace(boundary=boundary))

    assert boundary.displaying_units == set()
    assert boundary.all_on_flag is False
    assert resets == [True]

    # Outside a level LT has no boundary at all.
    clear_overlay(SimpleNamespace(boundary=None))


def test_web_shell_reports_pointer_focus_and_fullscreen_overlay_exits() -> None:
    assert "window.winternightTakeOverlayClear = () =>" in WEB_SHELL_SCRIPT
    assert 'window.addEventListener("blur", requestOverlayClear);' in WEB_SHELL_SCRIPT
    assert "if (pointerLeftCanvas(event)) requestOverlayClear();" in WEB_SHELL_SCRIPT
    assert WEB_SHELL_SCRIPT.count("requestOverlayClear()") >= 3
    pointer_leave = WEB_SHELL_SCRIPT.index('canvas.addEventListener("pointerleave"')
    # Touch pointers are destroyed after every tap; only a mouse can leave.
    assert 'if (event.pointerType !== "mouse") return;' in WEB_SHELL_SCRIPT[
        pointer_leave : pointer_leave + 400
    ]
    fullscreen = WEB_SHELL_SCRIPT.index('document.addEventListener("fullscreenchange"')
    assert "requestOverlayClear();" in WEB_SHELL_SCRIPT[fullscreen : fullscreen + 200]


def test_web_runtime_clears_sticky_enemy_range_overlay(compiled_campaign) -> None:
    """LT keeps a selected enemy's red attack range drawn until the same select.

    A browser pointer that leaves the canvas can never repeat that select, so
    the danger tiles used to stay on the map for the rest of the round.
    """
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        runtime = runpy.run_path(str(ROOT / "web" / "runtime_main.py"))
    clear_overlay = runtime["_clear_enemy_range_overlay"]

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    engine_path = str(ENGINE_ROOT)
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(ENGINE_ROOT):
        from app import sprites as sprite_catalog
        from app.constants import WINHEIGHT, WINWIDTH
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import config as cf
        from app.engine import driver, engine, game_state

        with isolated_engine_runtime(ENGINE_ROOT) as runtime_root, _working_directory(
            runtime_root
        ):
            sprite_catalog.reset()
            RESOURCES.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            DB.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            cf.SETTINGS["autoend_turn"] = 0
            try:
                game = game_state.start_level("wn02_village_defense")
                surf = engine.create_surface((WINWIDTH, WINHEIGHT))
                game.state.clear()
                game.state.change("free")
                for _ in range(4):
                    engine.update_time()
                    surf, _ = game.state.update(None, surf)
                assert game.state.current() == "free"

                enemy = next(
                    unit
                    for unit in game.units
                    if unit.position and unit.team == "enemy"
                )
                game.cursor.set_pos(enemy.position)
                engine.update_time()
                surf, _ = game.state.update("SELECT", surf)
                assert game.boundary.displaying_units == {enemy.nid}
                assert game.boundary.dictionaries["attack"][enemy.nid]

                engine.update_time()
                surf, _ = game.state.update("BACK", surf)
                assert game.boundary.displaying_units == {enemy.nid}

                clear_overlay(game)
                assert game.boundary.displaying_units == set()
            finally:
                engine.terminate()


def test_stage_web_application_uses_pinned_runtime_without_editor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "fixture.ltproj"
    project.mkdir()
    (project / "metadata.json").write_text("{}\n", encoding="utf-8")
    (project / "build_manifest.json").write_text("{}\n", encoding="utf-8")

    fake_root = tmp_path / "repo"
    (fake_root / "build").mkdir(parents=True)
    (fake_root / "web").mkdir()
    (fake_root / "web" / "runtime_main.py").write_text("async def main(): pass\n")

    engine = tmp_path / "engine"
    for directory in ("app/data", "app/engine", "app/events", "app/utilities"):
        (engine / directory).mkdir(parents=True)
        (engine / directory / "__init__.py").write_text("")
    (engine / "app" / "__init__.py").write_text("")
    (engine / "app" / "editor" / "lib" / "math").mkdir(parents=True)
    (engine / "app" / "editor" / "lib" / "math" / "math_utils.py").write_text("")
    (engine / "sprites").mkdir()
    (engine / "sprites" / "cursor.png").write_bytes(b"png")
    (engine / "resources" / "platforms").mkdir(parents=True)
    (engine / "resources" / "platforms" / "Plain.png").write_bytes(b"png")
    (engine / "favicon.ico").write_bytes(b"ico")
    (engine / "LICENSE.txt").write_text("MIT\n")

    output = fake_root / "build" / "web-app"
    manifest = stage_web_application(fake_root, project, engine, output, "abc123")

    assert manifest["engine_commit"] == "abc123"
    assert (output / "main.py").is_file()
    assert (output / "app" / "engine" / "__init__.py").is_file()
    assert (output / "app" / "editor" / "lib" / "math" / "math_utils.py").is_file()
    assert not (output / "app" / "editor" / "settings.py").exists()
    assert (output / "winternight.ltproj" / "metadata.json").is_file()
    assert json.loads((output / "web_manifest.json").read_text())[
        "adapter_version"
    ] == WEB_ADAPTER_VERSION


def test_mobile_landscape_canvas_keeps_integer_scaled_aspect_ratio() -> None:
    assert """
        canvas#canvas.emscripten {
            width: 480px !important;
            height: 320px !important;
""" in WEB_SHELL_STYLE
    assert """
            #winternight-sp canvas#canvas.emscripten {
                width: var(--winternight-game-width) !important;
                height: var(--winternight-game-height) !important;
""" in WEB_SHELL_STYLE
    assert """
        #winternight-sp.is-play-mode canvas#canvas.emscripten {
            width: var(--winternight-game-width) !important;
            height: var(--winternight-game-height) !important;
""" in WEB_SHELL_STYLE
    assert "width: 100vw !important" not in WEB_SHELL_STYLE
    assert "height: 100dvh !important" not in WEB_SHELL_STYLE
    assert "const scale = fit >= 1 ? Math.floor(fit) : fit;" in WEB_SHELL_SCRIPT


def test_mobile_portrait_bottom_controls_do_not_share_thumb_zones() -> None:
    # The rotate hint must not sit in the pill's bottom row, or it covers the
    # only Full screen control in portrait.
    assert """
            .sp-orientation-hint:not([hidden]) {
                display: flex;
                top: max(12px, env(safe-area-inset-top));
                bottom: auto;
            }
""" in WEB_SHELL_STYLE
    assert """
            .sp-fullscreen-toggle {
                top: auto;
                left: 50%;
                right: auto;
                bottom: max(10px, env(safe-area-inset-bottom));
                transform: translateX(-50%);
            }
""" in WEB_SHELL_STYLE
    assert """
            .sp-system-buttons {
                left: auto;
                right: max(10px, env(safe-area-inset-right));
                bottom: max(88px, calc(env(safe-area-inset-bottom) + 78px));
                gap: 8px;
                transform: none;
            }
""" in WEB_SHELL_STYLE
    assert """
            #winternight-sp.is-play-mode .sp-fullscreen-toggle {
                top: max(10px, env(safe-area-inset-top));
                left: max(10px, env(safe-area-inset-left));
                right: auto;
                bottom: auto;
                transform: none;
            }
""" in WEB_SHELL_STYLE
    assert """
            #winternight-sp.is-play-mode .sp-system-buttons {
                left: auto;
                right: max(10px, env(safe-area-inset-right));
                bottom: max(10px, env(safe-area-inset-bottom));
                gap: 8px;
                transform: none;
            }
""" in WEB_SHELL_STYLE
    assert """
            #winternight-sp.is-play-mode .sp-dpad,
            #winternight-sp.is-play-mode .sp-actions {
                bottom: max(74px, calc(env(safe-area-inset-bottom) + 64px));
            }
""" in WEB_SHELL_STYLE
    assert """
            #winternight-sp.is-play-mode .sp-orientation-hint:not([hidden]) {
                display: none;
            }
""" in WEB_SHELL_STYLE


def test_browser_audio_unlocks_from_any_trusted_gesture_not_fullscreen() -> None:
    unlock, shell = WEB_SHELL_SCRIPT.split("        (() => {\n")[1:3]
    # The unlock must be installed before the shell so it wraps the audio
    # constructor before Pygbag's runtime module opens its audio device.
    assert "audioContexts" in unlock
    assert 'for (const name of ["AudioContext", "webkitAudioContext"]) {' in unlock
    assert "Tracked.prototype = Original.prototype;" in unlock
    assert "if (!event.isTrusted) return;" in unlock
    assert 'if (context.state === "suspended") {' in unlock
    # Touch grants user activation on release, so a press-only binding is
    # refused; "once" would spend the single attempt that gets refused.
    assert """
            for (const type of ["pointerup", "touchend", "mousedown", "click", "keydown"]) {
                window.addEventListener(type, unlockGameAudio, {
                    capture: true,
                    passive: true
                });
            }
""" in unlock
    assert "resume" not in shell
    assert "audioContexts" not in shell
    assert "requestFullscreen" in shell


def test_hidden_page_gives_up_audio_ownership() -> None:
    """Only the visible instance may play.

    Every page instance runs its own engine and its own audio device, and a
    hidden tab keeps its device running, so a duplicate tab or an installed
    window plays a second song underneath the visible game that the player
    cannot reach from it.
    """
    unlock, shell = WEB_SHELL_SCRIPT.split("        (() => {\n")[1:3]
    assert 'document.addEventListener("visibilitychange", () => {' in unlock
    assert """
                if (document.hidden) {
                    for (const context of audioContexts) {
                        if (context.state === "running") {
                            context.suspend().catch(() => {});
                        }
                    }
                    return;
                }
                resumeGameAudio();
""" in unlock
    # Returning to the page resumes through the same helper the trusted-gesture
    # unlock uses, and that unlock stays armed for policies that refuse a
    # resume without a fresh gesture.
    assert unlock.count("resumeGameAudio();") == 2
    assert "visibilitychange" not in shell


def test_web_stage_rejects_output_outside_build(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="web stage must be a child"):
        stage_web_application(tmp_path, tmp_path / "game.ltproj", tmp_path, tmp_path / "web", "x")


def test_finalize_pygbag_build_vendors_browserfs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import winternight_gen.web_export as web_export

    browserfs = b"known browserfs fixture"
    fixture_hash = hashlib.sha256(browserfs).hexdigest()
    monkeypatch.setattr(web_export, "BROWSERFS_SHA256", fixture_hash)
    output = tmp_path / "build" / "web-app" / "build" / "web"
    output.mkdir(parents=True)
    (output / "index.html").write_text(
        f"<head>{BROKEN_BROWSERFS_SCRIPT} {DEBUG_TERMINAL_CONFIG}</head><body></body>",
        encoding="utf-8",
    )
    Image.new("RGBA", (16, 16), "#10151b").save(output / "favicon.png")
    splash_source = tmp_path / "assets" / "generated_sources" / "title_dragon_wheel-v1.png"
    splash_source.parent.mkdir(parents=True)
    Image.new("RGBA", (32, 32), "#e1ad43").save(splash_source)
    background_source = tmp_path / "assets" / "generated_sources" / "inn.png"
    Image.new("RGB", (160, 90), "#804020").save(background_source)
    asset_manifest = tmp_path / "design" / "asset_manifest.yaml"
    asset_manifest.parent.mkdir()
    asset_manifest.write_text(
        """assets:
  - id: test_inn
    type: background
    source_path: assets/generated_sources/inn.png
    approval_status: approved
""",
        encoding="utf-8",
    )

    result = finalize_pygbag_build(tmp_path, output, browserfs_bytes=browserfs)
    repeated_result = finalize_pygbag_build(tmp_path, output, browserfs_bytes=browserfs)

    assert (output / "browserfs.min.js").read_bytes() == browserfs
    finalized = (output / "index.html").read_text()
    assert '<script src="browserfs.min.js"></script> data-os="snd,gui"' in finalized
    assert finalized.count('id="winternight-web-shell"') == 1
    assert 'data-code="KeyC" aria-label="Open dialogue log">Log</button>' in finalized
    assert 'event.target.closest?.("#winternight-sp button")' in finalized
    assert finalized.count('id="winternight-integer-scaling"') == 1
    assert WEB_SHELL_STYLE in finalized
    assert WEB_SHELL_SCRIPT in finalized
    assert "image-rendering: auto" in finalized
    assert "canvas#canvas.emscripten {" in finalized
    assert "\n        canvas.emscripten {" not in finalized
    assert ".sp-loading-mark" in finalized
    assert "image-rendering: pixelated" in finalized
    assert 'shell.id = "winternight-sp"' in finalized
    assert 'class="sp-screen-glass"' in finalized
    assert 'class="sp-loading-splash"' in finalized
    assert 'src="winternight-splash.png"' in finalized
    assert 'aria-label="Eye of the World is loading"' in finalized
    assert "new MutationObserver" in finalized
    assert 'attributeFilter: ["width", "height"]' in finalized
    assert 'dismissOrientationHint.addEventListener("click"' in finalized
    assert 'fullscreenToggle.addEventListener("click"' in finalized
    assert 'data-code="KeyX"' in finalized
    assert 'data-code="ArrowUp"' in finalized
    assert '"--winternight-sp-scale", scale' in finalized
    assert "@media (pointer: coarse), (max-width: 680px), (max-height: 600px)" in finalized
    assert "height: 100dvh" in finalized
    assert 'button.classList.contains("sp-key")' in finalized
    assert 'button.addEventListener("lostpointercapture", release)' in finalized
    assert "Module.PyRun_SimpleString" not in finalized
    assert 'tap screen to choose' in finalized
    assert 'height: 44px' in finalized
    assert "new KeyboardEvent" in finalized
    assert 'event.key !== "Enter"' in finalized
    assert 'dispatchKeyboardEvent(type, "x", "KeyX", event.repeat)' in finalized
    assert "height: var(--winternight-cutscene-height)" in finalized
    assert '"A <kbd>Enter' not in finalized
    assert "new MouseEvent" in finalized
    assert 'dispatchGamePointer("mousedown", event)' in finalized
    assert 'dispatchGamePointer("mouseup", event)' in finalized
    assert 'class="sp-fullscreen-toggle"' in finalized
    assert "#winternight-sp.is-play-mode" in finalized
    assert "width: 100vw !important" not in finalized
    assert 'fullscreenToggle.textContent = enabled ? "Exit full screen"' in finalized
    assert 'window.screen.orientation?.lock?.("landscape")' in finalized
    assert "void setPlayMode(true)" in finalized
    assert 'class="sp-orientation-hint"' in finalized
    assert "Rotate your phone for a wider view." in finalized
    assert "orientation-hint-dismissed:v1" in finalized
    assert "orientationHint.hidden = true" in finalized
    assert "height: 22px" in finalized
    assert 'canvas.addEventListener("pointermove"' in finalized
    assert 'window.winternightSetCutsceneMode = (enabled, background) =>' in finalized
    assert 'shell.classList.toggle("is-cutscene", enabled)' in finalized
    assert 'fetch("./cutscene-wide/manifest.json")' in finalized
    assert 'class="sp-cutscene-backdrop"' in finalized
    assert "grid-template-columns:" in finalized
    assert "Math.floor(fit)" in finalized
    assert "window.innerWidth / frameWidth" in finalized
    assert "window.innerHeight / frameHeight" in finalized
    assert "--winternight-cutscene-width" in finalized
    assert "#winternight-sp.is-cutscene canvas#canvas.emscripten" in finalized
    assert "#winternight-sp.is-cutscene .sp-controls" not in finalized
    assert '"A <kbd>X</kbd>"' in finalized
    assert '"B <kbd>Z</kbd>"' in finalized
    assert '"Log <kbd>C</kbd>"' in finalized
    manifest = json.loads((output / "manifest.webmanifest").read_text())
    assert manifest["display"] == "fullscreen"
    assert manifest["display_override"] == ["fullscreen", "standalone"]
    assert manifest["name"] == "Eye of the World"
    assert manifest["short_name"] == "Eye of the World"
    assert 'viewport-fit=cover' in finalized
    assert 'rel="manifest" href="manifest.webmanifest"' in finalized
    assert 'navigator.serviceWorker.register("./sw.js")' in finalized
    assert '.requestFullscreen({navigationUI: "hide"})' in finalized
    service_worker = (output / "sw.js").read_text()
    assert PWA_CACHE_NAME == f"winternight-pwa-v{WEB_ADAPTER_VERSION}"
    assert service_worker.startswith(f'const CACHE_NAME = "{PWA_CACHE_NAME}";')
    assert '"./cutscene-wide/manifest.json"' in service_worker
    assert '"./winternight-splash.png"' in service_worker
    assert '    "./",' not in service_worker
    assert Image.open(output / "pwa-icon-192.png").size == (192, 192)
    assert Image.open(output / "pwa-icon-512.png").size == (512, 512)
    assert (output / "winternight-splash.png").read_bytes() == splash_source.read_bytes()
    backdrop_manifest = json.loads(
        (output / "cutscene-wide" / "manifest.json").read_text()
    )
    assert backdrop_manifest == {
        "test_inn": {
            "left": "./cutscene-wide/test_inn-left.png",
            "right": "./cutscene-wide/test_inn-right.png",
        }
    }
    assert Image.open(output / "cutscene-wide" / "test_inn-left.png").size == (22, 160)
    assert Image.open(output / "cutscene-wide" / "test_inn-right.png").size == (22, 160)
    assert result["browserfs_sha256"] == fixture_hash
    assert result["splash_sha256"] == hashlib.sha256(splash_source.read_bytes()).hexdigest()
    assert result["cutscene_backdrops"] == 1
    assert result["cutscene_backdrop_manifest_sha256"] == hashlib.sha256(
        (output / "cutscene-wide" / "manifest.json").read_bytes()
    ).hexdigest()
    assert repeated_result == result


def test_finalize_pygbag_build_rejects_unpinned_browserfs(tmp_path: Path) -> None:
    output = tmp_path / "build" / "web-app" / "build" / "web"
    output.mkdir(parents=True)
    (output / "index.html").write_text(
        f"<head>{BROKEN_BROWSERFS_SCRIPT} {DEBUG_TERMINAL_CONFIG}</head><body></body>",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="BrowserFS hash mismatch"):
        finalize_pygbag_build(tmp_path, output, browserfs_bytes=b"wrong")
