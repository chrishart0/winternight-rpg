from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .asset_pipeline import CAMPAIGN_TILE_VARIANTS, CampaignAssetPaths
from .event_compiler import (
    compile_failure_condition,
    compile_mission_event,
    compile_scene_v2,
)
from .lt_adapter import EQUATIONS, FONT_NIDS, STATS, _import_lt, _set_constant
from .lt_runtime import generated_component_system
from .models import CampaignBundle
from .music_pipeline import (
    apply_lt_music_assignments,
    load_music_design,
    register_lt_music,
)
from .sfx_pipeline import (
    load_sfx_design,
    register_lt_sfx,
    verify_authored_sfx_references,
)

UI_TRANSLATIONS = {
    "Unit_desc": "Review every unit on the map.",
    "Objective_desc": "Review the current objective and battle status.",
    "Options_desc": "Adjust display, audio, and controls.",
    "Suspend_desc": "Suspend this chapter and return to the title screen.",
    "End_desc": "Finish the player phase.",
    "Talk_desc": "Speak with an adjacent character.",
    "Rescue_desc": "Carry an adjacent ally to safety.",
    "Item_desc": "Review, equip, or use carried items.",
    "Wait_desc": "End this unit's action.",
    "Visit_desc": "Interact with this location.",
    "Search_desc": "Search the marked location.",
    "Escape_desc": "Leave through the marked route.",
    "Attack_desc": "Attack a target with an equipped weapon.",
    "config_desc": "Adjust game settings.",
    "controls_desc": "Review or change keyboard controls.",
    "animation_desc": "Choose when combat animations play.",
    "screen_size_desc": "Change the window scale.",
    "display_fps_desc": "Show or hide the frame-rate counter.",
    "battle_bg_desc": "Show or hide combat backgrounds.",
    "unit_speed_desc": "Change map movement speed.",
    "text_speed_desc": "Change dialogue typing speed.",
    "mouse_desc": "Enable or disable mouse controls.",
    "show_terrain_desc": "Show terrain details under the cursor.",
    "forecast_desc": "Choose the combat forecast detail level.",
    "show_objective_desc": "Show the chapter objective on the map.",
    "autocursor_desc": "Start each turn on the lead unit.",
    "hp_map_team_desc": "Choose which teams show map HP bars.",
    "hp_map_cull_desc": "Choose when map HP bars are hidden.",
    "music_volume_desc": "Adjust music volume.",
    "sound_volume_desc": "Adjust sound-effect volume.",
    "talk_boop_desc": "Enable or disable dialogue sounds.",
    "show_bounds_desc": "Show or hide map boundaries.",
    "grid_opacity_desc": "Adjust tactical grid visibility.",
    "autoend_turn_desc": "End the phase when no units can act.",
    "confirm_end_desc": "Confirm before ending a phase manually.",
    "display_hints_desc": "Show or hide tutorial hints.",
    "keymap_desc": "Choose a control and assign a new key.",
    "get_input_desc": "Press a new key, or Back to cancel.",
    "key_SELECT": "Confirm",
    "key_BACK": "Back",
    "key_INFO": "Info",
    "key_AUX": "Auxiliary",
    "key_LEFT": "Left",
    "key_RIGHT": "Right",
    "key_UP": "Up",
    "key_DOWN": "Down",
    "key_START": "Start",
}


def _components(item):
    import app.engine.item_component_access as item_components
    from app.utilities.data import Data

    if item.kind == "weapon":
        values = [
            ("weapon", None),
            ("target_enemy", None),
            ("min_range", item.min_range),
            ("max_range", item.max_range),
            ("damage", item.might),
            ("hit", item.hit),
            ("crit", 0),
            ("weight", 0),
            ("uses", item.uses),
            ("uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}),
            ("level_exp", None),
            ("weapon_type", item.weapon_type),
            ("weapon_rank", "E"),
        ]
        if item.weapon_type == "Magic":
            values.append(("magic", None))
    elif item.kind == "healing":
        values = [
            ("usable", None),
            ("target_ally", None),
            ("uses", item.uses),
            ("uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}),
            ("heal", item.heal_amount),
            ("map_hit_add_blend", [96, 144, 232]),
            ("map_cast_pose", None),
        ]
    else:
        values = [("value", 0)]
    restored = [item_components.restore_component(value) for value in values]
    return Data([component for component in restored if component])


def _bases(combat) -> dict[str, int]:
    return {
        "HP": combat.hp,
        "STR": combat.strength,
        "MAG": combat.magic,
        "SKL": combat.skill,
        "SPD": combat.speed,
        "LCK": combat.luck,
        "DEF": combat.defense,
        "RES": combat.resistance,
        "CON": combat.constitution,
        "MOV": combat.movement,
    }


def make_campaign_database(bundle: CampaignBundle):
    import app.engine.skill_component_access as skill_components
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
    from app.data.database.level_units import UniqueUnit, UnitGroup
    from app.data.database.levels import LevelPrefab
    from app.data.database.parties import PartyPrefab
    from app.data.database.skills import SkillPrefab
    from app.data.database.stats import StatPrefab
    from app.data.database.terrain import Terrain
    from app.data.database.translations import Translation
    from app.data.database.units import UnitPrefab
    from app.data.database.weapons import WeaponRank, WeaponType, WexpGain
    from app.events.event_prefab import EventPrefab
    from app.events.regions import Region, RegionHighlight, RegionType
    from app.utilities.data import Data

    db = Database()
    for data_type in db.save_data_types:
        catalog = getattr(db, data_type)
        if isinstance(catalog, CategorizedCatalog):
            catalog.categories = Categories()
    _set_constant(db, "game_nid", bundle.campaign.id)
    _set_constant(db, "title", bundle.campaign.title)
    _set_constant(db, "title_particles", False)
    # An empty credits catalog produces a dead Extras destination. Keep the
    # working sound room and settings, but do not advertise an unimplemented
    # credits screen in the player build.
    _set_constant(db, "title_credits", False)
    _set_constant(db, "turnwheel", False)
    _set_constant(db, "battle_animation", False)
    _set_constant(db, "autogenerate_grey_map_sprites", True)
    _set_constant(db, "music_game_over", None)
    # This fixed vertical slice does not use leveling. Zero combat experience
    # avoids interrupting its short story missions with an unnecessary EXP UI.
    _set_constant(db, "exp_magnitude", 0.0)
    _set_constant(db, "kill_multiplier", 0.0)
    _set_constant(db, "boss_bonus", 0)
    _set_constant(db, "min_exp", 0)

    db.stats.clear()
    for nid, name, maximum, position in STATS:
        db.stats.append(StatPrefab(nid, name, maximum, "Campaign stat", position))
    db.equations.clear()
    for nid, expression in EQUATIONS:
        db.equations.append(Equation(nid, expression))

    terrain_by_id = {}
    for layout in bundle.maps:
        for entry in layout.legend.values():
            terrain_by_id.setdefault(entry.terrain_id, entry)
    terrain_ids = sorted(terrain_by_id)
    db.mcost.terrain_types = terrain_ids
    db.mcost.unit_types = ["Foot"]
    db.mcost.grid = [[terrain_by_id[terrain_id].movement_cost] for terrain_id in terrain_ids]
    for terrain_id in terrain_ids:
        entry = terrain_by_id[terrain_id]
        db.terrain.append(
            Terrain(
                terrain_id,
                entry.name,
                entry.color,
                entry.minimap,
                entry.platform,
                None,
                terrain_id,
            )
        )

    db.weapon_ranks.append(WeaponRank("E", 1))
    for weapon_type in bundle.gameplay.weapon_types:
        db.weapons.append(WeaponType(weapon_type, weapon_type))
    for item in bundle.gameplay.items:
        db.items.append(
            ItemPrefab(item.id, item.name, item.description, components=_components(item))
        )

    protected_unit_ids = {
        placement.id
        for mission in bundle.missions
        for placement in mission.units
        if placement.survival_floor == 1
    }
    if protected_unit_ids:
        guardian_component = skill_components.restore_component(("TrueMiracle", None))
        if guardian_component is None:
            raise RuntimeError("pinned engine no longer provides the TrueMiracle component")
        db.skills.append(
            SkillPrefab(
                "story_guardian",
                "Story Guardian",
                "Prevents a story-critical scripted survivor from falling below 1 HP.",
                components=Data([guardian_component]),
            )
        )

    character_by_id = {character.id: character for character in bundle.characters.characters}
    stat_maximums = {nid: maximum for nid, _, maximum, _ in STATS}
    zero_stats = {nid: 0 for nid, *_ in STATS}
    classes = {}
    for character in bundle.characters.characters:
        combat = character.combat
        if combat.class_id in classes:
            continue
        usable_weapon_types = {combat.weapon_type, *combat.additional_weapon_types}
        wexp = {
            weapon_type: WexpGain(weapon_type in usable_weapon_types, 1, 1)
            for weapon_type in bundle.gameplay.weapon_types
        }
        klass = Klass(
            nid=combat.class_id,
            name=combat.class_name,
            movement_group="Foot",
            bases=_bases(combat),
            growths=zero_stats.copy(),
            growth_bonus=zero_stats.copy(),
            promotion=zero_stats.copy(),
            max_stats=stat_maximums.copy(),
            wexp_gain=wexp,
            map_sprite_nid=combat.map_sprite,
        )
        db.classes.append(klass)
        classes[combat.class_id] = klass

    instance_character: dict[str, str] = {}
    instance_items: dict[str, tuple[str, ...]] = {}
    instance_survival_floor: dict[str, int | None] = {}
    for mission in bundle.missions:
        for placement in mission.units:
            previous = instance_character.setdefault(placement.id, placement.character)
            if previous != placement.character:
                raise ValueError(f"unit instance {placement.id} changes character template")
            previous_items = instance_items.setdefault(placement.id, tuple(placement.items))
            if previous_items != tuple(placement.items):
                raise ValueError(f"unit instance {placement.id} changes instance starting items")
            previous_floor = instance_survival_floor.setdefault(
                placement.id, placement.survival_floor
            )
            if previous_floor != placement.survival_floor:
                raise ValueError(f"unit instance {placement.id} changes survival floor")
    for unit_id, character_id in instance_character.items():
        character = character_by_id[character_id]
        combat = character.combat
        usable_weapon_types = {combat.weapon_type, *combat.additional_weapon_types}
        wexp = {
            weapon_type: WexpGain(weapon_type in usable_weapon_types, 1, 1)
            for weapon_type in bundle.gameplay.weapon_types
        }
        db.units.append(
            UnitPrefab(
                nid=unit_id,
                name=character.name,
                desc=character.description,
                klass=combat.class_id,
                bases=_bases(combat),
                growths=zero_stats.copy(),
                stat_cap_modifiers=zero_stats.copy(),
                starting_items=[
                    [item, False]
                    for item in dict.fromkeys([*combat.starting_items, *instance_items[unit_id]])
                ],
                learned_skills=(
                    [[1, "story_guardian"]] if unit_id in protected_unit_ids else []
                ),
                wexp_gain=wexp,
                portrait_nid=character.portrait,
            )
        )

    party_id = f"{bundle.campaign.id}_party"
    db.parties.append(
        PartyPrefab(party_id, bundle.campaign.party_name, bundle.campaign.party_leader)
    )
    for profile in bundle.gameplay.ai_profiles:
        ai = AIPrefab(profile.id, 20)
        if profile.behavior == "pursue":
            ai.behaviours = [
                AIBehaviour("Attack", "Enemy", -4),
                AIBehaviour.DoNothing(),
                AIBehaviour.DoNothing(),
            ]
        elif profile.behavior == "patrol":
            ai.behaviours = [
                AIBehaviour("Attack", "Enemy", profile.detection_radius),
                AIBehaviour(
                    "Move_to",
                    "Position",
                    -4,
                    target_spec=list(profile.destination),
                ),
                AIBehaviour.DoNothing(),
            ]
        else:
            ai.behaviours = [
                AIBehaviour.DoNothing(),
                AIBehaviour.DoNothing(),
                AIBehaviour.DoNothing(),
            ]
        db.ai.append(ai)

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
    db.translations.append(Translation("_attribution", "Private technical proof of concept"))
    for nid, text in UI_TRANSLATIONS.items():
        db.translations.append(Translation(nid, text))

    mission_by_id = {mission.id: mission for mission in bundle.missions}
    for mission_id in bundle.campaign.chapter_order:
        mission = mission_by_id[mission_id]
        level = LevelPrefab(mission.id, mission.title)
        level.tilemap = f"{mission.map.template}__{mission.map.variant}"
        level.party = party_id
        placement_by_id = {placement.id: placement for placement in mission.units}

        def failure_label(
            failure,
            placements=placement_by_id,
            characters=character_by_id,
        ) -> str:
            if failure.unit and failure.unit in placements:
                placement = placements[failure.unit]
                return characters[placement.character].name
            return (failure.unit or failure.type).replace("_", " ").title()

        level.objective = {
            "simple": mission.objective.display_text,
            "win": mission.objective.display_text,
            "loss": "; ".join(
                f"{failure_label(failure)} must survive"
                for failure in mission.failure_conditions
            ),
        }
        for placement in mission.units:
            character = character_by_id[placement.character]
            level.units.append(
                UniqueUnit(
                    nid=placement.id,
                    team=placement.team,
                    ai=(
                        placement.ai
                        or character.combat.ai
                        or ("do_nothing" if placement.team != "enemy" else None)
                    ),
                    starting_position=placement.position if placement.starts_on_map else None,
                )
            )
        for region_spec in mission.regions:
            region = Region(region_spec.id)
            region.region_type = RegionType(region_spec.region_type)
            region.position = region_spec.position
            region.size = region_spec.size
            region.sub_nid = region_spec.sub_id
            region.only_once = region_spec.only_once
            region.interrupt_move = region_spec.interrupt_move
            if region_spec.highlight:
                region.highlight = RegionHighlight(region_spec.highlight)
            level.regions.append(region)
        placement_by_id = {placement.id: placement for placement in mission.units}
        for reinforcement in mission.reinforcements:
            level.unit_groups.append(
                UnitGroup(
                    reinforcement.id,
                    reinforcement.unit_ids,
                    {
                        unit_id: placement_by_id[unit_id].position
                        for unit_id in reinforcement.unit_ids
                    },
                )
            )
        db.levels.append(level)

    for scene in bundle.scenes:
        event = EventPrefab(scene.id)
        event.level_nid = scene.chapter
        event.trigger = None
        event.condition = "True"
        event.only_once = False
        event.source = compile_scene_v2(scene)
        db.events.append(event)
    for mission in bundle.missions:
        for event_spec in mission.events:
            trigger, condition, source = compile_mission_event(mission, event_spec)
            event = EventPrefab(event_spec.id)
            event.level_nid = mission.id
            event.trigger = trigger
            event.condition = condition
            event.only_once = event_spec.only_once
            event.priority = event_spec.priority
            event.source = source
            db.events.append(event)
        for index, failure in enumerate(mission.failure_conditions):
            if failure.type != "unit_death" or not failure.unit:
                continue
            event = EventPrefab(f"failure_{index}_{failure.unit}")
            event.level_nid = mission.id
            event.trigger = "unit_death"
            event.condition = compile_failure_condition(failure.unit, failure.active_until_flag)
            event.only_once = True
            event.source = "lose_game"
            db.events.append(event)
    return db


def make_campaign_resources(bundle: CampaignBundle, assets: CampaignAssetPaths):
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
    for asset_id, path in sorted(assets.backgrounds.items()):
        resources.panoramas.append(Panorama(asset_id, str(path), 1))
    for asset_id, path in sorted(assets.portraits.items()):
        portrait = PortraitPrefab(asset_id, str(path))
        portrait.blinking_offset = [34, 31]
        portrait.smiling_offset = [34, 48]
        resources.portraits.append(portrait)
    for asset_id, (stand, move) in sorted(assets.map_sprites.items()):
        resources.map_sprites.append(MapSprite(asset_id, str(stand), str(move)))

    tileset_id = assets.tileset_id
    tileset = TileSet(tileset_id, str(assets.tileset))
    for (terrain_id, _lighting, _variant), coordinate in assets.terrain_tiles.items():
        tileset.terrain_grid[coordinate] = terrain_id
    resources.tilesets.append(tileset)
    for layout in bundle.maps:
        for variant in layout.variants:
            tilemap = TileMapPrefab(f"{layout.id}__{variant.id}")
            tilemap.width, tilemap.height = layout.width, layout.height
            tilemap.tilesets = [tileset_id]
            for y, row in enumerate(variant.rows):
                for x, symbol in enumerate(row):
                    terrain_id = layout.legend[symbol].terrain_id
                    visual_variant = hashlib.sha256(
                        f"{layout.id}:{variant.id}:{terrain_id}:{x}:{y}".encode()
                    ).digest()[0] % CAMPAIGN_TILE_VARIANTS
                    tilemap.layers[0].set_sprite(
                        (x, y),
                        tileset_id,
                        assets.terrain_tiles[
                            (terrain_id, variant.lighting, visual_variant)
                        ],
                    )
                    tilemap.layers[0].terrain_grid[(x, y)] = terrain_id
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


def write_campaign_lt_project(
    bundle: CampaignBundle,
    assets: CampaignAssetPaths,
    content_root: Path,
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
    music_design_path = content_root / "design" / "music.yaml"
    music_design = load_music_design(music_design_path) if music_design_path.is_file() else None
    sfx_design_path = content_root / "design" / "sfx.yaml"
    sfx_design = load_sfx_design(sfx_design_path) if sfx_design_path.is_file() else None
    if sfx_design is not None:
        verify_authored_sfx_references(sfx_design, content_root)
    with generated_component_system(engine_root):
        database = make_campaign_database(bundle)
        resources = make_campaign_resources(bundle, assets)
        if music_design is not None:
            apply_lt_music_assignments(database, music_design)
            register_lt_music(resources, music_design, content_root / "assets" / "music")
        if sfx_design is not None:
            register_lt_sfx(resources, sfx_design, content_root / "assets" / "sfx")
        settings = MainSettingsController(company=bundle.campaign.id, product="story-generator")
        settings.set_preference(Preference.SAVE_CHUNKS, False)
        resources.save(output)
        if not database.serialize(output, as_chunks=False):
            raise RuntimeError("LT database serializer reported failure")
    metadata = {
        "date": "1970-01-01 00:00:00",
        "engine_version": VERSION,
        "serialization_version": CURRENT_SERIALIZATION_VERSION,
        "project": bundle.campaign.id,
        "has_fatal_errors": False,
        "as_chunks": False,
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=4, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "ENGINE_COMMIT").write_text(engine_commit + "\n", encoding="utf-8")
    for loose in ("custom_components", "custom_sprites", "system"):
        (output / "resources" / loose).mkdir(parents=True, exist_ok=True)
    custom_sprites = output / "resources" / "custom_sprites"
    for asset_id, source in sorted(assets.ui_sprites.items()):
        # LT's title state looks up the historical sprite key ``logo`` rather
        # than the content-facing asset ID used by the design manifest.
        filename = "logo.png" if asset_id == "title_logo" else f"{asset_id}.png"
        shutil.copyfile(source, custom_sprites / filename)
    provenance = content_root / "design" / "asset_manifest.yaml"
    shutil.copyfile(provenance, output / "ASSET_PROVENANCE.yaml")
    if music_design is not None:
        shutil.copyfile(
            content_root / "assets" / "music" / "music_manifest.json",
            output / "MUSIC_PROVENANCE.json",
        )
    if sfx_design is not None:
        shutil.copyfile(
            content_root / "assets" / "sfx" / "sfx_manifest.json",
            output / "SFX_PROVENANCE.json",
        )
