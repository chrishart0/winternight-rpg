from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .asset_pipeline import AssetPaths
from .event_compiler import compile_outcome, compile_scene
from .lt_runtime import generated_component_system
from .models import MinimalSpec

FONT_NIDS = (
    "bconvo",
    "chapter",
    "class",
    "convo",
    "credit",
    "credit_title",
    "iconvo",
    "info",
    "label",
    "narrow",
    "nconvo",
    "number_big",
    "number_big2",
    "number_big3",
    "number_small",
    "number_small2",
    "number_small3",
    "number_small4",
    "rank",
    "reel",
    "short",
    "small",
    "stat",
    "text",
    "text_numbers",
)

STATS = (
    ("HP", "HP", 60, "hidden"),
    ("STR", "Str", 30, "left"),
    ("MAG", "Mag", 30, "left"),
    ("SKL", "Skill", 30, "left"),
    ("SPD", "Spd", 30, "left"),
    ("LCK", "Luck", 30, "right"),
    ("DEF", "Def", 30, "left"),
    ("RES", "Res", 30, "left"),
    ("CON", "Con", 25, "right"),
    ("MOV", "Move", 15, "right"),
)

EQUATIONS = (
    ("HITPOINTS", "HP"),
    ("MOVEMENT", "MOV"),
    ("ATTACK_SPEED", "SPD"),
    ("DEFENSE_SPEED", "SPD"),
    ("HIT", "SKL*2 + LCK//2"),
    ("AVOID", "SPD*2 + LCK"),
    ("CRIT_HIT", "SKL//2"),
    ("CRIT_AVOID", "LCK"),
    ("DAMAGE", "STR"),
    ("DEFENSE", "DEF"),
    ("MAGIC_DAMAGE", "MAG"),
    ("MAGIC_DEFENSE", "RES"),
    ("MAGIC_RANGE", "max(1, MAG//2)"),
    ("CRIT_ADD", "0"),
    ("CRIT_MULT", "3"),
    ("THRACIA_CRIT", "0"),
    ("SPEED_TO_DOUBLE", "4"),
    ("RATING", "HP + STR + SKL + SPD + DEF + RES"),
    ("RESCUE_AID", "max(0, CON - 1)"),
    ("RESCUE_WEIGHT", "CON"),
    ("STEAL_ATK", "SPD"),
    ("STEAL_DEF", "SPD"),
    ("HEAL", "MAG + 10"),
    ("CONSTITUTION", "CON"),
    ("INITIATIVE", "SPD"),
    ("MANA", "0"),
    ("ZERO", "0"),
)


def _import_lt(engine_root: Path) -> None:
    engine = str(engine_root.resolve())
    if engine not in sys.path:
        sys.path.insert(0, engine)


def _set_constant(db, nid: str, value) -> None:
    constant = db.constants.get(nid)
    if constant:
        constant.set_value(value)


def _make_database(spec: MinimalSpec):
    import app.engine.item_component_access as item_components
    from app.data.category import Categories, CategorizedCatalog
    from app.data.database.ai import AIBehaviour, AIPrefab
    from app.data.database.database import Database
    from app.data.database.difficulty_modes import (
        DifficultyModePrefab,
        GrowthOption,
        PermadeathOption,
        RNGOption,
    )
    from app.data.database.equations import Equation
    from app.data.database.items import ItemPrefab
    from app.data.database.klass import Klass
    from app.data.database.level_units import UniqueUnit
    from app.data.database.levels import LevelPrefab
    from app.data.database.parties import PartyPrefab
    from app.data.database.stats import StatPrefab
    from app.data.database.terrain import Terrain
    from app.data.database.units import UnitPrefab
    from app.data.database.weapons import WeaponRank, WeaponType, WexpGain
    from app.events.event_prefab import EventPrefab
    from app.utilities.data import Data

    db = Database()
    for data_type in db.save_data_types:
        catalog = getattr(db, data_type)
        if isinstance(catalog, CategorizedCatalog):
            catalog.categories = Categories()
    _set_constant(db, "game_nid", spec.project.id)
    _set_constant(db, "title", spec.project.title)
    _set_constant(db, "title_particles", False)
    _set_constant(db, "turnwheel", False)
    _set_constant(db, "battle_animation", False)
    _set_constant(db, "autogenerate_grey_map_sprites", True)
    _set_constant(db, "music_game_over", None)

    db.stats.clear()
    for nid, name, maximum, position in STATS:
        db.stats.append(StatPrefab(nid, name, maximum, "Graybox stat", position))
    db.equations.clear()
    for nid, expression in EQUATIONS:
        db.equations.append(Equation(nid, expression))

    db.mcost.grid = [[1]]
    db.mcost.terrain_types = ["Floor"]
    db.mcost.unit_types = ["Foot"]
    db.terrain.append(
        Terrain(spec.map.terrain_id, "Floor", (91, 112, 95), "Floor", "Floor", None, "Floor")
    )
    db.weapon_ranks.append(WeaponRank("E", 1))
    db.weapons.append(WeaponType("Training", "Training"))

    component_values = (
        ("weapon", None),
        ("target_enemy", None),
        ("min_range", 1),
        ("max_range", 1),
        ("damage", 5),
        ("hit", 100),
        ("crit", 0),
        ("weight", 0),
        ("uses", 40),
        ("uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}),
        ("level_exp", None),
        ("weapon_type", "Training"),
        ("weapon_rank", "E"),
    )
    components = Data([
        component
        for component in (item_components.restore_component(value) for value in component_values)
        if component
    ])
    db.items.append(
        ItemPrefab(
            "training_blade",
            "Training Blade",
            "A graybox test weapon.",
            components=components,
        )
    )

    stat_maximums = {nid: maximum for nid, _, maximum, _ in STATS}
    zero_stats = {nid: 0 for nid, *_ in STATS}
    wexp = {"Training": WexpGain(True, 1, 1)}
    unit_by_id = {unit.id: unit for unit in spec.units}
    for unit in spec.units:
        bases = zero_stats.copy()
        bases.update(
            HP=unit.hp,
            STR=unit.strength,
            MAG=0,
            SKL=8,
            SPD=5,
            LCK=0,
            DEF=unit.defense,
            RES=0,
            CON=8,
            MOV=5,
        )
        klass = Klass(
            nid=unit.class_id,
            name=unit.name,
            movement_group="Foot",
            bases=bases.copy(),
            growths=zero_stats.copy(),
            growth_bonus=zero_stats.copy(),
            promotion=zero_stats.copy(),
            max_stats=stat_maximums.copy(),
            wexp_gain=wexp.copy(),
            map_sprite_nid=spec.assets.map_sprite,
        )
        db.classes.append(klass)
        db.units.append(
            UnitPrefab(
                nid=unit.id,
                name=unit.name,
                desc="Original Phase 0 graybox unit.",
                klass=unit.class_id,
                bases=bases,
                growths=zero_stats.copy(),
                stat_cap_modifiers=zero_stats.copy(),
                starting_items=[["training_blade", False]],
                wexp_gain=wexp.copy(),
                portrait_nid=unit.portrait,
            )
        )

    player = next(unit for unit in spec.units if unit.team == "player")
    db.parties.append(PartyPrefab("graybox_party", "Graybox Party", player.id))
    attack_ai = AIPrefab("pursue", 20)
    attack_ai.behaviours = [
        AIBehaviour("Attack", "Enemy", -4),
        AIBehaviour.DoNothing(),
        AIBehaviour.DoNothing(),
    ]
    db.ai.append(attack_ai)

    difficulty = DifficultyModePrefab(
        "normal",
        "Normal",
        "blue",
        PermadeathOption.CLASSIC,
        GrowthOption.FIXED,
        RNGOption.CLASSIC,
    )
    difficulty.init_bases(db)
    difficulty.init_growths(db)
    db.difficulty_modes.append(difficulty)

    level = LevelPrefab(spec.project.level_id, spec.project.level_title)
    level.tilemap = spec.map.id
    level.party = "graybox_party"
    level.objective = {
        "simple": spec.project.objective,
        "win": spec.project.objective,
        "loss": spec.project.loss,
    }
    for unit in spec.units:
        level.units.append(
            UniqueUnit(
                nid=unit.id,
                team=unit.team,
                ai="pursue" if unit.team == "enemy" else None,
                starting_position=unit.position,
            )
        )
    db.levels.append(level)

    for scene in (spec.scenes.intro, spec.scenes.outro):
        event = EventPrefab(scene.id)
        event.level_nid = spec.project.level_id
        event.trigger = scene.trigger
        event.only_once = True
        event.source = compile_scene(scene)
        db.events.append(event)
    for outcome, command in ((spec.victory, "win_game"), (spec.failure, "lose_game")):
        event = EventPrefab(outcome.event_id)
        event.level_nid = spec.project.level_id
        event.trigger = outcome.trigger
        event.condition, event.source = compile_outcome(outcome, command)
        event.only_once = True
        db.events.append(event)

    assert unit_by_id[spec.victory.defeated_unit].team == "enemy"
    assert unit_by_id[spec.failure.defeated_unit].team == "player"
    return db


def _make_resources(spec: MinimalSpec, assets: AssetPaths):
    from app.data.category import Categories, CategorizedCatalog
    from app.data.resources.fonts import Font
    from app.data.resources.map_sprites import MapSprite
    from app.data.resources.panoramas import Panorama
    from app.data.resources.portraits import PortraitPrefab
    from app.data.resources.resources import Resources
    from app.data.resources.tiles import TileMapPrefab, TileSet

    resources = Resources()
    for data_type in resources.save_data_types:
        catalog = getattr(resources, data_type)
        if isinstance(catalog, CategorizedCatalog):
            catalog.categories = Categories()
    resources.panoramas.append(Panorama(spec.assets.background, str(assets.background), 1))
    for portrait_id, path in assets.portraits.items():
        portrait = PortraitPrefab(portrait_id, str(path))
        portrait.blinking_offset = [34, 31]
        portrait.smiling_offset = [34, 48]
        resources.portraits.append(portrait)
    resources.map_sprites.append(
        MapSprite(spec.assets.map_sprite, str(assets.map_sprite_stand), str(assets.map_sprite_move))
    )
    tileset = TileSet(spec.assets.tileset, str(assets.tileset))
    tileset.terrain_grid[(0, 0)] = spec.map.terrain_id
    resources.tilesets.append(tileset)
    tilemap = TileMapPrefab(spec.map.id)
    tilemap.width, tilemap.height = spec.map.width, spec.map.height
    tilemap.tilesets = [spec.assets.tileset]
    for y in range(spec.map.height):
        for x in range(spec.map.width):
            tilemap.layers[0].set_sprite((x, y), spec.assets.tileset, (0, 0))
            tilemap.layers[0].terrain_grid[(x, y)] = spec.map.terrain_id
    resources.tilemaps.append(tilemap)

    palettes = {
        "black": [(32, 36, 42, 255)],
        "white": [(248, 248, 248, 255)],
        "blue": [(80, 112, 248, 255)],
        "green": [(112, 160, 72, 255)],
        "red": [(224, 72, 72, 255)],
        "grey": [(160, 160, 160, 255)],
        "yellow": [(248, 240, 136, 255)],
        "brown": [(160, 120, 72, 255)],
    }
    for nid in FONT_NIDS:
        font = Font(nid, default_color="white", palettes=palettes)
        font.file_name = str(assets.font_image.with_suffix(""))
        resources.fonts.append(font)
    return resources


def write_lt_project(
    spec: MinimalSpec,
    assets: AssetPaths,
    output: Path,
    engine_root: Path,
    engine_commit: str,
) -> None:
    _import_lt(engine_root)
    from app.constants import VERSION
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    from app.editor.settings import MainSettingsController
    from app.editor.settings.preference_definitions import Preference

    output.mkdir(parents=True, exist_ok=False)
    with generated_component_system(engine_root):
        db = _make_database(spec)
        resources = _make_resources(spec, assets)
        settings = MainSettingsController(company="winternight", product="generator")
        settings.set_preference(Preference.SAVE_CHUNKS, False)
        resources.save(output)
        if not db.serialize(output, as_chunks=False):
            raise RuntimeError("LT database serializer reported failure")
    metadata = {
        "date": "1970-01-01 00:00:00",
        "engine_version": VERSION,
        "serialization_version": CURRENT_SERIALIZATION_VERSION,
        "project": spec.project.id,
        "has_fatal_errors": False,
        "as_chunks": False,
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=4, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "ENGINE_COMMIT").write_text(engine_commit + "\n", encoding="utf-8")
    for loose in ("custom_components", "custom_sprites", "system"):
        (output / "resources" / loose).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        Path(__file__).resolve().parents[2] / "assets" / "placeholders" / "README.md",
        output / "ASSET_PROVENANCE.md",
    )
