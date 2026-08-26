from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def generated_component_system(engine_root: Path):
    """Create LT's normal generated runtime modules, then remove newly created files."""
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    generated = (
        engine_root / "app" / "engine" / "item_system.py",
        engine_root / "app" / "engine" / "skill_system.py",
        engine_root
        / "app"
        / "events"
        / "python_eventing"
        / "python_event_command_wrappers.py",
    )
    preexisting = {path: path.exists() for path in generated}
    from app.engine.codegen.source_generator import generate_all

    generate_all()
    try:
        yield
    finally:
        for path in generated:
            if not preexisting[path] and path.exists():
                path.unlink()
