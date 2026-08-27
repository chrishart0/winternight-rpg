from __future__ import annotations

from pathlib import Path

from winternight_gen.event_compiler import compile_scene_v2
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


def test_campaign_patrol_events_lower_to_lt_change_ai(compiled_campaign):
    analysis = analyze_project(compiled_campaign, ENGINE_ROOT)
    commands = analysis["events"]
    assert "change_ai" in commands["wn03_return_to_farm trolloc_patrol_turn_east"]
    assert "change_ai" in commands["wn03_return_to_farm trolloc_patrol_turn_west"]


def test_campaign_scenes_emit_real_sound_and_silent_cast_portrait(compiled_campaign):
    analysis = analyze_project(compiled_campaign, ENGINE_ROOT)
    commands = analysis["events"]
    assert "sound" in commands["wn01_farm_escape sc_c1_farmhouse_calm"]
    appearance = commands["wn03_return_to_farm sc_c3_trolloc_appears"]
    assert "sound" in appearance
    assert "add_portrait" in appearance
    assert set(analysis["resources"]["sfx"]) >= {
        "impact_heavy",
        "combat_distant",
        "growl_nearby",
    }


def test_campaign_dialogue_uses_fire_emblem_portrait_and_text_layout(campaign_bundle):
    scene = next(
        scene for scene in campaign_bundle.scenes if scene.id == "sc_c0_quarry_road"
    )
    commands = compile_scene_v2(scene).splitlines()

    assert "add_portrait;rand_neutral;Left;immediate" in commands
    assert "add_portrait;tam_neutral;Right;immediate" in commands
    dialogue = [
        command
        for command in commands
        if command.startswith(("speak;rand_neutral;", "speak;tam_neutral;"))
    ]
    assert dialogue
    assert all(command.endswith(";;;;;black;no_sound") for command in dialogue)
