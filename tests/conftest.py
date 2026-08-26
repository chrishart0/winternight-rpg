from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from winternight_gen.campaign_compiler import compile_campaign_project, compile_project
from winternight_gen.models import load_campaign_bundle, load_spec

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "design" / "minimal.yaml"
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


def engine_commit() -> str:
    return subprocess.check_output(
        ["git", "-C", str(ENGINE_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


@pytest.fixture(scope="session")
def spec():
    return load_spec(SPEC_PATH)


@pytest.fixture(scope="session")
def campaign_bundle():
    return load_campaign_bundle(ROOT)


@pytest.fixture(scope="session")
def compiled_project(tmp_path_factory: pytest.TempPathFactory, spec):
    root = tmp_path_factory.mktemp("compiled")
    output = root / "minimal.ltproj"
    compile_project(spec, SPEC_PATH, output, ENGINE_ROOT, engine_commit(), root)
    return output


@pytest.fixture(scope="session")
def compiled_campaign(tmp_path_factory: pytest.TempPathFactory, campaign_bundle):
    root = tmp_path_factory.mktemp("compiled-campaign")
    output = root / "winternight.ltproj"
    compile_campaign_project(
        campaign_bundle,
        ROOT,
        output,
        ENGINE_ROOT,
        engine_commit(),
        root,
    )
    return output
