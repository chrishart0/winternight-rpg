from __future__ import annotations

import json

from winternight_gen.event_compiler import compile_action
from winternight_gen.models import EventActionSpec


def _catalog(compiled_campaign, name: str):
    path = compiled_campaign / "game_data" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_rescue_actions_map_directly_to_lt_commands():
    pair = EventActionSpec(type="pair_up", target="tam_litter", value="rand")
    separate = EventActionSpec(type="separate", target="rand")

    assert compile_action(pair) == ["pair_up;tam_litter;rand"]
    assert compile_action(separate) == ["separate;rand"]


def test_rescue_skill_applies_the_carrier_movement_penalty(compiled_campaign):
    rescue = next(
        skill for skill in _catalog(compiled_campaign, "skills") if skill["nid"] == "Rescue"
    )

    assert ["hidden", None] in rescue["components"]
    assert ["stat_change", [["MOV", -2]]] in rescue["components"]


def test_march_ai_moves_without_an_attack_behaviour(compiled_campaign):
    profiles = {profile["nid"]: profile for profile in _catalog(compiled_campaign, "ai")}

    for profile_id in ("column_march", "rider_return_march", "rider_depart_march"):
        behaviours = profiles[profile_id]["behaviours"]
        assert [behaviour["action"] for behaviour in behaviours] == ["Move_to", "None", "None"]
        assert all(behaviour["action"] != "Attack" for behaviour in behaviours)


def test_hide_check_catches_only_unhidden_rand_on_turn_seven(compiled_campaign):
    event = next(
        event
        for event in _catalog(compiled_campaign, "events")
        if event["nid"] == "wn04_long_road caught_on_road"
    )

    assert "not game.level_vars.get('rand_hidden', False)" in event["condition"]
    assert "game.turncount >= 7" in event["condition"]
    assert "game.turncount <= 7" in event["condition"]
    assert "contains" not in event["condition"]


def test_activated_gated_region_receives_its_condition(compiled_campaign):
    event = next(
        event
        for event in _catalog(compiled_campaign, "events")
        if event["nid"] == "wn04_long_road rider_halts"
    )
    source = event["_source"]
    add_index = next(
        index
        for index, command in enumerate(source)
        if command.startswith("add_region;rider_watch;")
    )

    assert source[add_index + 1] == (
        "region_condition;rider_watch;"
        "game.level_vars.get('rider_watching', False)"
    )


def test_rider_halt_shows_threat_then_shelters_and_pauses_sweepers(compiled_campaign):
    events = {
        event["nid"]: event for event in _catalog(compiled_campaign, "events")
    }
    source = events["wn04_long_road rider_halts"]["_source"]

    rider = source.index("flicker_cursor;rider_stop")
    scene = source.index("trigger_script;sc_c4_rider_stops")
    upper = source.index("flicker_cursor;shelter_upper")
    lower = source.index("flicker_cursor;shelter_lower")
    watched = source.index("flicker_cursor;rider_watch")

    assert rider < scene < upper < lower < watched
    assert "change_ai;sweep_a;do_nothing" in source
    assert "change_ai;sweep_b;do_nothing" in source
    leaves = events["wn04_long_road rider_leaves"]["_source"]
    assert "change_ai;sweep_a;pursue" in leaves
    assert "change_ai;sweep_b;pursue" in leaves
    assert "game.turncount == 4" in events["wn04_long_road sweepers"]["condition"]
