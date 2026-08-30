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
            from app.engine.objects.region import RegionObject
            from app.events.regions import RegionType

            rand = game.get_unit("rand")
            mat = game.get_unit("mat")
            # The post-raven inn walk was cut, so this region no longer exists;
            # build it synthetically to prove nothing still listens for it.
            removed_inn_door = RegionObject("inn_door", RegionType.EVENT)
            game.level_vars.update(
                talked_to_mat=False,
                mat_throw_done=False,
                raven_done=False,
            )
            talk_matches = matched(triggers.OnTalk(rand, mat, rand.position))
            early = matched(
                triggers.RegionTrigger(
                    "Return to Mat",
                    rand,
                    rand.position,
                    game.get_region("inn_before_mat"),
                )
            )
            before_throw = matched(triggers.EnemyTurnChange())
            game.level_vars["mat_throw_done"] = True
            after_throw = matched(triggers.EnemyTurnChange())
            door_matches = matched(
                triggers.RegionTrigger(
                    "Enter Inn", rand, rand.position, removed_inn_door
                )
            )
            return {
                "mat_talk_routes": "tutorial_mat" in talk_matches,
                "early_inn_redirects_to_mat": "tutorial_inn_before_mat" in early,
                "raven_waits_for_both_throws": (
                    "tutorial_raven_flees" not in before_throw
                ),
                "raven_sequence_starts_after_mat_throw": (
                    "tutorial_raven_flees" in after_throw
                ),
                "no_post_raven_inn_trigger": not door_matches,
            }
        if level_id == "wn01_farm_escape":
            game.turncount = 8
            game.level_vars.update(
                caught_by_dawn=False,
                tam_wound_started=False,
                tam_wounded=False,
            )
            trigger = triggers.TurnChange()
            timeout = next(
                event
                for event in game.events.get_triggered_events(trigger, level_id)
                if event.nid.endswith(" farm_timeout_loss")
            )
            executed = _execute_skipped_event(timeout, trigger, game)
            return {
                "turn_eight_caught_loss": (
                    executed
                    and game.level_vars.get("caught_by_dawn") is True
                    and game.level_vars.get("_lose_game") is True
                ),
                "caught_loss_does_not_wound_tam": (
                    game.level_vars.get("tam_wound_started") is False
                    and game.level_vars.get("tam_wounded") is False
                ),
            }
        if level_id == "wn02_village_defense":
            game.turncount = 9
            game.level_vars.update(residents_returned=3, inn_breached=False)
            success = matched(triggers.TurnChange())
            game.level_vars["residents_returned"] = 2
            failure = matched(triggers.TurnChange())
            luhhan = game.get_unit("luhhan_defender")
            luhhan_death = matched(
                triggers.UnitDeath(luhhan, None, luhhan.position)
            )
            militia = game.get_unit("militia_west")
            militia_death = matched(
                triggers.UnitDeath(militia, None, militia.position)
            )
            recruits = (
                game.get_unit("mat_c2"),
                game.get_unit("egwene_c2"),
                game.get_unit("nynaeve_c2"),
            )
            return {
                "three_returns_win_at_turn_nine": (
                    "defense_win" in success
                    and "defense_loss_quota" not in success
                ),
                "two_returns_lose_at_turn_nine": (
                    "defense_win" not in failure
                    and "defense_loss_quota" in failure
                ),
                "named_recruits_are_mortal": all(
                    all(skill.nid != "story_guardian" for skill in unit.skills)
                    for unit in recruits
                ),
                "playable_death_offers_recovery_choice": (
                    "nynaeve_permadeath"
                    in matched(
                        triggers.UnitDeath(
                            recruits[2], None, recruits[2].position
                        )
                    )
                ),
                "luhhan_death_does_not_lose": not any(
                    name.startswith("failure_") for name in luhhan_death
                ),
                "luhhan_is_mortal": not any(
                    skill.nid == "story_guardian" for skill in luhhan.skills
                ),
                "unnamed_green_death_does_not_lose": not any(
                    name.startswith("failure_") for name in militia_death
                ),
            }
        if level_id == "wn03_return_to_farm":
            from app.engine.objects.region import RegionObject
            from app.events.regions import RegionType

            rand = game.get_unit("rand")
            long_exit = game.get_region("westwood_exit")
            quick_exit = RegionObject("westwood_quick_exit", RegionType.EVENT)
            required = (
                "water_found",
                "bandages_found",
                "blankets_found",
                "sword_found",
                "narg_encountered",
            )
            for flag in required:
                game.level_vars[flag] = False
            long_blocked = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, long_exit)
            )
            for flag in required:
                game.level_vars[flag] = True
            long_allowed = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, long_exit)
            )
            game.level_vars["trolloc_defeated"] = False
            quick_blocked = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, quick_exit)
            )
            game.level_vars["trolloc_defeated"] = True
            quick_allowed = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, quick_exit)
            )
            game.turncount = 10
            warning = matched(triggers.TurnChange())
            game.turncount = 13
            deadline = matched(triggers.TurnChange())
            return {
                "early_long_escape_blocked": "return_escape" not in long_blocked,
                "supplies_sword_and_encounter_unlock_long_escape": (
                    "return_escape" in long_allowed
                ),
                "quick_exit_blocked_before_narg_defeat": (
                    "quick_return_escape" not in quick_blocked
                ),
                "narg_defeat_unlocks_quick_exit": (
                    "quick_return_escape" in quick_allowed
                ),
                "turn_ten_warns_of_tam_fever": "tam_fever_warning" in warning,
                "turn_thirteen_reaches_deadline_loss": (
                    "fever_deadline_loss" in deadline
                ),
            }
        if level_id == "wn04_long_road":
            from app.engine.objects.region import RegionObject
            from app.events.regions import RegionType

            rand = game.get_unit("rand")
            tam = game.get_unit("tam_litter")
            column = game.get_unit("column_a")
            watched = RegionObject("rider_watch", RegionType.EVENT)
            shelter = RegionObject("shelter_lower", RegionType.EVENT)
            game.level_vars["rider_watching"] = False
            unwatched = matched(
                triggers.RegionTrigger("Watched", rand, rand.position, watched)
            )
            game.level_vars["rider_watching"] = True
            watching = matched(
                triggers.RegionTrigger("Watched", rand, rand.position, watched)
            )
            game.level_vars["rand_hidden"] = False
            hide_available = matched(
                triggers.RegionTrigger("Hide", rand, rand.position, shelter)
            )
            game.turncount = 7
            unhidden_check = matched(triggers.TurnChange())
            game.level_vars["rand_hidden"] = True
            hidden_check = matched(triggers.TurnChange())

            exit_region = game.get_region("east_exit")
            game.level_vars["column_released"] = False
            early_escape = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, exit_region)
            )
            game.level_vars["column_released"] = True
            released_escape = matched(
                triggers.RegionTrigger("Escape", rand, rand.position, exit_region)
            )

            game.level_vars["column_on_road"] = False
            inactive_combat = matched(
                triggers.CombatStart(tam, column, tam.position, tam.get_weapon(), False)
            )
            game.level_vars["column_on_road"] = True
            active_combat = matched(
                triggers.CombatStart(tam, column, tam.position, tam.get_weapon(), False)
            )
            game.turncount = 3
            warning = matched(triggers.TurnChange())
            game.turncount = 4
            sweepers = matched(triggers.TurnChange())
            return {
                "watched_region_ignores_unwatched_rider": "seen_on_road" not in unwatched,
                "watched_region_matches_watching_rider": "seen_on_road" in watching,
                "shelter_sets_hidden_route": "hide_lower" in hide_available,
                "turn_seven_catches_unhidden_rand": "caught_on_road" in unhidden_check,
                "turn_seven_spares_hidden_rand": "caught_on_road" not in hidden_check,
                "early_road_escape_blocked": "road_escape" not in early_escape,
                "released_column_unlocks_escape": "road_escape" in released_escape,
                "tam_combat_ignored_off_road": "tam_engages_column" not in inactive_combat,
                "tam_combat_matches_column_on_road": "tam_engages_column" in active_combat,
                "turn_three_warns_of_sweepers": "sweeper_warning" in warning,
                "turn_four_spawns_sweepers": "sweepers" in sweepers,
            }
        if level_id == "wn05_out_of_the_woods":
            from app.engine.objects.region import RegionObject
            from app.events.regions import RegionType

            rand = game.get_unit("rand")
            tam = game.get_unit("tam_litter")
            bonfires = RegionObject("bonfires", RegionType.EVENT)
            game.level_vars.update(
                tam_at_inn=False,
                talked_luhhan=False,
                talked_egwene=False,
            )
            early = matched(
                triggers.RegionTrigger("Bonfires", rand, rand.position, bonfires)
            )
            game.level_vars.update(
                tam_at_inn=True,
                talked_luhhan=True,
                talked_egwene=True,
            )
            both_talks = matched(
                triggers.RegionTrigger("Bonfires", rand, rand.position, bonfires)
            )
            game.level_vars["talked_egwene"] = False
            fallback = matched(
                triggers.RegionTrigger("Bonfires", rand, rand.position, bonfires)
            )
            game.level_vars.update(
                luhhan_helped=True,
                luhhan_help_used=False,
            )
            assist = matched(triggers.UnitWait(tam, tam.position, None, True))
            game.level_vars["luhhan_help_used"] = True
            assist_used = matched(triggers.UnitWait(tam, tam.position, None, True))
            fever_events: set[str] = set()
            game.level_vars["tam_at_inn"] = False
            for turn in (4, 6, 8):
                game.turncount = turn
                fever_events.update(matched(triggers.TurnChange()))
            game.level_vars["tam_at_inn"] = True
            game.turncount = 8
            delivered = matched(triggers.TurnChange())
            return {
                "bonfire_arrival_blocked_before_tam_at_inn": not {
                    "bonfire_arrival",
                    "bonfire_arrival_without_both_talks",
                }
                & early,
                "both_talks_select_callback_arrival": (
                    "bonfire_arrival" in both_talks
                    and "bonfire_arrival_without_both_talks" not in both_talks
                ),
                "missing_talk_selects_fallback_arrival": (
                    "bonfire_arrival" not in fallback
                    and "bonfire_arrival_without_both_talks" in fallback
                ),
                "luhhan_assist_refreshes_once": (
                    "luhhan_litter_assist" in assist
                    and "luhhan_litter_assist" not in assist_used
                ),
                "fever_barks_fire_while_tam_is_outside": {
                    "fever_turn_4",
                    "fever_turn_6",
                    "fever_turn_8",
                }
                <= fever_events,
                "fever_barks_stop_after_delivery": "fever_turn_8" not in delivered,
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

    all_levels_initialized = all(level["player_units"] for level in per_level.values())
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
