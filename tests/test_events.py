from __future__ import annotations

from pathlib import Path

import pytest

from winternight_gen.event_compiler import (
    compile_action,
    compile_mission_event,
    compile_scene_v2,
)
from winternight_gen.models import EventActionSpec
from winternight_gen.static_analysis import analyze_project

ENGINE_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "lt-maker"


def test_generated_events_parse_through_lt(compiled_project):
    analysis = analyze_project(compiled_project, ENGINE_ROOT)
    events = analysis["events"]
    assert events["minimal_chapter minimal_intro"] == [
        "change_background",
        "add_portrait",
        "speak",
        "add_portrait",
        "speak",
        "remove_portrait",
        "remove_portrait",
        "change_background",
    ]
    assert events["minimal_chapter minimal_victory"] == ["win_game"]
    assert events["minimal_chapter minimal_failure"] == ["lose_game"]


def test_chapter_has_intro_outro_win_and_loss(compiled_project):
    analysis = analyze_project(compiled_project, ENGINE_ROOT)
    commands = analysis["events"]
    assert any("speak" in event for event in commands.values())
    assert any("win_game" in event for event in commands.values())
    assert any("lose_game" in event for event in commands.values())


def test_narg_combat_events_unlock_escape_from_either_attack_order(compiled_campaign):
    analysis = analyze_project(compiled_campaign, ENGINE_ROOT)
    commands = analysis["events"]
    for event_id in ("rand_trolloc_combat_quote", "narg_rand_combat_quote"):
        event = commands[f"wn03_return_to_farm {event_id}"]
        assert "trigger_script" in event
        assert "level_var" in event
        assert "change_objective_simple" in event


def test_tutorial_uses_talk_weapon_pick_and_auto_continues(compiled_campaign):
    commands = analyze_project(compiled_campaign, ENGINE_ROOT)["events"]

    cellar = commands["wn00_tutorial tutorial_cider_cellar"]
    assert {
        "change_team",
        "remove_tag",
        "add_group",
        "add_region",
        "speak",
        "show_layer",
    } <= set(cellar)
    assert "remove_item" not in cellar

    rand_ready = commands["wn00_tutorial tutorial_rand_attack_tile"]
    assert {"give_item", "speak"} <= set(rand_ready)
    assert "equip_item" not in rand_ready

    rand_done = commands["wn00_tutorial tutorial_rand_throw_done"]
    assert {"remove_item", "equip_item", "show_layer"} <= set(rand_done)
    assert "give_item" not in rand_done

    assert "hide_layer" not in rand_ready
    assert "hide_layer" not in rand_done
    assert "hide_layer" not in commands["wn00_tutorial tutorial_mat_attack_tile"]
    assert "hide_layer" not in commands["wn00_tutorial tutorial_mat_throw_done"]
    assert commands["wn00_tutorial tutorial_rand_throw_script"] == [
        "set_combat_script"
    ]
    assert commands["wn00_tutorial tutorial_mat_throw_script"] == [
        "set_combat_script"
    ]

    raven_flees = commands["wn00_tutorial tutorial_raven_flees"]
    assert raven_flees[:3] == ["move_unit", "remove_unit", "level_var"]
    assert raven_flees.index("remove_unit") < raven_flees.index("trigger_script")
    assert raven_flees[-1] == "win_game"
    assert "wn00_tutorial tutorial_enter_inn" not in commands


def test_tutorial_miss_scripts_bind_to_each_attacker(campaign_bundle):
    mission = next(
        mission for mission in campaign_bundle.missions if mission.id == "wn00_tutorial"
    )
    events = {event.id: event for event in mission.events}

    for event_id, actor in (
        ("tutorial_rand_throw_script", "rand"),
        ("tutorial_mat_throw_script", "mat"),
    ):
        trigger, condition, source = compile_mission_event(mission, events[event_id])
        assert trigger == "combat_start"
        assert f"unit.nid == '{actor}'" in condition
        assert "unit2.nid == 'raven'" in condition
        assert source == "set_combat_script;miss1,end"
        if actor == "rand":
            assert events[event_id].only_once is False
            assert "rand_throw_done" not in condition
    rand_done = events["tutorial_rand_throw_done"]
    _, rand_done_condition, _ = compile_mission_event(mission, rand_done)
    assert "item.nid == 'thrown_stone'" in rand_done_condition
    bow_retry = events["tutorial_rand_bow_retry"]
    _, bow_retry_condition, bow_retry_source = compile_mission_event(mission, bow_retry)
    assert "item.nid == 'hunting_bow'" in bow_retry_condition
    assert "Choose Attack, then Thrown Stone." in bow_retry_source
    assert bow_retry_source.endswith("reset;rand")


def test_campaign_scenes_emit_real_sound_and_silent_cast_portrait(compiled_campaign):
    analysis = analyze_project(compiled_campaign, ENGINE_ROOT)
    commands = analysis["events"]
    assert "sound" in commands["wn01_farm_escape sc_c1_door_bursts"]
    appearance = commands["wn03_return_to_farm sc_c3_trolloc_appears"]
    assert "sound" in appearance
    assert "add_portrait" in appearance
    assert set(analysis["resources"]["sfx"]) >= {
        "impact_heavy",
        "combat_distant",
        "growl_nearby",
    }


def test_campaign_dialogue_uses_fire_emblem_portrait_and_text_layout(campaign_bundle):
    scene = next(scene for scene in campaign_bundle.scenes if scene.id == "sc_c0_quarry_road")
    commands = compile_scene_v2(scene).splitlines()

    assert "add_portrait;rand_neutral;Right;immediate" in commands
    assert "add_portrait;tam_neutral;Left;immediate" in commands
    dialogue = [
        command
        for command in commands
        if command.startswith(("speak;rand_neutral;", "speak;tam_neutral;"))
    ]
    assert dialogue
    assert all(command.endswith(";;;;2.0;black;no_talk") for command in dialogue)
    assert all("no_sound" not in command for command in dialogue)


def test_tutorial_opening_never_hides_dialogue_behind_a_transition(campaign_bundle):
    scene = next(scene for scene in campaign_bundle.scenes if scene.id == "sc_c0_quarry_road")
    commands = compile_scene_v2(scene).splitlines()

    assert "transition;Close" not in commands
    assert "transition;Open" not in commands
    assert len([command for command in commands if command.startswith("speak;")]) == 8


def test_move_unit_visibly_exits_without_dragging_the_camera():
    action = EventActionSpec(type="move_unit", target="raven", value="0,8")

    assert compile_action(action) == [
        "move_unit;raven;0,8;normal;giveup;40;no_follow"
    ]


def test_remove_tag_maps_directly_to_lt_command():
    action = EventActionSpec(type="remove_tag", target="mat", value="Tile")

    assert compile_action(action) == ["remove_tag;mat;Tile"]


def test_remove_tag_rejects_unknown_lt_tag():
    with pytest.raises(ValueError, match="known LT tag"):
        EventActionSpec(type="remove_tag", target="mat", value="tile")
