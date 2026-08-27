from __future__ import annotations

import json
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

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


def _execute_skipped_event(event_prefab, trigger, game) -> bool:
    from app.events.event import Event

    event = Event(event_prefab, trigger, game=game)
    event.skip(super_skip=True)
    for _ in range(256):
        event.update()
        if event.finished():
            return True
    return False


def _scenario_truth_table(level_id: str, game, triggers) -> dict[str, bool]:
    def matched(trigger) -> set[str]:
        return {
            event.nid.rsplit(" ", 1)[-1]
            for event in game.events.get_triggered_events(trigger, level_id)
        }

    original_turn = game.turncount
    original_vars = game.level_vars.copy()
    try:
        if level_id == "wn00_tutorial":
            rand = game.get_unit("rand")
            mat = game.get_unit("mat")
            region = game.get_region("inn_barrels")
            talk_matches = matched(triggers.OnTalk(rand, mat, rand.position))
            game.level_vars["talked_to_mat"] = False
            blocked = matched(triggers.RegionTrigger("Visit", rand, rand.position, region))
            game.level_vars["talked_to_mat"] = True
            allowed = matched(triggers.RegionTrigger("Visit", rand, rand.position, region))
            return {
                "mat_talk_routes": "tutorial_mat" in talk_matches,
                "delivery_requires_mat": "tutorial_delivery" not in blocked,
                "delivery_unlocks_after_mat": "tutorial_delivery" in allowed,
            }
        if level_id == "wn01_farm_escape":
            game.turncount = 8
            game.level_vars["tam_wound_started"] = False
            before = matched(triggers.TurnChange())
            game.level_vars["tam_wound_started"] = True
            after = matched(triggers.TurnChange())
            return {
                "turn_eight_forces_wound": "farm_timeout_success" in before,
                "wound_sequence_is_once": "farm_timeout_success" not in after,
            }
        if level_id == "wn02_village_defense":
            game.turncount = 7
            rescue_flags = ("rescued_west", "rescued_east", "rescued_south")
            for flag in rescue_flags:
                game.level_vars[flag] = True
            success = matched(triggers.TurnChange())
            game.level_vars["rescued_west"] = False
            failure = matched(triggers.TurnChange())
            return {
                "all_rescued_wins": "defense_win" in success
                and not any(name.startswith("defense_loss_") for name in success),
                "missing_rescue_loses": "defense_win" not in failure
                and "defense_loss_west" in failure,
            }
        if level_id == "wn03_return_to_farm":
            rand = game.get_unit("rand")
            region = game.get_region("westwood_exit")
            required = ("water_found", "bandages_found", "blankets_found", "sword_found")
            for flag in required:
                game.level_vars[flag] = False
            blocked = matched(triggers.RegionTrigger("Escape", rand, rand.position, region))
            for flag in required:
                game.level_vars[flag] = True
            allowed = matched(triggers.RegionTrigger("Escape", rand, rand.position, region))
            return {
                "early_escape_blocked": "return_escape" not in blocked,
                "supplies_and_sword_unlock_escape": "return_escape" in allowed,
            }
        return {"generic_runtime_ready": True}
    finally:
        game.turncount = original_turn
        game.level_vars.clear()
        game.level_vars.update(original_vars)


def smoke_project(project: Path, engine_root: Path) -> dict[str, object]:
    """Load and initialize every chapter through the pinned LT runtime.

    This complements static analysis by exercising tile movement grids, unit
    construction, event trigger registration, dialogue resources, and one real
    driver loop. It intentionally does not claim to complete tactical objectives.
    """
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import driver, engine, game_state
        from app.events import triggers
        from app.events.event_commands import parse_script_to_commands

        metadata = json.loads((project / "metadata.json").read_text(encoding="utf-8"))
        RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
        DB.load(project, CURRENT_SERIALIZATION_VERSION)
        level_ids = list(DB.levels.keys())
        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            driver.start(DB.constants.value("title"), from_editor=True)
            per_level: dict[str, dict[str, object]] = {}
            scene_count = 0
            for level_id in level_ids:
                game = game_state.start_level(level_id)
                player_units = [unit.nid for unit in game.units if unit.team == "player"]
                enemy_units = [unit.nid for unit in game.units if unit.team == "enemy"]
                intro_ready = game.events.should_trigger(triggers.LevelStart(), level_id)
                outro_ready = game.events.should_trigger(triggers.LevelEnd(), level_id)
                level_events = [event for event in DB.events if event.level_nid == level_id]
                scene_events = [event for event in level_events if event.trigger is None]
                scenes_executed = all(
                    _execute_skipped_event(event, triggers.GenericTrigger(), game)
                    for event in scene_events
                )
                scene_count += len(scene_events)
                command_nids = {
                    event.nid: [command.nid for command in parse_script_to_commands(event.source)]
                    for event in level_events
                }
                scenario_truth_table = _scenario_truth_table(level_id, game, triggers)
                victory_paths = [
                    event_id
                    for event_id, commands in command_nids.items()
                    if "win_game" in commands
                ]
                loss_paths = [
                    event_id
                    for event_id, commands in command_nids.items()
                    if "lose_game" in commands
                ]
                victory_command_executed = False
                if victory_paths:
                    victory_event = next(
                        event for event in level_events if event.nid == victory_paths[0]
                    )
                    game.level_vars.pop("_win_game", None)
                    finished = _execute_skipped_event(
                        victory_event, triggers.GenericTrigger(), game
                    )
                    victory_command_executed = finished and game.level_vars.get("_win_game") is True
                per_level[level_id] = {
                    "tilemap": game.tilemap.nid,
                    "player_units": player_units,
                    "enemy_units": enemy_units,
                    "intro_trigger_ready": intro_ready,
                    "outro_trigger_ready": outro_ready,
                    "scene_count": len(scene_events),
                    "scenes_executed": scenes_executed,
                    "victory_paths": victory_paths,
                    "victory_command_executed": victory_command_executed,
                    "loss_paths": loss_paths,
                    "scenario_truth_table": scenario_truth_table,
                }

            loop_game = game_state.start_level(level_ids[0])
            import pygame

            quit_timer = threading.Timer(
                0.75, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT))
            )
            quit_timer.start()
            try:
                driver.run(loop_game)
                full_game_loop_exited = True
            finally:
                quit_timer.cancel()
            engine.terminate()

    all_levels_initialized = all(
        level["player_units"] and level["enemy_units"] for level in per_level.values()
    )
    all_intro_outro_ready = all(
        level["intro_trigger_ready"] and level["outro_trigger_ready"]
        for level in per_level.values()
    )
    all_scenes_executed = all(level["scenes_executed"] for level in per_level.values())
    all_victory_paths_present = all(level["victory_paths"] for level in per_level.values())
    all_victory_commands_executed = all(
        level["victory_command_executed"] for level in per_level.values()
    )
    all_loss_paths_present = all(level["loss_paths"] for level in per_level.values())
    all_scenario_checks_passed = all(
        all(level["scenario_truth_table"].values()) for level in per_level.values()
    )
    result = {
        "engine_version": metadata["engine_version"],
        "project_loaded": True,
        "level_count": len(level_ids),
        "levels_initialized": level_ids,
        "scene_count": scene_count,
        "all_levels_initialized": all_levels_initialized,
        "all_intro_outro_ready": all_intro_outro_ready,
        "all_scenes_executed": all_scenes_executed,
        "all_victory_paths_present": all_victory_paths_present,
        "all_victory_commands_executed": all_victory_commands_executed,
        "all_loss_paths_present": all_loss_paths_present,
        "all_scenario_checks_passed": all_scenario_checks_passed,
        "full_game_loop_exited_cleanly": full_game_loop_exited,
        "per_level": per_level,
    }
    required = (
        "project_loaded",
        "all_levels_initialized",
        "all_intro_outro_ready",
        "all_scenes_executed",
        "all_victory_paths_present",
        "all_victory_commands_executed",
        "all_loss_paths_present",
        "all_scenario_checks_passed",
        "full_game_loop_exited_cleanly",
    )
    if not level_ids or not all(result[key] for key in required):
        raise RuntimeError(f"engine smoke check failed: {result}")
    return result
