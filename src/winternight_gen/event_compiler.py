from __future__ import annotations

from .models import (
    ActionSceneBeat,
    DialogueSceneBeat,
    EventActionSpec,
    EventConditionSpec,
    MissionEventSpec,
    MissionSpec,
    OutcomeSpec,
    SceneSpec,
    SceneSpecV2,
)

_LT_PORTRAIT_POSITIONS = {
    "left": "Left",
    "right": "Right",
    "center": "72,Bottom",
}


def compile_scene(scene: SceneSpec) -> str:
    commands = [f"change_background;{scene.background}"]
    visible: list[str] = []
    for line in scene.lines:
        if line.portrait not in visible:
            commands.append(
                f"add_portrait;{line.portrait};"
                f"{_LT_PORTRAIT_POSITIONS[line.position]};immediate"
            )
            visible.append(line.portrait)
        commands.append(f"speak;{line.portrait};{line.text};;;;;black;no_sound")
    commands.extend(f"remove_portrait;{portrait};immediate" for portrait in visible)
    commands.append("change_background")
    return "\n".join(commands)


def compile_outcome(outcome: OutcomeSpec, command: str) -> tuple[str, str]:
    condition = f"unit1 and unit1.nid == '{outcome.defeated_unit}'"
    return condition, command


def _literal(value: str | int | bool | None) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, int):
        return str(value)
    return repr(value)


def compile_scene_v2(scene: SceneSpecV2) -> str:
    cast = {member.character: member for member in scene.cast}
    commands = [f"change_background;{scene.background}"]
    visible: dict[str, str] = {}

    def show_portrait(member) -> None:
        current = visible.get(member.position)
        if current and current != member.portrait:
            commands.append(f"remove_portrait;{current};immediate")
        if current != member.portrait:
            commands.append(
                f"add_portrait;{member.portrait};"
                f"{_LT_PORTRAIT_POSITIONS[member.position]};immediate"
            )
            visible[member.position] = member.portrait

    for beat in scene.beats:
        if isinstance(beat, DialogueSceneBeat):
            member = cast[beat.speaker]
            show_portrait(member)
            commands.append(
                f"speak;{member.portrait};{beat.text};;;;;black;no_sound"
            )
        elif isinstance(beat, ActionSceneBeat):
            if beat.action == "narration" and beat.text:
                commands.append(f"speak;;{beat.text};bottom;;noir;no_sound")
            elif beat.action == "sound":
                commands.append(f"sound;{beat.asset}")
            elif beat.action == "show_portrait" and beat.asset:
                member = next(member for member in scene.cast if member.portrait == beat.asset)
                show_portrait(member)
            elif beat.action == "transition_close":
                commands.append("transition;Close")
            elif beat.action == "transition_open":
                commands.append("transition;Open")
            elif beat.action == "ending_card":
                commands.extend(
                    f"remove_portrait;{portrait};immediate" for portrait in visible.values()
                )
                visible.clear()
                if beat.asset:
                    commands.append(f"change_background;{beat.asset}")
                if beat.text:
                    commands.append(f"speak;;{beat.text};bottom;;noir;no_sound")
    commands.extend(f"remove_portrait;{portrait};immediate" for portrait in visible.values())
    commands.append("change_background")
    return "\n".join(commands)


def _compile_condition(condition: EventConditionSpec) -> list[str]:
    clauses = [f"game.level_vars.get({flag!r}, False)" for flag in condition.all_flags]
    if condition.not_all_flags:
        flags = ", ".join(repr(flag) for flag in condition.not_all_flags)
        clauses.append(f"not all(game.level_vars.get(flag, False) for flag in ({flags},))")
    if condition.any_flags:
        flags = ", ".join(repr(flag) for flag in condition.any_flags)
        clauses.append(f"any(game.level_vars.get(flag, False) for flag in ({flags},))")
    if condition.flag_false:
        clauses.append(f"not game.level_vars.get({condition.flag_false!r}, False)")
    if condition.turn_at_least is not None:
        clauses.append(f"game.turncount >= {condition.turn_at_least}")
    if condition.unit_dead:
        unit = condition.unit_dead
        clauses.append(f"game.get_unit({unit!r}) and game.get_unit({unit!r}).dead")
    return clauses


def compile_action(action: EventActionSpec) -> list[str]:
    if action.type == "play_scene":
        return [f"trigger_script;{action.target}"]
    if action.type == "set_flag":
        return [f"level_var;{action.target};{_literal(action.value)}"]
    if action.type == "increment_flag":
        value = action.value if action.value is not None else 1
        return [f"inc_level_var;{action.target};{value}"]
    if action.type == "spawn_group":
        return [f"add_group;{action.target};{action.target};immediate;closest"]
    if action.type == "remove_unit":
        return [f"remove_unit;{action.target};fade"]
    if action.type == "give_item":
        return [f"give_item;{action.target};{action.value};no_banner"]
    if action.type == "equip_item":
        return [f"equip_item;{action.target};{action.value}"]
    if action.type == "change_ai":
        return [f"change_ai;{action.target};{action.value}"]
    if action.type == "add_talk":
        return [f"add_talk;{action.target};{action.value}"]
    if action.type == "remove_talk":
        return [f"remove_talk;{action.target};{action.value}"]
    if action.type == "mark_visited":
        return [f"has_visited;{action.target}"]
    if action.type == "show_layer":
        return [f"show_layer;{action.target};immediate"]
    if action.type == "change_objective":
        return [f"change_objective_{action.target};{action.value}"]
    if action.type == "set_fog":
        radius = int(action.value or 3)
        return ["enable_fog_of_war;True", f"set_fog_of_war;gba;{radius};{radius}"]
    if action.type == "skip_save":
        return [f"skip_save;{_literal(action.value)}"]
    if action.type == "win":
        return ["win_game"]
    if action.type == "lose":
        return ["lose_game"]
    if action.type == "set_next_chapter":
        return [f"set_next_chapter;{action.target}"]
    raise ValueError(f"unsupported event action {action.type}")


def compile_mission_event(
    mission: MissionSpec, event: MissionEventSpec
) -> tuple[str | None, str, str]:
    trigger = event.trigger
    trigger_name: str | None
    clauses: list[str] = []
    if trigger.type in {
        "level_start",
        "level_end",
        "unit_wait",
        "unit_death",
        "combat_start",
    }:
        trigger_name = trigger.type
    elif trigger.type == "turn_start":
        trigger_name = "turn_change"
        clauses.append(f"game.turncount == {trigger.turn}")
    elif trigger.type == "talk":
        trigger_name = "on_talk"
    elif trigger.type == "region_interact":
        region = next(region for region in mission.regions if region.id == trigger.region)
        trigger_name = region.sub_id or "on_region_interact"
    elif trigger.type == "call":
        trigger_name = None
    else:
        raise ValueError(f"unsupported event trigger {trigger.type}")
    if trigger.unit:
        clauses.append(f"unit and unit.nid == {trigger.unit!r}")
    if trigger.unit2:
        clauses.append(f"unit2 and unit2.nid == {trigger.unit2!r}")
    if trigger.region:
        clauses.append(f"region and region.nid == {trigger.region!r}")
    clauses.extend(_compile_condition(event.condition))
    condition = " and ".join(f"({clause})" for clause in clauses) or "True"
    source = "\n".join(command for action in event.actions for command in compile_action(action))
    return trigger_name, condition, source


def compile_failure_condition(unit: str, active_until_flag: str | None) -> str:
    clauses = [f"unit and unit.nid == {unit!r}"]
    if active_until_flag:
        clauses.append(f"not game.level_vars.get({active_until_flag!r}, False)")
    return " and ".join(f"({clause})" for clause in clauses)
