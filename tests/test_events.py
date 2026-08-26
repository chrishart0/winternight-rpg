from __future__ import annotations

from pathlib import Path

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
