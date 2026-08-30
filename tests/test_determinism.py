from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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


def test_concurrent_compiles_serialize_shared_output(tmp_path: Path, spec) -> None:
    output = tmp_path / "shared.ltproj"

    def compile_once(report_name: str) -> None:
        compile_project(
            spec,
            SPEC_PATH,
            output,
            ENGINE_ROOT,
            engine_commit(),
            tmp_path / report_name,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(compile_once, "first-report"),
            pool.submit(compile_once, "second-report"),
        ]
        for future in futures:
            future.result()

    reference = tmp_path / "reference.ltproj"
    compile_project(
        spec,
        SPEC_PATH,
        reference,
        ENGINE_ROOT,
        engine_commit(),
        tmp_path / "reference-report",
    )
    assert tree_hash(output) == tree_hash(reference)
