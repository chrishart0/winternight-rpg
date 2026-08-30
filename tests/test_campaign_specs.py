from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from winternight_gen.campaign_lt_adapter import make_campaign_database
from winternight_gen.lt_adapter import _import_lt
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.models import (
    CampaignBundle,
    DialogueSceneBeat,
    EventActionSpec,
    GuidePathSpec,
    MissionSpec,
    SceneSpecV2,
)
from winternight_gen.semantic_validation import (
    CampaignSemanticError,
    validate_campaign_semantics,
)

ENGINE_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "lt-maker"
SCENE_TEXT_CHARACTER_BUDGET = 56
SOURCE_CHAPTER_DIR = Path(__file__).resolve().parents[1] / "source" / "private" / "eotw"


def normalized_words(text: str) -> str:
    """Reduce prose to comparable lowercase words, ignoring punctuation."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def source_chapter_words(*filenames: str) -> str:
    """Return the normalized words of the private source chapters."""
    return normalized_words(
        " ".join(
            (SOURCE_CHAPTER_DIR / filename).read_text(encoding="utf-8")
            for filename in filenames
        )
    )


def assert_direct_dialogue_quotes_source(chapter_scenes, chapter_words, label):
    """Every direct-canon dialogue line must be a trimmed source quotation."""
    for scene in chapter_scenes.values():
        if scene.canon_status != "direct":
            continue
        for beat in scene.beats:
            if isinstance(beat, DialogueSceneBeat):
                assert normalized_words(beat.text) in chapter_words, (
                    f"{scene.id} dialogue is not a trimmed {label} quotation: "
                    f"{beat.text!r}"
                )


@pytest.fixture(scope="module")
def campaign_database(campaign_bundle):
    _import_lt(ENGINE_ROOT)
    with generated_component_system(ENGINE_ROOT):
        return make_campaign_database(campaign_bundle)


def test_campaign_graph_has_six_ordered_chapters_and_five_layout_budget(campaign_bundle):
    assert campaign_bundle.campaign.title == "Eye of the World"
    assert campaign_bundle.campaign.chapter_order == [
        "wn00_tutorial",
        "wn01_farm_escape",
        "wn02_village_defense",
        "wn03_return_to_farm",
        "wn04_long_road",
        "wn05_out_of_the_woods",
    ]
    assert {mission.map.template for mission in campaign_bundle.missions} == {
        "emonds_field",
        "emonds_field_battle",
        "althor_farm",
        "westwood_road",
    }
    assert campaign_bundle.campaign.constraints.unique_map_layouts_max == 5
    assert {mission.map.variant for mission in campaign_bundle.missions} == {
        "festival_day",
        "night_attack",
        "winternight_attack",
        "ruined_return",
        "night_march",
        "burned_dawn",
    }
    assert campaign_bundle.canon_bible.ending_boundary.final_beat == "c5_moiraine_heals"
    assert campaign_bundle.canon_bible.ending_boundary.excluded_topics == []
    assert campaign_bundle.campaign.story_boundary.forbidden_terms == []


def test_requested_tutorial_and_return_mechanics_are_explicit(campaign_bundle):
    missions = {mission.id: mission for mission in campaign_bundle.missions}
    tutorial = missions["wn00_tutorial"]
    return_mission = missions["wn03_return_to_farm"]

    assert tutorial.narrative_constraints["required_deliveries"] == 1
    assert tutorial.narrative_constraints["scripted_attack_misses"] == 2
    assert tutorial.scripted_forecast_lessons == []
    assert tutorial.objective.region is None
    assert all(item.id != "cider_cask" for item in campaign_bundle.gameplay.items)

    regions = {region.id: region for region in tutorial.regions}
    assert set(regions) == {
        "inn_before_mat",
        "cider_cart",
        "inn_cellar",
        "rand_attack_tile",
        "mat_attack_tile",
    }
    assert regions["rand_attack_tile"].position == (10, 7)
    assert regions["mat_attack_tile"].position == (11, 10)
    assert regions["rand_attack_tile"].highlight == "lightyellow"
    assert regions["mat_attack_tile"].highlight == "lightyellow"
    guides = {guide.id: guide for guide in tutorial.guide_paths}
    assert guides["rand_attack_line"].points == [
        (9, 6),
        (10, 6),
        (10, 7),
    ]
    assert guides["mat_attack_line"].points == [(13, 10), (12, 10), (11, 10)]

    events = {event.id: event for event in tutorial.events}
    for event_id, actor in (
        ("tutorial_rand_throw_script", "rand"),
        ("tutorial_mat_throw_script", "mat"),
    ):
        event = events[event_id]
        assert (event.trigger.type, event.trigger.unit, event.trigger.unit2) == (
            "combat_start", actor, "raven"
        )
        assert [action.value for action in event.actions] == ["miss1,end"]
    cellar_actions = [
        (action.type, action.target, action.value)
        for action in events["tutorial_cider_cellar"].actions
    ]
    assert ("remove_item", "rand", "hunting_bow") not in cellar_actions
    assert [
        (action_type, value)
        for action_type, target, value in cellar_actions
        if target == "mat"
    ] == [
        ("change_team", "player"),
        ("remove_tag", "Tile"),
        ("refresh_unit", None),
    ]
    assert [
        (action.type, action.value)
        for action in events["tutorial_rand_attack_tile"].actions
        if action.type in {"give_item", "equip_item"}
    ] == [("give_item", "thrown_stone")]
    assert next(
        action.value
        for action in events["tutorial_rand_attack_tile"].actions
        if action.type == "tutorial_text"
    ) == "Choose Attack, then Thrown Stone."
    assert [
        (action.type, action.value)
        for action in events["tutorial_rand_throw_done"].actions
        if action.type in {"give_item", "equip_item", "remove_item"}
    ] == [
        ("remove_item", "thrown_stone"),
        ("equip_item", "hunting_bow"),
    ]
    assert [
        (action.type, action.target, action.value)
        for action in events["tutorial_raven_flees"].actions[:3]
    ] == [
        ("move_unit", "raven", "19,8"),
        ("remove_unit", "raven", None),
        ("set_flag", "raven_done", True),
    ]
    assert [
        action.target
        for action in events["tutorial_raven_flees"].actions
        if action.type == "play_scene"
    ] == [
        "sc_c0_moiraine_coin",
        "sc_c0_fain_news",
        "sc_c0_fain_aftershock",
        "sc_c0_thom_performance",
        "sc_c0_inn_council",
    ]
    assert events["tutorial_raven_flees"].actions[-1].type == "win"
    assert {
        "tutorial_enter_inn",
        "tutorial_fain",
        "tutorial_thom",
    }.isdisjoint(events)
    assert tutorial.narrative_constraints["optional_village_talks"] == 3
    stone = next(item for item in campaign_bundle.gameplay.items if item.id == "thrown_stone")
    assert (stone.min_range, stone.max_range, stone.map_target_cast_anim) == (
        2,
        2,
        "StoneThrow",
    )

    units = {unit.id: unit for unit in tutorial.units}
    assert units["mat"].team == "other"
    assert all(unit.phase_inert for unit in tutorial.units if unit.team == "other")
    assert units["raven"].position == (11, 8)
    assert units["raven"].team == "enemy"
    assert units["raven"].starts_on_map is False
    raven = next(
        character for character in campaign_bundle.characters.characters
        if character.id == "raven"
    )
    assert raven.combat.hp == 22

    tutorial_scenes = {
        scene.id for scene in campaign_bundle.scenes if scene.chapter == "wn00_tutorial"
    }
    assert {
        "sc_c0_cider_first",
        "sc_c0_raven_attack",
        "sc_c0_moiraine_coin",
    } <= tutorial_scenes
    assert {
        "sc_c0_cider_second",
        "sc_c0_fain_optional",
        "sc_c0_thom_optional",
    }.isdisjoint(tutorial_scenes)
    assert return_mission.objective.display_text == "Find supplies,By turn 12"
    assert any(region.id == "farmhouse_approach" for region in return_mission.regions)
    # The gold farmhouse tile is an optional scene, never a gate: a player who
    # walks straight to the supplies must still be able to search them.
    return_regions = {region.id: region for region in return_mission.regions}
    for supply in ("water", "bandages", "blankets"):
        assert return_regions[supply].required_flags == []
    assert return_regions["tams_sword"].required_flags == [
        "water_found",
        "bandages_found",
        "blankets_found",
    ]
    return_events = {event.id: event for event in return_mission.events}
    for event_id in ("find_water", "find_bandages", "find_blankets"):
        assert "farmhouse_reached" not in (return_events[event_id].condition.all_flags)


@pytest.mark.parametrize(
    ("points", "message"),
    [
        ([(0, 0)], "at least 2"),
        ([(0, 0), (2, 0)], "tile-adjacent"),
        ([(0, 0), (0, 1), (0, 0)], "repeats a tile"),
        (
            [(0, 0), (0, 1), (1, 1), (1, 0)],
            "non-consecutive adjacent tiles",
        ),
    ],
)
def test_guide_paths_reject_invalid_geometry(points, message):
    with pytest.raises(ValidationError, match=message):
        GuidePathSpec(
            id="bad_route",
            destination_region="destination",
            points=points,
        )


def test_mission_rejects_duplicate_guide_layer_ids(campaign_bundle):
    mission = next(
        mission for mission in campaign_bundle.missions if mission.id == "wn00_tutorial"
    )
    data = mission.model_dump(mode="python")
    data["guide_paths"].append(data["guide_paths"][0])
    with pytest.raises(ValidationError, match="guide path IDs must be unique"):
        MissionSpec.model_validate(data)


def test_guide_paths_validate_tiles_and_layer_actions(campaign_bundle):
    blocked = campaign_bundle.model_copy(deep=True)
    mission = next(
        mission for mission in blocked.missions if mission.id == "wn00_tutorial"
    )
    mission.guide_paths[0].points[1] = (7, 7)
    with pytest.raises(CampaignSemanticError, match="crosses blocked"):
        validate_campaign_semantics(blocked)

    mismatched = campaign_bundle.model_copy(deep=True)
    mission = next(
        mission for mission in mismatched.missions if mission.id == "wn00_tutorial"
    )
    mission.guide_paths[0].points[-1] = (10, 6)
    with pytest.raises(CampaignSemanticError, match="does not end in destination"):
        validate_campaign_semantics(mismatched)

    unknown = campaign_bundle.model_copy(deep=True)
    mission = next(
        mission for mission in unknown.missions if mission.id == "wn00_tutorial"
    )
    mission.events[0].actions.append(
        EventActionSpec(type="show_layer", target="missing_guide")
    )
    with pytest.raises(CampaignSemanticError, match="unknown map layer"):
        validate_campaign_semantics(unknown)


def test_farm_escape_book_text_scene_contract(campaign_bundle):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn01_farm_escape"
    )
    events = {event.id: event for event in mission.events}
    regions = {region.id: region for region in mission.regions}
    chapter_scenes = {
        scene.id: scene
        for scene in campaign_bundle.scenes
        if scene.chapter == "wn01_farm_escape"
    }

    assert mission.title == "Winternight"
    assert mission.objective.display_text == "Reach Westwood,by dawn"
    assert regions["westwood_exit"].sub_id == "Westwood"
    assert regions["farm_kit"].sub_id == "Clean Cloth"
    assert [
        action.target
        for action in events["farm_start"].actions
        if action.type == "play_scene"
    ] == [
        "sc_c1_farmhouse_calm",
        "sc_c1_locked_doors",
        "sc_c1_door_bursts",
    ]
    assert set(chapter_scenes) == {
        "sc_c1_farmhouse_calm",
        "sc_c1_locked_doors",
        "sc_c1_door_bursts",
        "sc_c1_farm_kit",
        "sc_c1_tam_combat_quote",
        "sc_c1_pursuit",
        "sc_c1_tam_wounded",
        "sc_c1_supplies_needed",
        "sc_c1_caught",
    }
    assert events["farm_reinforcements"].trigger.turn == 2
    assert [
        (action.type, action.target, action.value)
        for action in events["farm_timeout_loss"].actions
    ] == [
        ("set_flag", "caught_by_dawn", True),
        ("play_scene", "sc_c1_caught", None),
        ("lose", None, None),
    ]
    assert [
        (action.type, action.target, action.value)
        for action in events["farm_escape_success"].actions
        if action.type in {"set_flag", "play_scene", "win"}
    ] == [
        ("set_flag", "tam_wound_started", True),
        ("set_flag", "tam_wounded", True),
        ("play_scene", "sc_c1_tam_wounded", None),
        ("win", None, None),
    ]
    assert not any(
        action.target in {"tam_wound_started", "tam_wounded"}
        for action in events["farm_timeout_loss"].actions
    )
    assert "farm_timeout_success" not in events

    scene_text = {
        scene_id: " ".join(beat.text for beat in scene.beats if beat.text)
        for scene_id, scene in chapter_scenes.items()
    }
    assert "Rand and Tam reach their Westwood farm" in scene_text["sc_c1_farmhouse_calm"]
    assert "No one in the Two Rivers does that" in scene_text["sc_c1_locked_doors"]
    assert "boiling kettle" in scene_text["sc_c1_door_bursts"]
    assert "Out the back! Go! Go! I'll follow!" in scene_text["sc_c1_door_bursts"]
    assert "Some Trollocs can hear like a dog" in scene_text["sc_c1_tam_wounded"]
    assert "It's just a scratch" in scene_text["sc_c1_tam_wounded"]
    assert "takes Tam's heron-marked sword" in scene_text["sc_c1_supplies_needed"]
    assert "We need the cart" in scene_text["sc_c1_supplies_needed"]

    story_beats = {beat.id: beat for beat in campaign_bundle.story_beats.beats}
    assert {
        beat_id: story_beats[beat_id].source_locator
        for beat_id in story_beats
        if beat_id.startswith("c1_")
    } == {
        "c1_farmhouse_evening": "05:9-57",
        "c1_tam_reveals_sword": "05:59-71",
        "c1_trollocs_breach_farm": "05:73-85",
        "c1_rand_flees": "05:87-117",
        "c1_pursuit_closes": "05:103-111",
        "c1_tam_wounded": "05:117-145",
        "c1_supplies_needed": "05:147-161",
    }
    assert "stewpot" in story_beats["c1_farmhouse_evening"].summary
    assert "tea kettle" in story_beats["c1_trollocs_breach_farm"].summary
    assert "fever-hot wound" in story_beats["c1_tam_wounded"].summary
    assert "takes the unfamiliar sword" in story_beats["c1_supplies_needed"].summary

    decisions = {
        decision.id: decision for decision in campaign_bundle.adaptation_rules.decisions
    }
    assert decisions["farmhouse_opening_split"].source_beats == [
        "c1_farmhouse_evening",
        "c1_tam_reveals_sword",
        "c1_trollocs_breach_farm",
    ]
    assert decisions["scripted_tam_wound"].source_beats == [
        "c1_rand_flees",
        "c1_tam_wounded",
    ]
    assert decisions["farm_escape_deadline"].source_beats == [
        "c1_rand_flees",
        "c1_pursuit_closes",
    ]

    assert_direct_dialogue_quotes_source(
        chapter_scenes,
        source_chapter_words("05_winternight.txt"),
        "Chapter 5",
    )


def test_return_to_farm_book_text_scene_contract(campaign_bundle):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn03_return_to_farm"
    )
    events = {event.id: event for event in mission.events}
    regions = {region.id: region for region in mission.regions}
    chapter_scenes = {
        scene.id: scene
        for scene in campaign_bundle.scenes
        if scene.chapter == "wn03_return_to_farm"
    }

    assert mission.title == "The Ruined Farm"
    assert mission.objective.display_text == "Find supplies,By turn 12"
    assert (
        regions["sheep_pen"].position,
        regions["sheep_pen"].size,
        regions["sheep_pen"].sub_id,
        regions["sheep_pen"].interrupt_move,
    ) == ((4, 6), (1, 3), "Visit", True)
    assert any(
        action.type == "set_flag"
        and action.target == "dead_flock_seen"
        and action.value is False
        for action in events["return_start"].actions
    )
    assert [
        action.target
        for action in events["dead_flock"].actions
        if action.type == "play_scene"
    ] == ["sc_c3_dead_flock"]
    assert [
        action.value for action in events["dead_flock"].actions if action.type == "set_fog"
    ] == [4]
    assert [
        action.target
        for action in events["dead_flock"].actions
        if action.type == "highlight_target"
    ] == ["farmhouse_approach"]
    assert [
        action.target
        for action in events["trolloc_defeated"].actions
        if action.type == "activate_region"
    ] == ["westwood_quick_exit"]
    assert events["tam_fever_warning"].trigger.turn == 10
    assert events["fever_deadline_loss"].trigger.turn == 13
    assert any(action.type == "lose" for action in events["fever_deadline_loss"].actions)
    assert [
        action.target
        for action in events["quick_return_escape"].actions
        if action.type == "win"
    ] == [None]
    assert [
        action.target
        for action in events["return_outro"].actions
        if action.type == "play_scene"
    ] == ["sc_c3_cart_shafts", "sc_c3_rejoin_tam"]
    assert set(chapter_scenes) == {
        "sc_c3_return_intro",
        "sc_c3_dead_flock",
        "sc_c3_farmhouse_approach",
        "sc_c3_water",
        "sc_c3_bandages",
        "sc_c3_blankets",
        "sc_c3_sword_recovery",
        "sc_c3_trolloc_appears",
        "sc_c3_rand_combat_quote",
        "sc_c3_fever_warning",
        "sc_c3_fever_caught",
        "sc_c3_cart_shafts",
        "sc_c3_rejoin_tam",
    }

    scene_text = {
        scene_id: " ".join(beat.text for beat in scene.beats if beat.text)
        for scene_id, scene in chapter_scenes.items()
    }
    assert "Curly wool, then wetness" in scene_text["sc_c3_dead_flock"]
    assert "fills the waterbag with shaking hands" in scene_text["sc_c3_water"]
    assert "pulls clean cloths" in scene_text["sc_c3_bandages"]
    assert "gathers the least-torn blankets" in scene_text["sc_c3_blankets"]
    assert "The blade comes up in time" in scene_text["sc_c3_rand_combat_quote"]
    assert "cart lies on its side" in scene_text["sc_c3_cart_shafts"]
    assert "Three blankets weave" in scene_text["sc_c3_rejoin_tam"]

    narg_dialogue = [
        beat.text
        for beat in chapter_scenes["sc_c3_trolloc_appears"].beats
        if isinstance(beat, DialogueSceneBeat)
    ]
    assert narg_dialogue == [
        "Others go away. Narg stay. Narg smart.",
        "Narg know some come back sometime.",
        "Narg wait. You no need sword. Put sword down.",
        "Narg no hurt.",
        "You put sword down.",
        "Stay back.",
        "Why did you do this? Why?",
        "Put sword down. Narg no hurt. Myrddraal want talk you.",
        "Others come back, you talk Myrddraal.",
        "You put sword down.",
        "All right.",
        "I'll talk.",
    ]

    story_beats = {beat.id: beat for beat in campaign_bundle.story_beats.beats}
    assert {
        beat_id: story_beats[beat_id].source_locator
        for beat_id in story_beats
        if beat_id.startswith("c3_")
    } == {
        "c3_rand_returns_alone": "05:147-167",
        "c3_recover_sword": "05:149-157",
        "c3_dead_flock": "05:169-173",
        "c3_home_changed": "05:175-181",
        "c3_supply_search": "05:181,209-213",
        "c3_lone_trolloc": "05:183-207",
        "c3_wounded_trolloc_setup": "05:183-201",
        "c3_rand_rejoins_tam": "05:225-233; 06:9-29",
        "c3_litter_built": "05:215-225; 06:31-43",
    }
    assert "broken speech" in story_beats["c3_lone_trolloc"].summary
    assert "waterbag" in story_beats["c3_supply_search"].summary
    assert "makeshift litter" in story_beats["c3_litter_built"].summary

    decisions = {
        decision.id: decision for decision in campaign_bundle.adaptation_rules.decisions
    }
    assert decisions["dead_flock_interrupt"].source_beats == ["c3_dead_flock"]
    assert decisions["sword_search_reorder"].source_beats == [
        "c3_supply_search",
        "c3_recover_sword",
        "c3_lone_trolloc",
    ]
    assert decisions["narg_lunge_exchange"].source_beats == [
        "c3_lone_trolloc",
        "c3_wounded_trolloc_setup",
    ]
    assert decisions["cart_litter_outro_split"].source_beats == [
        "c3_rand_rejoins_tam",
        "c3_litter_built",
    ]

    chapter_words = source_chapter_words(
        "05_winternight.txt", "06_the_westwood.txt"
    )
    for line in narg_dialogue:
        assert normalized_words(line) in chapter_words, (
            f"Narg line is not verbatim-trimmed: {line!r}"
        )
    assert_direct_dialogue_quotes_source(
        chapter_scenes, chapter_words, "Chapter 5 or 6"
    )


def test_village_defense_allies_tutorial_and_inn_npcs(campaign_bundle):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn02_village_defense"
    )
    units = {unit.id: unit for unit in mission.units}
    green_units = [unit for unit in mission.units if unit.team == "other"]
    named = {unit_id: units[unit_id] for unit_id in ("mat_c2", "egwene_c2", "nynaeve_c2")}
    inn_npcs = {unit_id: units[unit_id] for unit_id in ("bran_c2", "thom_c2")}
    defenders = [
        unit
        for unit in green_units
        if unit.id not in {*named, *inn_npcs}
    ]
    luhhan = units["luhhan_defender"]
    events = {event.id: event for event in mission.events}

    assert len(green_units) == 10
    assert len(defenders) == mission.narrative_constraints["allied_defenders"] == 6
    assert named["nynaeve_c2"].team == "player"
    assert named["egwene_c2"].team == named["mat_c2"].team == "other"
    assert mission.narrative_constraints["named_playables_are_mortal"] is True
    assert mission.failure_conditions == []
    assert luhhan.ai == "patrol_luhhan_south"
    assert luhhan.stat_bonus == {"HP": 8, "DEF": 2}
    assert mission.title == "The Village Burns"
    assert mission.objective.display_text == "Return 3,Hold inn 8 turns"
    assert luhhan.position == (11, 10)
    assert sum(
        abs(a - b)
        for a, b in zip(
            named["nynaeve_c2"].position,
            named["egwene_c2"].position,
            strict=True,
        )
    ) == 1
    assert all(
        9 <= unit.position[0] <= 12 and 6 <= unit.position[1] <= 8
        for unit in inn_npcs.values()
    )
    assert {unit.ai for unit in inn_npcs.values()} == {
        "patrol_bran_west",
        "patrol_thom_east",
    }
    assert all(not unit.phase_inert for unit in inn_npcs.values())
    assert "hunting_bow" in named["mat_c2"].items
    assert (
        events["recruit_egwene_nynaeve"].trigger.unit,
        events["recruit_egwene_nynaeve"].trigger.unit2,
    ) == ("nynaeve_c2", "egwene_c2")
    assert (
        events["recruit_mat_egwene"].trigger.unit,
        events["recruit_mat_egwene"].trigger.unit2,
    ) == ("egwene_c2", "mat_c2")
    assert any(
        action.type == "highlight_target" and action.target == "house_east_door"
        for action in events["recruit_mat_egwene"].actions
    )
    assert any(
        action.type == "flash_objective"
        for action in events["save_house_east"].actions
    )
    assert events["begin_inn_hold"].trigger.type == "unit_wait"
    assert events["begin_inn_hold"].condition.level_var_compare.value == 3
    assert [
        action.value
        for action in events["recruit_egwene_nynaeve"].actions
        if action.type == "tutorial_text"
    ] == ["Move Nynaeve beside Haral. Use Healing Herbs."]
    death_events = {
        event.trigger.unit: event
        for event in events.values()
        if event.id.endswith("_permadeath")
    }
    expected_names = {
        "lan": "Lan",
        "moiraine": "Moiraine",
        "mat_c2": "Mat",
        "egwene_c2": "Egwene",
        "nynaeve_c2": "Nynaeve",
    }
    assert death_events.keys() == expected_names.keys()
    for unit_id, event in death_events.items():
        assert event.condition.trigger_unit_team == "player"
        assert event.actions == [
            EventActionSpec(
                type="permadeath_choice",
                target=unit_id,
                value=expected_names[unit_id],
            )
        ]
    assert {
        events["talk_bran_at_inn"].trigger.unit2,
        events["talk_thom_at_inn"].trigger.unit2,
    } == {"bran_c2", "thom_c2"}

    chapter_scenes = {
        scene.id: scene
        for scene in campaign_bundle.scenes
        if scene.chapter == "wn02_village_defense"
    }
    intro = chapter_scenes["sc_c2_attack_begins"]
    outro = chapter_scenes["sc_c2_defense_end"]
    briefing = chapter_scenes["sc_c2_mission_briefing"]
    intro_text = " ".join(beat.text for beat in intro.beats if beat.text)
    outro_text = " ".join(beat.text for beat in outro.beats if beat.text)
    briefing_text = " ".join(beat.text for beat in briefing.beats if beat.text)

    assert intro.canon_status == "direct"
    assert intro.source_beats == ["c2_bran_account"]
    assert outro.canon_status == "direct"
    assert outro.source_beats == ["c2_bran_account"]
    assert "Winternight visits just beginning" in intro_text
    assert "ball lightning out of a clear night sky" in intro_text
    assert "The man himself is a weapon" in outro_text
    assert "Not every Trolloc lying out there fell to the two of them" in outro_text
    assert "Four neighbors are trapped in their homes" in briefing_text
    assert "The Winespring Inn is their only refuge" in briefing_text
    assert "Keep Haral Luhhan alive" not in briefing_text


def test_tam_litter_is_a_noncombatant(campaign_bundle):
    character = next(
        character
        for character in campaign_bundle.characters.characters
        if character.id == "tam_litter"
    )
    placements = [
        unit
        for mission in campaign_bundle.missions
        for unit in mission.units
        if unit.id == "tam_litter"
    ]

    assert character.combat.weapon_type == "Utility"
    assert character.combat.starting_items == []
    assert character.combat.movement == 3
    assert {unit.character for unit in placements} == {"tam_litter"}


def test_every_required_objective_route_is_reachable(campaign_bundle):
    result = validate_campaign_semantics(campaign_bundle)
    routes = result["reachability"]
    assert routes["wn00_tutorial"] == {}
    assert routes["wn01_farm_escape"] == {"rand->westwood_exit": True}
    assert routes["wn02_village_defense"] == {}
    assert routes["wn03_return_to_farm"] == {"rand->westwood_exit": True}
    assert routes["wn04_long_road"] == {"tam_litter->east_exit": True}
    assert routes["wn05_out_of_the_woods"] == {"tam_litter->inn_door": True}


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


def test_every_scene_text_box_fits_native_dialogue_window(campaign_bundle):
    violations = [
        f"{scene.id} beat {index}: {len(beat.text)} chars: {beat.text!r}"
        for scene in campaign_bundle.scenes
        for index, beat in enumerate(scene.beats)
        if beat.text and len(beat.text) > SCENE_TEXT_CHARACTER_BUDGET
    ]

    assert not violations, "\n".join(violations)


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


def test_every_terrain_uses_engine_supported_gui_keys(compiled_campaign):
    terrain = json.loads(
        (compiled_campaign / "game_data" / "terrain.json").read_text(encoding="utf-8")
    )
    minimap_types = {
        "Grass",
        "House",
        "Forest",
        "Thicket",
        "Floor",
        "Pillar",
        "Ruins",
        "Wall",
        "River",
        "Lava",
    }
    platform_types = {
        "Plains",
        "Road",
        "Forest",
        "Thicket",
        "Floor",
        "Pillar",
        "Ruins",
        "Wall",
        "House",
    }

    assert terrain
    assert all(entry["minimap"] in minimap_types for entry in terrain)
    assert all(entry["platform"] in platform_types for entry in terrain)
    assert all(len(entry["name"]) <= 12 for entry in terrain)


def test_player_facing_objectives_use_character_names(compiled_campaign):
    levels = json.loads(
        (compiled_campaign / "game_data" / "levels.json").read_text(encoding="utf-8")
    )
    tutorial = next(level for level in levels if level["nid"] == "wn00_tutorial")

    loss_lines = tutorial["objective"]["loss"].split(",")
    assert " ".join(loss_lines) == "Rand must survive"
    assert all(len(line) <= 16 for line in loss_lines)


def test_title_screen_attribution_is_blank(campaign_database):
    assert campaign_database.translations.get("_attribution").text == ""


def test_clean_project_defines_descriptions_for_visible_gui(compiled_campaign):
    translations = json.loads(
        (compiled_campaign / "game_data" / "translations.json").read_text(encoding="utf-8")
    )
    translated = {entry["nid"]: entry["text"] for entry in translations}

    assert translated["_attribution"] == ""

    required = {
        "Unit_desc",
        "Objective_desc",
        "Options_desc",
        "Suspend_desc",
        "End_desc",
        "Talk_desc",
        "Rescue_desc",
        "Item_desc",
        "Wait_desc",
        "Visit_desc",
        "Search_desc",
        "Escape_desc",
        "Attack_desc",
        "config_desc",
        "controls_desc",
        "animation_desc",
        "screen_size_desc",
        "display_fps_desc",
        "battle_bg_desc",
        "unit_speed_desc",
        "text_speed_desc",
        "mouse_desc",
        "show_terrain_desc",
        "forecast_desc",
        "show_objective_desc",
        "autocursor_desc",
        "hp_map_team_desc",
        "hp_map_cull_desc",
        "music_volume_desc",
        "sound_volume_desc",
        "talk_boop_desc",
        "show_bounds_desc",
        "grid_opacity_desc",
        "autoend_turn_desc",
        "confirm_end_desc",
        "display_hints_desc",
        "keymap_desc",
        "get_input_desc",
        "key_SELECT",
        "key_BACK",
        "key_INFO",
        "key_AUX",
        "key_LEFT",
        "key_RIGHT",
        "key_UP",
        "key_DOWN",
        "key_START",
    }

    assert required <= translated.keys()
    assert all(translated[nid] != nid for nid in required)
    assert not any(translated[nid].startswith("key_") for nid in required)
    assert translated["key_INFO"] == "Dialogue Log"


def test_empty_credits_destination_is_hidden(compiled_campaign):
    constants = json.loads(
        (compiled_campaign / "game_data" / "constants.json").read_text(encoding="utf-8")
    )
    values = {entry[0]: entry[1] for entry in constants}
    credits = json.loads(
        (compiled_campaign / "game_data" / "credit.json").read_text(encoding="utf-8")
    )

    assert credits == []
    assert values["title_credits"] is False
    assert values["title_sound"] is True


def test_tutorial_objective_regions_start_hidden_until_their_stage(campaign_database):
    tutorial = campaign_database.levels.get("wn00_tutorial")
    assert "inn_door" not in tutorial.regions


def test_tutorial_enemy_phase_is_reserved_for_the_scripted_raven(campaign_database):
    tutorial = campaign_database.levels.get("wn00_tutorial")
    enemies = [unit for unit in tutorial.units if unit.team == "enemy"]
    assert [unit.nid for unit in enemies] == ["raven"]
    assert enemies[0].ai == "do_nothing"


def test_named_playables_compile_without_story_guardian(compiled_campaign):
    skills = json.loads(
        (compiled_campaign / "game_data" / "skills.json").read_text(encoding="utf-8")
    )
    units = json.loads(
        (compiled_campaign / "game_data" / "units.json").read_text(encoding="utf-8")
    )

    assert all(skill["nid"] != "story_guardian" for skill in skills)
    assert all(
        learned_skill[1] != "story_guardian"
        for unit in units
        for learned_skill in unit["learned_skills"]
    )


def test_campaign_enables_leveling_and_applies_enemy_tiers(campaign_database):
    assert campaign_database.constants.value("exp_magnitude") == 15.0
    assert campaign_database.constants.value("exp_curve") == 0.12
    assert campaign_database.constants.value("kill_multiplier") == 3.0

    rand = campaign_database.units.get("rand")
    opening_raider = campaign_database.units.get("breach_axe_a")
    late_raider = campaign_database.units.get("flank_wave_a")
    assert rand.level == 1
    assert rand.growths["HP"] == 70
    assert "hunting_bow" in rand.starting_items[0]
    assert rand.growths["STR"] == 35
    assert opening_raider.level == 1
    assert late_raider.level == 2
    assert late_raider.bases["HP"] == opening_raider.bases["HP"]
    assert late_raider.bases["STR"] == opening_raider.bases["STR"]


def test_story_boundary_rejects_later_beat(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    broken.story_beats.beats[0].chronology = 999

    with pytest.raises(ValidationError, match="story beats exceed campaign boundary"):
        CampaignBundle.model_validate(broken.model_dump())


def test_long_road_book_text_scene_contract(campaign_bundle):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn04_long_road"
    )
    events = {event.id: event for event in mission.events}
    regions = {region.id: region for region in mission.regions}
    chapter_scenes = {
        scene.id: scene
        for scene in campaign_bundle.scenes
        if scene.chapter == "wn04_long_road"
    }

    assert mission.objective.display_text == "Reach east edge"
    assert (
        mission.target_play.minimum_turns,
        mission.target_play.maximum_turns,
    ) == (9, 12)
    assert set(chapter_scenes) == {
        "sc_c4_setting_out",
        "sc_c4_laman_outburst",
        "sc_c4_column_passes",
        "sc_c4_rider_stops",
        "sc_c4_seen",
        "sc_c4_rider_leaves",
        "sc_c4_avendesora",
        "sc_c4_sweeper_warning",
        "sc_c4_sweepers",
        "sc_c4_dragonmount_speech",
    }
    assert {scene.background for scene in chapter_scenes.values()} == {"westwood_road_night"}

    scene_text = {
        scene_id: " ".join(beat.text for beat in scene.beats if beat.text)
        for scene_id, scene in chapter_scenes.items()
    }
    assert "litter scrapes east through the Westwood" in scene_text["sc_c4_setting_out"]
    assert "Every sound stops him" in scene_text["sc_c4_setting_out"]
    assert "How many died for Laman's sin" in scene_text["sc_c4_laman_outburst"]
    assert "cloak lies still as death" in scene_text["sc_c4_rider_stops"]
    assert "Battles are always hot" in scene_text["sc_c4_dragonmount_speech"]
    assert "Slope of the mountain" in scene_text["sc_c4_dragonmount_speech"]
    assert "Crying in the snow" in scene_text["sc_c4_dragonmount_speech"]
    assert "Rand is a good name" in scene_text["sc_c4_dragonmount_speech"]
    assert "Light, who am I?" in scene_text["sc_c4_dragonmount_speech"]

    assert events["sweeper_warning"].trigger.turn == 3
    assert events["sweepers"].trigger.turn == 4
    assert events["rider_halts"].trigger.turn == 6
    assert {
        region_id: (regions[region_id].position, regions[region_id].starts_active)
        for region_id in ("shelter_upper", "shelter_lower", "rider_stop")
    } == {
        "shelter_upper": ((15, 5), False),
        "shelter_lower": ((16, 8), False),
        "rider_stop": ((25, 3), False),
    }
    assert events["caught_on_road"].condition.flag_false == "rand_hidden"
    assert (
        events["caught_on_road"].condition.turn_at_least,
        events["caught_on_road"].condition.turn_at_most,
    ) == (7, 7)
    for event_id in ("hide_upper", "hide_lower"):
        assert [
            action.target
            for action in events[event_id].actions
            if action.type == "deactivate_region"
        ] == ["shelter_upper", "shelter_lower"]

    story_beats = {beat.id: beat for beat in campaign_bundle.story_beats.beats}
    assert {
        beat_id: story_beats[beat_id].source_locator
        for beat_id in story_beats
        if beat_id.startswith("c4_")
    } == {
        "c4_night_road": "06:43-53",
        "c4_hide_mechanics": "06:63-79",
        "c4_laman_outburst": "06:55-63",
        "c4_column_passes": "06:63-69",
        "c4_rider_returns": "06:69-83",
        "c4_avendesora": "06:89-95",
        "c4_dragonmount_speech": "06:97-105",
    }

    decisions = {
        decision.id: decision for decision in campaign_bundle.adaptation_rules.decisions
    }
    assert decisions["litter_as_rescue_traveler"].source_beats == [
        "c3_litter_built",
        "c4_night_road",
    ]
    assert "litter_as_escort" not in decisions

    assert_direct_dialogue_quotes_source(
        chapter_scenes,
        source_chapter_words("06_the_westwood.txt"),
        "Chapter 6",
    )


def test_out_of_the_woods_book_text_scene_contract(campaign_bundle):
    mission = next(
        mission
        for mission in campaign_bundle.missions
        if mission.id == "wn05_out_of_the_woods"
    )
    events = {event.id: event for event in mission.events}
    regions = {region.id: region for region in mission.regions}
    chapter_scenes = {
        scene.id: scene
        for scene in campaign_bundle.scenes
        if scene.chapter == "wn05_out_of_the_woods"
    }

    assert mission.objective.display_text == "Bring Tam to inn"
    assert (mission.objective.unit, mission.objective.region) == (
        "tam_litter",
        "inn_door",
    )
    assert [
        (failure.type, failure.unit) for failure in mission.failure_conditions
    ] == [
        ("unit_death", "rand"),
        ("unit_death", "tam_litter"),
    ]
    assert set(regions) == {"wisdom_rows", "inn_door", "bonfires"}
    assert regions["bonfires"].starts_active is False
    assert set(events) == {
        "dawn_start",
        "luhhan_talk",
        "egwene_talk",
        "luhhan_litter_assist",
        "fever_turn_4",
        "fever_turn_6",
        "fever_turn_8",
        "wisdom_reached",
        "inn_delivery",
        "bonfire_arrival",
        "bonfire_arrival_without_both_talks",
        "dawn_outro",
    }
    assert [
        (action.target, action.value)
        for action in events["dawn_start"].actions
        if action.type == "add_talk"
    ] == [("rand", "luhhan"), ("rand", "egwene")]
    assert [
        (action.target, action.value)
        for event in mission.events
        for action in event.actions
        if action.type == "change_objective"
    ] == [
        ("both", "Bring Tam to inn"),
        ("both", "Bring Tam to inn"),
        ("both", "Find Moiraine"),
        ("loss", "Keep Rand alive"),
    ]
    assert [
        (event.id, action.target, action.value)
        for event in mission.events
        for action in event.actions
        if action.type == "set_flag" and action.target == "tam_at_inn"
    ] == [
        ("dawn_start", "tam_at_inn", False),
        ("inn_delivery", "tam_at_inn", True),
    ]
    assert events["bonfire_arrival"].condition.all_flags == [
        "tam_at_inn",
        "talked_luhhan",
        "talked_egwene",
    ]
    assert events["bonfire_arrival_without_both_talks"].condition.all_flags == [
        "tam_at_inn"
    ]
    assert events["bonfire_arrival_without_both_talks"].condition.not_all_flags == [
        "talked_luhhan",
        "talked_egwene",
    ]
    assert [
        (action.type, action.target)
        for action in events["inn_delivery"].actions
        if action.type in {"remove_unit", "deactivate_region", "activate_region"}
    ] == [
        ("remove_unit", "tam_litter"),
        ("deactivate_region", "inn_door"),
        ("activate_region", "bonfires"),
    ]
    assert [
        (action.type, action.target, action.value)
        for action in events["luhhan_litter_assist"].actions
    ] == [
        ("set_flag", "luhhan_help_used", True),
        ("refresh_unit", "tam_litter", None),
    ]
    assert events["luhhan_litter_assist"].condition.all_flags == ["luhhan_helped"]
    assert events["luhhan_litter_assist"].condition.flag_false == "luhhan_help_used"
    for turn in (4, 6, 8):
        event = events[f"fever_turn_{turn}"]
        assert event.trigger.turn == turn
        assert event.condition.flag_false == "tam_at_inn"
        assert not any(action.type == "lose" for action in event.actions)
    assert not any(
        action.type == "lose" for event in mission.events for action in event.actions
    )
    assert mission.narrative_constraints["two_playable_legs"] is True

    def played_scenes(event_id):
        return [
            action.target
            for action in events[event_id].actions
            if action.type == "play_scene"
        ]

    assert {
        event_id: played_scenes(event_id)
        for event_id in (
            "dawn_start",
            "luhhan_talk",
            "egwene_talk",
            "wisdom_reached",
            "inn_delivery",
            "bonfire_arrival",
            "bonfire_arrival_without_both_talks",
            "dawn_outro",
        )
    } == {
        "dawn_start": ["sc_c5_burned_dawn"],
        "luhhan_talk": ["sc_c5_luhhan"],
        "egwene_talk": ["sc_c5_egwene"],
        "wisdom_reached": ["sc_c5_nynaeve"],
        "inn_delivery": ["sc_c5_dragons_fang", "sc_c5_bran_and_thom"],
        "bonfire_arrival": [
            "sc_c5_bonfires",
            "sc_c5_any_price",
        ],
        "bonfire_arrival_without_both_talks": [
            "sc_c5_bonfires",
            "sc_c5_any_price",
        ],
        "dawn_outro": ["sc_c5_moiraine_heals", "sc_c5_ending_card"],
    }

    assert set(chapter_scenes) == {
        "sc_c5_burned_dawn",
        "sc_c5_luhhan",
        "sc_c5_egwene",
        "sc_c5_nynaeve",
        "sc_c5_dragons_fang",
        "sc_c5_bran_and_thom",
        "sc_c5_bonfires",
        "sc_c5_any_price",
        "sc_c5_moiraine_heals",
        "sc_c5_ending_card",
    }
    outdoor_scenes = set(chapter_scenes) - {
        "sc_c5_bran_and_thom",
        "sc_c5_ending_card",
    }
    assert {
        chapter_scenes[scene_id].background for scene_id in outdoor_scenes
    } == {"emonds_field_burned_dawn"}
    assert chapter_scenes["sc_c5_bran_and_thom"].background == "winespring_inn"
    assert chapter_scenes["sc_c5_ending_card"].background == "winternight_ending"
    assert chapter_scenes["sc_c5_ending_card"].canon_status == "gameplay_invention"

    scene_text = {
        scene_id: " ".join(beat.text for beat in scene.beats if beat.text)
        for scene_id, scene in chapter_scenes.items()
    }
    assert "At gray dawn, Rand hauls Tam into town" in scene_text["sc_c5_burned_dawn"]
    assert (
        "Trollocs, boy? Here, too. Here, too."
        in scene_text["sc_c5_luhhan"]
    )
    assert "bedsheets torn into bandages" in scene_text["sc_c5_egwene"]
    assert (
        "Light, I wish there was something I could do"
        in scene_text["sc_c5_egwene"]
    )
    assert "There's nothing I can do" in scene_text["sc_c5_nynaeve"]
    assert (
        "I know what I can do with my medicines, and I know when it's too late"
        in scene_text["sc_c5_nynaeve"]
    )
    assert "goat's horn" in scene_text["sc_c5_dragons_fang"]
    assert "Dragon's Fang" in scene_text["sc_c5_dragons_fang"]
    assert "Aes Sedai can heal, Rand" in scene_text["sc_c5_bran_and_thom"]
    assert "That makes seven bands so far" in scene_text["sc_c5_bonfires"]
    assert (
        "I'll pay any price in my power if you help him. Anything."
        in scene_text["sc_c5_any_price"]
    )
    assert (
        "only fools are willing to pay that price"
        in scene_text["sc_c5_moiraine_heals"]
    )
    assert (
        "Take me to your father, Rand. I will help him as much as I am able."
        in scene_text["sc_c5_moiraine_heals"]
    )
    assert scene_text["sc_c5_ending_card"] == "Light, who am I?"


    story_beats = {beat.id: beat for beat in campaign_bundle.story_beats.beats}
    assert {
        beat_id: story_beats[beat_id].source_locator
        for beat_id in story_beats
        if beat_id.startswith("c5_")
    } == {
        "c5_burned_village": "07:9-21",
        "c5_luhhan_meets": "07:23-49",
        "c5_nynaeve_refusal": "07:51-83",
        "c5_to_the_inn": "07:85-113",
        "c5_bran_and_thom": "07:115-165",
        "c5_bonfires": "07:167-183",
        "c5_walk_leg_split": "07:165-167",
        "c5_any_price": "07:185-187",
        "c5_moiraine_heals": "07:189-205",
    }

    decisions = {
        decision.id: decision for decision in campaign_bundle.adaptation_rules.decisions
    }
    assert decisions["walk_leg_split"].source_beats == [
        "c5_walk_leg_split",
        "c5_to_the_inn",
        "c5_bonfires",
    ]
    assert decisions["c5_green_talk_staging"].source_beats == [
        "c5_luhhan_meets",
        "c5_nynaeve_refusal",
        "c5_to_the_inn",
    ]
    assert decisions["ending_question_card"].source_beats == [
        "c4_dragonmount_speech",
        "c5_moiraine_heals",
    ]

    assert_direct_dialogue_quotes_source(
        chapter_scenes,
        source_chapter_words("07_out_of_the_woods.txt"),
        "Chapter 7",
    )


def test_scene_rejects_dialogue_behind_a_closed_transition(campaign_bundle):
    scene = next(scene for scene in campaign_bundle.scenes if scene.id == "sc_c0_quarry_road")
    broken = scene.model_dump()
    broken["beats"].insert(
        2, {"type": "action", "action": "transition_close", "asset": None, "text": None}
    )

    with pytest.raises(ValidationError, match="dialogue behind a closed transition"):
        SceneSpecV2.model_validate(broken)


def test_story_boundary_allows_only_ending_card_after_final_scene(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    ending_card = next(scene for scene in broken.scenes if scene.id == "sc_c5_ending_card")
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
            if scene.id == "sc_c5_moiraine_heals"
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
    assert rand["wexp_gain"]["Utility"][0] is True

def test_village_mat_can_equip_hunting_bow(compiled_campaign):
    units = json.loads(
        (compiled_campaign / "game_data" / "units.json").read_text(encoding="utf-8")
    )
    mat = next(unit for unit in units if unit["nid"] == "mat_c2")

    assert ["hunting_bow", False] in mat["starting_items"]
    assert mat["wexp_gain"]["Bow"][0] is True


# FE8U commit ecc6798b68fc7d0d164b2b6dd96a9fee4306cadb: gClassData in
# src/data_classes.c supplies the Myrmidon/Thief/Fighter bases, constitution,
# movement, and weapon ranks; gPromoJidLut in src/classchg-data.c supplies the
# promotion targets; the tier-2 entries own the promotion gains that
# ApplyUnitPromotion adds (src/bmbattle.c:1414-1459).
def test_farm_lad_class_lines_carry_fe8_progression(campaign_database, compiled_campaign):
    classes = json.loads(
        (compiled_campaign / "game_data" / "classes.json").read_text(encoding="utf-8")
    )
    by_nid = {klass["nid"]: klass for klass in classes}

    for base, name, promotions in (
        ("swordsman", "Swordsman", ["blademark"]),
        ("trickster", "Trickster", ["nightblade", "highwayman"]),
        ("apprentice", "Apprentice", ["hammerhand"]),
    ):
        assert by_nid[base]["name"] == name
        assert by_nid[base]["tier"] == 1
        assert by_nid[base]["turns_into"] == promotions
        options = campaign_database.classes.get(base).promotion_options(campaign_database)
        assert options == promotions
        for promotion in promotions:
            assert by_nid[promotion]["tier"] == 2
            assert by_nid[promotion]["promotes_from"] == base

    # FE8 Swordmaster gains +5 HP, +2 Pow, +2 Def, +1 Res over Myrmidon and
    # steps constitution 8 -> 9 and movement 5 -> 6.
    assert by_nid["blademark"]["promotion"]["HP"] == 5
    assert by_nid["blademark"]["bases"]["CON"] == by_nid["swordsman"]["bases"]["CON"] + 1
    assert by_nid["blademark"]["bases"]["MOV"] == by_nid["swordsman"]["bases"]["MOV"] + 1

    # FE8 weapon locks: swords for the Myrmidon and Thief lines, axes for the
    # Fighter line, and bows only after the Warrior-equivalent promotion. Rand
    # and Mat keep the declared Bow/Utility tutorial exception.
    assert by_nid["swordsman"]["wexp_gain"]["Sword"][0] is True
    assert by_nid["trickster"]["wexp_gain"]["Sword"][0] is True
    assert by_nid["apprentice"]["wexp_gain"]["Axe"][0] is True
    assert by_nid["apprentice"]["wexp_gain"]["Sword"][0] is False
    assert by_nid["apprentice"]["wexp_gain"]["Bow"][0] is False
    assert by_nid["hammerhand"]["wexp_gain"]["Axe"][0] is True
    assert by_nid["hammerhand"]["wexp_gain"]["Bow"][0] is True
    assert by_nid["nightblade"]["wexp_gain"]["Bow"][0] is True


def test_semantics_rejects_equipping_an_unsupported_weapon(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    rand = next(character for character in broken.characters.characters if character.id == "rand")
    rand.combat.additional_weapon_types = []

    with pytest.raises(CampaignSemanticError, match="equips hunting_bow on incompatible"):
        validate_campaign_semantics(broken)


def test_semantics_rejects_unknown_trigger_item(campaign_bundle):
    broken = campaign_bundle.model_copy(deep=True)
    tutorial = next(mission for mission in broken.missions if mission.id == "wn00_tutorial")
    event = next(
        event for event in tutorial.events if event.id == "tutorial_rand_throw_done"
    )
    event.trigger.item = "missing_item"

    with pytest.raises(CampaignSemanticError, match="unknown trigger item"):
        validate_campaign_semantics(broken)
