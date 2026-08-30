from __future__ import annotations

from .models import (
    ActionSceneBeat,
    DialogueSceneBeat,
    EventActionSpec,
    EventConditionSpec,
    EventTriggerSpec,
    FailureCondition,
    MissionEventSpec,
    MissionSpec,
    OutcomeSpec,
    RegionSpec,
    SceneSpec,
    SceneSpecV2,
    ScriptedForecastLessonSpec,
)
from .objective_text import OBJECTIVE_FLASH_LEVEL_VAR

_LT_PORTRAIT_POSITIONS = {
    "left": "Left",
    "right": "Right",
    "center": "72,Bottom",
}

# Multiplier applied to the engine's global text_speed setting (32 ms/char
# default). 2.0 -> 64 ms/char (~16 chars/sec), retaining LT's
# player-confirmed progression between text boxes.
_SPEAK_TEXT_SPEED = "2.0"


def _dialogue(portrait: str, text: str) -> str:
    return f"speak;{portrait};{text};;;;{_SPEAK_TEXT_SPEED};black;no_talk"


def _narration(text: str) -> str:
    return f"speak;;{text};bottom;;noir;{_SPEAK_TEXT_SPEED};;no_sound"


def compile_scene(scene: SceneSpec) -> str:
    commands = [f"change_background;{scene.background}"]
    visible: list[str] = []
    for line in scene.lines:
        if line.portrait not in visible:
            commands.append(
                f"add_portrait;{line.portrait};{_LT_PORTRAIT_POSITIONS[line.position]};immediate"
            )
            visible.append(line.portrait)
        commands.append(_dialogue(line.portrait, line.text))
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

def compile_region_condition(region: RegionSpec) -> str:
    clauses = [
        *(f"game.level_vars.get({flag!r}, False)" for flag in region.required_flags),
        *(
            [f"unit and unit.nid in {tuple(region.allowed_units)!r}"]
            if region.allowed_units
            else []
        ),
    ]
    return " and ".join(clauses) or "True"


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
            commands.append(_dialogue(member.portrait, beat.text))
        elif isinstance(beat, ActionSceneBeat):
            if beat.action == "narration" and beat.text:
                commands.append(_narration(beat.text))
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
                    commands.append(_narration(beat.text))
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
    if condition.turn_at_most is not None:
        clauses.append(f"game.turncount <= {condition.turn_at_most}")
    if condition.unit_dead:
        unit = condition.unit_dead
        clauses.append(f"game.get_unit({unit!r}) and game.get_unit({unit!r}).dead")
    if condition.unit_in_region:
        unit = condition.unit_in_region.unit
        region = condition.unit_in_region.region
        clauses.append(
            f"game.get_unit({unit!r}) and {region!r} in game.level.regions and "
            f"game.level.regions.get({region!r}).contains(game.get_unit({unit!r}).position)"
        )
    if condition.trigger_unit_in_region:
        team = condition.trigger_unit_in_region.team
        region = condition.trigger_unit_in_region.region
        clauses.append(
            f"unit and unit.team == {team!r} and unit.position and "
            f"{region!r} in game.level.regions and "
            f"game.level.regions.get({region!r}).contains(unit.position)"
        )
    if condition.trigger_unit_team:
        clauses.append(f"unit and unit.team == {condition.trigger_unit_team!r}")
    if condition.level_var_compare:
        comparison = condition.level_var_compare
        operator = {"ge": ">=", "le": "<=", "eq": "=="}[comparison.op]
        clauses.append(
            f"game.level_vars.get({comparison.name!r}, 0) {operator} {comparison.value}"
        )
    return clauses


def compile_action(action: EventActionSpec, mission: MissionSpec | None = None) -> list[str]:
    if action.type == "play_scene":
        return [f"trigger_script;{action.target}"]
    if action.type == "tutorial_text":
        return [_narration(action.value)]
    if action.type == "permadeath_choice":
        choice_id = f"death_{action.target}"
        return [
            _narration(f"{action.value} died and is gone as a playable unit."),
            _narration("They will still appear in story scenes."),
            (
                f"choice;{choice_id};Restart the level?;"
                "restart|Restart,continue|Continue"
            ),
            f"if;game.game_vars.get({choice_id!r}) == 'restart'",
            "lose_game",
            "end",
        ]
    if action.type == "set_flag":
        return [f"level_var;{action.target};{_literal(action.value)}"]
    if action.type == "increment_flag":
        value = action.value if action.value is not None else 1
        return [f"inc_level_var;{action.target};{value}"]
    if action.type == "set_current_hp":
        return [f"set_current_hp;{action.target};{action.value}"]
    if action.type == "spawn_group":
        return [f"add_group;{action.target};{action.target};immediate;closest"]
    if action.type == "remove_unit":
        return [f"remove_unit;{action.target};fade"]
    if action.type == "move_unit":
        return [f"move_unit;{action.target};{action.value};normal;giveup;40;no_follow"]
    if action.type == "give_item":
        return [f"give_item;{action.target};{action.value}"]
    if action.type == "equip_item":
        return [f"equip_item;{action.target};{action.value}"]
    if action.type == "remove_item":
        return [f"remove_item;{action.target};{action.value};no_banner"]
    if action.type == "change_team":
        return [f"change_team;{action.target};{action.value}"]
    if action.type == "remove_tag":
        return [f"remove_tag;{action.target};{action.value}"]
    if action.type == "change_ai":
        return [f"change_ai;{action.target};{action.value}"]
    if action.type == "script_combat":
        return [f"set_combat_script;{action.value}"]
    if action.type == "start_forecast_lesson":
        if mission is None:
            raise ValueError("start_forecast_lesson requires mission context")
        lesson = next(
            (
                lesson
                for lesson in mission.scripted_forecast_lessons
                if lesson.id == action.target
            ),
            None,
        )
        if lesson is None:
            raise ValueError(f"unknown scripted forecast lesson {action.target!r}")
        return [
            f"add_group;{lesson.target_group};{lesson.target_group};immediate;closest",
            f"give_item;{lesson.actor};{lesson.item};no_banner",
            f"equip_item;{lesson.actor};{lesson.item}",
            _narration(lesson.prompt),
            f"level_var;{lesson.id}_active;True",
            f"reset;{lesson.actor}",
            f"flicker_cursor;{lesson.target}",
        ]
    if action.type == "add_talk":
        return [f"add_talk;{action.target};{action.value}"]
    if action.type == "remove_talk":
        return [f"remove_talk;{action.target};{action.value}"]
    if action.type == "mark_visited":
        return [f"has_visited;{action.target}"]
    if action.type == "activate_region":
        if mission is None:
            raise ValueError("activate_region requires mission context")
        region = next(
            (region for region in mission.regions if region.id == action.target),
            None,
        )
        if region is None:
            raise ValueError(f"unknown region {action.target!r}")
        flags = []
        if region.only_once:
            flags.append("only_once")
        if region.interrupt_move:
            flags.append("interrupt_move")
        fields = [
            "add_region",
            region.id,
            f"{region.position[0]},{region.position[1]}",
            f"{region.size[0]},{region.size[1]}",
            region.region_type,
            region.sub_id or "",
            "",
            "",
            region.highlight or "none",
            *flags,
        ]
        commands = [";".join(fields)]
        condition = compile_region_condition(region)
        if condition != "True":
            commands.append(f"region_condition;{region.id};{condition}")
        return commands
    if action.type == "deactivate_region":
        return [f"remove_region;{action.target}"]
    if action.type == "refresh_unit":
        return [f"reset;{action.target}"]
    if action.type == "highlight_target":
        return [f"flicker_cursor;{action.target}"]
    if action.type == "show_layer":
        return [f"show_layer;{action.target};immediate"]
    if action.type == "hide_layer":
        return [f"hide_layer;{action.target};immediate"]
    if action.type == "change_objective":
        if action.target == "both":
            return [
                f"change_objective_simple;{action.value}",
                f"change_objective_win;{action.value}",
            ]
        return [f"change_objective_{action.target};{action.value}"]
    if action.type == "flash_objective":
        # The patched map HUD consumes this level var once, then blinks the
        # persistent objective panel and settles it back from an enlarged draw.
        return [f"level_var;{OBJECTIVE_FLASH_LEVEL_VAR};True"]
    if action.type == "set_fog":
        radius = int(action.value or 3)
        return ["enable_fog_of_war;True", f"set_fog_of_war;gba;{radius};{radius}"]
    if action.type == "skip_save":
        return [f"skip_save;{_literal(action.value)}"]
    if action.type == "pair_up":
        if not action.target or not isinstance(action.value, str):
            raise ValueError("pair_up requires target=follower and value=carrier")
        return [f"pair_up;{action.target};{action.value}"]
    if action.type == "separate":
        if not action.target:
            raise ValueError("separate requires target=carrier")
        return [f"separate;{action.target}"]
    if action.type == "win":
        return ["win_game"]
    if action.type == "lose":
        return ["lose_game"]
    if action.type == "set_next_chapter":
        return [f"set_next_chapter;{action.target}"]
    raise ValueError(f"unsupported event action {action.type}")


def compile_failure_commands(failure: FailureCondition) -> list[str]:
    if failure.failure_scene:
        return [f"trigger_script;{failure.failure_scene}", "lose_game"]
    return ["lose_game"]


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
        "combat_end",
    }:
        trigger_name = trigger.type
    elif trigger.type in {"turn_start", "enemy_turn_start"}:
        trigger_name = (
            "turn_change" if trigger.type == "turn_start" else "enemy_turn_change"
        )
        if trigger.turn is not None:
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
    if trigger.item:
        clauses.append(f"item and item.nid == {trigger.item!r}")
    if trigger.region:
        clauses.append(f"region and region.nid == {trigger.region!r}")
    clauses.extend(_compile_condition(event.condition))
    condition = " and ".join(f"({clause})" for clause in clauses) or "True"
    source = "\n".join(
        command for action in event.actions for command in compile_action(action, mission)
    )
    return trigger_name, condition, source


def scripted_forecast_events(
    lesson: ScriptedForecastLessonSpec,
) -> tuple[MissionEventSpec, MissionEventSpec]:
    active_flag = f"{lesson.id}_active"
    complete_flag = f"{lesson.id}_complete"
    condition = EventConditionSpec(
        all_flags=[active_flag],
        flag_false=complete_flag,
    )
    script = MissionEventSpec(
        id=f"{lesson.id}__script",
        trigger=EventTriggerSpec(
            type="combat_start",
            unit=lesson.actor,
            unit2=lesson.target,
        ),
        condition=condition,
        actions=[EventActionSpec(type="script_combat", value="miss1,end")],
        priority=0,
    )
    complete = MissionEventSpec(
        id=f"{lesson.id}__complete",
        trigger=EventTriggerSpec(
            type="combat_end",
            unit=lesson.actor,
            unit2=lesson.target,
        ),
        condition=condition,
        actions=[
            EventActionSpec(type="set_flag", target=active_flag, value=False),
            EventActionSpec(type="set_flag", target=complete_flag, value=True),
            EventActionSpec(
                type="remove_item",
                target=lesson.actor,
                value=lesson.item,
            ),
            EventActionSpec(type="remove_unit", target=lesson.target),
            *lesson.completion_actions,
        ],
        priority=0,
    )
    return script, complete


def compile_failure_condition(unit: str, active_until_flag: str | None) -> str:
    clauses = [f"unit and unit.nid == {unit!r}"]
    if active_until_flag:
        clauses.append(f"not game.level_vars.get({active_until_flag!r}, False)")
    return " and ".join(f"({clause})" for clause in clauses)
