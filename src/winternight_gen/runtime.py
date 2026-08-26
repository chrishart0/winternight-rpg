from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path


def prepare_engine_runtime(runtime_root: Path, engine_root: Path) -> Path:
    runtime_root.mkdir(parents=True, exist_ok=True)
    for name in ("sprites", "favicon.ico"):
        target = (engine_root / name).resolve()
        link = runtime_root / name
        if link.exists() or link.is_symlink():
            if link.resolve() != target:
                raise RuntimeError(f"runtime asset {link} points to the wrong target")
            continue
        link.symlink_to(target, target_is_directory=target.is_dir())
    (runtime_root / "saves").mkdir(exist_ok=True)
    return runtime_root


@contextmanager
def isolated_engine_runtime(engine_root: Path):
    with tempfile.TemporaryDirectory(prefix="winternight-engine-runtime-") as temp:
        yield prepare_engine_runtime(Path(temp), engine_root)
