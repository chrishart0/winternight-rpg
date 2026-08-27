from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from .build_report import sha256, tree_hash
from .smoke import smoke_project

PACKAGE_NAME = "winternight-private-linux"


def _files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def _tracked_files(repository: Path, directory: str) -> list[Path]:
    output = subprocess.check_output(
        ["git", "-C", str(repository), "ls-files", "-z", directory]
    )
    return [
        repository / relative.decode("utf-8")
        for relative in sorted(filter(None, output.split(b"\0")))
    ]


def _add_file(archive: tarfile.TarFile, source: Path, target: Path) -> None:
    data = source.read_bytes()
    info = tarfile.TarInfo(f"{PACKAGE_NAME}/{target.as_posix()}")
    info.size = len(data)
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o755 if source.name == "run.sh" else 0o644
    with tempfile.SpooledTemporaryFile() as payload:
        payload.write(data)
        payload.seek(0)
        archive.addfile(info, payload)


def package_private_build(
    root: Path, project: Path, engine_root: Path, dist: Path
) -> dict[str, object]:
    dist.mkdir(parents=True, exist_ok=True)
    output = dist / f"{PACKAGE_NAME}.tar.gz"
    with (
        output.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for source in _files(project):
            _add_file(archive, source, Path("winternight.ltproj") / source.relative_to(project))
        for source in _tracked_files(engine_root, "app"):
            _add_file(archive, source, Path("engine/app") / source.relative_to(engine_root / "app"))
        for source in _tracked_files(engine_root, "sprites"):
            target = Path("engine/sprites") / source.relative_to(engine_root / "sprites")
            _add_file(archive, source, target)
        for relative in ("run_engine.py", "LICENSE.txt", "favicon.ico"):
            _add_file(archive, engine_root / relative, Path("engine") / relative)
        for source in _tracked_files(engine_root, "licenses"):
            target = Path("engine/licenses") / source.relative_to(engine_root / "licenses")
            _add_file(archive, source, target)
        for relative in ("launch.py", "run.sh", "README.md"):
            _add_file(archive, root / "packaging" / relative, Path(relative))
        for relative in ("KNOWN_ISSUES.md", "THIRD_PARTY_NOTICES.md"):
            _add_file(archive, root / "docs" / relative, Path(relative))
        _add_file(
            archive,
            project / "ASSET_PROVENANCE.yaml",
            Path("ASSET_PROVENANCE.yaml"),
        )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = dist / f"{output.name}.sha256"
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"archive": output.as_posix(), "sha256": digest, "size": output.stat().st_size}


def smoke_package(archive: Path, engine_commit: str, evidence_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="winternight-package-smoke-") as temp:
        temp_root = Path(temp)
        with tarfile.open(archive, "r:gz") as package:
            package.extractall(temp_root, filter="data")
        root = temp_root / PACKAGE_NAME
        packaged_project = root / "winternight.ltproj"
        smoke = smoke_project(packaged_project, root / "engine")
        launcher_environment = os.environ.copy()
        launcher_environment.update(
            SDL_VIDEODRIVER="dummy",
            SDL_AUDIODRIVER="dummy",
            WINTERNIGHT_PACKAGE_LAUNCH_SMOKE="1",
        )
        launcher = subprocess.run(
            [str(root / "run.sh")],
            cwd=root,
            env=launcher_environment,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        launch_evidence_path = root / "launch-smoke.json"
        launch_evidence = (
            json.loads(launch_evidence_path.read_text(encoding="utf-8"))
            if launch_evidence_path.exists()
            else {}
        )
        result = {
            "verification_kind": "packaged_project_engine_smoke",
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "engine_commit": engine_commit,
            "project_tree_hash": tree_hash(packaged_project),
            "project_manifest_sha256": sha256(packaged_project / "build_manifest.json"),
            "all_levels_initialized": smoke["all_levels_initialized"],
            "all_scenes_executed": smoke["all_scenes_executed"],
            "full_game_loop_exited_cleanly": smoke["full_game_loop_exited_cleanly"],
            "packaged_run_sh_exit_code": launcher.returncode,
            "packaged_run_sh_window_created": launch_evidence.get("window_created", False),
            "packaged_run_sh_window_caption": launch_evidence.get("window_caption"),
            "packaged_run_sh_window_size": launch_evidence.get("window_size"),
            "packaged_run_sh_sdl_driver": launch_evidence.get("sdl_video_driver"),
            "packaged_run_sh_screenshot_sha256": launch_evidence.get("screenshot_sha256"),
            "packaged_run_sh_stdout_tail": launcher.stdout[-2000:],
            "packaged_run_sh_stderr_tail": launcher.stderr[-2000:],
        }
    if not all(
        result[key]
        for key in (
            "all_levels_initialized",
            "all_scenes_executed",
            "full_game_loop_exited_cleanly",
            "packaged_run_sh_window_created",
        )
    ) or result["packaged_run_sh_exit_code"] != 0:
        raise RuntimeError(f"packaged smoke failed: {result}")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
