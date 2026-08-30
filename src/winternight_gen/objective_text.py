from __future__ import annotations

import re
from collections import Counter
from textwrap import wrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CharacterSpec, MissionSpec

BANNER_LINE_CHARACTER_LIMIT = 30
OBJECTIVE_LINE_CHARACTER_LIMIT = 16

# Level var the patched LT map HUD consumes once to blink the objective panel.
OBJECTIVE_FLASH_LEVEL_VAR = "_objective_flash"

# LT evaluates these display expressions while drawing the objective, so the
# native character budget applies to the drawn result, not the raw source.
_DISPLAY_EXPRESSION = re.compile(
    r"\{(?:v|var|e|eval|f|field|s|skill|i|item):[^{}]*\}"
)


def rendered_line(line: str) -> str:
    """Approximate one drawn objective line, one character per expression."""
    return _DISPLAY_EXPRESSION.sub("0", line)


def display_lines(text: str) -> list[str]:
    """Return LT objective lines with escaped display commas restored."""
    return [line.replace("{comma}", ",") for line in text.split(",")]


def _encoded_lines(lines: list[str]) -> str:
    return ",".join(line.replace(",", "{comma}") for line in lines)


def _wrapped(text: str) -> list[str]:
    return wrap(
        text,
        width=OBJECTIVE_LINE_CHARACTER_LIMIT,
        break_long_words=False,
        break_on_hyphens=False,
    )


def synthesize_loss_text(
    mission: MissionSpec, characters_by_id: dict[str, CharacterSpec]
) -> str:
    """Build compact, deduplicated loss-condition lines for LT's status screen."""
    placements = {unit.id: unit for unit in mission.units}
    protected_units: set[str] = set()
    entries: list[tuple[str, str]] = []

    for failure in mission.failure_conditions:
        if not failure.unit or failure.unit in protected_units:
            continue
        protected_units.add(failure.unit)
        placement = placements.get(failure.unit)
        if placement:
            entries.append(
                (characters_by_id[placement.character].name, placement.role)
            )

    counts = Counter(entries)
    protected_names: list[str] = []
    grouped_entries: list[tuple[str, str]] = []
    for entry in entries:
        if counts[entry] == 1:
            if entry[0] not in protected_names:
                protected_names.append(entry[0])
        elif entry not in grouped_entries:
            grouped_entries.append(entry)

    lines: list[str] = []
    if protected_names:
        if len(protected_names) == 1:
            named_condition = f"{protected_names[0]} must survive"
        else:
            named_condition = (
                f"{', '.join(protected_names[:-1])} and {protected_names[-1]} must survive"
            )
        lines.extend(_wrapped(named_condition))

    for name, role in grouped_entries:
        count = counts[(name, role)]
        total = sum(
            characters_by_id[unit.character].name == name and unit.role == role
            for unit in mission.units
        )
        prefix = "All " if count == total else ""
        noun = name.lower() if count == 1 else f"{name.lower()}s"
        lines.extend(_wrapped(f"{prefix}{count} {noun} must survive"))

    return _encoded_lines(lines)
