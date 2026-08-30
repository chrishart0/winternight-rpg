from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

from PIL import Image

from .asset_pipeline import GUIDE_LINE_CORE, GUIDE_LINE_EDGE
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


def _capture_records(captures: dict[str, Path], key: str, root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, output in sorted(captures.items()):
        with Image.open(output) as image:
            dimensions = list(image.size)
        records.append(
            {
                key: name,
                "path": output.relative_to(root).as_posix(),
                "dimensions": dimensions,
                "sha256": sha256(output.read_bytes()).hexdigest(),
            }
        )
    return records


_GUIDE_COLORS = {GUIDE_LINE_EDGE[:3], GUIDE_LINE_CORE[:3]}


def _guide_pixel_count(path: Path) -> int:
    with Image.open(path) as image:
        return sum(pixel[:3] in _GUIDE_COLORS for pixel in image.convert("RGBA").getdata())


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

    screenshots = evidence_path.parent / "screenshots"
    transition_screenshot = screenshots / "chapter-transition.png"
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
    tutorial_capture_names = {
        "start": "tutorial-start.png",
        "mat_talk_menu": "tutorial-mat-talk-menu.png",
        "after_mat": "tutorial-after-mat.png",
        "rand_guide": "tutorial-rand-guide.png",
        "mat_guide": "tutorial-mat-guide.png",
        "forecast_targeting": "tutorial-forecast-targeting.png",
        "stone_throw": "tutorial-stone-throw.png",
        "miss_badge": "tutorial-miss-badge.png",
        "raven_flight": "tutorial-raven-flight.png",
        "end_confirmation": "tutorial-end-confirmation.png",
    }
    transition_screenshot.unlink(missing_ok=True)
    for name in (*gui_capture_names.values(), *tutorial_capture_names.values()):
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
            gui_captures: dict[str, Path] = {}
            tutorial_captures: dict[str, Path] = {}
            tutorial_forecast_result: dict[str, object] = {}
            tutorial_end_confirmation_stage = 0
            wn02_turn_log: dict[int, dict[str, Any]] = {}
            wn02_action_keys: set[tuple[int, str, str]] = set()
            # Guided heal attempts that reach the Item menu without a legal Use
            # are abandoned for that unit and turn, so the planner can never
            # bounce between the item list and its submenu.
            wn02_heal_blocked: set[tuple[int, str]] = set()
            wn02_haral_hp_trace: list[dict[str, Any]] = []
            wn02_heal_result: dict[str, Any] = {}
            wn02_death_choices: list[dict[str, str]] = []
            wn02_flag_names = (
                "nynaeve_guided_heal_done",
                "house_west_saved",
                "house_north_saved",
                "house_east_saved",
                "house_south_saved",
                "house_west_ruined",
                "house_north_ruined",
                "house_east_ruined",
                "house_south_ruined",
                "residents_returned",
                "inn_hold_started",
                "inn_breached",
                "_win_game",
                "_lose_game",
            )

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
                    if flags.get("carrying_cider"):
                        return "Inn Cellar", [(9, 6)], None
                    if not flags.get("cider_delivered"):
                        return "Cider Cart", [(12, 9)], None
                    if not flags.get("rand_attack_ready"):
                        return "Rand Attack Tile", [(10, 7)], None
                    raven = game.get_unit("raven")
                    if not flags.get("rand_throw_done"):
                        return "Attack", [raven.position], "raven"
                    if unit.nid == "mat":
                        if not flags.get("mat_attack_ready"):
                            return "Mat Attack Tile", [(11, 10)], None
                        if not flags.get("raven_done"):
                            return "Attack", [raven.position], "raven"
                    return "Wait", [unit.position], None
                if level_id == "wn01_farm_escape":
                    if unit.nid == "rand":
                        return "Escape", [(0, 5)], None
                    return "Wait", [unit.position], None
                if level_id == "wn02_village_defense":
                    mat = game.get_unit("mat_c2")
                    egwene = game.get_unit("egwene_c2")
                    nynaeve = game.get_unit("nynaeve_c2")
                    if unit.nid == nynaeve.nid and egwene.team != "player":
                        return "Talk", [egwene.position], egwene.nid
                    if unit.nid == egwene.nid and mat.team != "player":
                        return "Talk", [mat.position], mat.nid
                    if unit.nid == nynaeve.nid and not flags.get(
                        "nynaeve_guided_heal_done"
                    ):
                        haral = game.get_unit("luhhan_defender")
                        adjacent = [
                            (haral.position[0] + dx, haral.position[1] + dy)
                            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                        ]
                        # Herbs are a range-0-1 carried item, so the Item command
                        # only offers Use once she actually ends her move beside a
                        # wounded ally. Committing to Item from too far away would
                        # open a menu with nothing to select.
                        endpoint = choose_destination(
                            nynaeve, "Item", [haral.position]
                        )
                        beside_haral = (
                            abs(endpoint[0] - haral.position[0])
                            + abs(endpoint[1] - haral.position[1])
                            <= 1
                        )
                        if (
                            beside_haral
                            and haral.get_hp() < haral.get_max_hp()
                            and (game.turncount, unit.nid) not in wn02_heal_blocked
                        ):
                            return "Item", [haral.position], haral.nid
                        return "Wait", adjacent, None

                    resident_flag = {
                        "resident_west": "resident_west_returned",
                        "resident_north": "resident_north_returned",
                        "resident_east": "resident_east_returned",
                        "resident_south": "resident_south_returned",
                    }.get(unit.nid)
                    if resident_flag and not flags.get(resident_flag):
                        return (
                            "Wait",
                            [(x, y) for y in range(6, 9) for x in range(9, 13)],
                            None,
                        )

                    # Mirrors what the chapter teaches: Mat is sent to the east
                    # door, and Lan takes the west door his start position is
                    # closest to.
                    house_assignment = {
                        "mat_c2": ("east", (18, 7)),
                        "lan": ("west", (3, 7)),
                        "moiraine": ("south", (12, 16)),
                    }.get(unit.nid)
                    if house_assignment:
                        house, door = house_assignment
                        if not (
                            flags.get(f"house_{house}_saved")
                            or flags.get(f"house_{house}_ruined")
                        ):
                            occupant = game.board.get_unit(door)
                            if occupant and occupant.team == "enemy":
                                return "Attack", [door], occupant.nid
                            return "Visit", [door], None

                    threshold_post = {
                        "egwene_c2": (10, 6),
                        "mat_c2": (3, 7),
                        "nynaeve_c2": (11, 6),
                        "lan": (10, 9),
                        "moiraine": (11, 9),
                    }.get(unit.nid)
                    if threshold_post:
                        return "Wait", [threshold_post], None
                    return "Wait", [unit.position], None
                if level_id == "wn03_return_to_farm":
                    if not flags.get("dead_flock_seen"):
                        return "Visit", [(4, y) for y in range(6, 9)], None
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
                    return "Escape", [(4, y) for y in range(5, 9)], None
                if level_id == "wn04_long_road":
                    if flags.get("rider_watching") and not flags.get("rand_hidden"):
                        return "Hide", [(16, 8)], None
                    if flags.get("rider_watching") and game.turncount <= 7:
                        return "Wait", [unit.position], None
                    return "Escape", [(25, 6), (25, 7)], None

                if level_id == "wn05_out_of_the_woods":
                    if unit.nid == "tam_litter":
                        return "Deliver", [(9, 8)], None
                    if not flags.get("talked_luhhan"):
                        luhhan = game.get_unit("luhhan")
                        return "Talk", [luhhan.position], "luhhan"
                    if not flags.get("tam_at_inn"):
                        return "Wait", [(8, 10)], None
                    if not flags.get("talked_egwene"):
                        egwene = game.get_unit("egwene")
                        return "Talk", [egwene.position], "egwene"
                    return "Bonfires", [(13, 14), (14, 14)], None
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
                if action not in {"Talk", "Item", "Spells"}:
                    return targets
                target = targets[0]
                offsets = (
                    ((0, -1), (-1, 0), (1, 0), (0, 1))
                    if action == "Spells"
                    else ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                return [(target[0] + dx, target[1] + dy) for dx, dy in offsets]

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
                level_id = game.level_nid
                priority = {
                    "wn00_tutorial": ["rand"],
                    "wn01_farm_escape": ["rand", "tam"],
                    "wn02_village_defense": [
                        "nynaeve_c2",
                        "lan",
                        "egwene_c2",
                        "mat_c2",
                        "resident_south",
                        "resident_west",
                        "resident_east",
                        "resident_north",
                        "moiraine",
                    ],
                    "wn03_return_to_farm": ["rand"],
                    "wn04_long_road": ["rand"],
                    "wn05_out_of_the_woods": ["rand", "tam_litter"],
                }[level_id]
                if (
                    level_id == "wn00_tutorial"
                    and game.level_vars.get("rand_throw_done")
                    and not game.level_vars.get("raven_done")
                ):
                    priority = ["mat", "rand"]
                if (
                    level_id == "wn05_out_of_the_woods"
                    and game.level_vars.get("talked_luhhan")
                    and game.turncount > 1
                ):
                    priority = ["tam_litter", "rand"]
                for nid in priority:
                    unit = game.get_unit(nid)
                    if (
                        unit
                        and unit.team == "player"
                        and unit.position
                        and not unit.finished
                    ):
                        return unit
                return None

            def move_menu_to(menu, desired: str) -> int | None:
                import pygame

                options = getattr(menu, "options", getattr(menu, "_data", []))
                labels = [_menu_label(option) for option in options]
                if desired not in labels:
                    desired = "Wait"
                if desired not in labels:
                    return pygame.K_z
                current_index = (
                    menu.get_current_index()
                    if hasattr(menu, "get_current_index")
                    else menu.get_selected_idx()
                )
                desired_index = labels.index(desired)
                if current_index == desired_index:
                    return pygame.K_x
                down = (desired_index - current_index) % len(labels)
                up = (current_index - desired_index) % len(labels)
                return pygame.K_DOWN if down <= up else pygame.K_UP

            def drive_state() -> int | None:
                nonlocal last_event, last_combat, last_exp, last_save_state
                nonlocal completed, diagnostic, failure
                nonlocal tutorial_end_confirmation_stage

                import pygame

                state = game.state.current()
                state_object = game.state.current_state()
                if state == "event":
                    event = getattr(state_object, "event", None)
                    if event is not None and event is not last_event:
                        last_event = event
                    if (
                        event is not None
                        and event.nid == "wn00_tutorial tutorial_raven_flees"
                    ):
                        return None
                    return pygame.K_s
                last_event = None
                if state == "combat":
                    if game.level_nid == "wn00_tutorial":
                        return None
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
                if (
                    state == "option_menu"
                    and game.level_nid == "wn00_tutorial"
                    and tutorial_end_confirmation_stage in {1, 3}
                ):
                    if tutorial_end_confirmation_stage == 3:
                        tutorial_end_confirmation_stage = 4
                        return pygame.K_z
                    key = move_menu_to(state_object.menu, "End")
                    if key == pygame.K_x:
                        tutorial_end_confirmation_stage = 2
                    return key
                if (
                    state == "option_child"
                    and game.level_nid == "wn00_tutorial"
                    and tutorial_end_confirmation_stage == 2
                ):
                    key = move_menu_to(state_object.menu, "No")
                    if key == pygame.K_x:
                        tutorial_end_confirmation_stage = 3
                    return key

                if state == "game_over":
                    diagnostic = {
                        "flags": dict(game.level_vars),
                        "units": {
                            unit.nid: {
                                "position": unit.position,
                                "hp": unit.get_hp(),
                                "dead": unit.dead,
                            }
                            for unit in game.units
                            if unit.position or unit.dead
                        },
                    }
                    failure = f"unexpected game over in {game.level_nid} turn {game.turncount}"
                    return None
                if state == "free":
                    if (
                        game.level_nid == "wn00_tutorial"
                        and game.level_vars.get("rand_throw_done")
                        and not game.level_vars.get("mat_attack_ready")
                        and tutorial_end_confirmation_stage == 0
                    ):
                        empty_tile = (0, 0)
                        cursor = game.cursor.position
                        if cursor != empty_tile:
                            return direction_key(cursor, empty_tile)
                        tutorial_end_confirmation_stage = 1
                        return pygame.K_x
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
                    if game.level_nid == "wn02_village_defense":
                        action_key = (game.turncount, unit.nid, action)
                        if action_key not in wn02_action_keys:
                            wn02_action_keys.add(action_key)
                            wn02_turn_log.setdefault(
                                game.turncount,
                                {
                                    "turn": game.turncount,
                                    "phases_seen": [],
                                    "actions": [],
                                },
                            )["actions"].append(
                                {
                                    "unit": unit.nid,
                                    "action": action,
                                    "from": unit.position,
                                    "destination": destination,
                                    "targets": targets,
                                }
                            )
                    cursor = game.cursor.position
                    if game.level_vars.get("_forced_move_unit") == unit.nid:
                        forced_destination = tuple(
                            int(value)
                            for value in game.level_vars["_forced_move_position"].split(",")
                        )
                        if cursor == forced_destination:
                            return pygame.K_x
                        return direction_key(cursor, forced_destination)
                    if cursor == destination:
                        return pygame.K_x
                    path = list(reversed(game.path_system.get_path(unit, destination)))
                    if cursor not in path:
                        return pygame.K_z
                    index = path.index(cursor)
                    if index + 1 >= len(path):
                        return pygame.K_x
                    return direction_key(cursor, path[index + 1])
                if state == "player_choice":
                    choice_nid = getattr(state_object, "nid", "")
                    if choice_nid.startswith("death_"):
                        selected = state_object.menu.get_selected()
                        if selected == "continue":
                            wn02_death_choices.append(
                                {
                                    "unit": choice_nid.removeprefix("death_"),
                                    "prompt": state_object.header,
                                    "selection": selected,
                                }
                            )
                            return pygame.K_x
                        return pygame.K_DOWN
                    return pygame.K_x
                if state == "menu":
                    menu = getattr(state_object, "menu", None)
                    if menu is None:
                        return None
                    unit = state_object.cur_unit
                    action, _, _ = intent_for(unit)
                    if (
                        game.level_nid == "wn02_village_defense"
                        and unit.nid == "nynaeve_c2"
                        and not game.level_vars.get("nynaeve_guided_heal_done")
                    ):
                        options = [_menu_label(option) for option in menu.options]
                        wn02_heal_result.update(
                            action_command="Item",
                            action_menu_options=options,
                            engine_action="Item",
                        )
                    return move_menu_to(menu, action)
                if state in {"item", "item_child"}:
                    guided_heal = (
                        game.level_nid == "wn02_village_defense"
                        and game.cursor.cur_unit.nid == "nynaeve_c2"
                        and not game.level_vars.get("nynaeve_guided_heal_done")
                        and (game.turncount, game.cursor.cur_unit.nid)
                        not in wn02_heal_blocked
                    )
                    labels = [
                        _menu_label(option) for option in state_object.menu.options
                    ]
                    # Never re-enter a submenu that cannot offer Use: record the
                    # attempt, back out of the item flow, and let the planner
                    # fall through to Wait for this unit and turn.
                    desired = "Healing Herbs" if state == "item" else "Use"
                    if not guided_heal or desired not in labels:
                        if guided_heal:
                            wn02_heal_blocked.add(
                                (game.turncount, game.cursor.cur_unit.nid)
                            )
                        return pygame.K_z
                    if state == "item_child":
                        wn02_heal_result["activation_state"] = state
                    return move_menu_to(state_object.menu, desired)
                if state == "spell_choice":
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
                        if game.level_nid == "wn00_tutorial":
                            return move_menu_to(menu, "Thrown Stone")
                        return pygame.K_x
                    return None
                return None

            def save_capture(surface, output: Path) -> Path:
                output.parent.mkdir(parents=True, exist_ok=True)
                engine.save_surface(surface, str(output))
                return output

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
                tutorial_capture_key = None
                if game.level_nid == "wn00_tutorial":
                    flags = game.level_vars
                    raven = game.get_unit("raven")
                    if flags.get("raven_done") and not tutorial_forecast_result:
                        rand = game.get_unit("rand")
                        mat = game.get_unit("mat")
                        rand_items = {item.nid for item in rand.items}
                        mat_items = {item.nid for item in mat.items}
                        tutorial_forecast_result.update(
                            current_hp=raven.get_hp(),
                            maximum_hp=raven.get_max_hp(),
                            target_removed=raven.position is None,
                            target_dead=raven.dead,
                            temporary_item_removed=(
                                "thrown_stone" not in rand_items
                                and "thrown_stone" not in mat_items
                            ),
                            bow_retained="hunting_bow" in rand_items,
                        )
                    if state == "free" and not flags.get("talked_to_mat"):
                        tutorial_capture_key = "start"
                    elif state == "menu" and not flags.get("talked_to_mat"):
                        menu = getattr(game.state.current_state(), "menu", None)
                        if menu and "Talk" in {
                            _menu_label(option) for option in getattr(menu, "options", [])
                        }:
                            tutorial_capture_key = "mat_talk_menu"
                    elif (
                        state == "free"
                        and flags.get("cider_delivered")
                        and not flags.get("rand_attack_ready")
                    ):
                        tutorial_capture_key = "rand_guide"
                    elif (
                        state == "free"
                        and flags.get("rand_throw_done")
                        and not flags.get("mat_attack_ready")
                    ):
                        tutorial_capture_key = "mat_guide"
                    elif (
                        state == "combat_targeting"
                        and (
                            flags.get("rand_attack_ready")
                            or flags.get("mat_attack_ready")
                        )
                    ):
                        tutorial_capture_key = "forecast_targeting"
                    elif state == "free" and flags.get("talked_to_mat"):
                        tutorial_capture_key = "after_mat"
                    if state == "combat":
                        combat_state = game.state.current_state()
                        combat = getattr(combat_state, "combat", combat_state)
                        animation_nids = {
                            animation.nid
                            for animation in getattr(combat, "animations", [])
                        }
                        if (
                            "MapMiss" in animation_nids
                            and "miss_badge" not in tutorial_captures
                        ):
                            tutorial_capture_key = "miss_badge"
                        elif (
                            "StoneThrow" in animation_nids
                            and "stone_throw" not in tutorial_captures
                        ):
                            tutorial_capture_key = "stone_throw"
                    elif (
                        state == "movement"
                        and flags.get("mat_throw_done")
                        and not flags.get("raven_done")
                        and raven.sprite.position[0] >= 15
                    ):
                        tutorial_capture_key = "raven_flight"
                    elif (
                        state == "option_child"
                        and tutorial_end_confirmation_stage == 2
                    ):
                        tutorial_capture_key = "end_confirmation"
                    for layer_id, capture_key in (
                        ("rand_attack_line", "rand_guide"),
                        ("mat_attack_line", "mat_guide"),
                    ):
                        layer = game.tilemap.layers.get(layer_id)
                        if (
                            state == "free"
                            and layer
                            and layer.visible
                            and capture_key not in tutorial_captures
                        ):
                            tutorial_capture_key = capture_key
                            break
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
                        gui_captures[state] = save_capture(
                            surface, screenshots / pending_gui_capture
                        )
                immediate_capture = tutorial_capture_key in {
                    "rand_guide",
                    "mat_guide",
                    "stone_throw",
                    "miss_badge",
                    "raven_flight",
                }
                if (
                    tutorial_capture_key
                    and tutorial_capture_key not in tutorial_captures
                    and (immediate_capture or frame - state_enter_frame >= 12)
                ):
                    output = screenshots / tutorial_capture_names[tutorial_capture_key]
                    tutorial_captures[tutorial_capture_key] = save_capture(surface, output)
                if (
                    state in {"in_chapter_save", "title_save"}
                    and not transition_screenshot.is_file()
                    and getattr(game.state.current_state(), "menu", None)
                    and not getattr(game.state.current_state(), "wait_time", 0)
                ):
                    save_capture(surface, transition_screenshot)
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
                if level_id == "wn02_village_defense":
                    turn_entry = wn02_turn_log.setdefault(
                        game.turncount,
                        {
                            "turn": game.turncount,
                            "phases_seen": [],
                            "actions": [],
                        },
                    )
                    phase = game.phase.get_current() if game.phase else None
                    if phase and phase not in turn_entry["phases_seen"]:
                        turn_entry["phases_seen"].append(phase)
                    turn_entry["flags"] = {
                        name: game.level_vars.get(name) for name in wn02_flag_names
                    }
                    haral = game.get_unit("luhhan_defender")
                    if haral:
                        turn_entry["haral_hp"] = haral.get_hp()
                        if (
                            not wn02_haral_hp_trace
                            or wn02_haral_hp_trace[-1]["hp"] != haral.get_hp()
                        ):
                            wn02_haral_hp_trace.append(
                                {
                                    "turn": game.turncount,
                                    "phase": phase,
                                    "state": state,
                                    "hp": haral.get_hp(),
                                }
                            )
                    if (
                        "uses" not in wn02_heal_result
                        and state == "free"
                        and game.level_vars.get("nynaeve_guided_heal_done")
                    ):
                        nynaeve = game.get_unit("nynaeve_c2")
                        herbs = next(item for item in nynaeve.items if item.nid == "herb_pouch")
                        wn02_heal_result.update(
                            exp=nynaeve.exp,
                            uses=herbs.data.get("uses", 0),
                        )
                    turn_entry["recruit_teams"] = {
                        nid: game.get_unit(nid).team
                        for nid in ("mat_c2", "egwene_c2", "nynaeve_c2")
                    }
                    turn_entry["resident_positions"] = {
                        nid: game.get_unit(nid).position
                        for nid in (
                            "resident_west",
                            "resident_north",
                            "resident_east",
                            "resident_south",
                        )
                    }
                    turn_entry["waves_on_map"] = {
                        nid: game.get_unit(nid).position
                        for nid in (
                            "north_wave_a",
                            "north_wave_b",
                            "flank_wave_a",
                            "flank_wave_b",
                            "final_south_a",
                            "final_south_b",
                            "hold_north_a",
                            "hold_north_b",
                            "hold_south_a",
                            "hold_south_b",
                        )
                        if game.get_unit(nid).position
                    }
                    turn_entry["visible_damage_layers"] = [
                        layer
                        for layer in (
                            "background_west_burning",
                            "background_west_ruined",
                            "background_east_burning",
                            "background_east_ruined",
                        )
                        if game.tilemap.layers.get(layer).visible
                    ]

                if held_key is not None:
                    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=held_key))
                    held_key = None
                    cooldown = 1
                elif cooldown:
                    cooldown -= 1
                elif (pending_gui_capture and state not in gui_captures) or (
                    tutorial_capture_key and tutorial_capture_key not in tutorial_captures
                ):
                    # Hold this exact screen until it has been recorded at native
                    # resolution, before the semantic input planner advances state.
                    pass
                elif not completed and failure is None:
                    key = drive_state()
                    if key is not None:
                        post_key(key)

                # LT's exp state accepts no input and a multi-level-up chain from
                # one ai-phase allied kill can legitimately animate past the state
                # deadline; the global frame deadline still bounds real hangs.
                if state != "exp" and frame - state_enter_frame >= 900 and failure is None:
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
                            [_menu_label(option) for option in getattr(menu, "options", [])]
                        ),
                        "menu_current": (
                            _menu_label(menu.get_current())
                            if menu and hasattr(menu, "get_current")
                            else (
                                _menu_label(menu.get_selected())
                                if menu and hasattr(menu, "get_selected")
                                else None
                            )
                        ),
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
        "level_results": level_results,
        "state_timeline": state_timeline,
        "tutorial_forecast": tutorial_forecast_result,
        "wn02_turn_log": [
            wn02_turn_log[turn] for turn in sorted(wn02_turn_log)
        ],
        "wn02_haral_hp_trace": wn02_haral_hp_trace,
        "wn02_heal_result": wn02_heal_result,
        "wn02_death_choices": wn02_death_choices,
        "tutorial_forecast_input_states": [
            state
            for state in (
                "wn00_tutorial:menu",
                "wn00_tutorial:weapon_choice",
                "wn00_tutorial:combat_targeting",
                "wn00_tutorial:combat",
            )
            if state in state_timeline
        ],
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not completed or failure or visited != chapter_order:
        raise RuntimeError(f"input-driven campaign playthrough failed: {result}")
    # Scripted misses must leave the raven untouched at full HP.
    raven_max_hp = tutorial_forecast_result.get("maximum_hp")
    if tutorial_forecast_result != {
        "current_hp": raven_max_hp,
        "maximum_hp": raven_max_hp,
        "target_removed": True,
        "target_dead": False,
        "temporary_item_removed": True,
        "bow_retained": True,
    }:
        raise RuntimeError(
            f"scripted attack cleanup was incomplete: {tutorial_forecast_result}"
        )
    if len(result["tutorial_forecast_input_states"]) != 4:
        raise RuntimeError(
            "scripted attacks did not traverse menu, weapon, target, and combat states"
        )
    wn02_result = next(
        result for result in level_results if result["level"] == "wn02_village_defense"
    )
    if not (
        wn02_result["completed_turn"] == 9
        and wn02_result["flags"].get("nynaeve_guided_heal_done") is True
        and wn02_result["flags"].get("residents_returned", 0) >= 3
        and not wn02_result["flags"].get("_lose_game", False)
        and any(entry["hp"] == 28 for entry in wn02_haral_hp_trace)
        and any(entry["hp"] == 36 for entry in wn02_haral_hp_trace)
        and wn02_heal_result.get("action_command") == "Item"
        and "Item" in wn02_heal_result.get("action_menu_options", [])
        and wn02_heal_result.get("engine_action") == "Item"
        and wn02_heal_result.get("activation_state") == "item_child"
        and wn02_heal_result.get("exp") == 11
        and wn02_heal_result.get("uses") == 2
        and wn02_death_choices
        and all(
            choice["prompt"] == "Restart the level?"
            and choice["selection"] == "continue"
            for choice in wn02_death_choices
        )
        and any(
            entry["flags"].get("inn_hold_started") is True
            and {
                "hold_north_a",
                "hold_north_b",
                "hold_south_a",
                "hold_south_b",
            }
            <= entry["waves_on_map"].keys()
            for entry in result["wn02_turn_log"]
        )
    ):
        raise RuntimeError(
            f"{wn02_result}, hp={wn02_haral_hp_trace}, "
            f"heal={wn02_heal_result}"
        )
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
    result["gui_screenshots"] = _capture_records(gui_captures, "state", evidence_path.parent)
    missing_tutorial_captures = sorted(set(tutorial_capture_names) - set(tutorial_captures))
    if missing_tutorial_captures:
        raise RuntimeError(
            f"input playthrough missed tutorial clarity captures: {missing_tutorial_captures}"
        )
    guide_pixel_counts = {
        stage: _guide_pixel_count(tutorial_captures[stage])
        for stage in ("start", "after_mat", "rand_guide", "mat_guide")
    }
    if (
        guide_pixel_counts["start"]
        or guide_pixel_counts["after_mat"]
        or not guide_pixel_counts["rand_guide"]
        or not guide_pixel_counts["mat_guide"]
    ):
        raise RuntimeError(f"tutorial guide-line pixels are incorrect: {guide_pixel_counts}")
    result["tutorial_guide_pixel_counts"] = guide_pixel_counts
    result["tutorial_clarity_screenshots"] = _capture_records(
        tutorial_captures, "stage", evidence_path.parent
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
