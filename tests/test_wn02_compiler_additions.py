from __future__ import annotations

import copy
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
from pydantic import ValidationError

from winternight_gen.event_compiler import compile_action, compile_mission_event
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.mechanics import _drain_trigger
from winternight_gen.models import EventActionSpec, MapLayoutSpec, MissionEventSpec
from winternight_gen.runtime import isolated_engine_runtime

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@pytest.fixture(scope="module")
def compiled_lt_data(compiled_campaign):
    with generated_component_system(ENGINE_ROOT):
        import sys

        sys.path.insert(0, str(ENGINE_ROOT))
        from app.data.database.database import Database
        from app.data.resources.resources import Resources
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

        resources = Resources()
        resources.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
        database = Database()
        database.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
    return database, resources


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
        from app.engine import action, driver, engine, game_state, skill_system
        from app.events import triggers

        with isolated_engine_runtime(ENGINE_ROOT) as runtime_root, _working_directory(
            runtime_root
        ):
            sprite_catalog.reset()
            RESOURCES.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            DB.load(compiled_campaign, CURRENT_SERIALIZATION_VERSION)
            driver.start(DB.constants.value("title"), from_editor=True)
            try:
                yield DB, action, game_state, skill_system, triggers
            finally:
                engine.terminate()


def _layer_layout() -> dict[str, object]:
    return {
        "schema_version": "0.2",
        "id": "layer_fixture",
        "width": 8,
        "height": 8,
        "legend": {
            "G": {
                "terrain_id": "grass",
                "name": "Grass",
                "color": [1, 2, 3],
                "minimap": "Grass",
                "platform": "Plains",
                "movement_cost": 1,
            }
        },
        "variants": [
            {
                "id": "base",
                "lighting": "day",
                "rows": ["G" * 8] * 8,
                "layers": [
                    {
                        "id": "damage",
                        "tiles": {"1,2": "G"},
                    }
                ],
            }
        ],
    }


def test_sparse_layer_model_rejects_bad_coordinates_symbols_and_duplicate_ids():
    out_of_bounds = _layer_layout()
    out_of_bounds["variants"][0]["layers"][0]["tiles"] = {"8,2": "G"}
    with pytest.raises(ValidationError, match="out of bounds"):
        MapLayoutSpec.model_validate(out_of_bounds)

    unknown_symbol = _layer_layout()
    unknown_symbol["variants"][0]["layers"][0]["tiles"] = {"1,2": "X"}
    with pytest.raises(ValidationError, match="unknown tile"):
        MapLayoutSpec.model_validate(unknown_symbol)

    duplicate_ids = _layer_layout()
    duplicate_ids["variants"][0]["layers"].append(
        copy.deepcopy(duplicate_ids["variants"][0]["layers"][0])
    )
    with pytest.raises(ValidationError, match="layer IDs must be unique"):
        MapLayoutSpec.model_validate(duplicate_ids)


def test_house_state_layers_cover_facades_and_aligned_doors(compiled_lt_data):
    _, resources = compiled_lt_data
    tilemap = resources.tilemaps.get("emonds_field_battle__winternight_attack")
    houses = {
        "west": ({(2, 6), (3, 6), (4, 6), (2, 7), (3, 7), (4, 7)}, (3, 7)),
        "north": (
            {
                (9, 1),
                (10, 1),
                (11, 1),
                (12, 1),
                (9, 2),
                (10, 2),
                (11, 2),
                (12, 2),
            },
            (10, 2),
        ),
        "east": (
            {(17, 6), (18, 6), (19, 6), (17, 7), (18, 7), (19, 7)},
            (18, 7),
        ),
        "south": (
            {
                (9, 15),
                (10, 15),
                (11, 15),
                (12, 15),
                (9, 16),
                (10, 16),
                (11, 16),
                (12, 16),
            },
            (12, 16),
        ),
    }

    for house, (footprint, door) in houses.items():
        saved = tilemap.layers.get(f"house_{house}_saved")
        ruined = tilemap.layers.get(f"house_{house}_ruined")

        assert saved.visible is ruined.visible is False
        assert saved.foreground is ruined.foreground is False
        assert set(saved.sprite_grid) == set(saved.terrain_grid) == {door}
        assert saved.terrain_grid[door] == "closed_door"
        assert set(ruined.sprite_grid) == set(ruined.terrain_grid) == footprint
        assert ruined.terrain_grid[door] == "fire"


def test_inn_region_only_interrupts_rescued_residents(compiled_lt_data):
    database, _ = compiled_lt_data
    level = database.levels.get("wn02_village_defense")
    inn = next(region for region in level.regions if region.nid == "inn_safe")

    assert inn.interrupt_move is True
    assert inn.condition == (
        "unit and unit.nid in "
        "('resident_west', 'resident_north', 'resident_east', 'resident_south')"
    )


def test_waiting_on_inn_floor_auto_returns_resident(lt_runtime):
    _, action, game_state, _, triggers = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    _drain_trigger(game, triggers.LevelStart(), "wn02_village_defense")
    visitor = game.get_unit("nynaeve_c2")
    door = game.get_region("house_west_door")
    action.do(action.Warp(visitor, door.position))
    _drain_trigger(
        game,
        triggers.RegionTrigger("Visit", visitor, visitor.position, door),
        "wn02_village_defense",
    )
    resident = game.get_unit("resident_west")
    action.do(action.Warp(resident, (9, 6)))
    action.do(action.Wait(resident))

    while event := game.events.get():
        event.skip(super_skip=True)
        for _ in range(512):
            event.update()
            if event.finished():
                break
        else:
            raise RuntimeError(f"event did not finish: {event.nid}")
        game.events.end(event)

    assert game.level_vars["resident_west_returned"] is True
    assert game.level_vars["residents_returned"] == 1
    assert resident.position is None

def test_mat_fires_hunting_bow_through_pinned_combat_solver(lt_runtime):
    from app.engine.combat import interaction

    _, action, game_state, _, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    mat = game.get_unit("mat_c2")
    target = game.get_unit("raider_east")
    bow = mat.get_weapon()
    assert bow.nid == "hunting_bow"

    action.do(action.Warp(mat, (12, 12)))
    action.do(action.Warp(target, (14, 12)))
    hp_before = target.get_hp()
    combat = interaction.engage(
        mat,
        [target.position],
        bow,
        skip=True,
        script=["hit1", "end"],
        total_rounds=1,
    )

    assert target.get_hp() < hp_before
    assert combat.get_from_full_playback("damage_hit")

def test_healing_herbs_use_item_action_and_target_self_or_adjacent_ally(lt_runtime):
    from app.engine import item_funcs
    from app.engine.general_states import ItemState, MenuState

    database, action, game_state, _, triggers = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    _drain_trigger(game, triggers.LevelStart(), "wn02_village_defense")
    nynaeve = game.get_unit("nynaeve_c2")
    haral = game.get_unit("luhhan_defender")
    herbs = next(item for item in nynaeve.items if item.nid == "herb_pouch")

    action.do(action.Warp(nynaeve, (10, 10)))
    action.do(action.SetHP(nynaeve, nynaeve.get_max_hp() - 8))
    game.cursor.cur_unit = nynaeve
    game.cursor.set_pos(nynaeve.position)
    menu_state = MenuState()
    menu_state.start()
    menu_state.begin()
    options = [
        option.get() if callable(getattr(option, "get", None)) else str(option)
        for option in menu_state.menu.options
    ]

    # The herb pouch is a carried remedy: it reaches the Item command and the
    # weave action is not offered to a village Wisdom at all.
    assert "Item" in options
    assert "Spells" not in options
    assert item_funcs.can_use(nynaeve, herbs) is True
    assert game.target_system.get_valid_targets(nynaeve, herbs) >= {
        nynaeve.position,
        haral.position,
    }

    item_state = ItemState()
    item_state.start()
    item_state.begin()
    assert "Healing Herbs" in [option.get().name for option in item_state.menu.options]
    assert database.translations.get("Spells").text == "Weave"

    # Both authored targets still resolve through the Item command.
    from app.engine.combat import interaction

    wounded_self = nynaeve.get_hp()
    interaction.engage(nynaeve, [nynaeve.position], herbs, skip=True, total_rounds=1)
    assert nynaeve.get_hp() == wounded_self + 8

    action.do(action.SetHP(haral, haral.get_max_hp() - 12))
    wounded_ally = haral.get_hp()
    interaction.engage(nynaeve, [haral.position], herbs, skip=True, total_rounds=1)
    assert haral.get_hp() == wounded_ally + 8
    assert herbs.data["uses"] == 1

def test_classic_permadeath_keeps_dead_playable_off_field_but_story_events_exist(
    lt_runtime,
):
    database, action, game_state, _, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    nynaeve = game.get_unit("nynaeve_c2")

    action.do(action.Die(nynaeve))
    game.clean_up(full=False)
    game.start_level("wn02_village_defense")

    assert game.current_mode.permadeath is True
    assert game.get_unit("nynaeve_c2").dead is True
    assert game.get_unit("nynaeve_c2").position is None
    assert any(
        event.nid.endswith(" sc_c2_nynaeve_first_heal")
        or event.nid == "sc_c2_nynaeve_first_heal"
        for event in database.events
    )


def test_event_conditions_and_current_hp_compile_to_exact_lt_contract(compiled_lt_data):
    database, _ = compiled_lt_data
    events = {event.nid: event for event in database.events}
    defense_start = events["wn02_village_defense defense_start"]
    ruin = events["wn02_village_defense ruin_house_west"]
    win = events["wn02_village_defense defense_win"]
    loss = events["wn02_village_defense defense_loss_quota"]
    permadeath = events["wn02_village_defense nynaeve_permadeath"]

    assert "set_current_hp;luhhan_defender;28" in defense_start.source.splitlines()
    assert "inc_level_var;houses_ruined;1" in ruin.source.splitlines()
    assert "unit and unit.team == 'enemy'" in ruin.condition
    assert "'house_west_door' in game.level.regions" in ruin.condition
    assert ".contains(unit.position)" in ruin.condition
    assert "game.level_vars.get('residents_returned', 0) >= 3" in win.condition
    assert "game.level_vars.get('residents_returned', 0) <= 2" in loss.condition
    assert permadeath.condition == (
        "(unit and unit.nid == 'nynaeve_c2') and "
        "(unit and unit.team == 'player')"
    )
    assert permadeath.source.splitlines() == [
        (
            "speak;;Nynaeve died and is gone as a playable unit.;"
            "bottom;;noir;2.0;;no_sound"
        ),
        "speak;;They will still appear in story scenes.;bottom;;noir;2.0;;no_sound",
        (
            "choice;death_nynaeve_c2;Restart the level?;"
            "restart|Restart,continue|Continue"
        ),
        "if;game.game_vars.get('death_nynaeve_c2') == 'restart'",
        "lose_game",
        "end",
    ]


@pytest.mark.parametrize(
    ("op", "operator"),
    (("ge", ">="), ("le", "<="), ("eq", "==")),
)
def test_level_var_compare_supports_each_operator(campaign_bundle, op, operator):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn02_village_defense"
    )
    event = MissionEventSpec.model_validate(
        {
            "id": "comparison",
            "trigger": {"type": "turn_start", "turn": 9},
            "condition": {
                "level_var_compare": {
                    "name": "residents_returned",
                    "op": op,
                    "value": 3,
                }
            },
            "actions": [{"type": "win"}],
        }
    )

    _, condition, _ = compile_mission_event(mission, event)

    assert f"game.level_vars.get('residents_returned', 0) {operator} 3" in condition


@pytest.mark.parametrize("value", (0, -1, True, "28"))
def test_set_current_hp_rejects_non_positive_or_non_integer_values(value):
    with pytest.raises(ValidationError, match="positive integer"):
        EventActionSpec(type="set_current_hp", target="luhhan_defender", value=value)


def test_set_current_hp_emits_pinned_lt_command():
    action = EventActionSpec(
        type="set_current_hp", target="luhhan_defender", value=28
    )

    assert compile_action(action) == ["set_current_hp;luhhan_defender;28"]


def test_trigger_unit_condition_rejects_triggers_without_unit_context():
    with pytest.raises(ValidationError, match="requires a trigger with unit context"):
        MissionEventSpec.model_validate(
            {
                "id": "invalid",
                "trigger": {"type": "turn_start", "turn": 2},
                "condition": {
                    "trigger_unit_in_region": {
                        "team": "enemy",
                        "region": "door",
                    }
                },
                "actions": [{"type": "set_flag", "target": "bad", "value": True}],
            }
        )


def test_wn02_additions_execute_through_lt_runtime(lt_runtime):
    _, action, game_state, _, triggers = lt_runtime
    level_id = "wn02_village_defense"
    game = game_state.start_level(level_id)
    executed = _drain_trigger(game, triggers.LevelStart(), level_id)

    assert game.get_unit("luhhan_defender").get_hp() == 28
    assert game.tilemap.layers.get("house_west_ruined").visible is False

    lan = game.get_unit("lan")
    lan_start = lan.position
    action.do(action.Warp(lan, (3, 7)))
    ally_wait = triggers.UnitWait(lan, lan.position, game.get_region("house_west_door"), True)
    assert not any(
        event.name == "ruin_house_west"
        for event in game.events.get_triggered_events(ally_wait, level_id)
    )
    action.do(action.Warp(lan, lan_start))

    torch = game.get_unit("torch_west")
    action.do(action.Warp(torch, (3, 7)))
    executed += _drain_trigger(
        game,
        triggers.UnitWait(
            torch,
            torch.position,
            game.get_region("house_west_door"),
            False,
        ),
        level_id,
    )
    assert game.level_vars["houses_ruined"] == 1
    assert "house_west_door" not in game.level.regions
    assert game.tilemap.layers.get("house_west_ruined").visible is True

    game.turncount = 2
    executed += _drain_trigger(game, triggers.TurnChange(), level_id)
    assert game.tilemap.layers.get("background_west_burning").visible is True

    game.level_vars["residents_returned"] = 3
    game.turncount = 9
    executed += _drain_trigger(game, triggers.TurnChange(), level_id)
    assert game.level_vars.get("_win_game") is True
    assert "wn02_village_defense defense_win" in executed

    losing_game = game_state.start_level(level_id)
    _drain_trigger(losing_game, triggers.LevelStart(), level_id)
    losing_game.level_vars["residents_returned"] = 2
    losing_game.turncount = 9
    losing_events = _drain_trigger(losing_game, triggers.TurnChange(), level_id)
    assert losing_game.level_vars.get("_lose_game") is True
    assert "wn02_village_defense defense_loss_quota" in losing_events


def test_enemy_occupied_tile_forces_a_detour_in_the_village_map(lt_runtime):
    _, action, game_state, skill_system, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    mover = game.get_unit("lan")
    blocker = game.get_unit("raider_west")
    start = (2, 11)
    occupied = (3, 11)
    target = (4, 11)

    action.do(action.Warp(mover, start))
    action.do(action.Warp(blocker, occupied))

    assert skill_system.pass_through(mover) is False
    assert mover.get_movement() >= 4
    assert game.board.can_move_through("player", occupied) is False
    assert occupied not in game.path_system.get_valid_moves(mover)

    enemy_blocked_path = game.path_system.get_path(
        mover, target, use_limit=mover.get_movement()
    )
    assert occupied not in enemy_blocked_path
    assert game.path_system.get_path_cost(mover, enemy_blocked_path) == 4

    action.do(action.ChangeTeam(blocker, "player"))
    assert game.board.can_move_through("player", occupied) is True
    assert game.board.get_unit(occupied) is blocker
    assert occupied in game.path_system.get_valid_moves(mover)

    ally_path = game.path_system.get_path(
        mover, target, use_limit=mover.get_movement()
    )
    assert occupied in ally_path
    assert game.path_system.get_path_cost(mover, ally_path) == 2


def test_manual_end_turn_with_unused_player_units_does_not_throw(lt_runtime):
    from app.engine import general_states

    database, _, game_state, skill_system, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    unused_units = [
        unit
        for unit in game.get_player_units()
        if unit.position and not unit.finished and skill_system.can_select(unit)
    ]
    assert len(unused_units) >= 2
    game.state.clear()
    game.state.process_temp_state()
    game.state.change("option_menu")
    game.state.process_temp_state()
    option_menu = game.state.current_state()
    assert isinstance(option_menu, general_states.OptionMenuState)
    option_menu.start()
    option_menu.menu.set_selection("End")
    option_menu.take_input("SELECT")
    game.state.process_temp_state()

    confirmation = game.state.current_state()
    assert isinstance(confirmation, general_states.OptionChildState)
    confirmation.begin()
    confirmation.menu.set_selection("Yes")
    confirmation.take_input("SELECT")
    game.state.process_temp_state()
    assert game.state.current() == "ai"

    while game.phase.get_current() != "other":
        game.phase.next()
    ai_state = general_states.AIState("ai")
    ai_state.start()
    next_unit = ai_state.get_next_unit()

    assert next_unit is not None
    assert next_unit.team == "other"
    assert database.ai.get(next_unit.get_ai()) is not None


def test_egwene_can_talk_mat_in_one_move_after_joining(lt_runtime):
    _, _, game_state, _, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    egwene = game.get_unit("egwene_c2")
    mat = game.get_unit("mat_c2")
    nynaeve = game.get_unit("nynaeve_c2")
    moiraine = game.get_unit("moiraine")

    assert mat.position not in {nynaeve.position, moiraine.position}
    moves = game.path_system.get_valid_moves(egwene, force=True)
    assert any(
        abs(move[0] - mat.position[0]) + abs(move[1] - mat.position[1]) == 1
        for move in moves
    )


def test_east_house_lesson_makes_the_villager_quota_unmissable(compiled_lt_data):
    database, _ = compiled_lt_data
    events = {event.nid: event for event in database.events}
    east = events["wn02_village_defense save_house_east"]
    recruit = events["wn02_village_defense recruit_mat_egwene"]
    lines = east.source.splitlines()

    assert "flicker_cursor;house_east_door" in recruit.source.splitlines()
    assert "flicker_cursor;house_south_door" not in recruit.source
    assert "At the east door, choose Visit." in recruit.source
    assert (
        "change_objective_simple;{v:residents_returned}/3 villagers saved" in lines
    )
    assert "level_var;_objective_flash;True" in lines
    assert lines.index("level_var;_objective_flash;True") > lines.index(
        "change_objective_simple;{v:residents_returned}/3 villagers saved"
    )
    # The heal lesson must not overwrite the quota banner it now follows.
    heal = events["wn02_village_defense nynaeve_guided_heal"]
    assert "change_objective" not in heal.source


def test_inn_hold_waits_for_the_third_counted_villager(lt_runtime):
    _, _, game_state, _, triggers = lt_runtime
    level_id = "wn02_village_defense"
    game = game_state.start_level(level_id)
    _drain_trigger(game, triggers.LevelStart(), level_id)
    lan = game.get_unit("lan")

    def hold_events(count):
        game.level_vars["residents_returned"] = count
        wait = triggers.UnitWait(lan, lan.position, None, True)
        return [
            event.name
            for event in game.events.get_triggered_events(wait, level_id)
        ]

    assert "begin_inn_hold" not in hold_events(2)
    assert "begin_inn_hold" in hold_events(3)

    executed = _drain_trigger(
        game, triggers.UnitWait(lan, lan.position, None, True), level_id
    )
    assert f"{level_id} begin_inn_hold" in executed
    assert game.level_vars["inn_hold_started"] is True
    assert game.level.objective["simple"] == "Hold inn,Through turn 8"
    assert game.get_unit("hold_north_a").position is not None
    assert game.get_unit("hold_south_a").position is not None


def test_objective_panel_blinks_then_settles_after_a_flash_request(lt_runtime):
    from app.engine import engine as lt_engine
    from app.engine.ui_view import UIView

    view = UIView()
    panel = lt_engine.create_surface((72, 27), transparent=True)
    settled = view.emphasize_obj_info(panel)
    assert settled is panel

    view.obj_pulse_start = 0
    original_get_time = lt_engine.get_time
    try:
        lt_engine.get_time = lambda: 50
        assert view.emphasize_obj_info(panel) is None
        lt_engine.get_time = lambda: 150
        blinked_in = view.emphasize_obj_info(panel)
        assert blinked_in.get_width() > panel.get_width()
        lt_engine.get_time = lambda: 700
        easing = view.emphasize_obj_info(panel)
        assert panel.get_width() < easing.get_width() < blinked_in.get_width()
        lt_engine.get_time = lambda: 900
        assert view.emphasize_obj_info(panel) is panel
        assert view.obj_pulse_start is None
    finally:
        lt_engine.get_time = original_get_time

    # The enlarged panel must still fit inside the native 240x160 frame.
    assert 4 + int(panel.get_width() * view.obj_pulse_scale) < 240


def test_bran_defends_the_inn_with_a_village_weapon(lt_runtime):
    _, _, game_state, _, _ = lt_runtime
    game = game_state.start_level("wn02_village_defense")
    bran = game.get_unit("bran_c2")

    weapon = bran.get_weapon()
    assert weapon is not None
    assert weapon.nid == "boar_spear"
    assert bran.team == "other"
    assert bran.get_ai() == "patrol_bran_west"
    assert "Tile" not in bran.tags
