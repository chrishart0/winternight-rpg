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


def verify_tam_mortality(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    """Prove lethal combat can kill Tam independently of his scripted wound."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import action, combat_calcs, driver, engine, game_state
        from app.engine.combat import interaction

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                game = game_state.start_level("wn01_farm_escape")
                tam = game.get_unit("tam")
                attacker = game.get_unit("breach_axe_a")
                weapon = attacker.get_weapon()
                guardian = tam.get_skill("story_guardian")
                wound_event = next(
                    iter(
                        DB.events.get_by_nid_or_name(
                            "farm_escape_success", "wn01_farm_escape"
                        )
                    ),
                    None,
                )
                action.do(action.SetHP(tam, 8))
                damage = combat_calcs.compute_damage(
                    attacker,
                    tam,
                    weapon,
                    tam.get_weapon(),
                    "attack",
                    (0, 0),
                )
                combat = interaction.engage(
                    attacker,
                    [tam.position],
                    weapon,
                    skip=True,
                    script=["hit1", "end"],
                    total_rounds=1,
                )
                combat_finished = False
                for _ in range(3):
                    combat_finished = combat.update()
                if not combat_finished:
                    raise RuntimeError("pinned simple combat did not finish cleanup")
                marked_dying = tam.is_dying
                game.death.force_death(tam)
                hp_after_strike = tam.get_hp()
                playback_nids = [brush.nid for brush in combat.full_playback]
                damage_hits = [
                    {"damage": brush.damage, "true_damage": brush.true_damage}
                    for brush in combat.get_from_full_playback("damage_hit")
                ]
                guardian_procs = [
                    {"unit": brush.unit.nid, "skill": brush.skill.nid}
                    for brush in combat.get_from_full_playback("defense_hit_proc")
                ]
            finally:
                engine.terminate()

    checks = {
        "story_guardian_absent": guardian is None,
        "incoming_damage_was_lethal": damage is not None and damage >= 8,
        "tam_reaches_zero_hp": hp_after_strike == 0,
        "tam_marked_dying_after_combat": marked_dying,
        "tam_dead_after_death_manager": tam.dead,
        "no_guardian_proc": not guardian_procs,
        "scripted_wound_remains_a_separate_story_event": (
            wound_event is not None
            and "level_var;tam_wound_started;True" in wound_event.source
            and "trigger_script;sc_c1_tam_wounded" in wound_event.source
        ),
    }
    result = {
        "verification_kind": "real_simple_combat_solver_mortality",
        "engine_commit": (project / "ENGINE_COMMIT").read_text().strip(),
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(
            (project / "build_manifest.json").read_bytes()
        ).hexdigest(),
        "attacker": attacker.nid,
        "weapon": weapon.nid,
        "computed_damage": damage,
        "tam_hp_before": 8,
        "tam_hp_after": hp_after_strike,
        "playback": playback_nids,
        "damage_hits": damage_hits,
        "guardian_procs": guardian_procs,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    if not result["all_checks_passed"]:
        raise RuntimeError(f"Tam mortality verification failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
