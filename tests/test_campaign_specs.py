from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from winternight_gen.models import CampaignBundle, DialogueSceneBeat
from winternight_gen.semantic_validation import (
    CampaignSemanticError,
    validate_campaign_semantics,
)


def test_campaign_graph_has_four_ordered_chapters_and_two_layouts(campaign_bundle):
    assert campaign_bundle.campaign.chapter_order == [
        "wn00_tutorial",
        "wn01_farm_escape",
        "wn02_village_defense",
        "wn03_return_to_farm",
    ]
    assert {mission.map.template for mission in campaign_bundle.missions} == {
        "emonds_field",
        "althor_farm",
    }
    assert {mission.map.variant for mission in campaign_bundle.missions} == {
        "festival_day",
        "night_attack",
        "winternight_attack",
        "ruined_return",
    }
    assert campaign_bundle.canon_bible.ending_boundary.final_beat == "c3_rand_rejoins_tam"


def test_requested_tutorial_and_return_mechanics_are_explicit(campaign_bundle):
    missions = {mission.id: mission for mission in campaign_bundle.missions}
    tutorial = missions["wn00_tutorial"]
    return_mission = missions["wn03_return_to_farm"]

    assert tutorial.target_play.expected_minutes == (10, 15)
    delivery_scene = next(scene for scene in campaign_bundle.scenes if scene.id == "sc_c0_delivery")
    assert any("Item" in beat.text and "Equip" in beat.text for beat in delivery_scene.beats)

    assert return_mission.objective.display_text == "Reach the farmhouse"
    assert any(region.id == "farmhouse_approach" for region in return_mission.regions)
    patrol_events = {event.id: event for event in return_mission.events if "patrol" in event.id}
    assert set(patrol_events) == {"trolloc_patrol_turn_east", "trolloc_patrol_turn_west"}
    assert {
        action.value
        for event in patrol_events.values()
        for action in event.actions
        if action.type == "change_ai"
    } == {"patrol_east", "patrol_west"}


def test_every_required_objective_route_is_reachable(campaign_bundle):
    result = validate_campaign_semantics(campaign_bundle)
    routes = result["reachability"]
    assert routes["wn00_tutorial"] == {"rand->inn_barrels": True}
    assert routes["wn01_farm_escape"] == {"rand->westwood_exit": True}
    assert routes["wn02_village_defense"] == {
        "civilian_west->inn_safe": True,
        "civilian_east->inn_safe": True,
        "civilian_south->inn_safe": True,
    }
    assert routes["wn03_return_to_farm"] == {"rand->westwood_exit": True}


def test_story_boundary_rejects_forbidden_chapter_six_dialogue(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    dialogue = next(
        beat
        for scene in broken.scenes
        for beat in scene.beats
        if isinstance(beat, DialogueSceneBeat)
    )
    dialogue.text = "A parentage revelation that must remain outside this slice."
    with pytest.raises(ValidationError, match="crosses story boundary"):
        CampaignBundle.model_validate(broken.model_dump())


def test_dialogue_cannot_inject_raw_lt_commands(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    dialogue = next(
        beat
        for scene in broken.scenes
        for beat in scene.beats
        if isinstance(beat, DialogueSceneBeat)
    )
    dialogue.text = "Unsafe;win_game"
    with pytest.raises(CampaignSemanticError, match="unsafe characters"):
        validate_campaign_semantics(broken)


def test_every_terrain_uses_a_registered_movement_cost(compiled_campaign):
    terrain = json.loads(
        (compiled_campaign / "game_data" / "terrain.json").read_text(encoding="utf-8")
    )
    movement_costs = json.loads(
        (compiled_campaign / "game_data" / "mcost.json").read_text(encoding="utf-8")
    )
    registered_types = set(movement_costs[1])

    assert terrain
    assert all(entry["mtype"] in registered_types for entry in terrain)


def test_story_critical_tam_is_protected_only_during_farm_escape(compiled_campaign):
    skills = json.loads(
        (compiled_campaign / "game_data" / "skills.json").read_text(encoding="utf-8")
    )
    units = json.loads((compiled_campaign / "game_data" / "units.json").read_text(encoding="utf-8"))
    guardian = next(skill for skill in skills if skill["nid"] == "story_guardian")
    tam = next(unit for unit in units if unit["nid"] == "tam")
    village_tam = next(unit for unit in units if unit["nid"] == "tam_village")

    assert ["TrueMiracle", None] in guardian["components"]
    assert [1, "story_guardian"] in tam["learned_skills"]
    assert [1, "story_guardian"] not in village_tam["learned_skills"]


def test_story_boundary_rejects_later_beat(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    broken.story_beats.beats[0].chronology = 999

    with pytest.raises(ValidationError, match="story beats exceed campaign boundary"):
        CampaignBundle.model_validate(broken.model_dump())


def test_story_boundary_allows_only_ending_card_after_final_scene(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    ending_card = next(scene for scene in broken.scenes if scene.id == "sc_c3_ending_card")
    ending_card.beats = [
        DialogueSceneBeat(
            type="dialogue",
            speaker="rand",
            intent="forbidden_epilogue",
            text="The story continues.",
        )
    ]
    ending_card.cast = [
        next(
            member
            for scene in broken.scenes
            if scene.id == "sc_c3_rejoin_tam"
            for member in scene.cast
            if member.character == "rand"
        )
    ]

    with pytest.raises(ValidationError, match="story-bearing scene"):
        CampaignBundle.model_validate(broken.model_dump())


def test_rand_can_equip_bow_and_recovered_sword(compiled_campaign):
    units = json.loads((compiled_campaign / "game_data" / "units.json").read_text(encoding="utf-8"))
    rand = next(unit for unit in units if unit["nid"] == "rand")

    assert rand["wexp_gain"]["Bow"][0] is True
    assert rand["wexp_gain"]["Sword"][0] is True


def test_semantics_rejects_equipping_an_unsupported_weapon(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    rand = next(character for character in broken.characters.characters if character.id == "rand")
    rand.combat.additional_weapon_types = []

    with pytest.raises(CampaignSemanticError, match="equips tams_sword on incompatible"):
        validate_campaign_semantics(broken)
