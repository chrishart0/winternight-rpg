"""Contracts for the indestructible hero blades and the background rider.

Blade naming evidence (``source/private/eotw/05_winternight.txt``):
- 05:59 puts a bronze heron on the black scabbard and another on the long hilt,
  and states that except for the herons Tam's sword looked a good deal like
  Lan's sword -- one make, two blades.
- 05:63 has a third heron etched into the steel.
- Chapters 1-7 never hyphenate "heron-mark" and never use the word
  "Power-wrought"; Lan's sword is never given a proper name (02:177 gives only
  "the long hilt of a sword", 07:143 names him a Warder). Both display names are
  therefore descriptive, and `power_wrought_blades_never_break` in
  `source/adaptation_rules.yaml` records that Lan's comes from the wider series.

Rider evidence: 05:195 has Narg say the Myrddraal wants to talk and that the
others are coming back; 06:65 gives the Westwood column a horseman whose hooded
cloak hangs undisturbed by the wind. It never fights on-page in these chapters,
so the wn02 encounter is inert until the player strikes it.
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
LEVEL = "wn02_village_defense"
UNBREAKABLE = ("tams_sword", "warder_blade")


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


def _mission(campaign_bundle, mission_id: str = LEVEL):
    return next(mission for mission in campaign_bundle.missions if mission.id == mission_id)


def _warp(game, action, unit, position: tuple[int, int]) -> None:
    """Warp onto a verified-empty tile.

    wn02 is crowded; silently stacking two units on one tile makes
    ``board.get_unit`` return the wrong one and a combat test then measures the
    wrong victim.
    """
    occupant = game.board.get_unit(position)
    assert occupant in (None, unit), (position, getattr(occupant, "nid", occupant))
    action.do(action.Warp(unit, position))


def test_hero_blades_compile_without_any_durability_component(compiled_campaign):
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}

    assert items["tams_sword"]["name"] == "Heron Blade"
    assert items["warder_blade"]["name"] == "Power-wrought"
    for nid in UNBREAKABLE:
        components = _components(items[nid])
        # LT has no unbreakable flag; the absence of these components IS the
        # engine's infinite-durability path.
        assert "uses" not in components, nid
        assert "uses_options" not in components, nid
        assert "c_uses" not in components, nid
        assert "cooldown" not in components, nid
        # Everything that made them play the way they did is preserved.
        assert components["weapon"] is None, nid
        assert components["min_range"] == 1, nid
        assert components["max_range"] == 1, nid
        assert components["weapon_type"] == "Sword", nid
    assert _components(items["tams_sword"])["damage"] == 9
    assert _components(items["tams_sword"])["hit"] == 100
    assert _components(items["warder_blade"])["damage"] == 10
    assert _components(items["warder_blade"])["hit"] == 95


def test_finite_weapons_still_carry_their_uses(compiled_campaign):
    """Guard the flag: only the two authored blades lose durability tracking."""
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}

    assert _components(items["hunting_bow"])["uses"] == 35
    assert _components(items["trolloc_axe"])["uses"] == 40
    assert _components(items["rider_blade"])["uses"] == 40
    assert _components(items["ball_lightning"])["uses"] == 5


def test_unbreakable_and_authored_uses_cannot_be_combined():
    from pydantic import ValidationError

    from winternight_gen.models import ItemDefinition

    with pytest.raises(ValidationError, match="unbreakable items cannot author uses"):
        ItemDefinition.model_validate(
            {
                "id": "bad_blade",
                "name": "Bad Blade",
                "description": "x",
                "kind": "weapon",
                "weapon_type": "Sword",
                "unbreakable": True,
                "uses": 40,
            }
        )


def test_repeated_combat_never_consumes_or_breaks_the_warder_blade(lt_runtime):
    from app.engine import item_funcs, item_system
    from app.engine.combat import interaction

    _database, action, game_state, triggers = lt_runtime
    game = game_state.start_level(LEVEL)
    _drain_trigger(game, triggers.LevelStart(), LEVEL)

    lan = game.get_unit("lan")
    target = game.get_unit("raider_east")
    blade = lan.get_weapon()
    assert blade.nid == "warder_blade"
    assert blade.uses is None
    assert "uses" not in blade.data

    _warp(game, action, lan, (16, 8))
    _warp(game, action, target, (17, 8))
    for _round in range(12):
        action.do(action.SetHP(target, target.get_max_hp()))
        interaction.engage(
            lan,
            [target.position],
            blade,
            skip=True,
            script=["hit1", "hit2", "end"],
            total_rounds=1,
        )
        assert target.get_hp() < target.get_max_hp()

    assert blade in lan.items
    assert "uses" not in blade.data
    assert item_system.is_broken(lan, blade) is False
    assert item_funcs.available(lan, blade) is True
    assert lan.get_weapon().nid == "warder_blade"


def test_unbreakable_blades_render_no_durability_count(lt_runtime):
    """LT draws '--' when every uses source is absent (menu_options.ItemOption.draw)."""
    from app.engine import item_funcs
    from app.engine.game_menus.uses_display_config import UsesDisplayConfig

    _database, _action, game_state, triggers = lt_runtime
    game = game_state.start_level(LEVEL)
    _drain_trigger(game, triggers.LevelStart(), LEVEL)

    lan = game.get_unit("lan")
    blade = next(item for item in lan.items if item.nid == "warder_blade")
    dressing = next(item for item in lan.items if item.nid == "field_dressing")

    # Every branch LT consults before falling back to '--'.
    assert blade.uses is None
    assert blade.c_uses is None
    assert blade.cooldown is None
    assert blade.parent_item is None
    config = UsesDisplayConfig.from_item(blade, lan)
    assert config is None or config.get_uses() is None
    assert item_funcs.can_repair(lan, blade) is False

    # A finite item in the same inventory still reports a real count, so the
    # blank is the blade's property and not a broken renderer.
    assert dressing.data["uses"] == 3


def test_background_rider_is_placed_clear_of_every_objective_path(campaign_bundle):
    mission = _mission(campaign_bundle)
    units = {unit.id: unit for unit in mission.units}
    rider = units["rider_watch"]

    assert rider.character == "myrddraal"
    assert rider.team == "enemy"
    assert rider.position == (1, 1)
    assert rider.ai == "do_nothing"
    assert rider.items == ["rider_blade"]
    assert rider.role == "combatant"
    assert rider.starts_on_map is True
    assert rider.group is None

    # Not on a door, the inn, or any other unit's tile.
    regions = {region.id: region for region in mission.regions}
    for region_id in (
        "house_west_door",
        "house_north_door",
        "house_east_door",
        "house_south_door",
        "inn_safe",
        "inn_threshold",
    ):
        region = regions[region_id]
        x, y = region.position
        width, height = region.size
        cells = {(cx, cy) for cy in range(y, y + height) for cx in range(x, x + width)}
        assert rider.position not in cells, region_id
    others = [unit.position for unit in mission.units if unit.id != "rider_watch"]
    assert rider.position not in others

    # It is in no reinforcement group and no objective bookkeeping.
    grouped = {
        unit_id
        for group in mission.reinforcements
        for unit_id in group.unit_ids
    }
    assert "rider_watch" not in grouped
    assert mission.objective.rescue_count == 3
    assert mission.target_play.maximum_turns == 8


def test_background_rider_starts_inert_and_no_passive_trigger_wakes_it(lt_runtime):
    database, action, game_state, triggers = lt_runtime
    game = game_state.start_level(LEVEL)
    _drain_trigger(game, triggers.LevelStart(), LEVEL)

    rider = game.get_unit("rider_watch")
    lan = game.get_unit("lan")

    assert rider.position == (1, 1)
    assert rider.get_ai() == "do_nothing"
    # An all-'None' behaviour list is what makes the enemy phase a no-op.
    behaviours = database.ai.get(rider.get_ai()).behaviours
    assert behaviours and all(behaviour.action == "None" for behaviour in behaviours)

    def wakes(trigger) -> bool:
        return any(
            event.name == "rider_wakes_when_struck"
            for event in game.events.get_triggered_events(trigger, LEVEL)
        )

    # Standing next to it, ending turns, and enemy phases must all leave it alone.
    _warp(game, action, lan, (2, 1))
    assert not wakes(triggers.UnitWait(lan, lan.position, None, True))
    game.turncount = 3
    assert not wakes(triggers.TurnChange())
    assert not wakes(triggers.EnemyTurnChange())
    # Its own attack, or another enemy's, must not wake it either.
    blade = next(item for item in rider.items if item.nid == "rider_blade")
    assert not wakes(triggers.CombatEnd(rider, lan, rider.position, blade, []))

    assert rider.get_ai() == "do_nothing"
    assert rider.position == (1, 1)


def test_striking_the_background_rider_wakes_it_and_it_answers_the_blow(lt_runtime):
    from app.engine.combat import interaction

    _database, action, game_state, triggers = lt_runtime
    game = game_state.start_level(LEVEL)
    _drain_trigger(game, triggers.LevelStart(), LEVEL)

    rider = game.get_unit("rider_watch")
    lan = game.get_unit("lan")
    blade = lan.get_weapon()

    _warp(game, action, lan, (2, 1))
    rider_hp = rider.get_hp()
    lan_hp = lan.get_hp()

    combat = interaction.engage(
        lan, [rider.position], blade, skip=True, script=["hit1", "hit2", "end"], total_rounds=1
    )

    # A do_nothing unit still counterattacks: legality is decided by the combat
    # solver, never by AI.
    assert rider.get_hp() < rider_hp
    assert rider.get_hp() > 0
    assert lan.get_hp() < lan_hp
    assert combat.get_from_full_playback("damage_hit")

    executed = _drain_trigger(
        game, triggers.CombatEnd(lan, rider, lan.position, blade, []), LEVEL
    )

    assert f"{LEVEL} rider_wakes_when_struck" in executed
    assert rider.get_ai() == "pursue"


def test_rider_wake_event_is_compiled_as_a_single_player_only_trigger(compiled_campaign):
    events = {
        event["nid"]: event
        for event in _catalog(compiled_campaign, "events")
        if event["nid"].endswith("rider_wakes_when_struck")
    }
    (event,) = events.values()

    assert event["trigger"] == "combat_end"
    assert "unit2.nid == 'rider_watch'" in event["condition"]
    assert "unit.team == 'player'" in event["condition"]
    assert event["only_once"] is True
    assert "change_ai;rider_watch;pursue" in event["_source"]
