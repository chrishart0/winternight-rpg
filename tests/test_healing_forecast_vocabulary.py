from __future__ import annotations

import json
from pathlib import Path

import pytest

from winternight_gen.campaign_lt_adapter import make_campaign_database
from winternight_gen.lt_adapter import _import_lt
from winternight_gen.lt_runtime import generated_component_system
from winternight_gen.models import MissionSpec

ENGINE_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "lt-maker"


def _catalog(project: Path, name: str):
    path = project / "game_data" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _components(item: dict) -> dict:
    return dict(item["components"])


@pytest.fixture(scope="module")
def compiled_forecast_database(tmp_path_factory, campaign_bundle):
    mission_index = next(
        index
        for index, mission in enumerate(campaign_bundle.missions)
        if mission.id == "wn00_tutorial"
    )
    mission_data = campaign_bundle.missions[mission_index].model_dump(mode="python")
    mission_data["scripted_forecast_lessons"] = [
        {
            "id": "raven_forecast",
            "actor": "rand",
            "target": "raven",
            "item": "thrown_stone",
            "target_group": "raven_omen",
            "outcome": "miss",
            "prompt": "Choose Attack, inspect the forecast, then confirm the raven.",
            "completion_actions": [
                {"type": "set_flag", "target": "forecast_chain_continued", "value": True}
            ],
        }
    ]
    start_event = next(event for event in mission_data["events"] if event["id"] == "tutorial_start")
    start_event["actions"].append(
        {"type": "start_forecast_lesson", "target": "raven_forecast"}
    )

    bundle = campaign_bundle.model_copy(deep=True)
    bundle.missions[mission_index] = MissionSpec.model_validate(mission_data)
    output = tmp_path_factory.mktemp("forecast-database")
    _import_lt(ENGINE_ROOT)
    with generated_component_system(ENGINE_ROOT):
        database = make_campaign_database(bundle)
        assert database.serialize(output, as_chunks=False)
    return output


def test_healing_items_compile_with_authored_range_and_experience(compiled_campaign):
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}

    dressing = _components(items["field_dressing"])
    assert dressing["usable"] is None
    assert dressing["heal"] == 10
    assert dressing["min_range"] == 0
    assert dressing["max_range"] == 1
    assert "exp" not in dressing

    herbs = _components(items["herb_pouch"])
    assert items["herb_pouch"]["name"] == "Healing Herbs"
    # A physical remedy belongs to the ordinary Item command, never the weave
    # (LT "Spells") action a channeler uses.
    assert herbs["usable"] is None
    assert "spell" not in herbs
    assert herbs["target_ally"] is None
    assert herbs["heal"] == 8
    assert herbs["min_range"] == 0
    assert herbs["max_range"] == 1
    assert herbs["uses"] == 3
    assert herbs["exp"] == 11
    assert "weapon_type" not in herbs
    assert "weapon_rank" not in herbs
    assert "magic" not in herbs


def test_weave_of_spirit_compiles_as_an_ungated_ranged_healing_spell(compiled_campaign):
    items = {item["nid"]: item for item in _catalog(compiled_campaign, "items")}
    weave = items["weave_of_spirit"]
    components = _components(weave)

    assert weave["name"] == "Weave of Spirit"
    assert weave["desc"] == (
        "Spirit knits a battle wound; the root of a fever lies beyond it."
    )
    assert components["spell"] is None
    assert components["target_ally"] is None
    assert components["heal"] == 14
    assert components["min_range"] == 1
    assert components["max_range"] == 2
    assert components["uses"] == 3
    assert components["exp"] == 12
    assert "usable" not in components
    assert "weapon_type" not in components
    assert "heal_exp" not in components


def test_moiraine_compiles_with_weave_of_spirit_in_her_inventory(compiled_campaign):
    units = {unit["nid"]: unit for unit in _catalog(compiled_campaign, "units")}

    assert ["weave_of_spirit", False] in units["moiraine"]["starting_items"]


def test_scripted_forecast_lesson_compiles_setup_script_and_completion(
    compiled_forecast_database,
):
    events = {
        event["nid"]: event for event in _catalog(compiled_forecast_database, "events")
    }
    start = events["wn00_tutorial tutorial_start"]["_source"]
    script = events["wn00_tutorial raven_forecast__script"]
    complete = events["wn00_tutorial raven_forecast__complete"]

    assert start[-7:] == [
        "add_group;raven_omen;raven_omen;immediate;closest",
        "give_item;rand;thrown_stone;no_banner",
        "equip_item;rand;thrown_stone",
        (
            "speak;;Choose Attack, inspect the forecast, then confirm the raven.;"
            "bottom;;noir;2.0;;no_sound"
        ),
        "level_var;raven_forecast_active;True",
        "reset;rand",
        "flicker_cursor;raven",
    ]
    assert script["trigger"] == "combat_start"
    assert script["_source"] == ["set_combat_script;miss1,end"]
    assert complete["trigger"] == "combat_end"
    assert complete["_source"] == [
        "level_var;raven_forecast_active;False",
        "level_var;raven_forecast_complete;True",
        "remove_item;rand;thrown_stone;no_banner",
        "remove_unit;raven;fade",
        "level_var;forecast_chain_continued;True",
    ]


def test_mission_schema_documents_scripted_forecast_syntax():
    schema = MissionSpec.model_json_schema()
    lesson = schema["$defs"]["ScriptedForecastLessonSpec"]
    action = schema["$defs"]["EventActionSpec"]

    assert "start_forecast_lesson" in action["properties"]["type"]["description"]
    assert "forced miss" in lesson["properties"]["completion_actions"]["description"]
    assert "set_combat_script;miss1,end" in lesson["properties"]["outcome"]["description"]
    assert "creates hidden combat-start and combat-end events" in schema["properties"][
        "scripted_forecast_lessons"
    ]["description"]
