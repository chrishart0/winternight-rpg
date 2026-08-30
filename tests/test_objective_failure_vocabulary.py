from __future__ import annotations

import warnings

import pytest
from pydantic import ValidationError

from winternight_gen.event_compiler import compile_action, compile_failure_commands
from winternight_gen.models import EventActionSpec, FailureCondition, MissionSpec
from winternight_gen.objective_text import (
    BANNER_LINE_CHARACTER_LIMIT,
    OBJECTIVE_LINE_CHARACTER_LIMIT,
    display_lines,
    rendered_line,
    synthesize_loss_text,
)
from winternight_gen.semantic_validation import validate_campaign_semantics


def test_change_objective_both_updates_banner_then_persistent_win():
    action = EventActionSpec(
        type="change_objective", target="both", value="Find Moiraine,At the bonfires"
    )

    assert compile_action(action) == [
        "change_objective_simple;Find Moiraine,At the bonfires",
        "change_objective_win;Find Moiraine,At the bonfires",
    ]


def test_change_objective_rejects_unknown_objective_slot():
    with pytest.raises(ValidationError, match="simple, win, loss, or both"):
        EventActionSpec(type="change_objective", target="durable", value="Go east")


def test_failure_scene_precedes_game_over_command():
    failure = FailureCondition(
        type="unit_death", unit="luhhan_defender", failure_scene="sc_c2_luhhan_falls"
    )

    assert compile_failure_commands(failure) == [
        "trigger_script;sc_c2_luhhan_falls",
        "lose_game",
    ]


def test_synthesized_loss_conditions_are_deduplicated_and_fit(campaign_bundle):
    characters = {
        character.id: character for character in campaign_bundle.characters.characters
    }
    losses = {
        mission.id: display_lines(synthesize_loss_text(mission, characters))
        for mission in campaign_bundle.missions
    }

    assert all(
        len(line) <= OBJECTIVE_LINE_CHARACTER_LIMIT
        for mission_lines in losses.values()
        for line in mission_lines
    )
    assert not any(losses["wn02_village_defense"])
    woods = " ".join(losses["wn05_out_of_the_woods"])
    assert "Rand" in woods
    assert "Tam" in woods
    assert "villager" not in woods


def test_semantic_validation_warns_when_objective_text_exceeds_native_budget(
    campaign_bundle,
):
    mission = campaign_bundle.missions[0]
    oversized = mission.objective.model_copy(update={"display_text": "X" * 31})
    changed_mission = mission.model_copy(update={"objective": oversized})
    changed_bundle = campaign_bundle.model_copy(
        update={"missions": [changed_mission, *campaign_bundle.missions[1:]]}
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = validate_campaign_semantics(changed_bundle)

    assert any(
        "initial banner" in str(item.message)
        and "native 240x160 budget is 30" in str(item.message)
        for item in caught
    )
    assert any("initial banner" in message for message in result["warnings"])


def test_objective_budget_measures_the_drawn_line_not_the_raw_expression():
    live_quota = "{v:residents_returned}/3 villagers saved"

    assert rendered_line(live_quota) == "0/3 villagers saved"
    assert len(live_quota) > BANNER_LINE_CHARACTER_LIMIT
    assert len(rendered_line(live_quota)) <= BANNER_LINE_CHARACTER_LIMIT
    # `{comma}` is a display escape restored by display_lines, not an
    # expression, so the width proxy must leave it intact.
    assert rendered_line("Hold the inn{comma} eight turns") == (
        "Hold the inn{comma} eight turns"
    )


def test_generated_mission_schema_documents_new_vocabulary():
    schema = MissionSpec.model_json_schema()["$defs"]

    assert "16 characters" in schema["ObjectiveSpec"]["properties"]["display_text"][
        "description"
    ]
    assert "before lose_game" in schema["FailureCondition"]["properties"][
        "failure_scene"
    ]["description"]
    assert "simple, win, loss, or both" in schema["EventActionSpec"]["properties"][
        "target"
    ]["description"]
