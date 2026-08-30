"""Contract tests for Moiraine's canon-informed weave kit.

Bran's Chapter 7 account (``source/private/eotw/07_out_of_the_woods.txt``:135-141)
is the only channeling the book attributes to Moiraine on Winternight, and it
attributes exactly one weave: ball lightning called from a clear sky and sent
darting at the Trollocs. The same conversation states that Aes Sedai cure where
medicines fail (07:151) while the Wisdom's craft has already run out (07:185),
so village herbs belong to Nynaeve and Egwene, never to the channeler.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

import pytest

from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.mechanics import _drain_trigger
from winternight_gen.runtime import isolated_engine_runtime

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"

MOIRAINE_KIT = ["weave_of_air", "ball_lightning", "weave_of_spirit"]


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@pytest.fixture
def lt_runtime(compiled_campaign):
    import sys

    engine_path = str(ENGINE_ROOT.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(ENGINE_ROOT):
        from app import sprites as sprite_catalog
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import action, driver, engine, game_state
        from app.events import triggers

        with isolated_engine_runtime(ENGINE_ROOT) as runtime_root, _working_directory(
            runtime_root
        ):
            sprite_catalog.reset()
            RESOURCES.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            DB.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                yield DB, action, game_state, triggers
            finally:
                engine.terminate()


def _catalog(project: Path, name: str):
    return json.loads((project / "game_data" / f"{name}.json").read_text(encoding="utf-8"))


def _components(item: dict) -> dict:
    return dict(item["components"])


def _character(campaign_bundle, character_id: str):
    return next(
        character
        for character in campaign_bundle.characters.characters
        if character.id == character_id
    )


def _warp(game, action, unit, position: tuple[int, int]) -> None:
    """Warp onto a verified-empty tile.

    wn02 is crowded; silently stacking two units on one tile makes
    ``board.get_unit`` return the wrong one and a combat test then measures the
    wrong victim.
    """
    occupant = game.board.get_unit(position)
    assert occupant in (None, unit), (position, getattr(occupant, "nid", occupant))
    action.do(action.Warp(unit, position))


def test_moiraine_carries_no_village_herbs(campaign_bundle, compiled_campaign):
    moiraine = _character(campaign_bundle, "moiraine")

    assert "herb_pouch" not in moiraine.combat.starting_items
    assert "field_dressing" not in moiraine.combat.starting_items

    units = {unit["nid"]: unit for unit in _catalog(compiled_campaign, "units")}
    carried = [item for item, _dropped in units["moiraine"]["starting_items"]]
    assert "herb_pouch" not in carried


def test_village_healers_keep_their_herb_pouch(campaign_bundle, compiled_campaign):
    for healer_id in ("nynaeve", "egwene"):
        assert "herb_pouch" in _character(campaign_bundle, healer_id).combat.starting_items

    units = {unit["nid"]: unit for unit in _catalog(compiled_campaign, "units")}
    for unit_id in ("nynaeve_c2", "egwene_c2"):
        carried = [item for item, _dropped in units[unit_id]["starting_items"]]
        assert "herb_pouch" in carried, unit_id


def test_moiraine_kit_is_three_weaves_in_equip_order(campaign_bundle, compiled_campaign):
    moiraine = _character(campaign_bundle, "moiraine")

    # Weave of Air stays first so the engine equips her melee-capable weave and
    # she still counterattacks adjacent raiders.
    assert moiraine.combat.starting_items == MOIRAINE_KIT

    units = {unit["nid"]: unit for unit in _catalog(compiled_campaign, "units")}
    assert [item for item, _dropped in units["moiraine"]["starting_items"]] == MOIRAINE_KIT


def test_moiraine_needs_no_staff_rank_for_her_kit(campaign_bundle):
    moiraine = _character(campaign_bundle, "moiraine")
    items = {item.id: item for item in campaign_bundle.gameplay.items}

    assert moiraine.combat.weapon_type == "Magic"
    assert moiraine.combat.additional_weapon_types == []
    assert {items[item_id].weapon_type for item_id in moiraine.combat.starting_items} == {
        "Magic",
        None,
    }


def test_ball_lightning_compiles_as_a_scarce_reaching_magic_strike(compiled_campaign):
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}
    lightning = items["ball_lightning"]
    components = _components(lightning)

    assert lightning["name"] == "Ball Lightning"
    assert lightning["desc"] == (
        "Lightning called from a clear sky, sent darting at one raider."
    )
    assert components["weapon"] is None
    assert components["target_enemy"] is None
    assert components["magic"] is None
    # Reach the book's "darting straight at the Trollocs" without allowing a
    # melee shot: she must reposition or fall back on the Weave of Air.
    assert components["min_range"] == 2
    assert components["max_range"] == 3
    assert components["damage"] == 12
    assert components["hit"] == 85
    assert components["uses"] == 5
    assert components["weapon_type"] == "Magic"
    assert components["map_target_cast_anim"] == "BallLightning"


def test_weave_of_air_remains_her_short_range_workhorse(compiled_campaign):
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}
    components = _components(items["weave_of_air"])

    assert components["min_range"] == 1
    assert components["max_range"] == 2
    assert components["damage"] == 8
    assert components["uses"] == 15
    assert components["magic"] is None
    assert "map_target_cast_anim" not in components


def test_ball_lightning_does_not_one_shot_the_door_torchbearers(
    campaign_bundle, compiled_campaign
):
    """Keep enemy readability: lightning ends light spear raiders, not the clocks."""
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}
    units = {unit["nid"]: unit for unit in _catalog(compiled_campaign, "units")}
    might = _components(items["ball_lightning"])["damage"]
    magic = dict(units["moiraine"]["bases"])["MAG"]

    def survives(unit_nid: str) -> bool:
        bases = dict(units[unit_nid]["bases"])
        return bases["HP"] > magic + might - bases["RES"]

    assert not survives("raider_east")  # plain jagged-spear raider dies outright
    assert survives("raider_ne")  # axe raiders always need a follow-up
    for torch in ("torch_west", "torch_north", "torch_east", "torch_south"):
        assert survives(torch), torch


def test_weave_kit_carries_labelled_adaptation_decisions(campaign_bundle):
    decisions = {
        decision.id: decision for decision in campaign_bundle.adaptation_rules.decisions
    }

    lightning = decisions["moiraine_ball_lightning_weave"]
    assert lightning.canon_status == "gameplay_invention"
    assert lightning.source_beats == ["c2_bran_account", "c2_village_defense"]

    healing = decisions["moiraine_heals_by_weave_not_herbs"]
    assert healing.canon_status == "inferred"
    assert "c2_nynaeve_battle_aid" in healing.source_beats

    beats = {beat.id: beat for beat in campaign_bundle.story_beats.beats}
    assert beats["c2_bran_account"].canon_status == "direct"
    assert beats["c2_bran_account"].source_locator == "07:135-141"


def test_moiraine_heals_allies_through_the_spell_action_at_range_two(lt_runtime):
    from app.engine import item_funcs
    from app.engine.combat import interaction

    _database, action, game_state, triggers = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    _drain_trigger(game, triggers.LevelStart(), "wn02_village_defense")

    moiraine = game.get_unit("moiraine")
    haral = game.get_unit("luhhan_defender")
    raider = game.get_unit("raider_east")
    weave = next(item for item in moiraine.items if item.nid == "weave_of_spirit")

    assert [item.nid for item in moiraine.items] == MOIRAINE_KIT
    assert all(item.nid != "herb_pouch" for item in moiraine.items)

    _warp(game, action, moiraine, (16, 8))
    _warp(game, action, haral, (16, 10))
    _warp(game, action, raider, (15, 8))
    wounded = haral.get_max_hp() - 20
    action.do(action.SetHP(haral, wounded))

    # A spell, not a consumable: unusable from the item menu, reaches an ally
    # two tiles away, and never offers an adjacent enemy as a target.
    assert item_funcs.can_use(moiraine, weave) is False
    targets = game.target_system.get_valid_targets(moiraine, weave)
    assert haral.position in targets
    assert raider.position not in targets

    interaction.engage(moiraine, [haral.position], weave, skip=True, total_rounds=1)

    assert haral.get_hp() == wounded + 14


def test_moiraine_strikes_a_raider_three_tiles_away_with_ball_lightning(lt_runtime):
    from app.engine.combat import interaction

    _database, action, game_state, triggers = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    _drain_trigger(game, triggers.LevelStart(), "wn02_village_defense")

    moiraine = game.get_unit("moiraine")
    target = game.get_unit("raider_east")
    lightning = next(item for item in moiraine.items if item.nid == "ball_lightning")

    _warp(game, action, moiraine, (16, 8))
    _warp(game, action, target, (16, 11))
    assert target.position in game.target_system.get_valid_targets(moiraine, lightning)

    hp_before = target.get_hp()
    combat = interaction.engage(
        moiraine,
        [target.position],
        lightning,
        skip=True,
        script=["hit1", "end"],
        total_rounds=1,
    )

    assert combat.get_from_full_playback("damage_hit")
    assert target.get_hp() < hp_before

    # Adjacent raiders are out of reach; that is what the Weave of Air is for.
    _warp(game, action, target, (15, 8))
    assert target.position not in game.target_system.get_valid_targets(moiraine, lightning)
