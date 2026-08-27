from __future__ import annotations

from collections import deque

from .models import CampaignBundle, DialogueSceneBeat, MapLayoutSpec, MissionSpec


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


def _region_targets(mission: MissionSpec, region_id: str) -> set[tuple[int, int]]:
    region = next(region for region in mission.regions if region.id == region_id)
    x, y = region.position
    width, height = region.size
    cells = {(cell_x, cell_y) for cell_y in range(y, y + height) for cell_x in range(x, x + width)}
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


def validate_campaign_semantics(bundle: CampaignBundle) -> dict[str, object]:
    errors: list[str] = []
    scene_ids = {scene.id for scene in bundle.scenes}
    item_ids = {item.id for item in bundle.gameplay.items}
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
        layout = map_by_id[mission.map.template]
        passable = _passable(layout, mission.map.variant)

        for unit in mission.units:
            if unit.position and unit.position not in passable:
                errors.append(f"mission {mission.id} unit {unit.id} starts on blocked terrain")
            if not unit.starts_on_map and not unit.group:
                errors.append(f"mission {mission.id} off-map unit {unit.id} lacks a group")
            if unit.group and unit.group not in group_ids:
                errors.append(f"mission {mission.id} unit {unit.id} has unknown group")

        for failure in mission.failure_conditions:
            if failure.unit and failure.unit not in unit_ids:
                errors.append(f"mission {mission.id} failure references unknown unit")

        triggers = {event.trigger.type for event in mission.events}
        if "level_start" not in triggers or "level_end" not in triggers:
            errors.append(f"mission {mission.id} requires level_start and level_end events")
        if not any(action.type == "win" for event in mission.events for action in event.actions):
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
            for action in event.actions:
                if action.type == "play_scene" and action.target not in scene_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown scene")
                if action.type == "spawn_group" and action.target not in group_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown group")
                if action.type in {"remove_unit", "mark_visited"} and action.target not in unit_ids:
                    errors.append(f"mission {mission.id} event {event.id} has unknown unit")
                if action.type in {"add_talk", "remove_talk"}:
                    if action.target not in unit_ids or action.value not in unit_ids:
                        errors.append(
                            f"mission {mission.id} event {event.id} has unknown talk unit"
                        )
                if action.type in {"give_item", "equip_item"} and action.value not in item_ids:
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

    if errors:
        raise CampaignSemanticError("; ".join(errors))
    return {
        "chapter_count": len(bundle.missions),
        "map_layout_count": len(bundle.maps),
        "scene_count": len(bundle.scenes),
        "reachability": reachability,
    }
