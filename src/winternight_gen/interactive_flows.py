from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

from .build_report import tree_hash
from .input_playthrough import _menu_label
from .lt_runtime import generated_component_system
from .runtime import isolated_engine_runtime


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _menu_key(menu, desired: str):
    import pygame

    options = [_menu_label(option) for option in menu.options]
    if desired not in options:
        return None
    current = menu.get_current_index()
    target = options.index(desired)
    if current == target:
        return pygame.K_x
    down = (target - current) % len(options)
    up = (current - target) % len(options)
    return pygame.K_DOWN if down <= up else pygame.K_UP


def _run_input_flow(
    project: Path,
    engine_root: Path,
    start_level: str | None,
    planner_factory: Callable[[object], Callable[[], tuple[bool, str | None]]],
) -> dict[str, Any]:
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import config, driver, engine, game_state

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            config.SETTINGS["debug"] = 0
            config.SETTINGS["text_speed"] = 0
            config.SETTINGS["random_seed"] = 5002
            config.SETTINGS["show_terrain"] = 0
            game = (
                game_state.start_level(start_level)
                if start_level is not None
                else game_state.start_game()
            )
            planner = planner_factory(game)
            original_screenshot = driver.save_screenshot
            frame = 0
            held_key: int | None = None
            cooldown = 0
            inputs: dict[str, int] = {}
            failure: str | None = None
            complete = False

            def hook(raw_events, surface):
                nonlocal frame, held_key, cooldown, failure, complete
                frame += 1
                import pygame

                capture_request = game.memory.pop("_input_flow_capture_path", None)
                if capture_request:
                    capture_path = Path(capture_request)
                    capture_path.parent.mkdir(parents=True, exist_ok=True)
                    engine.save_surface(surface, str(capture_path))

                if held_key is not None:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=held_key))
                    held_key = None
                    cooldown = 1
                elif cooldown:
                    cooldown -= 1
                else:
                    complete, failure = planner()
                    key = game.memory.pop("_input_flow_key", None)
                    if key is not None:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
                        held_key = key
                        name = pygame.key.name(key)
                        inputs[name] = inputs.get(name, 0) + 1
                if frame >= 7_200 and not complete and failure is None:
                    failure = f"frame deadline in {game.level_nid}:{game.state.current()}"
                if complete or failure:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            driver.save_screenshot = hook
            try:
                driver.run(game)
            finally:
                driver.save_screenshot = original_screenshot
                engine.terminate()
    return {
        "complete": complete,
        "failure": failure,
        "frames": frame,
        "inputs": inputs,
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
    }


def verify_suspend_continue(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    details: dict[str, Any] = {"verification_kind": "real_pygame_suspend_continue"}

    def factory(game):
        import pygame

        stage = "intro"
        last_event = None
        title_pressed = False
        stable_frames = 0
        before: dict[str, Any] = {}

        def planner() -> tuple[bool, str | None]:
            nonlocal stage, last_event, title_pressed, stable_frames, before
            state = game.state.current()
            state_object = game.state.current_state()
            if state == "event":
                event = getattr(state_object, "event", None)
                if event is not None and event is not last_event:
                    last_event = event
                    game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            last_event = None
            if stage == "intro" and state == "free":
                stage = "open_menu"
                before = {
                    "level": game.level_nid,
                    "turn": game.turncount,
                    "rand_position": game.get_unit("rand").position,
                }
            if stage == "open_menu" and state == "free":
                rand_position = game.get_unit("rand").position
                if game.cursor.position == rand_position:
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                else:
                    game.memory["_input_flow_key"] = pygame.K_x
                return False, None
            if stage == "open_menu" and state == "option_menu":
                key = _menu_key(state_object.menu, "Suspend")
                if key is not None:
                    game.memory["_input_flow_key"] = key
                    if key == pygame.K_x:
                        stage = "confirm"
                return False, None
            if stage == "confirm" and state == "option_child":
                key = _menu_key(state_object.menu, "Yes")
                if key is not None:
                    game.memory["_input_flow_key"] = key
                    if key == pygame.K_x:
                        stage = "title"
                return False, None
            if stage == "title" and state == "title_start" and not title_pressed:
                title_pressed = True
                game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            if stage == "title" and state == "title_main":
                if getattr(state_object, "state", None) == "normal":
                    key = _menu_key(state_object.menu, "Continue")
                    if key is not None:
                        game.memory["_input_flow_key"] = key
                        if key == pygame.K_x:
                            stage = "resume"
                return False, None
            if stage == "resume" and state == "free":
                stable_frames += 1
                if stable_frames >= 60:
                    after = {
                        "level": game.level_nid,
                        "turn": game.turncount,
                        "rand_position": game.get_unit("rand").position,
                    }
                    details.update(before=before, after=after, stable_frames=stable_frames)
                    if before != after:
                        return False, f"resume mismatch: {before} != {after}"
                    return True, None
            return False, None

        return planner

    result = _run_input_flow(project, engine_root, "wn03_return_to_farm", factory)
    result.update(details)
    result["input_driven"] = True
    if not result["complete"] or result["failure"]:
        raise RuntimeError(f"suspend/continue failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def verify_game_over_recovery(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    details: dict[str, Any] = {"verification_kind": "real_pygame_game_over_recovery"}
    screenshot_path = evidence_path.parent / "screenshots" / "game-over.png"
    screenshot_path.unlink(missing_ok=True)

    def factory(game):
        import pygame

        last_event = None
        saw_game_over = False
        game_over_turn: int | None = None
        dead_player_units: list[str] = []
        game_over_stasis_frames = 0

        def planner() -> tuple[bool, str | None]:
            nonlocal last_event, saw_game_over, game_over_turn, dead_player_units
            nonlocal game_over_stasis_frames
            state = game.state.current()
            state_object = game.state.current_state()
            if state == "event":
                event = getattr(state_object, "event", None)
                if event is not None and event is not last_event:
                    last_event = event
                    game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            last_event = None
            if state == "free":
                unit = next(
                    (
                        unit
                        for unit in game.get_player_units()
                        if unit.position and not unit.finished
                    ),
                    None,
                )
                if unit:
                    if game.cursor.position != unit.position:
                        dx = unit.position[0] - game.cursor.position[0]
                        dy = unit.position[1] - game.cursor.position[1]
                        game.memory["_input_flow_key"] = (
                            pygame.K_LEFT
                            if dx < 0
                            else pygame.K_RIGHT
                            if dx > 0
                            else pygame.K_UP
                            if dy < 0
                            else pygame.K_DOWN
                        )
                    else:
                        game.memory["_input_flow_key"] = pygame.K_x
                return False, None
            if state == "move":
                game.memory["_input_flow_key"] = pygame.K_x
                return False, None
            if state == "menu":
                menu = getattr(state_object, "menu", None)
                if menu:
                    key = _menu_key(menu, "Wait")
                    if key is not None:
                        game.memory["_input_flow_key"] = key
                return False, None
            if state == "combat":
                game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            if state == "game_over":
                saw_game_over = True
                game_over_turn = game.turncount
                dead_player_units = sorted(
                    unit.nid for unit in game.get_player_units() if unit.dead or unit.get_hp() <= 0
                )
                if getattr(state_object, "state", None) != "stasis":
                    game_over_stasis_frames = 0
                    return False, None
                game_over_stasis_frames += 1
                if not screenshot_path.is_file() and game_over_stasis_frames >= 30:
                    game.memory["_input_flow_capture_path"] = str(screenshot_path)
                    return False, None
                if screenshot_path.is_file():
                    game.memory["_input_flow_key"] = pygame.K_x
                return False, None
            if saw_game_over and state == "title_start":
                details.update(
                    tested_level="wn02_village_defense",
                    saw_game_over=True,
                    game_over_turn=game_over_turn,
                    dead_player_units=dead_player_units,
                    recovered_destination="title_start",
                )
                return True, None
            return False, None

        return planner

    result = _run_input_flow(project, engine_root, "wn02_village_defense", factory)
    result.update(details)
    result["input_driven"] = True
    if not result["complete"] or result["failure"]:
        raise RuntimeError(f"game-over recovery failed: {result}")
    if not screenshot_path.is_file():
        raise RuntimeError("game-over recovery completed without capturing the loss screen")
    from PIL import Image

    with Image.open(screenshot_path) as image:
        result["game_over_screenshot_dimensions"] = list(image.size)
    result["game_over_screenshot"] = screenshot_path.relative_to(evidence_path.parent).as_posix()
    result["game_over_screenshot_sha256"] = sha256(screenshot_path.read_bytes()).hexdigest()
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def verify_gui_navigation(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    """Open and capture the map, objective, and settings menus with real input."""

    screenshot_root = evidence_path.parent / "screenshots"
    screenshot_paths = {
        "minimap": screenshot_root / "flow-minimap.png",
        "map_options": screenshot_root / "flow-map-options.png",
        "map_option_help": screenshot_root / "flow-map-option-help.png",
        "unit_list": screenshot_root / "flow-unit-list.png",
        "objective": screenshot_root / "flow-objective.png",
        "settings": screenshot_root / "flow-settings.png",
        "controls": screenshot_root / "flow-controls.png",
        "controls_scrolled": screenshot_root / "flow-controls-scrolled.png",
        "setting_detail": screenshot_root / "flow-setting-detail.png",
        "settings_scrolled": screenshot_root / "flow-settings-scrolled.png",
        "unit_info": screenshot_root / "flow-unit-info.png",
        "unit_info_equipment": screenshot_root / "flow-unit-info-equipment.png",
        "unit_info_weapon": screenshot_root / "flow-unit-info-weapon.png",
        "title_extras": screenshot_root / "flow-title-extras.png",
        "title_settings": screenshot_root / "flow-title-settings.png",
        "title_sound_room_track_1": screenshot_root / "flow-title-sound-room-track-1.png",
        "title_sound_room_track_2": screenshot_root / "flow-title-sound-room-track-2.png",
        "title_sound_room_track_3": screenshot_root / "flow-title-sound-room-track-3.png",
    }
    for path in screenshot_paths.values():
        path.unlink(missing_ok=True)
    # Remove the pre-audit single-track capture after expanding Sound Room
    # coverage to one frame per authored track.
    (screenshot_root / "flow-title-sound-room.png").unlink(missing_ok=True)
    details: dict[str, Any] = {"verification_kind": "real_pygame_gui_navigation"}

    def factory(game):
        import pygame

        stage = "intro"
        last_event = None
        help_frames = 0

        def request_capture(name: str) -> bool:
            path = screenshot_paths[name]
            if path.is_file():
                return True
            if "_input_flow_capture_path" not in game.memory:
                game.memory["_input_flow_capture_path"] = str(path)
            return False

        def planner() -> tuple[bool, str | None]:
            nonlocal stage, last_event, help_frames
            state = game.state.current()
            state_object = game.state.current_state()
            if state == "event":
                event = getattr(state_object, "event", None)
                if event is not None and event is not last_event:
                    last_event = event
                    game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            last_event = None

            if stage == "intro" and state == "free":
                stage = "open_minimap"
            if stage == "open_minimap" and state == "free":
                game.memory["_input_flow_key"] = pygame.K_s
                return False, None
            if stage == "open_minimap" and state == "minimap":
                if not getattr(state_object, "arrive_flag", True) and request_capture("minimap"):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "return_from_minimap"
                return False, None
            if stage == "return_from_minimap" and state == "free":
                stage = "open_options"
            if stage == "open_options" and state == "free":
                rand_position = game.get_unit("rand").position
                game.memory["_input_flow_key"] = (
                    pygame.K_RIGHT if game.cursor.position == rand_position else pygame.K_x
                )
                return False, None
            if stage == "open_options" and state == "option_menu":
                if request_capture("map_options"):
                    game.memory["_input_flow_key"] = pygame.K_c
                    stage = "map_option_help"
                return False, None
            if stage == "map_option_help" and state == "option_menu":
                if getattr(state_object.menu, "info_flag", False):
                    help_frames += 1
                    if help_frames >= 90 and request_capture("map_option_help"):
                        game.memory["_input_flow_key"] = pygame.K_c
                        stage = "choose_unit_list"
                return False, None
            if stage == "choose_unit_list" and state == "option_menu":
                key = _menu_key(state_object.menu, "Unit")
                if key is not None:
                    game.memory["_input_flow_key"] = key
                    if key == pygame.K_x:
                        stage = "unit_list"
                return False, None
            if stage == "unit_list" and state == "unit_menu":
                if request_capture("unit_list"):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "return_from_unit_list"
                return False, None
            if stage == "return_from_unit_list" and state == "option_menu":
                stage = "choose_objective"
            if stage == "choose_objective" and state == "option_menu":
                key = _menu_key(state_object.menu, "Objective")
                if key is not None:
                    game.memory["_input_flow_key"] = key
                    if key == pygame.K_x:
                        stage = "objective"
                return False, None
            if stage == "objective" and state == "objective_menu":
                if request_capture("objective"):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "return_from_objective"
                return False, None
            if stage == "return_from_objective" and state == "option_menu":
                stage = "choose_settings"
            if stage == "choose_settings" and state == "option_menu":
                key = _menu_key(state_object.menu, "Options")
                if key is not None:
                    game.memory["_input_flow_key"] = key
                    if key == pygame.K_x:
                        stage = "settings"
                return False, None
            if stage == "settings" and state == "settings_menu":
                if request_capture("settings"):
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                    stage = "controls"
                return False, None
            if (
                stage == "controls"
                and state == "settings_menu"
                and getattr(state_object, "state", None) == "top_menu_right"
            ):
                if request_capture("controls"):
                    game.memory["_input_flow_key"] = pygame.K_x
                    stage = "controls_scrolled"
                return False, None
            if stage == "controls_scrolled" and state == "settings_menu":
                settings_state = getattr(state_object, "state", None)
                if settings_state == "controls":
                    menu = state_object.controls_menu
                    if menu.get_current_index() < len(menu.options) - 1:
                        game.memory["_input_flow_key"] = pygame.K_DOWN
                    elif request_capture("controls_scrolled"):
                        stage = "return_from_controls"
                    return False, None
            if stage == "return_from_controls" and state == "settings_menu":
                settings_state = getattr(state_object, "state", None)
                if settings_state == "controls":
                    game.memory["_input_flow_key"] = pygame.K_UP
                elif settings_state == "top_menu_right":
                    game.memory["_input_flow_key"] = pygame.K_LEFT
                    stage = "enter_setting"
                return False, None
            if (
                stage == "enter_setting"
                and state == "settings_menu"
                and getattr(state_object, "state", None) == "top_menu_left"
            ):
                game.memory["_input_flow_key"] = pygame.K_x
                stage = "setting_detail"
                return False, None
            if (
                stage == "setting_detail"
                and state == "settings_menu"
                and getattr(state_object, "state", None) == "config"
            ):
                if request_capture("setting_detail"):
                    stage = "settings_scrolled"
                return False, None
            if stage == "settings_scrolled" and state == "settings_menu":
                settings_state = getattr(state_object, "state", None)
                if settings_state == "config":
                    menu = state_object.config_menu
                    if menu.get_current_index() < len(menu.options) - 1:
                        game.memory["_input_flow_key"] = pygame.K_DOWN
                    elif request_capture("settings_scrolled"):
                        game.memory["_input_flow_key"] = pygame.K_z
                        stage = "return_from_settings"
                return False, None
            if stage == "return_from_settings" and state == "option_menu":
                game.memory["_input_flow_key"] = pygame.K_z
                stage = "open_unit_info"
                return False, None
            if stage == "open_unit_info" and state == "free":
                target = game.get_unit("rand").position
                cursor = game.cursor.position
                dx, dy = target[0] - cursor[0], target[1] - cursor[1]
                game.memory["_input_flow_key"] = (
                    pygame.K_LEFT
                    if dx < 0
                    else pygame.K_RIGHT
                    if dx > 0
                    else pygame.K_UP
                    if dy < 0
                    else pygame.K_DOWN
                    if dy > 0
                    else pygame.K_c
                )
                if cursor == target:
                    stage = "unit_info"
                return False, None
            if stage == "unit_info" and state == "info_menu":
                if request_capture("unit_info"):
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                    stage = "unit_info_equipment"
                return False, None
            if (
                stage == "unit_info_equipment"
                and state == "info_menu"
                and getattr(state_object, "state", None) == "equipment"
                and not getattr(state_object, "transition", None)
            ):
                if request_capture("unit_info_equipment"):
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                    stage = "unit_info_weapon"
                return False, None
            if (
                stage == "unit_info_weapon"
                and state == "info_menu"
                and getattr(state_object, "state", None) == "support_skills"
                and not getattr(state_object, "transition", None)
            ):
                if request_capture("unit_info_weapon"):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "finish"
                return False, None
            if stage == "finish" and state == "free":
                return True, None
            return False, None

        return planner

    result = _run_input_flow(project, engine_root, "wn00_tutorial", factory)

    def title_factory(game):
        import pygame

        stage = "start"

        def request_capture(name: str) -> bool:
            path = screenshot_paths[name]
            if path.is_file():
                return True
            if "_input_flow_capture_path" not in game.memory:
                game.memory["_input_flow_capture_path"] = str(path)
            return False

        def planner() -> tuple[bool, str | None]:
            nonlocal stage
            state = game.state.current()
            state_object = game.state.current_state()
            if stage == "start" and state == "title_start":
                game.memory["_input_flow_key"] = pygame.K_s
                stage = "choose_extras"
                return False, None
            if stage == "choose_extras" and state == "title_main":
                if getattr(state_object, "state", None) == "normal":
                    key = _menu_key(state_object.menu, "Extras")
                    if key is not None:
                        game.memory["_input_flow_key"] = key
                        if key == pygame.K_x:
                            stage = "extras"
                return False, None
            if stage == "extras" and state == "title_extras":
                if getattr(state_object, "state", None) == "normal" and request_capture(
                    "title_extras"
                ):
                    key = _menu_key(state_object.menu, "Options")
                    if key is not None:
                        game.memory["_input_flow_key"] = key
                        if key == pygame.K_x:
                            stage = "settings"
                return False, None
            if stage == "settings" and state == "settings_menu":
                if request_capture("title_settings"):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "return_to_extras"
                return False, None
            if stage == "return_to_extras" and state == "title_extras":
                if getattr(state_object, "state", None) == "normal":
                    key = _menu_key(state_object.menu, "Sound Room")
                    if key is not None:
                        game.memory["_input_flow_key"] = key
                        if key == pygame.K_x:
                            stage = "sound_room"
                return False, None
            if stage == "sound_room" and state == "extras_sound_room":
                if request_capture("title_sound_room_track_1"):
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                    stage = "sound_room_track_2"
                return False, None
            if stage == "sound_room_track_2" and state == "extras_sound_room":
                if state_object.menu.get_current_index() == 1 and request_capture(
                    "title_sound_room_track_2"
                ):
                    game.memory["_input_flow_key"] = pygame.K_RIGHT
                    stage = "sound_room_track_3"
                return False, None
            if stage == "sound_room_track_3" and state == "extras_sound_room":
                if state_object.menu.get_current_index() == 2 and request_capture(
                    "title_sound_room_track_3"
                ):
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "return_from_sound_room"
                return False, None
            if stage == "return_from_sound_room" and state == "title_extras":
                if getattr(state_object, "state", None) == "normal":
                    game.memory["_input_flow_key"] = pygame.K_z
                    stage = "finish"
                return False, None
            if stage == "finish" and state == "title_main":
                return True, None
            return False, None

        return planner

    title_result = _run_input_flow(project, engine_root, None, title_factory)
    result.update(details)
    result["input_driven"] = True
    result["title_navigation"] = title_result
    if (
        not result["complete"]
        or result["failure"]
        or not title_result["complete"]
        or title_result["failure"]
    ):
        raise RuntimeError(f"GUI navigation failed: {result}")
    result["screenshots"] = []
    from PIL import Image

    for name, path in screenshot_paths.items():
        if not path.is_file():
            raise RuntimeError(f"GUI navigation did not capture {name}")
        with Image.open(path) as image:
            dimensions = list(image.size)
        result["screenshots"].append(
            {
                "screen": name,
                "path": path.relative_to(evidence_path.parent).as_posix(),
                "dimensions": dimensions,
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
        )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
