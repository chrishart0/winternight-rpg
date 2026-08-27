from __future__ import annotations

import json

from winternight_gen.build_report import (
    load_current_smoke,
    sha256,
    tree_hash,
    write_report,
)


def test_smoke_evidence_survives_only_for_identical_build(tmp_path) -> None:
    project = tmp_path / "story.ltproj"
    project.mkdir()
    (project / "build_manifest.json").write_text("{}\n", encoding="utf-8")
    (project / "data.txt").write_text("same build\n", encoding="utf-8")
    smoke = {
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(project / "build_manifest.json"),
        "all_levels_initialized": True,
    }
    report = write_report(
        tmp_path,
        project,
        "engine-commit",
        "0.2",
        "content-hash",
        smoke=smoke,
    )

    assert report["smoke"] == smoke
    assert load_current_smoke(tmp_path, project, "engine-commit", "content-hash") == smoke

    (project / "data.txt").write_text("changed build\n", encoding="utf-8")
    assert load_current_smoke(tmp_path, project, "engine-commit", "content-hash") == {}


def test_stale_smoke_is_reported_but_not_claimed(tmp_path) -> None:
    project = tmp_path / "story.ltproj"
    project.mkdir()
    (project / "build_manifest.json").write_text("{}\n", encoding="utf-8")
    report = write_report(
        tmp_path,
        project,
        "engine-commit",
        "0.2",
        "content-hash",
        smoke={
            "project_tree_hash": "old",
            "project_manifest_sha256": "old",
        },
    )

    assert report["smoke"] == {}
    assert report["stale_smoke"]["recorded_project_tree_hash"] == "old"


def test_live_launch_is_bound_only_to_the_current_project(tmp_path) -> None:
    project = tmp_path / "story.ltproj"
    project.mkdir()
    manifest = project / "build_manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    launch = {
        "verification_kind": "exact_interactive_launcher_window",
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(manifest),
        "window_created": True,
    }
    (evidence / "live_launch.json").write_text(
        json.dumps(launch) + "\n", encoding="utf-8"
    )

    report = write_report(
        tmp_path,
        project,
        "engine-commit",
        "0.2",
        "content-hash",
    )

    assert report["verification"]["live_launch.json"] == launch
