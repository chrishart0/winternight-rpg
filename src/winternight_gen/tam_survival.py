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


def verify_tam_survives_lethal_combat(
    project: Path, engine_root: Path, evidence_path: Path
) -> dict[str, Any]:
    """Run a real pinned-engine combat strike against Tam at one HP."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import action, combat_calcs, driver, engine, game_state
        from app.engine.combat import interaction

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(
            runtime_root
        ):
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
                if guardian is None:
                    raise RuntimeError("Tam is missing story_guardian in the live level")
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
        "guardian_loaded_on_live_tam": guardian is not None,
        "incoming_damage_was_lethal": damage is not None and damage >= 8,
        "tam_remains_at_one_hp": hp_after_strike == 1,
        "guardian_proc_in_playback": guardian_procs
        == [{"unit": "tam", "skill": "story_guardian"}],
        "tam_not_marked_dying": not tam.is_dying,
    }
    result = {
        "verification_kind": "real_simple_combat_solver",
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
        raise RuntimeError(f"Tam lethal combat verification failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
