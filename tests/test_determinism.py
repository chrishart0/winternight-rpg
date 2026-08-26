from __future__ import annotations

from pathlib import Path

from conftest import ENGINE_ROOT, SPEC_PATH, engine_commit

from winternight_gen.build_report import tree_hash
from winternight_gen.campaign_compiler import compile_project


def test_same_spec_builds_byte_identically(tmp_path: Path, spec):
    first = tmp_path / "first.ltproj"
    second = tmp_path / "second.ltproj"
    compile_project(spec, SPEC_PATH, first, ENGINE_ROOT, engine_commit(), tmp_path / "first-report")
    compile_project(
        spec,
        SPEC_PATH,
        second,
        ENGINE_ROOT,
        engine_commit(),
        tmp_path / "second-report",
    )
    assert tree_hash(first) == tree_hash(second)
