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
    start_level: str,
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
            config.SETTINGS["text_speed"] = 0
            config.SETTINGS["random_seed"] = 5002
            config.SETTINGS["show_terrain"] = 0
            game = game_state.start_level(start_level)
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

    def factory(game):
        import pygame

        last_event = None
        saw_game_over = False
        game_over_turn: int | None = None

        def planner() -> tuple[bool, str | None]:
            nonlocal last_event, saw_game_over, game_over_turn
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
                if getattr(state_object, "state", None) == "stasis":
                    game.memory["_input_flow_key"] = pygame.K_x
                return False, None
            if saw_game_over and state == "title_start":
                details.update(saw_game_over=True, game_over_turn=game_over_turn)
                return True, None
            return False, None

        return planner

    result = _run_input_flow(project, engine_root, "wn02_village_defense", factory)
    result.update(details)
    result["input_driven"] = True
    if not result["complete"] or result["failure"]:
        raise RuntimeError(f"game-over recovery failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
