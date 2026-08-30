from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

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


def _drain_trigger(game, trigger, level_id: str) -> list[str]:
    """Execute events reached through LT's public trigger router.

    This deliberately starts at ``EventManager.trigger`` instead of selecting a
    prefab by name. Nested scene scripts are drained from the same event stack.
    """
    matched = [event.nid for event in game.events.get_triggered_events(trigger, level_id)]
    if not game.events.trigger(trigger, level_id):
        raise RuntimeError(f"no event matched {level_id}: {trigger!r}")
    executed: list[str] = []
    while event := game.events.get():
        executed.append(event.nid)
        event.skip(super_skip=True)
        for _ in range(512):
            event.update()
            if event.finished():
                break
        else:
            raise RuntimeError(f"event did not finish: {event.nid}")
        game.events.end(event)
    missing = sorted(set(matched) - set(executed))
    if missing:
        raise RuntimeError(f"triggered events were not executed: {missing}")
    return executed


def _item_nids(unit) -> list[str]:
    return [item.nid for item in unit.items]


def _chapter_tutorial(game, triggers) -> dict[str, Any]:
    level_id = "wn00_tutorial"
    from app.engine import action, general_states, item_funcs

    def region_event(name: str, unit, region_id: str) -> list[str]:
        region = game.get_region(region_id)
        trigger = triggers.RegionTrigger(name, unit, unit.position, region)
        return _drain_trigger(game, trigger, level_id)

    def matched(trigger) -> list[str]:
        return [
            event.nid
            for event in game.events.get_triggered_events(trigger, level_id)
        ]

    def movement_lock(unit) -> bool:
        """Confirm the engine accepts only the forced tutorial destination."""
        _, destination = general_states._forced_tutorial_move()
        # The forced target may sit beyond the unit's reach from wherever the
        # trigger chain left it; warp adjacent so the lock check tests the
        # forced-move contract rather than incidental map distance.
        action.do(action.Warp(unit, (destination[0] - 1, destination[1])))
        game.cursor.cur_unit = unit
        game.cursor.set_pos(unit.position)
        move_state = general_states.MoveState()
        move_state.begin()
        locked = destination in move_state.valid_moves
        move_state.take_input("SELECT")
        rejected_wrong_tile = unit.current_move is None
        general_states._hide_forced_move_layer()
        move_state.end()
        game.cursor.cur_unit = None
        return locked and rejected_wrong_tile

    start = _drain_trigger(game, triggers.LevelStart(), level_id)
    next_phase_before_raven = game.phase.get_next()
    rand, mat = game.get_unit("rand"), game.get_unit("mat")
    early = region_event("Return to Mat", rand, "inn_before_mat")
    early_did_not_win = game.level_vars.get("_win_game") is not True
    talk = _drain_trigger(game, triggers.OnTalk(rand, mat, rand.position), level_id)
    cider = region_event("Cider Cart", rand, "cider_cart")
    cellar = region_event("Inn Cellar", rand, "inn_cellar")
    rand_bow_present_after_cellar = "hunting_bow" in _item_nids(rand)
    mat_activated = mat.team == "player" and "Tile" not in mat.tags and not mat.finished
    rand_line_shown = game.tilemap.layers.get("rand_attack_line").visible
    rand_movement_locked = movement_lock(rand)
    raven = game.get_unit("raven")
    raven_hp = raven.get_hp()
    raven_spawned = (
        raven.position is not None
        and raven.team == "enemy"
        and raven.ai == "do_nothing"
    )
    rand_tile = region_event("Rand Attack Tile", rand, "rand_attack_tile")
    rand_line_hidden = not game.tilemap.layers.get("rand_attack_line").visible
    forced_rand_cleared = not game.level_vars.get("_forced_move_unit")
    rand_stone = next(item for item in rand.items if item.nid == "thrown_stone")
    rand_stone_requires_weapon_pick = rand.get_weapon().nid == "hunting_bow"
    rand_bow_retry = _drain_trigger(
        game,
        triggers.CombatEnd(rand, raven, rand.position, rand.get_weapon(), []),
        level_id,
    )
    rand_bow_cannot_complete = (
        game.level_vars.get("rand_throw_done") is not True
        and "wn00_tutorial tutorial_rand_bow_retry" in rand_bow_retry
    )
    action.do(action.EquipItem(rand, rand_stone))
    rand_stone_is_ranged = (
        rand.get_weapon().nid == "thrown_stone"
        and item_funcs.get_range(rand, rand.get_weapon()) == {2}
    )
    rand_script = matched(
        triggers.CombatStart(rand, raven, rand.position, rand.get_weapon(), False)
    )
    rand_done = _drain_trigger(
        game,
        triggers.CombatEnd(rand, raven, rand.position, rand.get_weapon(), []),
        level_id,
    )
    rand_bow_present_after_throw = "hunting_bow" in _item_nids(rand)
    rand_repeat_script = matched(
        triggers.CombatStart(rand, raven, rand.position, rand.get_weapon(), False)
    )
    mat_line_shown = game.tilemap.layers.get("mat_attack_line").visible
    mat_movement_locked = movement_lock(mat)
    mat_tile = region_event("Mat Attack Tile", mat, "mat_attack_tile")
    mat_line_hidden = not game.tilemap.layers.get("mat_attack_line").visible
    forced_mat_cleared = not game.level_vars.get("_forced_move_unit")
    mat_script = matched(
        triggers.CombatStart(mat, raven, mat.position, mat.get_weapon(), False)
    )
    mat_done = _drain_trigger(
        game,
        triggers.CombatEnd(mat, raven, mat.position, mat.get_weapon(), []),
        level_id,
    )
    raven_flee = _drain_trigger(game, triggers.EnemyTurnChange(), level_id)
    checks = {
        "mat_talk_sets_flag": game.level_vars.get("talked_to_mat") is True,
        "early_inn_redirects_to_mat": "wn00_tutorial tutorial_inn_before_mat" in early,
        "early_inn_does_not_win": early_did_not_win,
        "single_cider_trip_completes": game.level_vars.get("cider_delivered") is True,
        "no_ai_phase_before_the_raven": next_phase_before_raven == "player",
        "mat_becomes_player_controlled": mat.team == "player",
        "mat_is_selectable_after_cider": mat_activated,
        "raven_spawns_as_stationary_enemy": raven_spawned,
        "rand_guide_line_shows_after_cider": rand_line_shown,
        "rand_movement_is_locked": rand_movement_locked,
        "rand_guide_line_hides_after_move": rand_line_hidden,
        "rand_forced_move_clears_at_destination": forced_rand_cleared,
        "rand_stone_requires_weapon_pick": rand_stone_requires_weapon_pick,
        "rand_bow_cannot_complete_stone_lesson": rand_bow_cannot_complete,
        "rand_stone_is_ranged": rand_stone_is_ranged,
        "mat_guide_line_shows_after_rand": mat_line_shown,
        "mat_movement_is_locked": mat_movement_locked,
        "mat_guide_line_hides_after_move": mat_line_hidden,
        "mat_forced_move_clears_at_destination": forced_mat_cleared,
        "rand_scripted_miss_is_routed": (
            "wn00_tutorial tutorial_rand_throw_script" in rand_script
        ),
        "mat_scripted_miss_is_routed": (
            "wn00_tutorial tutorial_mat_throw_script" in mat_script
        ),
        "rand_throw_completes": game.level_vars.get("rand_throw_done") is True,
        "mat_throw_completes": game.level_vars.get("mat_throw_done") is True,
        "scripted_misses_preserve_raven_hp": raven.get_hp() == raven_hp,
        "rand_bow_never_removed": (
            rand_bow_present_after_cellar and rand_bow_present_after_throw
        ),
        "rand_repeat_bow_attack_stays_scripted": (
            "wn00_tutorial tutorial_rand_throw_script" in rand_repeat_script
        ),
        "tutorial_stones_are_removed": "thrown_stone" not in {
            *_item_nids(rand),
            *_item_nids(mat),
        },
        "raven_flies_off_before_moiraine": (
            game.level_vars.get("raven_done") is True
            and raven.position is None
            and not raven.dead
        ),
        "raven_sequence_has_no_inn_destination": game.get_region("inn_door") is None,
        "raven_sequence_wins_automatically": game.level_vars.get("_win_game") is True,
    }
    return {
        "events": (
            start
            + early
            + talk
            + cider
            + cellar
            + rand_tile
            + rand_bow_retry
            + rand_script
            + rand_done
            + mat_tile
            + mat_script
            + mat_done
            + raven_flee
        ),
        "checks": checks,
    }


def _chapter_escape(game, triggers) -> dict[str, Any]:
    level_id = "wn01_farm_escape"
    start = _drain_trigger(game, triggers.LevelStart(), level_id)
    rand = game.get_unit("rand")
    kit_region = game.get_region("farm_kit")
    kit = _drain_trigger(
        game,
        triggers.RegionTrigger("Clean Cloth", rand, rand.position, kit_region),
        level_id,
    )
    game.turncount = 2
    wave = _drain_trigger(game, triggers.TurnChange(), level_id)
    spawned = {nid: game.get_unit(nid).position for nid in ("pursuit_a", "pursuit_b")}
    region = game.get_region("westwood_exit")
    escape = _drain_trigger(
        game,
        triggers.RegionTrigger("Westwood", rand, rand.position, region),
        level_id,
    )
    checks = {
        "farm_kit_sets_flag": game.level_vars.get("farm_kit_collected") is True,
        "farm_kit_grants_dressing": "field_dressing" in _item_nids(rand),
        "turn_two_spawns_wave": all(position is not None for position in spawned.values()),
        "escape_starts_wound_once": game.level_vars.get("tam_wound_started") is True,
        "escape_marks_tam_wounded": game.level_vars.get("tam_wounded") is True,
        "escape_wins": game.level_vars.get("_win_game") is True,
    }
    return {"events": start + kit + wave + escape, "spawned": spawned, "checks": checks}


def _chapter_defense(game, triggers) -> dict[str, Any]:
    level_id = "wn02_village_defense"
    from app.engine import action

    executed = _drain_trigger(game, triggers.LevelStart(), level_id)
    luhhan = game.get_unit("luhhan_defender")
    starting_hp = luhhan.get_hp()

    mat = game.get_unit("mat_c2")
    egwene = game.get_unit("egwene_c2")
    moiraine = game.get_unit("moiraine")
    nynaeve = game.get_unit("nynaeve_c2")
    nynaeve_started_player = nynaeve.team == "player"
    executed += _drain_trigger(
        game, triggers.OnTalk(nynaeve, egwene, nynaeve.position), level_id
    )
    egwene_refreshed = egwene.team == "player" and not egwene.finished
    executed += _drain_trigger(
        game, triggers.OnTalk(egwene, mat, egwene.position), level_id
    )
    mat_refreshed = mat.team == "player" and not mat.finished

    inn = game.get_region("inn_safe")
    residents: dict[str, object] = {}
    visitors = {
        "west": egwene,
        "south": mat,
        "east": moiraine,
    }
    for house, visitor in visitors.items():
        door = game.get_region(f"house_{house}_door")
        action.do(action.Warp(visitor, door.position))
        executed += _drain_trigger(
            game,
            triggers.RegionTrigger("Visit", visitor, visitor.position, door),
            level_id,
        )
        resident = game.get_unit(f"resident_{house}")
        action.do(action.Warp(resident, inn.position))
        executed += _drain_trigger(
            game,
            triggers.RegionTrigger("Return", resident, resident.position, inn),
            level_id,
        )
        residents[resident.nid] = resident.position
    quota_banner = game.level.objective["simple"]
    quota_flash_requested = game.level_vars.get("_objective_flash") is True
    # The hold now begins only after the third villager has been counted, which
    # LT cannot do inside the same Return trigger batch, so it fires on the next
    # unit wait instead.
    hold_started_before_wait = game.level_vars.get("inn_hold_started")
    executed += _drain_trigger(
        game,
        triggers.UnitWait(moiraine, moiraine.position, None, True),
        level_id,
    )
    hold_assault = {
        nid: game.get_unit(nid)
        for nid in ("hold_north_a", "hold_north_b", "hold_south_a", "hold_south_b")
    }

    wave_positions: dict[str, dict[str, object]] = {}
    for turn in range(2, 10):
        game.turncount = turn
        executed += _drain_trigger(game, triggers.TurnChange(), level_id)
        if turn == 3:
            wave_positions["north"] = {
                nid: game.get_unit(nid).position
                for nid in ("north_wave_a", "north_wave_b")
            }
        elif turn == 5:
            wave_positions["flank"] = {
                nid: game.get_unit(nid).position
                for nid in ("flank_wave_a", "flank_wave_b")
            }
        elif turn == 7:
            wave_positions["south"] = {
                nid: game.get_unit(nid).position
                for nid in ("final_south_a", "final_south_b")
            }

    checks = {
        "haral_starts_wounded": starting_hp == 28 and luhhan.get_max_hp() == 40,
        "talk_recruits_refresh": (
            nynaeve_started_player and egwene_refreshed and mat_refreshed
        ),
        "named_recruits_are_mortal": all(
            all(skill.nid != "story_guardian" for skill in unit.skills)
            for unit in (mat, egwene, nynaeve)
        ),
        "three_residents_return": game.level_vars.get("residents_returned") == 3,
        "returned_residents_leave_map": all(
            position is None for position in residents.values()
        ),
        "east_house_lesson_flashes_live_quota": (
            quota_banner == "{v:residents_returned}/3 villagers saved"
            and quota_flash_requested
        ),
        "hold_waits_for_the_counted_third_villager": (
            hold_started_before_wait is False
        ),
        "rescue_quota_starts_inn_assault": (
            game.level_vars.get("inn_hold_started") is True
            and all(unit.position for unit in hold_assault.values())
            and all(unit.get_ai() == "assault_inn" for unit in hold_assault.values())
            and game.level.objective["simple"] == "Hold inn,Through turn 8"
        ),
        "turn_three_north_wave": all(wave_positions["north"].values()),
        "turn_five_full_flank_without_mastery": all(wave_positions["flank"].values()),
        "turn_seven_final_wave": all(wave_positions["south"].values()),
        "progressive_burn_layers_reveal": all(
            game.tilemap.layers.get(layer).visible
            for layer in (
                "background_west_burning",
                "background_west_ruined",
                "background_east_burning",
                "background_east_ruined",
            )
        ),
        "turn_nine_wins_with_three_returns": game.level_vars.get("_win_game") is True,
    }
    return {
        "events": executed,
        "waves": wave_positions,
        "checks": checks,
    }


def _chapter_return(game, triggers) -> dict[str, Any]:
    level_id = "wn03_return_to_farm"
    executed = _drain_trigger(game, triggers.LevelStart(), level_id)
    rand = game.get_unit("rand")
    # The gold farmhouse tile is an optional scene, not a gate. Search the three
    # supplies first, exactly as a player who walks past that tile does.
    farmhouse_before_searches = game.level_vars.get("farmhouse_reached")
    for region_nid in ("water", "bandages", "blankets"):
        region = game.get_region(region_nid)
        executed += _drain_trigger(
            game,
            triggers.RegionTrigger("Search", rand, rand.position, region),
            level_id,
        )
    supplies_without_farmhouse = farmhouse_before_searches is False and all(
        game.level_vars.get(flag) is True
        for flag in ("water_found", "bandages_found", "blankets_found")
    )
    approach = game.get_region("farmhouse_approach")
    executed += _drain_trigger(
        game,
        triggers.RegionTrigger("Visit", rand, rand.position, approach),
        level_id,
    )
    sword_region = game.get_region("tams_sword")
    executed += _drain_trigger(
        game,
        triggers.RegionTrigger("Search", rand, rand.position, sword_region),
        level_id,
    )
    equipped = rand.get_weapon()
    trolloc = game.get_unit("lone_trolloc")
    trolloc_position = trolloc.position
    exit_region = game.get_region("westwood_exit")
    early_escape = triggers.RegionTrigger("Escape", rand, rand.position, exit_region)
    early_escape_blocked = not game.events.get_triggered_events(early_escape, level_id)
    executed += _drain_trigger(
        game,
        triggers.CombatStart(
            trolloc,
            rand,
            trolloc.position,
            trolloc.get_weapon(),
            False,
        ),
        level_id,
    )
    executed += _drain_trigger(
        game,
        triggers.UnitDeath(trolloc, rand, trolloc.position),
        level_id,
    )
    quick_exit_region = game.get_region("westwood_quick_exit")
    executed += _drain_trigger(
        game,
        triggers.RegionTrigger("Escape", rand, rand.position, quick_exit_region),
        level_id,
    )
    executed += _drain_trigger(game, triggers.LevelEnd(), level_id)
    items = _item_nids(rand)
    checks = {
        "farmhouse_stage_reached": game.level_vars.get("farmhouse_reached") is True,
        "supplies_searchable_before_farmhouse_visit": supplies_without_farmhouse,
        "all_supply_flags_set": all(
            game.level_vars.get(flag) is True
            for flag in ("water_found", "bandages_found", "blankets_found")
        ),
        "supplies_granted": all(
            nid in items for nid in ("water_flask", "bandages", "blankets")
        ),
        "sword_granted": "tams_sword" in items,
        "sword_equipped": equipped is not None and equipped.nid == "tams_sword",
        "sword_spawns_narg_in_intercept_range": tuple(trolloc_position or ()) == (13, 7),
        "escape_blocked_before_narg_encounter": early_escape_blocked,
        "narg_initiated_combat_unlocks_escape": game.level_vars.get("narg_encountered")
        is True,
        "narg_defeat_activates_quick_exit": (
            game.level_vars.get("trolloc_defeated") is True
            and quick_exit_region is not None
        ),
        "quick_escape_wins": game.level_vars.get("_win_game") is True,
        "ending_scene_executed": any(nid.endswith(" sc_c3_rejoin_tam") for nid in executed),
        # The campaign no longer ends here; the ending card belongs only to wn05.
        "ending_card_not_played_mid_campaign": not any(
            nid.endswith(" sc_c5_ending_card") for nid in executed
        ),

    }
    return {"events": executed, "items": items, "checks": checks}


def verify_campaign_mechanics(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    """Exercise every authored mechanic through LT's trigger/action runtime."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import driver, engine, game_state
        from app.events import triggers

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                chapters = {
                    "wn00_tutorial": _chapter_tutorial(
                        game_state.start_level("wn00_tutorial"), triggers
                    ),
                    "wn01_farm_escape": _chapter_escape(
                        game_state.start_level("wn01_farm_escape"), triggers
                    ),
                    "wn02_village_defense": _chapter_defense(
                        game_state.start_level("wn02_village_defense"), triggers
                    ),
                    "wn03_return_to_farm": _chapter_return(
                        game_state.start_level("wn03_return_to_farm"), triggers
                    ),
                }
            finally:
                engine.terminate()

    all_checks_passed = all(all(chapter["checks"].values()) for chapter in chapters.values())
    result = {
        "verification_kind": "public_trigger_and_action_runtime",
        "input_driven": False,
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
        "chapters": chapters,
        "all_checks_passed": all_checks_passed,
    }
    if not all_checks_passed:
        raise RuntimeError(f"campaign mechanics verification failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def verify_search_escape_sequence(
    project: Path,
    engine_root: Path,
    level_id: str,
    unit_id: str,
    search_region_id: str,
    exit_region_id: str,
) -> dict[str, Any]:
    """Exercise a generic Search-gated Escape mission through LT's event router."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import driver, engine, game_state
        from app.events import triggers

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                game = game_state.start_level(level_id)
                executed = _drain_trigger(game, triggers.LevelStart(), level_id)
                unit = game.get_unit(unit_id)
                exit_region = game.get_region(exit_region_id)
                early_escape = triggers.RegionTrigger("Escape", unit, unit.position, exit_region)
                early_blocked = not game.events.get_triggered_events(early_escape, level_id)
                search_region = game.get_region(search_region_id)
                executed += _drain_trigger(
                    game,
                    triggers.RegionTrigger("Search", unit, unit.position, search_region),
                    level_id,
                )
                executed += _drain_trigger(
                    game,
                    triggers.RegionTrigger("Escape", unit, unit.position, exit_region),
                    level_id,
                )
                won = game.level_vars.get("_win_game") is True
            finally:
                engine.terminate()
    result = {
        "level": level_id,
        "early_escape_blocked": early_blocked,
        "search_then_escape_wins": won,
        "events": executed,
    }
    if not early_blocked or not won:
        raise RuntimeError(f"search/escape mechanics verification failed: {result}")
    return result
