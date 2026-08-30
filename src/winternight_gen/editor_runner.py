from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from .lt_runtime import generated_component_system


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def run_editor(project: Path, engine_root: Path, *, smoke: bool = False) -> dict[str, object]:
    if smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with _working_directory(engine_root), generated_component_system(engine_root):
        import pygame
        from app import sprites as sprite_catalog
        from app.editor.editor_locale import init_locale
        from app.editor.main_editor import MainEditor
        from PyQt5.QtCore import QDir, QLockFile, QTimer
        from PyQt5.QtWidgets import QApplication

        lock = QLockFile(QDir.tempPath() + "/lt-maker.lock")
        if not lock.tryLock(100):
            raise RuntimeError("LT-Maker is already running")
        try:
            init_locale()
            pygame.font.init()
            # app.sprites scans cwd-relative "sprites/" at import time. If it was
            # imported before entering engine_root, rebuild the catalog here.
            sprite_catalog.reset()
            app = QApplication.instance() or QApplication(sys.argv[:1])
            window = MainEditor(str(project.resolve()))
            window.show()
            loaded_path = Path(window.project_save_load_handler.current_proj).resolve()
            loaded = loaded_path == project.resolve()
            if smoke:
                QTimer.singleShot(750, app.quit)
            exit_code = app.exec_()
            window.hide()
            window.deleteLater()
        finally:
            lock.unlock()
    result = {
        "editor_loaded_project": loaded,
        "editor_exit_code": exit_code,
        "editor_project": str(loaded_path),
    }
    if not loaded or exit_code != 0:
        raise RuntimeError(f"editor check failed: {result}")
    return result
