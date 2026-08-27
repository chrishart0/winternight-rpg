from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from winternight_gen.web_export import (
    BROKEN_BROWSERFS_SCRIPT,
    DEBUG_TERMINAL_CONFIG,
    WEB_SHELL_SCRIPT,
    WEB_SHELL_STYLE,
    finalize_pygbag_build,
    stage_web_application,
)

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "vendor" / "lt-maker"


def test_web_runtime_is_async_and_browser_yielding() -> None:
    runtime = (ROOT / "web" / "runtime_main.py").read_text(encoding="utf-8")
    assert "async def main()" in runtime
    assert "await asyncio.sleep(0)" in runtime
    assert "SAVE_STORAGE_KEY" in runtime
    assert 'save_root = Path("saves")' in runtime
    assert "save_root.mkdir(exist_ok=True)" in runtime
    assert "InlineThread" in runtime
    assert "BrowserTimer" in runtime


def test_stage_web_application_uses_pinned_runtime_without_editor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "fixture.ltproj"
    project.mkdir()
    (project / "metadata.json").write_text("{}\n", encoding="utf-8")
    (project / "build_manifest.json").write_text("{}\n", encoding="utf-8")

    fake_root = tmp_path / "repo"
    (fake_root / "build").mkdir(parents=True)
    (fake_root / "web").mkdir()
    (fake_root / "web" / "runtime_main.py").write_text("async def main(): pass\n")

    engine = tmp_path / "engine"
    for directory in ("app/data", "app/engine", "app/events", "app/utilities"):
        (engine / directory).mkdir(parents=True)
        (engine / directory / "__init__.py").write_text("")
    (engine / "app" / "__init__.py").write_text("")
    (engine / "app" / "editor" / "lib" / "math").mkdir(parents=True)
    (engine / "app" / "editor" / "lib" / "math" / "math_utils.py").write_text("")
    (engine / "sprites").mkdir()
    (engine / "sprites" / "cursor.png").write_bytes(b"png")
    (engine / "resources" / "platforms").mkdir(parents=True)
    (engine / "resources" / "platforms" / "Plain.png").write_bytes(b"png")
    (engine / "favicon.ico").write_bytes(b"ico")
    (engine / "LICENSE.txt").write_text("MIT\n")

    output = fake_root / "build" / "web-app"
    manifest = stage_web_application(fake_root, project, engine, output, "abc123")

    assert manifest["engine_commit"] == "abc123"
    assert (output / "main.py").is_file()
    assert (output / "app" / "engine" / "__init__.py").is_file()
    assert (output / "app" / "editor" / "lib" / "math" / "math_utils.py").is_file()
    assert not (output / "app" / "editor" / "settings.py").exists()
    assert (output / "winternight.ltproj" / "metadata.json").is_file()
    assert json.loads((output / "web_manifest.json").read_text())["adapter_version"] == "0.1"


def test_web_stage_rejects_output_outside_build(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="web stage must be a child"):
        stage_web_application(tmp_path, tmp_path / "game.ltproj", tmp_path, tmp_path / "web", "x")


def test_finalize_pygbag_build_vendors_browserfs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import winternight_gen.web_export as web_export

    browserfs = b"known browserfs fixture"
    fixture_hash = hashlib.sha256(browserfs).hexdigest()
    monkeypatch.setattr(web_export, "BROWSERFS_SHA256", fixture_hash)
    output = tmp_path / "build" / "web-app" / "build" / "web"
    output.mkdir(parents=True)
    (output / "index.html").write_text(
        f"<head>{BROKEN_BROWSERFS_SCRIPT} {DEBUG_TERMINAL_CONFIG}</head><body></body>",
        encoding="utf-8",
    )

    result = finalize_pygbag_build(tmp_path, output, browserfs_bytes=browserfs)
    repeated_result = finalize_pygbag_build(tmp_path, output, browserfs_bytes=browserfs)

    assert (output / "browserfs.min.js").read_bytes() == browserfs
    finalized = (output / "index.html").read_text()
    assert '<script src="browserfs.min.js"></script> data-os="snd,gui"' in finalized
    assert finalized.count('id="winternight-web-shell"') == 1
    assert finalized.count('id="winternight-integer-scaling"') == 1
    assert WEB_SHELL_STYLE in finalized
    assert WEB_SHELL_SCRIPT in finalized
    assert "image-rendering: auto" in finalized
    assert "image-rendering: pixelated" not in finalized
    assert "const maximumScale = 4" in finalized
    assert "Math.min(maximumScale, Math.floor(availableScale))" in finalized
    assert result["browserfs_sha256"] == fixture_hash
    assert repeated_result == result


def test_finalize_pygbag_build_rejects_unpinned_browserfs(tmp_path: Path) -> None:
    output = tmp_path / "build" / "web-app" / "build" / "web"
    output.mkdir(parents=True)
    (output / "index.html").write_text(
        f"<head>{BROKEN_BROWSERFS_SCRIPT} {DEBUG_TERMINAL_CONFIG}</head><body></body>",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="BrowserFS hash mismatch"):
        finalize_pygbag_build(tmp_path, output, browserfs_bytes=b"wrong")
