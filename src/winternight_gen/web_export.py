from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import urllib.request
from pathlib import Path

from .build_report import sha256, tree_hash

WEB_ADAPTER_VERSION = "0.1"
RUNTIME_DIRECTORIES = ("data", "engine", "events", "utilities")
BROWSERFS_URL = "https://pygame-web.github.io/archives/0.9/browserfs.min.js"
BROWSERFS_SHA256 = "ba01fda78db31a7ba579afe74b8b56cf4636381ca1b6c54ffba20467756a627f"
BROKEN_BROWSERFS_SCRIPT = (
    '<script src="https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js"></script>'
)
DEBUG_TERMINAL_CONFIG = 'data-os="vtx,snd,gui"'
WEB_SHELL_STYLE = """    <style id="winternight-web-shell">
        :root {
            --winternight-game-width: 480px;
            --winternight-game-height: 320px;
            color-scheme: dark;
        }
        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        body {
            background:
                radial-gradient(circle at 50% 45%, #172333 0%, #08111c 46%, #020509 100%)
                !important;
        }
        canvas.emscripten {
            width: var(--winternight-game-width) !important;
            height: var(--winternight-game-height) !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            position: fixed !important;
            inset: 0 !important;
            margin: auto !important;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            outline: 1px solid rgba(189, 155, 91, 0.68);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.72);
        }
        canvas.emscripten:focus-visible {
            outline: 2px solid #e1bd72;
            outline-offset: 2px;
        }
    </style>
"""
WEB_SHELL_SCRIPT = """    <script id="winternight-integer-scaling">
        (() => {
            const logicalWidth = 240;
            const logicalHeight = 160;

            function fitWinternightCanvas() {
                const availableScale = Math.min(
                    window.innerWidth / logicalWidth,
                    window.innerHeight / logicalHeight
                );
                const scale = availableScale >= 2
                    ? Math.floor(availableScale)
                    : availableScale;
                const width = Math.max(1, Math.floor(logicalWidth * scale));
                const height = Math.max(1, Math.floor(logicalHeight * scale));
                document.documentElement.style.setProperty(
                    "--winternight-game-width", `${width}px`
                );
                document.documentElement.style.setProperty(
                    "--winternight-game-height", `${height}px`
                );
            }

            window.addEventListener("resize", fitWinternightCanvas, {passive: true});
            fitWinternightCanvas();
            window.requestAnimationFrame(fitWinternightCanvas);
        })();
    </script>
"""


def _copytree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "test", "demo_code"),
    )


def stage_web_application(
    root: Path,
    project: Path,
    engine_root: Path,
    output: Path,
    engine_commit: str,
) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    build_root = (root / "build").resolve()
    if output == build_root or not output.is_relative_to(build_root):
        raise ValueError(f"web stage must be a child of {build_root}: {output}")
    if not project.is_dir():
        raise FileNotFoundError(f"compiled project is missing: {project}")
    runtime_main = root / "web" / "runtime_main.py"
    if not runtime_main.is_file():
        raise FileNotFoundError(f"browser runtime is missing: {runtime_main}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    app_source = engine_root / "app"
    app_output = output / "app"
    app_output.mkdir()
    for source in sorted(app_source.iterdir()):
        if source.is_file() and source.suffix == ".py":
            shutil.copy2(source, app_output / source.name)
        elif source.is_dir() and source.name in RUNTIME_DIRECTORIES:
            _copytree(source, app_output / source.name)

    # One runtime menu helper imports this small editor-independent math module.
    math_source = app_source / "editor" / "lib" / "math"
    math_output = app_output / "editor" / "lib" / "math"
    math_output.parent.mkdir(parents=True)
    _copytree(math_source, math_output)
    for package in (app_output / "editor", app_output / "editor" / "lib"):
        (package / "__init__.py").touch()

    _copytree(engine_root / "sprites", output / "sprites")
    _copytree(engine_root / "resources" / "platforms", output / "resources" / "platforms")
    _copytree(project, output / "winternight.ltproj")
    shutil.copy2(runtime_main, output / "main.py")
    shutil.copy2(engine_root / "favicon.ico", output / "favicon.ico")
    shutil.copy2(engine_root / "LICENSE.txt", output / "LEX_TALIONIS_LICENSE.txt")

    typing_extensions = importlib.util.find_spec("typing_extensions")
    if typing_extensions and typing_extensions.origin:
        shutil.copy2(typing_extensions.origin, output / "typing_extensions.py")

    manifest = {
        "adapter_version": WEB_ADAPTER_VERSION,
        "engine_commit": engine_commit,
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(project / "build_manifest.json"),
        "entry_point": "main.py",
    }
    (output / "web_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def finalize_pygbag_build(
    root: Path,
    output: Path,
    *,
    browserfs_bytes: bytes | None = None,
) -> dict[str, object]:
    """Make Pygbag 0.9.3's browser output self-consistent and deployable.

    Pygbag 0.9.3 emits a BrowserFS URL that no longer exists. We vendor the
    exact archived script into the generated site and verify its pinned hash.
    """
    root = root.resolve()
    output = output.resolve()
    build_root = (root / "build").resolve()
    if output == build_root or not output.is_relative_to(build_root):
        raise ValueError(f"web output must be a child of {build_root}: {output}")

    index_path = output / "index.html"
    if not index_path.is_file():
        raise FileNotFoundError(f"Pygbag index is missing: {index_path}")

    if browserfs_bytes is None:
        with urllib.request.urlopen(BROWSERFS_URL, timeout=30) as response:  # noqa: S310
            browserfs_bytes = response.read()
    actual_hash = hashlib.sha256(browserfs_bytes).hexdigest()
    if actual_hash != BROWSERFS_SHA256:
        raise RuntimeError(
            f"BrowserFS hash mismatch: expected {BROWSERFS_SHA256}, found {actual_hash}"
        )

    index = index_path.read_text(encoding="utf-8")
    if index.count(BROKEN_BROWSERFS_SCRIPT) != 1:
        raise RuntimeError("Pygbag BrowserFS script reference changed; update the web adapter")
    if index.count(DEBUG_TERMINAL_CONFIG) != 1:
        raise RuntimeError("Pygbag terminal configuration changed; update the web adapter")
    if index.count("</head>") != 1 or index.count("</body>") != 1:
        raise RuntimeError("Pygbag document structure changed; update the web adapter")
    index_path.write_text(
        index.replace(BROKEN_BROWSERFS_SCRIPT, '<script src="browserfs.min.js"></script>').replace(
            DEBUG_TERMINAL_CONFIG,
            'data-os="snd,gui"',
        ).replace("</head>", f"{WEB_SHELL_STYLE}</head>").replace(
            "</body>", f"{WEB_SHELL_SCRIPT}</body>"
        ),
        encoding="utf-8",
    )
    browserfs_path = output / "browserfs.min.js"
    browserfs_path.write_bytes(browserfs_bytes)
    return {
        "browserfs_sha256": actual_hash,
        "browserfs_url": BROWSERFS_URL,
        "web_output": str(output),
    }
