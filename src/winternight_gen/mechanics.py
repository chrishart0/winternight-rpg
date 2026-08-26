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
    start = _drain_trigger(game, triggers.LevelStart(), level_id)
    rand, mat = game.get_unit("rand"), game.get_unit("mat")
    talk = _drain_trigger(game, triggers.OnTalk(rand, mat, rand.position), level_id)
    region = game.get_region("inn_barrels")
    visit = _drain_trigger(
        game, triggers.RegionTrigger("Visit", rand, rand.position, region), level_id
    )
    tam = game.get_unit("tam_village")
    finish = _drain_trigger(game, triggers.OnTalk(rand, tam, rand.position), level_id)
    checks = {
        "mat_talk_sets_flag": game.level_vars.get("talked_to_mat") is True,
        "visit_sets_delivery_flag": game.level_vars.get("delivered_cider") is True,
        "visit_grants_hunting_bow": "hunting_bow" in _item_nids(rand),
        "tam_talk_wins": game.level_vars.get("_win_game") is True,
    }
    return {"events": start + talk + visit + finish, "checks": checks}


def _chapter_escape(game, triggers) -> dict[str, Any]:
    level_id = "wn01_farm_escape"
    start = _drain_trigger(game, triggers.LevelStart(), level_id)
    game.turncount = 3
    wave = _drain_trigger(game, triggers.TurnChange(), level_id)
    spawned = {
        nid: game.get_unit(nid).position for nid in ("pursuit_a", "pursuit_b")
    }
    rand = game.get_unit("rand")
    region = game.get_region("westwood_exit")
    escape = _drain_trigger(
        game, triggers.RegionTrigger("Escape", rand, rand.position, region), level_id
    )
    checks = {
        "turn_three_spawns_wave": all(position is not None for position in spawned.values()),
        "escape_starts_wound_once": game.level_vars.get("tam_wound_started") is True,
        "escape_marks_tam_wounded": game.level_vars.get("tam_wounded") is True,
        "escape_wins": game.level_vars.get("_win_game") is True,
    }
    return {"events": start + wave + escape, "spawned": spawned, "checks": checks}


def _chapter_defense(game, triggers) -> dict[str, Any]:
    level_id = "wn02_village_defense"
    executed = _drain_trigger(game, triggers.LevelStart(), level_id)
    region = game.get_region("inn_safe")
    rescued_positions: dict[str, object] = {}
    for unit_nid in ("civilian_west", "civilian_east", "civilian_south"):
        unit = game.get_unit(unit_nid)
        executed += _drain_trigger(
            game,
            triggers.RegionTrigger("Rescue", unit, unit.position, region),
            level_id,
        )
        rescued_positions[unit_nid] = unit.position
    game.turncount = 3
    executed += _drain_trigger(game, triggers.TurnChange(), level_id)
    north_positions = {
        nid: game.get_unit(nid).position for nid in ("north_wave_a", "north_wave_b")
    }
    game.turncount = 5
    executed += _drain_trigger(game, triggers.TurnChange(), level_id)
    flank_positions = {
        nid: game.get_unit(nid).position for nid in ("flank_wave_a", "flank_wave_b")
    }
    game.turncount = 7
    executed += _drain_trigger(game, triggers.TurnChange(), level_id)
    checks = {
        "all_rescue_flags_set": all(
            game.level_vars.get(flag) is True
            for flag in ("rescued_west", "rescued_east", "rescued_south")
        ),
        "rescued_units_removed": all(
            position is None for position in rescued_positions.values()
        ),
        "turn_three_spawns_north_wave": all(
            position is not None for position in north_positions.values()
        ),
        "turn_five_spawns_flank_wave": all(
            position is not None for position in flank_positions.values()
        ),
        "turn_seven_wins_after_rescues": game.level_vars.get("_win_game") is True,
    }
    return {
        "events": executed,
        "north_wave": north_positions,
        "flank_wave": flank_positions,
        "checks": checks,
    }


def _chapter_return(game, triggers) -> dict[str, Any]:
    level_id = "wn03_return_to_farm"
    executed = _drain_trigger(game, triggers.LevelStart(), level_id)
    rand = game.get_unit("rand")
    for region_nid in ("water", "bandages", "blankets"):
        region = game.get_region(region_nid)
        executed += _drain_trigger(
            game,
            triggers.RegionTrigger("Search", rand, rand.position, region),
            level_id,
        )
    sword_region = game.get_region("tams_sword")
    executed += _drain_trigger(
        game,
        triggers.RegionTrigger("Search", rand, rand.position, sword_region),
        level_id,
    )
    equipped = rand.get_weapon()
    trolloc_position = game.get_unit("lone_trolloc").position
    exit_region = game.get_region("westwood_exit")
    executed += _drain_trigger(
        game,
        triggers.RegionTrigger("Escape", rand, rand.position, exit_region),
        level_id,
    )
    executed += _drain_trigger(game, triggers.LevelEnd(), level_id)
    items = _item_nids(rand)
    checks = {
        "all_supply_flags_set": all(
            game.level_vars.get(flag) is True
            for flag in ("water_found", "bandages_found", "blankets_found")
        ),
        "supplies_recorded_without_inventory_slots": not any(
            nid in items for nid in ("water_flask", "bandages", "blankets")
        ),
        "sword_granted": "tams_sword" in items,
        "sword_equipped": equipped is not None and equipped.nid == "tams_sword",
        "sword_spawns_lone_trolloc": trolloc_position is not None,
        "escape_wins": game.level_vars.get("_win_game") is True,
        "ending_scene_executed": any(
            nid.endswith(" sc_c3_rejoin_tam") for nid in executed
        ),
        "ending_card_executed": any(
            nid.endswith(" sc_c3_ending_card") for nid in executed
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

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(
            runtime_root
        ):
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

    all_checks_passed = all(
        all(chapter["checks"].values()) for chapter in chapters.values()
    )
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
    evidence_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
