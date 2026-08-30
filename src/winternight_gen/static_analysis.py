from __future__ import annotations

import json
import sys
from pathlib import Path

from .lt_runtime import generated_component_system


class StaticAnalysisError(RuntimeError):
    pass


def _import_lt(engine_root: Path) -> None:
    engine = str(engine_root.resolve())
    if engine not in sys.path:
        sys.path.insert(0, engine)


def analyze_project(project: Path, engine_root: Path) -> dict[str, object]:
    _import_lt(engine_root)
    with generated_component_system(engine_root):
        from app.data.database.database import Database
        from app.data.resources.resources import Resources
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.events.event_commands import parse_script_to_commands, parse_text_to_command

        metadata = json.loads((project / "metadata.json").read_text(encoding="utf-8"))
        if metadata["serialization_version"] != CURRENT_SERIALIZATION_VERSION:
            raise StaticAnalysisError("serialization version does not match pinned engine")
        resources = Resources()
        resources.load(project, CURRENT_SERIALIZATION_VERSION)
        database = Database()
        database.load(project, CURRENT_SERIALIZATION_VERSION)

    errors: list[str] = []
    level_ids = database.levels.keys()
    if len(level_ids) != len(set(level_ids)):
        errors.append("duplicate level IDs")
    unit_ids = database.units.keys()
    if len(unit_ids) != len(set(unit_ids)):
        errors.append("duplicate unit IDs")
    event_ids = [event.nid for event in database.events]
    if len(event_ids) != len(set(event_ids)):
        errors.append("duplicate event IDs")
    combat_level_ids = set(metadata.get("combat_levels", level_ids))
    zero_enemy_level_ids = set(metadata.get("zero_enemies_by_intent", []))

    parsed_events: dict[str, list[str]] = {}
    for event in database.events:
        commands = parse_script_to_commands(event.source)
        parsed_events[event.nid] = [command.nid for command in commands]
        if not commands:
            errors.append(f"event {event.nid} has no parseable commands")
        for line_number, line in enumerate(event.source.splitlines(), start=1):
            command, _ = parse_text_to_command(line, strict=True)
            if command is None:
                errors.append(f"event {event.nid} line {line_number} is invalid: {line}")
            elif command.nid == "sound":
                sound_nid = command.parameters.get("Sound")
                if sound_nid not in resources.sfx:
                    errors.append(
                        f"event {event.nid} line {line_number} references missing SFX {sound_nid}"
                    )
    if not any("win_game" in commands for commands in parsed_events.values()):
        errors.append("no victory command")
    if not any("lose_game" in commands for commands in parsed_events.values()):
        errors.append("no loss command")

    for level in database.levels:
        if level.tilemap not in resources.tilemaps:
            errors.append(f"level {level.nid} references missing tilemap {level.tilemap}")
        tilemap = resources.tilemaps.get(level.tilemap)
        occupied: set[tuple[int, int]] = set()
        teams: set[str] = set()
        for level_unit in level.units:
            if level_unit.nid not in database.units:
                errors.append(f"level {level.nid} references missing unit {level_unit.nid}")
            if level_unit.starting_position is not None:
                position = tuple(level_unit.starting_position)
                if position in occupied:
                    errors.append(f"level {level.nid} has overlapping units at {position}")
                occupied.add(position)
                if not tilemap.check_bounds(position):
                    errors.append(f"level {level.nid} unit {level_unit.nid} is out of bounds")
            teams.add(level_unit.team)
        if "player" not in teams:
            errors.append(f"level {level.nid} lacks a player unit")
        if (
            level.nid in combat_level_ids
            and level.nid not in zero_enemy_level_ids
            and "enemy" not in teams
        ):
            errors.append(f"combat level {level.nid} lacks an enemy unit")
        level_events = [event for event in database.events if event.level_nid == level.nid]
        level_triggers = {event.trigger for event in level_events}
        for required in ("level_start", "level_end", "unit_death"):
            if required not in level_triggers:
                errors.append(f"level {level.nid} missing required trigger {required}")
        if not any("win_game" in parsed_events[event.nid] for event in level_events):
            errors.append(f"level {level.nid} has no victory command")
        if not any("lose_game" in parsed_events[event.nid] for event in level_events):
            errors.append(f"level {level.nid} has no loss command")

    for unit in database.units:
        if unit.klass not in database.classes:
            errors.append(f"unit {unit.nid} references missing class {unit.klass}")
        if unit.portrait_nid not in resources.portraits:
            errors.append(f"unit {unit.nid} references missing portrait {unit.portrait_nid}")
        for item_nid, _ in unit.starting_items:
            if item_nid not in database.items:
                errors.append(f"unit {unit.nid} references missing item {item_nid}")
    for klass in database.classes:
        if klass.map_sprite_nid not in resources.map_sprites:
            errors.append(f"class {klass.nid} references missing map sprite")

    expected_dimensions = {
        "background": (240, 160),
        "portrait": (160, 112),
        "stand": (192, 144),
        "move": (192, 160),
    }
    from PIL import Image

    for background in resources.panoramas:
        with Image.open(background.full_path) as image:
            if image.size != expected_dimensions["background"]:
                errors.append(f"background {background.nid} dimensions are invalid")
    for portrait in resources.portraits:
        with Image.open(portrait.full_path) as image:
            if image.size != expected_dimensions["portrait"]:
                errors.append(f"portrait {portrait.nid} dimensions are invalid")
    for sprite in resources.map_sprites:
        with Image.open(sprite.stand_full_path) as image:
            if image.size != expected_dimensions["stand"]:
                errors.append("standing sprite dimensions are invalid")
        with Image.open(sprite.move_full_path) as image:
            if image.size != expected_dimensions["move"]:
                errors.append("moving sprite dimensions are invalid")

    if errors:
        raise StaticAnalysisError("; ".join(errors))
    return {
        "levels": level_ids,
        "units": unit_ids,
        "events": parsed_events,
        "resources": {
            "portraits": resources.portraits.keys(),
            "backgrounds": resources.panoramas.keys(),
            "tilemaps": resources.tilemaps.keys(),
            "map_sprites": resources.map_sprites.keys(),
            "music": resources.music.keys(),
            "sfx": resources.sfx.keys(),
        },
    }
