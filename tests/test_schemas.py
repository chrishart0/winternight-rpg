from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from winternight_gen.models import MinimalSpec


def test_phase_zero_spec_resolves_all_references(spec):
    assert spec.project.level_id == "minimal_chapter"
    assert {unit.team for unit in spec.units} == {"player", "enemy"}
    assert spec.victory.defeated_unit == "automaton"
    assert spec.failure.defeated_unit == "guide"


def test_duplicate_unit_id_is_rejected():
    spec_path = Path(__file__).parents[1] / "design" / "minimal.yaml"
    raw = yaml.safe_load(spec_path.read_text())
    broken = copy.deepcopy(raw)
    broken["units"][1]["id"] = broken["units"][0]["id"]
    with pytest.raises(ValidationError, match="unit IDs must be unique"):
        MinimalSpec.model_validate(broken)


def test_out_of_bounds_spawn_is_rejected():
    spec_path = Path(__file__).parents[1] / "design" / "minimal.yaml"
    raw = yaml.safe_load(spec_path.read_text())
    raw["units"][0]["position"] = [999, 999]
    with pytest.raises(ValidationError, match="outside map bounds"):
        MinimalSpec.model_validate(raw)
