from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

PATCH_NAME = "lt-maker-winternight-runtime.patch"
EXPECTED_PATCH_SHA256 = "01904392e35d532c69da879bafd1dec74c6446e6b9707eeb34d56148de0faf83"
PATCHED_FILES = (
    "app/engine/general_states.py",
    "app/engine/ui_view.py",
)


def _patch_path(root: Path) -> Path:
    return root / "patches" / PATCH_NAME


def _current_diff(engine_root: Path) -> bytes:
    return subprocess.check_output(
        [
            "git",
            "-c",
            "diff.noprefix=false",
            "-c",
            "diff.mnemonicprefix=false",
            "diff",
            "HEAD",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--abbrev=7",
            "--unified=3",
            "--inter-hunk-context=0",
            "--",
            *PATCHED_FILES,
        ],
        cwd=engine_root,
    )


def _expected_patch(root: Path) -> bytes:
    path = _patch_path(root)
    patch = path.read_bytes()
    digest = hashlib.sha256(patch).hexdigest()
    if digest != EXPECTED_PATCH_SHA256:
        raise RuntimeError(
            f"LT patch hash mismatch: expected {EXPECTED_PATCH_SHA256}, found {digest}"
        )
    return patch


def verify_engine_patch(root: Path, engine_root: Path) -> None:
    expected = _expected_patch(root)
    actual = _current_diff(engine_root)
    if actual != expected:
        raise RuntimeError(
            "LT runtime patch is absent or modified; run `make bootstrap` to restore it"
        )


def apply_engine_patch(root: Path, engine_root: Path) -> None:
    expected = _expected_patch(root)
    if _current_diff(engine_root) == expected:
        return
    if _current_diff(engine_root):
        raise RuntimeError("LT submodule has unexpected local changes; refusing to patch")
    patch = _patch_path(root)
    subprocess.run(
        ["git", "apply", "--check", str(patch)],
        cwd=engine_root,
        check=True,
    )
    subprocess.run(
        ["git", "apply", str(patch)],
        cwd=engine_root,
        check=True,
    )
    verify_engine_patch(root, engine_root)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    apply_engine_patch(root, root / "vendor" / "lt-maker")


if __name__ == "__main__":
    main()
