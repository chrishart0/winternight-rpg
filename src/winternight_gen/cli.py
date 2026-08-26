from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .build_report import tree_hash, write_report
from .campaign_compiler import (
    campaign_content_hash,
    campaign_input_inventory,
    compile_campaign_project,
    compile_project,
)
from .editor_runner import run_editor
from .game_runner import play_project
from .input_playthrough import verify_input_playthrough
from .interactive_flows import verify_game_over_recovery, verify_suspend_continue
from .journey import verify_campaign_journey
from .mechanics import verify_campaign_mechanics
from .packager import PACKAGE_NAME, package_private_build, smoke_package
from .smoke import smoke_project
from .static_analysis import analyze_project
from .tam_survival import verify_tam_survives_lethal_combat
from .title_flow import verify_title_new_game_flow
from .validate import export_campaign_schemas, export_schema, validate_campaign, validate_spec
from .visual_capture import capture_all_levels, capture_level_frame

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "design" / "minimal.yaml"
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"
BUILD_ROOT = ROOT / "build"
PROJECT_PATH = BUILD_ROOT / "minimal.ltproj"
CAMPAIGN_PROJECT_PATH = BUILD_ROOT / "winternight.ltproj"
SCHEMA_PATH = ROOT / "schemas" / "minimal.schema.json"
LOCK_PATH = ROOT / "engine.lock"


def _engine_lock() -> dict[str, object]:
    values: dict[str, object] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        key, raw_value = raw_line.split("=", 1)
        values[key.strip()] = json.loads(raw_value.strip())
    return values


def _verify_engine(lock: dict[str, object]) -> None:
    if not (ENGINE_ROOT / ".git").exists():
        raise RuntimeError("LT-Maker submodule is missing; run make bootstrap")
    actual = subprocess.check_output(
        ["git", "-C", str(ENGINE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != lock["commit"]:
        raise RuntimeError(f"LT commit mismatch: expected {lock['commit']}, found {actual}")


def _compile_to(output: Path, build_root: Path) -> dict[str, object]:
    spec = validate_spec(SPEC_PATH)
    lock = _engine_lock()
    _verify_engine(lock)
    return compile_project(
        spec,
        SPEC_PATH,
        output,
        ENGINE_ROOT,
        str(lock["commit"]),
        build_root,
    )


def _compile_campaign_to(output: Path, build_root: Path) -> dict[str, object]:
    bundle = validate_campaign(ROOT)
    lock = _engine_lock()
    _verify_engine(lock)
    return compile_campaign_project(
        bundle,
        ROOT,
        output,
        ENGINE_ROOT,
        str(lock["commit"]),
        build_root,
    )


def command_validate() -> None:
    spec = validate_spec(SPEC_PATH)
    campaign = validate_campaign(ROOT)
    lock = _engine_lock()
    _verify_engine(lock)
    export_schema(SCHEMA_PATH)
    export_campaign_schemas(ROOT / "schemas")
    print(
        f"valid: fixture schema {spec.schema_version}, campaign schema "
        f"{campaign.campaign.schema_version}, {len(campaign.missions)} chapters, "
        f"engine {lock['commit']}"
    )


def command_compile() -> None:
    report = _compile_campaign_to(CAMPAIGN_PROJECT_PATH, BUILD_ROOT)
    print(
        f"compiled: {CAMPAIGN_PROJECT_PATH} "
        f"({len(report['generated_files'])} files)"
    )


def command_smoke() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    campaign = validate_campaign(ROOT)
    lock = _engine_lock()
    analysis = analyze_project(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT)
    smoke = smoke_project(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT)
    content_hash = campaign_content_hash(campaign_input_inventory(ROOT))
    write_report(
        BUILD_ROOT,
        CAMPAIGN_PROJECT_PATH,
        str(lock["commit"]),
        campaign.campaign.schema_version,
        content_hash,
        analysis,
        smoke,
    )
    print(json.dumps(smoke, sort_keys=True))


def command_report() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        raise RuntimeError("build/winternight.ltproj does not exist; run compile first")
    campaign = validate_campaign(ROOT)
    lock = _engine_lock()
    analysis = analyze_project(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT)
    content_hash = campaign_content_hash(campaign_input_inventory(ROOT))
    report_path = BUILD_ROOT / "report.json"
    existing = json.loads(report_path.read_text()) if report_path.exists() else {}
    report = write_report(
        BUILD_ROOT,
        CAMPAIGN_PROJECT_PATH,
        str(lock["commit"]),
        campaign.campaign.schema_version,
        content_hash,
        analysis,
        existing.get("smoke", {}),
    )
    print(f"report: {BUILD_ROOT / 'REPORT.md'} ({report['project_tree_hash']})")


def command_editor(*, smoke: bool = False) -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = run_editor(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT, smoke=smoke)
    if smoke:
        campaign = validate_campaign(ROOT)
        lock = _engine_lock()
        analysis = analyze_project(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT)
        report_path = BUILD_ROOT / "report.json"
        existing = json.loads(report_path.read_text()) if report_path.exists() else {}
        smoke_evidence = dict(existing.get("smoke", {}))
        smoke_evidence.update(result)
        write_report(
            BUILD_ROOT,
            CAMPAIGN_PROJECT_PATH,
            str(lock["commit"]),
            campaign.campaign.schema_version,
            campaign_content_hash(campaign_input_inventory(ROOT)),
            analysis,
            smoke_evidence,
        )
    print(json.dumps(result, sort_keys=True))


def command_play() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    play_project(CAMPAIGN_PROJECT_PATH, ENGINE_ROOT)


def command_capture(args: argparse.Namespace) -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    if args.command in {"capture-frame", "capture-scene"}:
        if not args.level or not args.output:
            raise ValueError(f"{args.command} requires --level and --output")
        if args.command == "capture-scene" and not args.scene:
            raise ValueError("capture-scene requires --scene")
        capture_level_frame(
            CAMPAIGN_PROJECT_PATH,
            ENGINE_ROOT,
            args.level,
            Path(args.output),
            skip_intro=args.skip_intro,
            scene_id=args.scene,
        )
        return
    campaign = validate_campaign(ROOT)
    result = capture_all_levels(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        campaign.campaign.chapter_order,
        BUILD_ROOT / "evidence",
    )
    print(json.dumps(result, sort_keys=True))


def command_journey() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    campaign = validate_campaign(ROOT)
    result = verify_campaign_journey(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        campaign.campaign.chapter_order,
        BUILD_ROOT / "evidence" / "journey.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_mechanics() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = verify_campaign_mechanics(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        BUILD_ROOT / "evidence" / "mechanics.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_title_flow() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = verify_title_new_game_flow(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        BUILD_ROOT / "evidence" / "title_flow.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_tam_survival() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = verify_tam_survives_lethal_combat(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        BUILD_ROOT / "evidence" / "tam_survival.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_input_playthrough() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    campaign = validate_campaign(ROOT)
    result = verify_input_playthrough(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        campaign.campaign.chapter_order,
        BUILD_ROOT / "evidence" / "input_playthrough.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_suspend_continue() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = verify_suspend_continue(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        BUILD_ROOT / "evidence" / "suspend_continue.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_game_over_recovery() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = verify_game_over_recovery(
        CAMPAIGN_PROJECT_PATH,
        ENGINE_ROOT,
        BUILD_ROOT / "evidence" / "game_over_recovery.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_package() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    result = package_private_build(ROOT, CAMPAIGN_PROJECT_PATH, ENGINE_ROOT, ROOT / "dist")
    print(json.dumps(result, sort_keys=True))


def command_package_smoke() -> None:
    archive = ROOT / "dist" / f"{PACKAGE_NAME}.tar.gz"
    if not archive.exists():
        command_package()
    result = smoke_package(
        archive,
        str(_engine_lock()["commit"]),
        BUILD_ROOT / "evidence" / "package_smoke.json",
    )
    print(json.dumps(result, sort_keys=True))


def command_determinism() -> None:
    if not CAMPAIGN_PROJECT_PATH.exists():
        command_compile()
    baseline = tree_hash(CAMPAIGN_PROJECT_PATH)
    with tempfile.TemporaryDirectory(prefix="winternight-determinism-") as temp:
        temp_root = Path(temp)
        candidate = temp_root / "winternight.ltproj"
        _compile_campaign_to(candidate, temp_root)
        rebuilt = tree_hash(candidate)
    if baseline != rebuilt:
        raise RuntimeError(f"non-deterministic build: {baseline} != {rebuilt}")
    print(f"deterministic: {baseline}")


def command_clean() -> None:
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)
    for path in (ROOT / ".pytest_cache", ROOT / ".ruff_cache"):
        if path.exists():
            shutil.rmtree(path)
    print("clean")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="winternight")
    parser.add_argument(
        "command",
        choices=(
            "validate",
            "compile",
            "smoke",
            "editor-smoke",
            "editor",
            "play",
            "capture",
            "capture-frame",
            "capture-scene",
            "journey",
            "mechanics",
            "title-flow",
            "tam-survival",
            "input-playthrough",
            "suspend-continue",
            "game-over-recovery",
            "package",
            "package-smoke",
            "report",
            "determinism",
            "clean",
        ),
    )
    parser.add_argument("--level")
    parser.add_argument("--output")
    parser.add_argument("--scene")
    parser.add_argument("--skip-intro", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    commands = {
        "validate": command_validate,
        "compile": command_compile,
        "smoke": command_smoke,
        "editor-smoke": lambda: command_editor(smoke=True),
        "editor": command_editor,
        "play": command_play,
        "journey": command_journey,
        "mechanics": command_mechanics,
        "title-flow": command_title_flow,
        "tam-survival": command_tam_survival,
        "input-playthrough": command_input_playthrough,
        "suspend-continue": command_suspend_continue,
        "game-over-recovery": command_game_over_recovery,
        "package": command_package,
        "package-smoke": command_package_smoke,
        "report": command_report,
        "determinism": command_determinism,
        "clean": command_clean,
    }
    if args.command in {"capture", "capture-frame", "capture-scene"}:
        command_capture(args)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
