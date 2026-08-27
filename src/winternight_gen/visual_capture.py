from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from PIL import Image

from .build_report import tree_hash
from .lt_runtime import generated_component_system
from .runtime import isolated_engine_runtime


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def capture_level_frame(
    project: Path,
    engine_root: Path,
    level_id: str,
    output: Path,
    *,
    skip_intro: bool,
    scene_id: str | None = None,
) -> None:
    output = output.resolve()
    engine_path = str(engine_root.resolve())
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    with generated_component_system(engine_root):
        from app.data.database.database import DB
        from app.data.resources.resources import RESOURCES
        from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
        from app.engine import config, driver, engine, game_state

        with isolated_engine_runtime(engine_root) as runtime_root, _working_directory(runtime_root):
            from app import sprites as sprite_catalog

            # Reset from the isolated engine sprite directory first, then load
            # project custom sprites so LT's documented override order is kept.
            sprite_catalog.reset()
            RESOURCES.load(project, CURRENT_SERIALIZATION_VERSION)
            DB.load(project, CURRENT_SERIALIZATION_VERSION)
            if level_id != "__title__" and level_id not in DB.levels:
                raise ValueError(f"unknown level: {level_id}")
            driver.start(DB.constants.value("title"), from_editor=True)
            config.SETTINGS["text_speed"] = 0
            game = (
                game_state.start_game()
                if level_id == "__title__"
                else game_state.start_level(level_id)
            )
            if scene_id:
                full_scene_nid = f"{level_id} {scene_id}"
                if not game.events.trigger_specific_event(full_scene_nid, force=True):
                    raise RuntimeError(f"could not trigger scene: {full_scene_nid}")
            original_screenshot = driver.save_screenshot
            frame = 0
            event_frames = 0
            scene_dialogue_frames = 0
            map_frames = 0
            saw_event = False
            scene_pending_key_up = False
            last_skipped_event: object | None = None
            skip_pending_key_up = False
            output.parent.mkdir(parents=True, exist_ok=True)

            def capture_hook(raw_events, surface):
                nonlocal event_frames, frame, map_frames, saw_event
                nonlocal scene_dialogue_frames, scene_pending_key_up
                nonlocal last_skipped_event, skip_pending_key_up
                frame += 1
                import pygame

                state = game.state.current()
                if state == "event":
                    saw_event = True
                    event_frames += 1
                    state_event = getattr(game.state.current_state(), "event", None)
                    is_target_scene_dialogue = (
                        scene_id
                        and state_event
                        and state_event.nid.endswith(f" {scene_id}")
                        and state_event.text_boxes
                    )
                    if is_target_scene_dialogue:
                        average = pygame.transform.average_color(surface)
                        if sum(average[:3]) > 24:
                            scene_dialogue_frames += 1
                        else:
                            # Some scenes intentionally begin with dialogue
                            # under a closed transition (offscreen sound). Use
                            # real SELECT pulses to advance until a visible
                            # milestone frame is available.
                            if scene_pending_key_up:
                                pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_x))
                                scene_pending_key_up = False
                            else:
                                pygame.event.post(
                                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x)
                                )
                                scene_pending_key_up = True
                elif saw_event:
                    map_frames += 1
                if skip_intro:
                    state_event = getattr(game.state.current_state(), "event", None)
                    if skip_pending_key_up:
                        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_s))
                        skip_pending_key_up = False
                    elif state == "event" and state_event is not last_skipped_event:
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))
                        last_skipped_event = state_event
                        skip_pending_key_up = True
                map_ready = skip_intro and saw_event and state == "free" and map_frames >= 20
                dialogue_ready = (
                    not skip_intro
                    and state == "event"
                    and (scene_dialogue_frames >= 15 if scene_id else event_frames >= 45)
                )
                title_ready = level_id == "__title__" and state == "title_start" and frame >= 45
                if map_ready or dialogue_ready or title_ready:
                    engine.save_surface(surface, str(output))
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif frame >= 600:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            driver.save_screenshot = capture_hook
            try:
                driver.run(game)
            finally:
                driver.save_screenshot = original_screenshot
                engine.terminate()
    if not output.exists():
        raise RuntimeError(
            f"engine did not capture {level_id}: state={game.state.current()}, "
            f"frames={frame}, event_frames={event_frames}, map_frames={map_frames}, "
            f"saw_event={saw_event}"
        )


def capture_all_levels(
    project: Path,
    engine_root: Path,
    level_ids: list[str],
    evidence_root: Path,
) -> dict[str, object]:
    screenshots = evidence_root / "screenshots"
    if screenshots.exists():
        shutil.rmtree(screenshots)
    screenshots.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    title_output = screenshots / "title.png"
    title_environment = os.environ.copy()
    title_environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "winternight_gen.cli",
            "capture-frame",
            "--level",
            "__title__",
            "--output",
            str(title_output),
        ],
        check=True,
        cwd=project.parent.parent,
        env=title_environment,
    )
    with Image.open(title_output) as image:
        title_dimensions = list(image.size)
    entries.append(
        {
            "level": None,
            "kind": "title",
            "path": title_output.relative_to(project.parent.parent).as_posix(),
            "dimensions": title_dimensions,
            "sha256": sha256(title_output.read_bytes()).hexdigest(),
        }
    )
    for level_id in level_ids:
        for kind, skip_intro in (("intro", False), ("map", True)):
            output = screenshots / f"{level_id}-{kind}.png"
            environment = os.environ.copy()
            environment.update(
                SDL_VIDEODRIVER="dummy",
                SDL_AUDIODRIVER="dummy",
            )
            command = [
                sys.executable,
                "-m",
                "winternight_gen.cli",
                "capture-frame",
                "--level",
                level_id,
                "--output",
                str(output),
            ]
            if skip_intro:
                command.append("--skip-intro")
            subprocess.run(
                command,
                check=True,
                cwd=project.parent.parent,
                env=environment,
            )
            with Image.open(output) as image:
                dimensions = list(image.size)
            entries.append(
                {
                    "level": level_id,
                    "kind": kind,
                    "path": output.relative_to(project.parent.parent).as_posix(),
                    "dimensions": dimensions,
                    "sha256": sha256(output.read_bytes()).hexdigest(),
                }
            )
    milestone_scenes = {
        "wn00_tutorial": [
            "sc_c0_mat_and_news",
            "sc_c0_fain_news",
            "sc_c0_travelers",
            "sc_c0_delivery",
        ],
        "wn01_farm_escape": ["sc_c1_tam_combat_quote", "sc_c1_tam_wounded"],
        "wn02_village_defense": [
            "sc_c2_mission_briefing",
            "sc_c2_rescue_man",
            "sc_c2_unavoidable_damage",
            "sc_c2_home_saved",
            "sc_c2_defense_end",
        ],
        "wn03_return_to_farm": [
            "sc_c3_sword_recovery",
            "sc_c3_trolloc_appears",
            "sc_c3_rand_combat_quote",
            "sc_c3_rejoin_tam",
            "sc_c3_ending_card",
        ],
    }
    for level_id, scene_ids in milestone_scenes.items():
        for scene_id in scene_ids:
            output = screenshots / f"{level_id}-{scene_id}.png"
            environment = os.environ.copy()
            environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "winternight_gen.cli",
                    "capture-scene",
                    "--level",
                    level_id,
                    "--scene",
                    scene_id,
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=project.parent.parent,
                env=environment,
            )
            with Image.open(output) as image:
                dimensions = list(image.size)
            entries.append(
                {
                    "level": level_id,
                    "kind": "milestone_scene",
                    "scene": scene_id,
                    "path": output.relative_to(project.parent.parent).as_posix(),
                    "dimensions": dimensions,
                    "sha256": sha256(output.read_bytes()).hexdigest(),
                }
            )
    compiled_manifest_path = project / "build_manifest.json"
    compiled_manifest = json.loads(compiled_manifest_path.read_text(encoding="utf-8"))
    manifest = {
        "project": project.relative_to(project.parent.parent).as_posix(),
        "engine_commit": compiled_manifest["engine_commit"],
        "content_hash": compiled_manifest["content_hash"],
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(compiled_manifest_path.read_bytes()).hexdigest(),
        "screenshots": entries,
    }
    (evidence_root / "screenshot_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
