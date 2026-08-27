from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_inventory(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for entry in file_inventory(root):
        digest.update(entry["path"].encode())
        digest.update(b"\0")
        digest.update(entry["sha256"].encode())
        digest.update(b"\n")
    return digest.hexdigest()


def load_current_smoke(
    build_root: Path,
    project: Path,
    engine_commit: str,
    content_hash: str,
) -> dict[str, object]:
    """Return smoke evidence only when it is bound to this exact build."""
    report_path = build_root / "report.json"
    if not report_path.exists() or not project.exists():
        return {}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    smoke = report.get("smoke") or {}
    if not isinstance(smoke, dict):
        return {}
    current_tree = tree_hash(project)
    current_manifest = sha256(project / "build_manifest.json")
    if not (
        report.get("engine_commit") == engine_commit
        and report.get("content_hash") == content_hash
        and report.get("project_tree_hash") == current_tree
        and smoke.get("project_tree_hash") == current_tree
        and smoke.get("project_manifest_sha256") == current_manifest
    ):
        return {}
    return smoke


def write_report(
    build_root: Path,
    project: Path,
    engine_commit: str,
    schema_version: str,
    content_hash: str,
    analysis: dict[str, object] | None = None,
    smoke: dict[str, object] | None = None,
    report_title: str = "Project",
) -> dict[str, object]:
    inventory = file_inventory(project)
    evidence_root = build_root / "evidence"
    evidence_inventory = file_inventory(evidence_root) if evidence_root.exists() else []
    verification: dict[str, object] = {}
    stale_verification: dict[str, object] = {}
    current_tree_hash = tree_hash(project)
    current_manifest_hash = sha256(project / "build_manifest.json")
    smoke_evidence = dict(smoke or {})
    stale_smoke: dict[str, object] = {}
    if smoke_evidence and not (
        smoke_evidence.get("project_tree_hash") == current_tree_hash
        and smoke_evidence.get("project_manifest_sha256") == current_manifest_hash
    ):
        stale_smoke = {
            "recorded_project_tree_hash": smoke_evidence.get("project_tree_hash"),
            "recorded_project_manifest_sha256": smoke_evidence.get("project_manifest_sha256"),
        }
        smoke_evidence = {}
    for name in (
        "screenshot_manifest.json",
        "journey.json",
        "mechanics.json",
        "title_flow.json",
        "tam_survival.json",
        "input_playthrough.json",
        "suspend_continue.json",
        "game_over_recovery.json",
        "package_smoke.json",
    ):
        path = evidence_root / name
        if path.exists():
            evidence = json.loads(path.read_text(encoding="utf-8"))
            is_current = (
                evidence.get("project_tree_hash") == current_tree_hash
                and evidence.get("project_manifest_sha256") == current_manifest_hash
            )
            if is_current:
                verification[name] = evidence
            else:
                stale_verification[name] = {
                    "recorded_project_tree_hash": evidence.get("project_tree_hash"),
                    "recorded_project_manifest_sha256": evidence.get("project_manifest_sha256"),
                }
    report: dict[str, object] = {
        "engine_commit": engine_commit,
        "schema_version": schema_version,
        "content_hash": content_hash,
        "project_tree_hash": current_tree_hash,
        "generated_files": inventory,
        "analysis": analysis or {},
        "smoke": smoke_evidence,
        "stale_smoke": stale_smoke,
        "evidence_files": evidence_inventory,
        "verification": verification,
        "stale_verification": stale_verification,
    }
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    smoke_lines = (
        "\n".join(f"- {key}: `{value}`" for key, value in sorted(smoke_evidence.items()))
        or "- Not run"
    )
    evidence_lines = (
        "\n".join(f"- `{entry['path']}`: `{entry['sha256']}`" for entry in evidence_inventory)
        or "- Not generated"
    )
    markdown = f"""# {report_title} build report

- Engine commit: `{engine_commit}`
- Schema version: `{schema_version}`
- Content hash: `{content_hash}`
- Project tree hash: `{report["project_tree_hash"]}`
- Generated files: {len(inventory)}

## Smoke evidence

{smoke_lines}

## Bound verification evidence

{evidence_lines}

The automated smoke check does not claim to replace an interactive playthrough.
"""
    (build_root / "REPORT.md").write_text(markdown, encoding="utf-8")
    return report
