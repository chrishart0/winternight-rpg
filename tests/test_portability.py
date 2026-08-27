from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from winternight_gen.build_report import tree_hash
from winternight_gen.campaign_compiler import compile_campaign_project
from winternight_gen.cli import _validated_pack_output
from winternight_gen.mechanics import verify_search_escape_sequence
from winternight_gen.models import CampaignBundle
from winternight_gen.smoke import smoke_project
from winternight_gen.title_flow import verify_title_new_game_flow
from winternight_gen.validate import validate_campaign

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor/lt-maker"
FIXTURE_ROOT = ROOT / "tests/fixtures/signal-lantern"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _engine_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", str(ENGINE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def test_second_story_compiles_without_winternight_assumptions(tmp_path, compiled_campaign) -> None:
    bundle = validate_campaign(FIXTURE_ROOT)
    first = tmp_path / "first" / "signal-lantern.ltproj"
    second = tmp_path / "second" / "signal-lantern.ltproj"
    compile_campaign_project(
        bundle,
        FIXTURE_ROOT,
        first,
        ENGINE_ROOT,
        _engine_commit(),
        first.parent,
    )
    compile_campaign_project(
        bundle,
        FIXTURE_ROOT,
        second,
        ENGINE_ROOT,
        _engine_commit(),
        second.parent,
    )

    assert tree_hash(first) == tree_hash(second)
    assert (first.parent / "REPORT.md").read_text(encoding="utf-8").startswith(
        "# Signal Lantern build report"
    )
    parties = json.loads((first / "game_data/parties.json").read_text(encoding="utf-8"))
    levels = json.loads((first / "game_data/levels.json").read_text(encoding="utf-8"))
    assert parties == [
        {
            "nid": "signal_lantern_party",
            "name": "Relay Keepers",
            "leader": "mara",
        }
    ]
    assert [(level["nid"], level["party"]) for level in levels] == [
        ("sl00_relay", "signal_lantern_party")
    ]
    serialized = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((first / "game_data").glob("*.json"))
    ).lower()
    for forbidden in ("rand", "tam", "trolloc", "story_guardian", "winternight"):
        assert forbidden not in serialized

    assert (first / "ASSET_PROVENANCE.yaml").read_bytes() == (
        FIXTURE_ROOT / "design/asset_manifest.yaml"
    ).read_bytes()
    assert _sha256(first / "resources/custom_sprites/logo.png") != _sha256(
        compiled_campaign / "resources/custom_sprites/logo.png"
    )

    smoke = smoke_project(first, ENGINE_ROOT)
    assert smoke["levels_initialized"] == ["sl00_relay"]
    assert smoke["all_levels_initialized"] is True
    assert smoke["all_scenes_executed"] is True
    assert smoke["all_victory_commands_executed"] is True
    mechanics = verify_search_escape_sequence(
        first,
        ENGINE_ROOT,
        "sl00_relay",
        "mara",
        "signal_lens",
        "relay_exit",
    )
    assert mechanics["early_escape_blocked"] is True
    assert mechanics["search_then_escape_wins"] is True
    title = verify_title_new_game_flow(
        first,
        ENGINE_ROOT,
        tmp_path / "signal-title-flow.json",
        bundle.campaign.entry_chapter,
    )
    assert title["first_level"] == "sl00_relay"
    assert title["reached_first_chapter"] is True


def test_party_leader_must_name_an_entry_mission_unit() -> None:
    raw = validate_campaign(FIXTURE_ROOT).model_dump(mode="json")
    raw["missions"][0]["units"][0]["id"] = "mara_slot"

    with pytest.raises(ValidationError, match="party leader must be a player unit"):
        CampaignBundle.model_validate(raw)


def test_entry_chapter_must_be_first_in_chapter_order() -> None:
    raw = validate_campaign(ROOT).model_dump(mode="json")
    raw["campaign"]["entry_chapter"] = raw["campaign"]["chapter_order"][1]

    with pytest.raises(ValidationError, match="entry chapter must be first"):
        CampaignBundle.model_validate(raw)


def test_compile_pack_rejects_broad_or_untyped_output_targets(tmp_path) -> None:
    with pytest.raises(ValueError, match="must end in .ltproj"):
        _validated_pack_output(FIXTURE_ROOT, ROOT)
    dangerous_ancestor = tmp_path / "ancestor.ltproj"
    nested_content = dangerous_ancestor / "content"
    nested_content.mkdir(parents=True)
    with pytest.raises(ValueError, match="unsafe compile-pack output"):
        _validated_pack_output(nested_content, dangerous_ancestor)
