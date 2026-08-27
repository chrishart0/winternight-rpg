from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import yaml

from .asset_pipeline import generate_assets, generate_campaign_assets
from .build_report import file_inventory, load_current_smoke, write_report
from .campaign_lt_adapter import write_campaign_lt_project
from .lt_adapter import write_lt_project
from .models import CampaignBundle, MinimalSpec
from .semantic_validation import validate_campaign_semantics
from .static_analysis import analyze_project


def compile_project(
    spec: MinimalSpec,
    spec_path: Path,
    output: Path,
    engine_root: Path,
    engine_commit: str,
    build_root: Path,
) -> dict[str, object]:
    if Path("/tmp/lt-maker.lock").exists():
        raise RuntimeError("LT-Maker lock detected; close the editor before compiling")
    if output.exists():
        shutil.rmtree(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="winternight-assets-") as temp:
        assets = generate_assets(Path(temp), spec.assets.portraits)
        write_lt_project(spec, assets, output, engine_root, engine_commit)
    content_hash = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    analysis = analyze_project(output, engine_root)
    manifest = {
        "engine_commit": engine_commit,
        "schema_version": spec.schema_version,
        "content_hash": content_hash,
        "generated_files": [entry["path"] for entry in file_inventory(output)],
    }
    (output / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    smoke = load_current_smoke(build_root, output, engine_commit, content_hash)
    return write_report(
        build_root,
        output,
        engine_commit,
        spec.schema_version,
        content_hash,
        analysis=analysis,
        smoke=smoke,
        report_title=spec.project.title,
    )


def campaign_input_inventory(root: Path) -> list[dict[str, str]]:
    paths = [
        root / "design/campaign.yaml",
        root / "design/gameplay.yaml",
        root / "design/asset_manifest.yaml",
        root / "design/visual_bible.yaml",
        root / "source/characters.yaml",
        root / "source/locations.yaml",
        root / "source/story_beats.yaml",
        root / "source/adaptation_rules.yaml",
        *sorted((root / "design/maps").glob("*.yaml")),
        *sorted((root / "design/missions").glob("*.yaml")),
        *sorted((root / "design/scenes").rglob("*.yaml")),
    ]
    manifest = yaml.safe_load((root / "design/asset_manifest.yaml").read_text(encoding="utf-8"))
    repository = root.resolve()
    for asset in manifest.get("assets", []):
        source_path = asset.get("source_path")
        if not source_path:
            continue
        source = (root / source_path).resolve()
        if not source.is_relative_to(repository):
            raise ValueError(f"asset source escapes repository: {source}")
        paths.append(source)
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(set(paths))
    ]


def campaign_content_hash(inventory: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for entry in inventory:
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def compile_campaign_project(
    bundle: CampaignBundle,
    root: Path,
    output: Path,
    engine_root: Path,
    engine_commit: str,
    build_root: Path,
) -> dict[str, object]:
    if Path("/tmp/lt-maker.lock").exists():
        raise RuntimeError("LT-Maker lock detected; close the editor before compiling")
    validate_campaign_semantics(bundle)
    if output.exists():
        shutil.rmtree(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="winternight-campaign-assets-") as temp:
        assets = generate_campaign_assets(Path(temp), bundle, root)
        write_campaign_lt_project(bundle, assets, root, output, engine_root, engine_commit)
    inputs = campaign_input_inventory(root)
    content_hash = campaign_content_hash(inputs)
    analysis = analyze_project(output, engine_root)
    manifest = {
        "engine_commit": engine_commit,
        "schema_version": bundle.campaign.schema_version,
        "content_hash": content_hash,
        "inputs": inputs,
        "generated_files": [entry["path"] for entry in file_inventory(output)],
    }
    (output / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    smoke = load_current_smoke(build_root, output, engine_commit, content_hash)
    return write_report(
        build_root,
        output,
        engine_commit,
        bundle.campaign.schema_version,
        content_hash,
        analysis=analysis,
        smoke=smoke,
        report_title=bundle.campaign.title,
    )
