from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

from PIL import Image

from .build_report import tree_hash
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


def _menu_label(option: object) -> str:
    getter = getattr(option, "get", None)
    if callable(getter):
        option = getter()
    if isinstance(option, str):
        return option
    return str(getattr(option, "name", getattr(option, "nid", option)))


def verify_input_playthrough(
    project: Path,
    engine_root: Path,
    chapter_order: list[str],
    evidence_path: Path,
) -> dict[str, Any]:
    """Complete the authored campaign using only posted pygame key events.

    The planner reads LT state to choose routes and semantic menu options, but
    it never calls actions, triggers, event skip methods, or mutates game data.
    """

    transition_screenshot = evidence_path.parent / "screenshots" / "chapter-transition.png"
    transition_screenshot.unlink(missing_ok=True)
    screenshots = evidence_path.parent / "screenshots"
    gui_capture_names = {
        "title_start": "flow-title-start.png",
        "title_main": "flow-title-main.png",
        "title_new": "flow-new-game-options.png",
        "menu": "flow-action-menu.png",
        "item": "flow-inventory.png",
        "item_child": "flow-item-actions.png",
        "weapon_choice": "flow-weapon-choice.png",
        "combat_targeting": "flow-combat-forecast.png",
    }
    for name in gui_capture_names.values():
        (screenshots / name).unlink(missing_ok=True)

    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
        with generated_component_system(engine_root):
            from app import sprites as sprite_catalog
            from app.data.database.database import DB
            from app.data.resources.resources import RESOURCES
            from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
            from app.engine import config, driver, engine, game_state

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            config.SETTINGS["debug"] = 0
            config.SETTINGS["text_speed"] = 0
            config.SETTINGS["random_seed"] = 5000
            config.SETTINGS["autoend_turn"] = 1
            game = game_state.start_game()
            # State registration imports banner through LT's normal module
            # order; importing it before start_game exposes an upstream cycle.
            from app.engine import banner

            banner.Pennant.bg_surf = sprite_catalog.SPRITES.get("pennant_bg")
            if banner.Pennant.bg_surf is None:
                raise RuntimeError("project/runtime lacks the pennant_bg UI sprite")
            original_screenshot = driver.save_screenshot
            frame = 0
            held_key: int | None = None
            cooldown = 0
            last_event: object | None = None
            last_combat: object | None = None
            last_exp: object | None = None
            last_save_state: object | None = None
            title_states_pressed: set[str] = set()
            visited: list[str] = []
            level_results: list[dict[str, Any]] = []
            previous_level: str | None = None
            last_level_snapshot: dict[str, Any] | None = None
            state_timeline: list[str] = []
            last_state: str | None = None
            input_counts: dict[str, int] = {}
            completed = False
            failure: str | None = None
            diagnostic: dict[str, Any] = {}
            state_enter_frame = 0
            tutorial_inventory_stage = 0
            gui_captures: dict[str, Path] = {}

            def post_key(key: int) -> None:
                nonlocal held_key
                import pygame

                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
                held_key = key
                name = pygame.key.name(key)
                input_counts[name] = input_counts.get(name, 0) + 1

            def direction_key(source: tuple[int, int], target: tuple[int, int]) -> int | None:
                import pygame

                dx, dy = target[0] - source[0], target[1] - source[1]
                if dx < 0:
                    return pygame.K_LEFT
                if dx > 0:
                    return pygame.K_RIGHT
                if dy < 0:
                    return pygame.K_UP
                if dy > 0:
                    return pygame.K_DOWN
                return None

            def intent_for(unit) -> tuple[str, list[tuple[int, int]], str | None]:
                level_id = game.level_nid
                flags = game.level_vars
                if level_id == "wn00_tutorial":
                    if not flags.get("talked_to_mat"):
                        target = game.get_unit("mat")
                        return "Talk", [target.position], "mat"
                    if not flags.get("delivered_cider"):
                        return "Visit", [(10, 5)], None
                    if tutorial_inventory_stage < 3:
                        return "Item", [unit.position], None
                    meetings = (
                        ("met_perrin", "perrin"),
                        ("met_egwene", "egwene"),
                        ("met_fain", "fain"),
                        ("met_travelers", "moiraine_village"),
                    )
                    for flag, target_nid in meetings:
                        if not flags.get(flag):
                            target = game.get_unit(target_nid)
                            return "Talk", [target.position], target_nid
                    for target_nid in ("target_a", "target_b"):
                        target = game.get_unit(target_nid)
                        if target and target.position and not target.dead:
                            return "Attack", [target.position], target_nid
                    target = game.get_unit("tam_village")
                    return "Talk", [target.position], "tam_village"
                if level_id == "wn01_farm_escape":
                    if unit.nid == "rand":
                        return "Escape", [(0, 5)], None
                    return "Wait", [unit.position], None
                if level_id == "wn02_village_defense":
                    rescue_flag = {
                        "civilian_west": "rescued_west",
                        "civilian_east": "rescued_east",
                        "civilian_south": "rescued_south",
                    }.get(unit.nid)
                    if rescue_flag and not flags.get(rescue_flag):
                        return "Rescue", [(x, y) for y in range(4, 7) for x in range(8, 12)], None
                    if unit.nid in {"lan", "moiraine"}:
                        enemies = [
                            other
                            for other in game.units
                            if other.team == "enemy"
                            and other.position
                            and not other.dead
                        ]
                        if enemies:
                            target = min(
                                enemies,
                                key=lambda other: abs(other.position[0] - unit.position[0])
                                + abs(other.position[1] - unit.position[1]),
                            )
                            return "Attack", [target.position], target.nid
                    return "Wait", [unit.position], None
                if level_id == "wn03_return_to_farm":
                    if not flags.get("farmhouse_reached"):
                        return "Visit", [(6, 7)], None
                    searches = (
                        ("water_found", (7, 10)),
                        ("bandages_found", (10, 5)),
                        ("blankets_found", (12, 7)),
                        ("sword_found", (10, 8)),
                    )
                    for flag, position in searches:
                        if not flags.get(flag):
                            return "Search", [position], None
                    target = game.get_unit("lone_trolloc")
                    if target and target.position and not target.dead:
                        return "Attack", [target.position], target.nid
                    return "Escape", [(0, y) for y in range(5, 9)], None
                raise RuntimeError(f"no input plan for {level_id}")

            def candidate_destinations(
                unit, action: str, targets: list[tuple[int, int]]
            ) -> list[tuple[int, int]]:
                if action == "Attack":
                    from app.engine import item_funcs

                    target = targets[0]
                    weapon = unit.get_weapon()
                    ranges = item_funcs.get_range(unit, weapon)
                    maximum = max(ranges)
                    return [
                        (x, y)
                        for x in range(target[0] - maximum, target[0] + maximum + 1)
                        for y in range(target[1] - maximum, target[1] + maximum + 1)
                        if abs(x - target[0]) + abs(y - target[1]) in ranges
                    ]
                if action != "Talk":
                    return targets
                target = targets[0]
                return [
                    (target[0] + dx, target[1] + dy)
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                ]

            def choose_destination(
                unit, action: str, targets: list[tuple[int, int]]
            ) -> tuple[int, int]:
                valid = set(game.path_system.get_valid_moves(unit))
                candidates = candidate_destinations(unit, action, targets)
                routes = []
                for candidate in candidates:
                    if not game.tilemap.check_bounds(candidate):
                        continue
                    occupant = game.board.get_unit(candidate)
                    if occupant is not None and occupant is not unit:
                        continue
                    path = game.path_system.get_path(unit, candidate)
                    if path and path[-1] == unit.position:
                        routes.append(path)
                if routes:
                    route = list(
                        reversed(
                            min(
                                routes,
                                key=lambda path: game.path_system.get_path_cost(unit, path),
                            )
                        )
                    )
                    endpoint = unit.position
                    for position in route[1:]:
                        if position not in valid:
                            break
                        if game.board.get_unit(position) is None:
                            endpoint = position
                    return endpoint
                return unit.position

            def choose_free_unit():
                priority = {
                    "wn00_tutorial": ["rand"],
                    "wn01_farm_escape": ["rand", "tam"],
                    "wn02_village_defense": [
                        "civilian_west",
                        "civilian_east",
                        "civilian_south",
                        "lan",
                        "moiraine",
                    ],
                    "wn03_return_to_farm": ["rand"],
                }[game.level_nid]
                for nid in priority:
                    unit = game.get_unit(nid)
                    if unit and unit.position and not unit.finished:
                        return unit
                return None

            def move_menu_to(menu, desired: str) -> int | None:
                import pygame

                options = [_menu_label(option) for option in menu.options]
                if desired not in options:
                    desired = "Wait"
                if desired not in options:
                    return pygame.K_z
                current_index = menu.get_current_index()
                desired_index = options.index(desired)
                if current_index == desired_index:
                    return pygame.K_x
                down = (desired_index - current_index) % len(options)
                up = (current_index - desired_index) % len(options)
                return pygame.K_DOWN if down <= up else pygame.K_UP

            def drive_state() -> int | None:
                nonlocal last_event, last_combat, last_exp, last_save_state
                nonlocal completed, failure, tutorial_inventory_stage
                import pygame

                state = game.state.current()
                state_object = game.state.current_state()
                if state == "event":
                    event = getattr(state_object, "event", None)
                    if event is not None and event is not last_event:
                        last_event = event
                    return pygame.K_s
                last_event = None
                if state == "combat":
                    if state_object is not last_combat:
                        last_combat = state_object
                        return pygame.K_s
                    return None
                last_combat = None
                if state == "exp":
                    if state_object is not last_exp:
                        last_exp = state_object
                        return pygame.K_x
                    return None
                last_exp = None
                if state in {"in_chapter_save", "title_save"}:
                    if (
                        state_object is not last_save_state
                        and getattr(state_object, "menu", None)
                        and not getattr(state_object, "wait_time", 0)
                    ):
                        last_save_state = state_object
                        return pygame.K_x
                    return None
                last_save_state = None

                if state == "title_start":
                    if visited == chapter_order:
                        completed = True
                        return None
                    if state not in title_states_pressed:
                        title_states_pressed.add(state)
                        return pygame.K_s
                    return None
                if state in {"title_main", "title_mode", "title_new"}:
                    internal = getattr(state_object, "state", None)
                    ready = internal in {
                        "normal",
                        "difficulty_wait",
                        "death_wait",
                        "growth_wait",
                    }
                    if ready and state not in title_states_pressed:
                        title_states_pressed.add(state)
                        return pygame.K_x
                    return None
                if state == "game_over":
                    failure = f"unexpected game over in {game.level_nid} turn {game.turncount}"
                    return None
                if state == "free":
                    unit = choose_free_unit()
                    if not unit:
                        return None
                    cursor = game.cursor.position
                    if cursor != unit.position:
                        return direction_key(cursor, unit.position)
                    return pygame.K_x
                if state == "move":
                    unit = game.cursor.cur_unit
                    action, targets, _ = intent_for(unit)
                    destination = choose_destination(unit, action, targets)
                    cursor = game.cursor.position
                    if cursor == destination:
                        return pygame.K_x
                    path = list(reversed(game.path_system.get_path(unit, destination)))
                    if cursor not in path:
                        return pygame.K_z
                    index = path.index(cursor)
                    if index + 1 >= len(path):
                        return pygame.K_x
                    return direction_key(cursor, path[index + 1])
                if state == "menu":
                    menu = getattr(state_object, "menu", None)
                    if menu is None:
                        return None
                    unit = state_object.cur_unit
                    action, _, _ = intent_for(unit)
                    return move_menu_to(menu, action)
                if state == "item":
                    if game.level_nid == "wn00_tutorial" and tutorial_inventory_stage == 0:
                        tutorial_inventory_stage = 1
                        return pygame.K_x
                    if game.level_nid == "wn00_tutorial" and tutorial_inventory_stage == 2:
                        tutorial_inventory_stage = 3
                        return pygame.K_z
                    return pygame.K_z
                if state == "item_child":
                    if game.level_nid == "wn00_tutorial" and tutorial_inventory_stage == 1:
                        tutorial_inventory_stage = 2
                        return pygame.K_x
                    return pygame.K_z
                if state in {"targeting", "combat_targeting"}:
                    unit = game.cursor.cur_unit
                    _, _, target_nid = intent_for(unit)
                    target = game.get_unit(target_nid) if target_nid else None
                    if not target or not target.position:
                        return pygame.K_z
                    if game.cursor.position != target.position:
                        return direction_key(game.cursor.position, target.position)
                    return pygame.K_x
                if state == "weapon_choice":
                    menu = getattr(state_object, "menu", None)
                    if menu and getattr(menu, "options", None):
                        return pygame.K_x
                    return None
                return None

            def input_hook(raw_events, surface):
                nonlocal frame, held_key, cooldown, previous_level, last_state, failure
                nonlocal state_enter_frame, diagnostic, last_level_snapshot
                frame += 1
                import pygame

                state = game.state.current()
                if state != last_state:
                    state_timeline.append(f"{game.level_nid or '-'}:{state}")
                    last_state = state
                    state_enter_frame = frame
                pending_gui_capture = gui_capture_names.get(state)
                if pending_gui_capture and state not in gui_captures:
                    state_object = game.state.current_state()
                    internal = getattr(state_object, "state", None)
                    title_ready = state not in {"title_main", "title_new"} or internal in {
                        "normal",
                        "difficulty_wait",
                        "death_wait",
                        "growth_wait",
                    }
                    # Let transitions, cursor animations, and menu construction
                    # settle before recording the exact screen a player sees.
                    if title_ready and frame - state_enter_frame >= 12:
                        output = screenshots / pending_gui_capture
                        output.parent.mkdir(parents=True, exist_ok=True)
                        engine.save_surface(surface, str(output))
                        gui_captures[state] = output
                if (
                    state in {"in_chapter_save", "title_save"}
                    and not transition_screenshot.is_file()
                    and getattr(game.state.current_state(), "menu", None)
                    and not getattr(game.state.current_state(), "wait_time", 0)
                ):
                    transition_screenshot.parent.mkdir(parents=True, exist_ok=True)
                    engine.save_surface(surface, str(transition_screenshot))
                level_id = game.level_nid
                if level_id and level_id not in visited:
                    visited.append(level_id)
                if previous_level and level_id != previous_level and last_level_snapshot:
                    level_results.append(last_level_snapshot)
                    last_level_snapshot = None
                previous_level = level_id
                if level_id:
                    last_level_snapshot = {
                        "level": level_id,
                        "completed_turn": game.turncount,
                        "flags": dict(game.level_vars),
                    }

                if held_key is not None:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=held_key))
                    held_key = None
                    cooldown = 1
                elif cooldown:
                    cooldown -= 1
                elif pending_gui_capture and state not in gui_captures:
                    # Preserve the screen long enough to capture it before the
                    # semantic input planner advances to the next state.
                    pass
                elif not completed and failure is None:
                    key = drive_state()
                    if key is not None:
                        post_key(key)

                if frame - state_enter_frame >= 900 and failure is None:
                    state_object = game.state.current_state()
                    menu = getattr(state_object, "menu", None)
                    diagnostic = {
                        "state_stack": game.state.state_names(),
                        "state": state,
                        "level": game.level_nid,
                        "turn": game.turncount,
                        "phase": game.phase.get_current() if game.phase else None,
                        "cursor": game.cursor.position if game.cursor else None,
                        "menu_options": (
                            [_menu_label(option) for option in menu.options] if menu else []
                        ),
                        "menu_current": _menu_label(menu.get_current()) if menu else None,
                        "flags": dict(game.level_vars),
                        "units": {
                            unit.nid: {
                                "position": unit.position,
                                "hp": unit.get_hp(),
                                "finished": unit.finished,
                                "ai": unit.get_ai(),
                            }
                            for unit in game.units
                        },
                    }
                    failure = f"state deadline exceeded in {game.level_nid}:{state}"
                if frame >= 30_000 and failure is None:
                    state_object = game.state.current_state()
                    menu = getattr(state_object, "menu", None)
                    diagnostic = {
                        "state_stack": game.state.state_names(),
                        "state": state,
                        "level": game.level_nid,
                        "turn": game.turncount,
                        "phase": game.phase.get_current() if game.phase else None,
                        "cursor": game.cursor.position if game.cursor else None,
                        "menu_options": (
                            [_menu_label(option) for option in menu.options] if menu else []
                        ),
                        "menu_current": _menu_label(menu.get_current()) if menu else None,
                        "flags": dict(game.level_vars),
                        "talk_options": list(game.talk_options),
                        "units": {
                            unit.nid: {
                                "position": unit.position,
                                "hp": unit.get_hp(),
                                "finished": unit.finished,
                                "ai": unit.get_ai(),
                            }
                            for unit in game.units
                        },
                    }
                    failure = "global frame deadline exceeded"
                if completed or failure is not None:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            driver.save_screenshot = input_hook
            try:
                driver.run(game)
            finally:
                driver.save_screenshot = original_screenshot
                engine.terminate()

    result = {
        "verification_kind": "real_pygame_full_campaign_input",
        "input_driven": True,
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
        "chapter_order_expected": chapter_order,
        "chapter_order_visited": visited,
        "completed": completed,
        "failure": failure,
        "diagnostic": diagnostic,
        "frames": frame,
        "inputs": input_counts,
        "tutorial_inventory_opened": tutorial_inventory_stage >= 1,
        "tutorial_bow_equipped_through_item_menu": tutorial_inventory_stage >= 3,
        "level_results": level_results,
        "state_timeline": state_timeline,
    }
    if not completed or failure or visited != chapter_order:
        raise RuntimeError(f"input-driven campaign playthrough failed: {result}")
    if not transition_screenshot.is_file():
        raise RuntimeError("input playthrough completed without a chapter-transition capture")
    with Image.open(transition_screenshot) as image:
        result["chapter_transition_screenshot_dimensions"] = list(image.size)
    result["chapter_transition_screenshot"] = transition_screenshot.relative_to(
        evidence_path.parent
    ).as_posix()
    result["chapter_transition_screenshot_sha256"] = sha256(
        transition_screenshot.read_bytes()
    ).hexdigest()
    result["gui_screenshots"] = []
    for state, output in sorted(gui_captures.items()):
        with Image.open(output) as image:
            dimensions = list(image.size)
        result["gui_screenshots"].append(
            {
                "state": state,
                "path": output.relative_to(evidence_path.parent).as_posix(),
                "dimensions": dimensions,
                "sha256": sha256(output.read_bytes()).hexdigest(),
            }
        )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
