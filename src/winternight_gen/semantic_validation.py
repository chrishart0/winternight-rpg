from __future__ import annotations

from collections import deque
from warnings import warn

from .models import CampaignBundle, DialogueSceneBeat, MapLayoutSpec, MissionSpec
from .objective_text import (
    BANNER_LINE_CHARACTER_LIMIT,
    OBJECTIVE_LINE_CHARACTER_LIMIT,
    display_lines,
    rendered_line,
    synthesize_loss_text,
)


class CampaignSemanticError(RuntimeError):
    pass


def _passable(layout: MapLayoutSpec, variant_id: str) -> set[tuple[int, int]]:
    variant = next(variant for variant in layout.variants if variant.id == variant_id)
    return {
        (x, y)
        for y, row in enumerate(variant.rows)
        for x, symbol in enumerate(row)
        if not layout.legend[symbol].blocks_movement
    }


def _reachable(
    start: tuple[int, int],
    targets: set[tuple[int, int]],
    passable: set[tuple[int, int]],
) -> bool:
    if start not in passable:
        return False
    queue = deque([start])
    visited = {start}
    while queue:
        current = queue.popleft()
        if current in targets:
            return True
        x, y = current
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if neighbor in passable and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False


def _region_cells(mission: MissionSpec, region_id: str) -> set[tuple[int, int]]:
    region = next(region for region in mission.regions if region.id == region_id)
    x, y = region.position
    width, height = region.size
    return {
        (cell_x, cell_y)
        for cell_y in range(y, y + height)
        for cell_x in range(x, x + width)
    }


def _region_targets(mission: MissionSpec, region_id: str) -> set[tuple[int, int]]:
    cells = _region_cells(mission, region_id)
    adjacent = {
        neighbor
        for cell_x, cell_y in cells
        for neighbor in (
            (cell_x - 1, cell_y),
            (cell_x + 1, cell_y),
            (cell_x, cell_y - 1),
            (cell_x, cell_y + 1),
        )
    }
    return cells | adjacent


def _objective_length_warnings(
    mission_id: str, field: str, text: str, limit: int
) -> list[str]:
    return [
        (
            f"mission {mission_id} {field} line {index} has {width} characters; "
            f"the native 240x160 budget is {limit}: {line!r}"
        )
        for index, line in enumerate(display_lines(text), start=1)
        if (width := len(rendered_line(line))) > limit
    ]


def validate_campaign_semantics(bundle: CampaignBundle) -> dict[str, object]:
    errors: list[str] = []
    objective_warnings: list[str] = []
    scene_ids = {scene.id for scene in bundle.scenes}
    item_ids = {item.id for item in bundle.gameplay.items}
    ai_ids = {profile.id for profile in bundle.gameplay.ai_profiles}
    items_by_id = {item.id: item for item in bundle.gameplay.items}
    weapon_types = set(bundle.gameplay.weapon_types)
    characters_by_id = {character.id: character for character in bundle.characters.characters}
    map_by_id = {layout.id: layout for layout in bundle.maps}

    for character in bundle.characters.characters:
        combat = character.combat
        for weapon_type in {combat.weapon_type, *combat.additional_weapon_types}:
            if weapon_type not in weapon_types:
                errors.append(f"character {character.id} uses unknown weapon type {weapon_type}")
        for item_id in combat.starting_items:
            if item_id not in item_ids:
                errors.append(f"character {character.id} has unknown starting item {item_id}")
        for promotion in combat.promotions:
            for weapon_type in promotion.additional_weapon_types:
                if weapon_type not in weapon_types:
                    errors.append(
                        f"character {character.id} promotion {promotion.class_id} "
                        f"uses unknown weapon type {weapon_type}"
                    )

    for scene in bundle.scenes:
        for beat in scene.beats:
            if isinstance(beat, DialogueSceneBeat):
                illegal = sorted(set(beat.text) & set(";{}#\n\r"))
                if illegal:
                    errors.append(f"scene {scene.id} dialogue contains unsafe characters {illegal}")

    reachability: dict[str, dict[str, bool]] = {}
    for mission in bundle.missions:
        unit_ids = {unit.id for unit in mission.units}
        units_by_id = {unit.id: unit for unit in mission.units}
        region_ids = {region.id for region in mission.regions}
        group_ids = {reinforcement.id for reinforcement in mission.reinforcements}
        guide_ids = {guide.id for guide in mission.guide_paths}
        layout = map_by_id[mission.map.template]
        variant = next(
            variant for variant in layout.variants if variant.id == mission.map.variant
        )
        map_layer_ids = {layer.id for layer in variant.layers}
        duplicate_layer_ids = guide_ids & map_layer_ids
        if duplicate_layer_ids:
            errors.append(
                f"mission {mission.id} reuses map layer IDs {sorted(duplicate_layer_ids)}"
            )
        layer_ids = guide_ids | map_layer_ids
        passable = _passable(layout, mission.map.variant)
        for field, text, limit in (
            ("initial banner", mission.objective.display_text, BANNER_LINE_CHARACTER_LIMIT),
            ("initial win", mission.objective.display_text, OBJECTIVE_LINE_CHARACTER_LIMIT),
            (
                "synthesized loss",
                synthesize_loss_text(mission, characters_by_id),
                OBJECTIVE_LINE_CHARACTER_LIMIT,
            ),
        ):
            objective_warnings.extend(
                _objective_length_warnings(mission.id, field, text, limit)
            )

        for unit in mission.units:
            if unit.position and unit.position not in passable:
                errors.append(f"mission {mission.id} unit {unit.id} starts on blocked terrain")
            if not unit.starts_on_map and not unit.group:
                errors.append(f"mission {mission.id} off-map unit {unit.id} lacks a group")
            if unit.group and unit.group not in group_ids:
                errors.append(f"mission {mission.id} unit {unit.id} has unknown group")
        for region in mission.regions:
            unknown_units = set(region.allowed_units) - unit_ids
            if unknown_units:
                errors.append(
                    f"mission {mission.id} region {region.id} allows unknown units "
                    f"{sorted(unknown_units)}"
                )
        for guide in mission.guide_paths:
            invalid_points = [point for point in guide.points if point not in passable]
            if invalid_points:
                errors.append(
                    f"mission {mission.id} guide {guide.id} crosses blocked or "
                    f"out-of-bounds tiles {invalid_points}"
                )
            destination = next(
                (
                    region
                    for region in mission.regions
                    if region.id == guide.destination_region
                ),
                None,
            )
            if destination is None:
                errors.append(
                    f"mission {mission.id} guide {guide.id} has unknown destination region"
                )
            elif guide.points[-1] not in _region_cells(
                mission, guide.destination_region
            ):
                errors.append(
                    f"mission {mission.id} guide {guide.id} does not end in "
                    f"destination region {guide.destination_region}"
                )

        for failure in mission.failure_conditions:
            if failure.unit and failure.unit not in unit_ids:
                errors.append(f"mission {mission.id} failure references unknown unit")
            if failure.failure_scene and failure.failure_scene not in scene_ids:
                errors.append(
                    f"mission {mission.id} failure references unknown scene "
                    f"{failure.failure_scene}"
                )
        triggers = {event.trigger.type for event in mission.events}
        if "level_start" not in triggers or "level_end" not in triggers:
            errors.append(f"mission {mission.id} requires level_start and level_end events")
        mission_actions = [
            *(action for event in mission.events for action in event.actions),
            *(
                action
                for lesson in mission.scripted_forecast_lessons
                for action in lesson.completion_actions
            ),
        ]
        if not any(action.type == "win" for action in mission_actions):
            errors.append(f"mission {mission.id} has no win action")
        if not any(
            action.type == "play_scene" and action.target == mission.intro_scene
            for event in mission.events
            for action in event.actions
        ):
            errors.append(f"mission {mission.id} does not invoke its intro scene")
        if not any(
            action.type == "play_scene" and action.target == mission.outro_scene
            for event in mission.events
            for action in event.actions
        ):
            errors.append(f"mission {mission.id} does not invoke its outro scene")

        for event in mission.events:
            trigger = event.trigger
            if trigger.unit and trigger.unit not in unit_ids:
                errors.append(f"mission {mission.id} event {event.id} has unknown trigger unit")
            if trigger.unit2 and trigger.unit2 not in unit_ids:
                errors.append(f"mission {mission.id} event {event.id} has unknown second unit")
            if trigger.region and trigger.region not in region_ids:
                errors.append(f"mission {mission.id} event {event.id} has unknown region")
            if trigger.item and trigger.item not in item_ids:
                errors.append(
                    f"mission {mission.id} event {event.id} has unknown trigger item"
                )
            if event.condition.unit_in_region:
                if event.condition.unit_in_region.unit not in unit_ids:
                    errors.append(
                        f"mission {mission.id} event {event.id} has unknown condition unit"
                    )
                if event.condition.unit_in_region.region not in region_ids:
                    errors.append(
                        f"mission {mission.id} event {event.id} has unknown condition region"
                    )
            if event.condition.trigger_unit_in_region:
                condition_region = event.condition.trigger_unit_in_region.region
                if condition_region not in region_ids:
                    errors.append(
                        f"mission {mission.id} event {event.id} has unknown "
                        f"trigger-unit condition region"
                    )
            for action in event.actions:
                if action.type == "change_objective" and isinstance(action.value, str):
                    if action.target in {"simple", "both"}:
                        objective_warnings.extend(
                            _objective_length_warnings(
                                mission.id,
                                f"event {event.id} banner",
                                action.value,
                                BANNER_LINE_CHARACTER_LIMIT,
                            )
                        )
                    if action.target in {"win", "loss", "both"}:
                        objective_warnings.extend(
                            _objective_length_warnings(
                                mission.id,
                                f"event {event.id} {action.target}",
                                action.value,
                                OBJECTIVE_LINE_CHARACTER_LIMIT,
                            )
                        )
                if action.type == "play_scene" and action.target not in scene_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown scene")
                if action.type == "spawn_group" and action.target not in group_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown group")
                if (
                    action.type in {"activate_region", "deactivate_region"}
                    and action.target not in region_ids
                ):
                    errors.append(f"mission {mission.id} event {event.id} has unknown region")
                if action.type in {"show_layer", "hide_layer"} and action.target not in layer_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown map layer")
                if action.type == "highlight_target" and action.target not in unit_ids | region_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown target")
                if (
                    action.type
                    in {
                        "remove_unit",
                        "move_unit",
                        "mark_visited",
                        "refresh_unit",
                        "give_item",
                        "set_current_hp",
                        "equip_item",
                        "remove_item",
                        "change_team",
                        "remove_tag",
                    }
                    and action.target not in unit_ids
                ):
                    errors.append(f"mission {mission.id} event {event.id} has unknown unit")
                if action.type == "move_unit" and isinstance(action.value, str):
                    destination = tuple(int(value) for value in action.value.split(","))
                    if destination not in passable:
                        errors.append(
                            f"mission {mission.id} event {event.id} moves a unit "
                            f"to blocked or out-of-bounds tile {destination}"
                        )
                if action.type == "pair_up" and (
                    action.target not in unit_ids or action.value not in unit_ids
                ):
                    errors.append(
                        f"mission {mission.id} event {event.id} has unknown pair-up unit"
                    )
                if action.type == "separate" and action.target not in unit_ids:
                    errors.append(
                        f"mission {mission.id} event {event.id} has unknown separate unit"
                    )
                if action.type == "change_ai":
                    if action.target not in unit_ids:
                        errors.append(f"mission {mission.id} event {event.id} has unknown unit")
                    if action.value not in ai_ids:
                        errors.append(f"mission {mission.id} event {event.id} has unknown AI")
                if action.type in {"add_talk", "remove_talk"}:
                    if action.target not in unit_ids or action.value not in unit_ids:
                        errors.append(
                            f"mission {mission.id} event {event.id} has unknown talk unit"
                        )
                if (
                    action.type in {"give_item", "equip_item", "remove_item"}
                    and action.value not in item_ids
                ):
                    errors.append(f"mission {mission.id} event {event.id} has unknown item")
                if (
                    action.type == "equip_item"
                    and action.target in units_by_id
                    and action.value in items_by_id
                ):
                    character = characters_by_id[units_by_id[action.target].character]
                    item = items_by_id[action.value]
                    usable = {
                        character.combat.weapon_type,
                        *character.combat.additional_weapon_types,
                    }
                    if item.weapon_type and item.weapon_type not in usable:
                        errors.append(
                            f"mission {mission.id} event {event.id} equips "
                            f"{action.value} on incompatible unit {action.target}"
                        )

        mission_reachability: dict[str, bool] = {}
        objective_region = mission.objective.region
        if objective_region:
            if objective_region not in region_ids:
                errors.append(f"mission {mission.id} objective references unknown region")
            else:
                targets = _region_targets(mission, objective_region) & passable
                relevant_units = [
                    unit
                    for unit in mission.units
                    if unit.starts_on_map
                    and unit.position
                    and (
                        unit.id == mission.objective.unit
                        or (mission.objective.type == "defend_rescue" and unit.role == "civilian")
                    )
                ]
                for unit in relevant_units:
                    reachable = _reachable(unit.position, targets, passable)
                    mission_reachability[f"{unit.id}->{objective_region}"] = reachable
                    if not reachable:
                        errors.append(
                            f"mission {mission.id} objective is unreachable for {unit.id}"
                        )
        reachability[mission.id] = mission_reachability
    for message in objective_warnings:
        warn(message, stacklevel=2)

    if errors:
        raise CampaignSemanticError("; ".join(errors))
    return {
        "chapter_count": len(bundle.missions),
        "map_layout_count": len(bundle.maps),
        "scene_count": len(bundle.scenes),
        "reachability": reachability,
        "warnings": objective_warnings,
    }
