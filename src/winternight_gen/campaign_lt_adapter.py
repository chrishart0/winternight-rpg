from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .asset_pipeline import (
    CAMPAIGN_TILE_VARIANTS,
    GUIDE_DIRECTION_BITS,
    CampaignAssetPaths,
    GuideTileKey,
)
from .event_compiler import (
    compile_failure_commands,
    compile_failure_condition,
    compile_mission_event,
    compile_region_condition,
    compile_scene_v2,
    scripted_forecast_events,
)
from .lt_adapter import EQUATIONS, FONT_NIDS, STATS, _import_lt, _set_constant
from .lt_runtime import generated_component_system
from .models import CampaignBundle, GuidePathSpec
from .music_pipeline import (
    MusicDesign,
    apply_lt_music_assignments,
    load_music_design,
    lt_music_resource_nids,
    register_lt_music,
)
from .objective_text import synthesize_loss_text
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
    "Spells": "Weave",
    "Spells_desc": "Channel a weave through the One Power.",
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
    "key_INFO": "Dialogue Log",
    "key_AUX": "Auxiliary",
    "key_LEFT": "Left",
    "key_RIGHT": "Right",
    "key_UP": "Up",
    "key_DOWN": "Down",
    "key_START": "Start",
}


COMMAND_UI_TRANSLATIONS = {
    "Return to Mat": "Talk to Mat before entering the Winespring Inn.",
    "Cider Cart": "Lift the marked cider cask.",
    "Inn Cellar": "Carry the cider cask into the cellar.",
}


def _components(item):
    import app.engine.item_component_access as item_components
    from app.utilities.data import Data

    if item.kind == "weapon":
        # LT has no unbreakable component: omitting uses is the engine's own
        # infinite-durability path, and every menu then renders "--" instead of
        # a count that would never move.
        durability = (
            []
            if item.unbreakable
            else [
                ("uses", item.uses),
                ("uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}),
            ]
        )
        values = [
            ("weapon", None),
            ("target_enemy", None),
            ("min_range", item.min_range),
            ("max_range", item.max_range),
            ("damage", item.might),
            ("hit", item.hit),
            ("crit", 0),
            ("weight", 0),
            *durability,
            ("level_exp", None),
            ("weapon_type", item.weapon_type),
            ("weapon_rank", "E"),
        ]
        if item.map_target_cast_anim:
            values.extend(
                [
                    ("map_target_cast_anim", item.map_target_cast_anim),
                    ("map_cast_pose", None),
                ]
            )
        if item.weapon_type == "Magic":
            values.append(("magic", None))
    elif item.kind in {"healing", "healing_spell"}:
        # A channeled weave reaches the Weave (LT "Spells") command; a physical
        # remedy is an ordinary carried item used from the Item command.
        values = [
            ("spell" if item.kind == "healing_spell" else "usable", None),
            ("target_ally", None),
            ("heal", item.heal_amount),
            ("min_range", item.min_range),
            ("max_range", item.max_range),
            ("uses", item.uses),
            ("uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}),
            ("map_hit_add_blend", [96, 144, 232]),
            ("map_cast_pose", None),
        ]
        if item.exp_on_use:
            values.append(("exp", item.exp_on_use))
    else:
        values = [("value", 0)]
    restored = [item_components.restore_component(value) for value in values]
    return Data([component for component in restored if component])


def _bases(combat, stat_bonus: dict[str, int] | None = None) -> dict[str, int]:
    bases = {
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
    for stat, bonus in (stat_bonus or {}).items():
        bases[stat] += bonus
    return bases


def _growths(combat) -> dict[str, int]:
    return {nid: combat.growths.get(nid, 0) for nid, *_ in STATS}


# Each unit instance compiles to a single LT UnitPrefab, so every mission that
# places the instance must agree on the attributes baked into that prefab.
def _require_stable_field(seen: dict, unit_id: str, value, description: str) -> None:
    previous = seen.setdefault(unit_id, value)
    if previous != value:
        raise ValueError(f"unit instance {unit_id} changes {description}")


def make_campaign_database(
    bundle: CampaignBundle, music_design: MusicDesign | None = None
):
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
    # music_game_over is owned by design/music.yaml through
    # apply_lt_music_assignments; pinned LT's default names a track we do not ship.
    _set_constant(db, "music_game_over", None)
    experience = bundle.gameplay.experience
    _set_constant(db, "exp_magnitude", experience.magnitude)
    _set_constant(db, "exp_curve", experience.curve)
    _set_constant(db, "kill_multiplier", experience.kill_multiplier)
    _set_constant(db, "boss_bonus", 0)
    _set_constant(db, "min_exp", experience.minimum)

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
    for index, weapon_type in enumerate(bundle.gameplay.weapon_types):
        weapon = WeaponType(weapon_type, weapon_type)
        weapon.icon_nid = "wexp_icons"
        weapon.icon_index = (index, 0)
        db.weapons.append(weapon)
    for index, item in enumerate(bundle.gameplay.items):
        db.items.append(
            ItemPrefab(
                item.id,
                item.name,
                item.description,
                icon_nid="item_icons",
                icon_index=(index, 0),
                components=_components(item),
            )
        )

    rescue_components = [
        skill_components.restore_component(("hidden", None)),
        skill_components.restore_component(("stat_change", [["MOV", -2]])),
    ]
    if any(component is None for component in rescue_components):
        raise RuntimeError("pinned engine no longer provides the Rescue skill components")
    db.skills.append(
        SkillPrefab(
            "Rescue",
            "Rescue",
            "Carrying another unit reduces movement by 2.",
            components=Data(rescue_components),
        )
    )


    character_by_id = {character.id: character for character in bundle.characters.characters}
    stat_maximums = {nid: maximum for nid, _, maximum, _ in STATS}
    zero_stats = {nid: 0 for nid, *_ in STATS}
    classes = {}

    def _wexp(usable: set[str]) -> dict:
        return {
            weapon_type: WexpGain(weapon_type in usable, 1, 1)
            for weapon_type in bundle.gameplay.weapon_types
        }

    for character in bundle.characters.characters:
        combat = character.combat
        if combat.class_id in classes:
            continue
        usable_weapon_types = {combat.weapon_type, *combat.additional_weapon_types}
        bases = _bases(combat)
        klass = Klass(
            nid=combat.class_id,
            name=combat.class_name,
            movement_group="Foot",
            turns_into=[promotion.class_id for promotion in combat.promotions],
            bases=bases.copy(),
            growths=zero_stats.copy(),
            growth_bonus=zero_stats.copy(),
            promotion=zero_stats.copy(),
            max_stats=stat_maximums.copy(),
            wexp_gain=_wexp(usable_weapon_types),
            map_sprite_nid=combat.map_sprite,
        )
        db.classes.append(klass)
        classes[combat.class_id] = klass
        for promotion in combat.promotions:
            gains = {**zero_stats, **promotion.stat_gains}
            promoted = Klass(
                nid=promotion.class_id,
                name=promotion.class_name,
                tier=2,
                movement_group="Foot",
                promotes_from=combat.class_id,
                bases={stat: value + gains[stat] for stat, value in bases.items()},
                growths=zero_stats.copy(),
                growth_bonus=zero_stats.copy(),
                promotion=gains,
                max_stats=stat_maximums.copy(),
                wexp_gain=_wexp(usable_weapon_types | set(promotion.additional_weapon_types)),
                map_sprite_nid=combat.map_sprite,
            )
            db.classes.append(promoted)
            classes[promotion.class_id] = promoted

    instance_character: dict[str, str] = {}
    instance_items: dict[str, tuple[str, ...]] = {}
    instance_level: dict[str, int | None] = {}
    instance_stat_bonus: dict[str, dict[str, int]] = {}
    instance_phase_inert: dict[str, bool] = {}
    for mission in bundle.missions:
        for placement in mission.units:
            unit_id = placement.id
            _require_stable_field(
                instance_character, unit_id, placement.character, "character template"
            )
            _require_stable_field(
                instance_items, unit_id, tuple(placement.items), "instance starting items"
            )
            _require_stable_field(instance_level, unit_id, placement.level, "starting level")
            _require_stable_field(
                instance_stat_bonus, unit_id, dict(placement.stat_bonus), "stat bonus"
            )
            _require_stable_field(
                instance_phase_inert, unit_id, placement.phase_inert, "phase behavior"
            )
    for unit_id, character_id in instance_character.items():
        character = character_by_id[character_id]
        combat = character.combat
        usable_weapon_types = {combat.weapon_type, *combat.additional_weapon_types}
        mission_level = instance_level[unit_id]
        db.units.append(
            UnitPrefab(
                nid=unit_id,
                name=character.name,
                desc=character.description,
                level=combat.level if mission_level is None else mission_level,
                klass=combat.class_id,
                bases=_bases(combat, instance_stat_bonus[unit_id]),
                growths=_growths(combat),
                stat_cap_modifiers=zero_stats.copy(),
                starting_items=[
                    [item, False]
                    for item in dict.fromkeys([*combat.starting_items, *instance_items[unit_id]])
                ],
                learned_skills=[],
                wexp_gain=_wexp(usable_weapon_types),
                portrait_nid=character.portrait,
                tags=(["Tile"] if instance_phase_inert[unit_id] else []),
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
        elif profile.behavior == "march":
            ai.behaviours = [
                AIBehaviour(
                    "Move_to",
                    "Position",
                    -4,
                    target_spec=list(profile.destination),
                ),
                AIBehaviour.DoNothing(),
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
    db.translations.append(Translation("_attribution", ""))
    for nid, text in UI_TRANSLATIONS.items():
        db.translations.append(Translation(nid, text))
    campaign_commands = {
        region.sub_id for mission in bundle.missions for region in mission.regions if region.sub_id
    }
    for command, text in COMMAND_UI_TRANSLATIONS.items():
        if command in campaign_commands:
            db.translations.append(Translation(f"{command}_desc", text))

    mission_by_id = {mission.id: mission for mission in bundle.missions}
    intro_music: dict[str, str] = {}
    if music_design is not None:
        resource_nids = lt_music_resource_nids(music_design)
        for mission in bundle.missions:
            phase_track = music_design.level_music.get(mission.id, {}).get("player_phase")
            if phase_track:
                intro_music[mission.intro_scene] = resource_nids[phase_track]
    for mission_id in bundle.campaign.chapter_order:
        mission = mission_by_id[mission_id]
        level = LevelPrefab(mission.id, mission.title)
        level.tilemap = f"{mission.map.template}__{mission.map.variant}"
        level.party = party_id

        level.objective = {
            "simple": mission.objective.display_text,
            "win": mission.objective.display_text,
            "loss": synthesize_loss_text(mission, character_by_id),
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
            if not region_spec.starts_active:
                continue
            region = Region(region_spec.id)
            region.region_type = RegionType(region_spec.region_type)
            region.position = region_spec.position
            region.size = region_spec.size
            region.sub_nid = region_spec.sub_id
            region.only_once = region_spec.only_once
            region.interrupt_move = region_spec.interrupt_move
            region.condition = compile_region_condition(region_spec)
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
        source = compile_scene_v2(scene)
        if scene.id in intro_music:
            source = f"music;{intro_music[scene.id]};400\n{source}"
        event.source = source
        db.events.append(event)
    for mission in bundle.missions:
        event_specs = (
            *mission.events,
            *(
                event_spec
                for lesson in mission.scripted_forecast_lessons
                for event_spec in scripted_forecast_events(lesson)
            ),
        )
        for event_spec in event_specs:
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
            event.source = "\n".join(compile_failure_commands(failure))
            db.events.append(event)
    return db




def _guide_tile_key(points: list[tuple[int, int]], index: int) -> GuideTileKey:
    x, y = points[index]
    neighbors = []
    if index:
        neighbors.append(points[index - 1])
    if index + 1 < len(points):
        neighbors.append(points[index + 1])
    mask = sum(GUIDE_DIRECTION_BITS[(nx - x, ny - y)] for nx, ny in neighbors)
    return mask, index == len(points) - 1


def _terrain_visual_variant(
    layout_id: str,
    variant_id: str,
    terrain_id: str,
    x: int,
    y: int,
    house_row: int | None = None,
) -> int:
    if house_row is not None:
        return house_row * 2 + x % 2
    return (
        hashlib.sha256(
            f"{layout_id}:{variant_id}:{terrain_id}:{x}:{y}".encode()
        ).digest()[0]
        % CAMPAIGN_TILE_VARIANTS
    )


def _variant_guide_paths(
    bundle: CampaignBundle, layout_id: str, variant_id: str
) -> dict[str, GuidePathSpec]:
    guide_paths: dict[str, GuidePathSpec] = {}
    for mission in bundle.missions:
        if mission.map.template != layout_id or mission.map.variant != variant_id:
            continue
        for guide in mission.guide_paths:
            previous = guide_paths.setdefault(guide.id, guide)
            if previous.points != guide.points:
                raise ValueError(
                    f"guide layer {guide.id} has conflicting paths on "
                    f"{layout_id}__{variant_id}"
                )
    return guide_paths


def make_campaign_resources(bundle: CampaignBundle, assets: CampaignAssetPaths):
    from app.data.category import Categories, CategorizedCatalog
    from app.data.resources.fonts import Font
    from app.data.resources.icons import IconSheet
    from app.data.resources.map_animations import MapAnimation
    from app.data.resources.map_sprites import MapSprite
    from app.data.resources.panoramas import Panorama
    from app.data.resources.portraits import PortraitPrefab
    from app.data.resources.resources import Resources
    from app.data.resources.tiles import LayerGrid, TileMapPrefab, TileSet

    resources = Resources()
    for data_type in resources.save_data_types:
        catalog = getattr(resources, data_type)
        if isinstance(catalog, CategorizedCatalog):
            catalog.categories = Categories()
    for asset_id, path in sorted(assets.backgrounds.items()):
        resources.panoramas.append(Panorama(asset_id, str(path), 1))
    for asset_id, path in sorted(assets.portraits.items()):
        portrait = PortraitPrefab(asset_id, str(path))
        portrait.blinking_offset = [30, 31]
        portrait.smiling_offset = [30, 48]
        resources.portraits.append(portrait)
    for asset_id, (stand, move) in sorted(assets.map_sprites.items()):
        resources.map_sprites.append(MapSprite(asset_id, str(stand), str(move)))
    weapon_icons = assets.ui_sprites.get("wexp_icons")
    if weapon_icons:
        aliases = {
            weapon_type: (index, 0)
            for index, weapon_type in enumerate(bundle.gameplay.weapon_types)
        }
        resources.icons16.append(IconSheet("wexp_icons", str(weapon_icons), aliases))
    item_icons = assets.ui_sprites.get("item_icons")
    if item_icons:
        aliases = {item.id: (index, 0) for index, item in enumerate(bundle.gameplay.items)}
        resources.icons16.append(IconSheet("item_icons", str(item_icons), aliases))
    # The pinned engine's level-up flow dereferences these animation nids
    # without a guard; an animation-less project hangs on any level up.
    for animation_nid in ("LevelUpMap", "LevelUpBattle", "StatUpSpark"):
        animation = MapAnimation(animation_nid, str(assets.level_up_animation))
        animation.frame_x, animation.frame_y = 4, 1
        animation.num_frames = 4
        animation.speed = 110
        animation.frame_times = [7, 7, 7, 7]
        resources.animations.append(animation)
    for animation_nid, path, frames, speed in (
        ("MapMiss", assets.miss_animation, 6, 120),
        ("StoneThrow", assets.stone_throw_animation, 6, 65),
        ("BallLightning", assets.ball_lightning_animation, 6, 70),
    ):
        animation = MapAnimation(animation_nid, str(path))
        animation.frame_x, animation.frame_y = frames, 1
        animation.num_frames = frames
        animation.speed = speed
        resources.animations.append(animation)

    tileset_id = assets.tileset_id
    tileset = TileSet(tileset_id, str(assets.tileset))
    for (terrain_id, _lighting, _variant), coordinate in assets.terrain_tiles.items():
        tileset.terrain_grid[coordinate] = terrain_id
    resources.tilesets.append(tileset)
    guide_tileset = TileSet(assets.guide_tileset_id, str(assets.guide_tileset))
    resources.tilesets.append(guide_tileset)
    for layout in bundle.maps:
        for variant in layout.variants:
            tilemap = TileMapPrefab(f"{layout.id}__{variant.id}")
            tilemap.width, tilemap.height = layout.width, layout.height
            tilemap.tilesets = [tileset_id, assets.guide_tileset_id]
            for y, row in enumerate(variant.rows):
                for x, symbol in enumerate(row):
                    entry = layout.legend[symbol]
                    terrain_id = entry.terrain_id
                    house_row = None
                    if entry.platform == "House":
                        house_row = int(
                            y > 0
                            and layout.legend[variant.rows[y - 1][x]].terrain_id
                            == terrain_id
                        )
                    visual_variant = _terrain_visual_variant(
                        layout.id, variant.id, terrain_id, x, y, house_row
                    )
                    tilemap.layers[0].set_sprite(
                        (x, y),
                        tileset_id,
                        assets.terrain_tiles[(terrain_id, variant.lighting, visual_variant)],
                    )
                    tilemap.layers[0].terrain_grid[(x, y)] = terrain_id
            for layer_spec in variant.layers:
                layer = LayerGrid(layer_spec.id, tilemap)
                layer.visible = layer_spec.initially_visible
                layer.foreground = layer_spec.foreground
                for coordinate, symbol in layer_spec.tiles.items():
                    x, y = (int(part) for part in coordinate.split(","))
                    terrain_id = layout.legend[symbol].terrain_id
                    visual_variant = _terrain_visual_variant(
                        layout.id, variant.id, terrain_id, x, y
                    )
                    layer.set_sprite(
                        (x, y),
                        tileset_id,
                        assets.terrain_tiles[
                            (terrain_id, variant.lighting, visual_variant)
                        ],
                    )
                    layer.terrain_grid[(x, y)] = terrain_id
                tilemap.layers.append(layer)
            for guide in _variant_guide_paths(bundle, layout.id, variant.id).values():
                layer = LayerGrid(guide.id, tilemap)
                layer.visible = False
                layer.foreground = False
                for index, point in enumerate(guide.points):
                    layer.set_sprite(
                        point,
                        assets.guide_tileset_id,
                        assets.guide_tiles[_guide_tile_key(guide.points, index)],
                    )
                tilemap.layers.append(layer)
            resources.tilemaps.append(tilemap)

    palettes = {
        "black": [(32, 36, 42, 255), (16, 20, 26, 0)],
        "white": [(248, 248, 248, 255), (8, 12, 16, 255)],
        "blue": [(104, 152, 255, 255), (24, 32, 64, 255)],
        "green": [(152, 216, 104, 255), (32, 56, 24, 255)],
        "red": [(232, 80, 80, 255), (72, 24, 24, 255)],
        "grey": [(184, 192, 200, 255), (48, 56, 64, 255)],
        "yellow": [(248, 240, 136, 255), (80, 72, 24, 255)],
        "brown": [(176, 128, 72, 255), (64, 40, 24, 255)],
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
        database = make_campaign_database(bundle, music_design)
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
        "combat_levels": sorted(
            mission.id
            for mission in bundle.missions
            if mission.objective.type != "tutorial"
        ),
        "zero_enemies_by_intent": sorted(
            mission.id
            for mission in bundle.missions
            if mission.narrative_constraints.get("zero_enemies_by_intent") is True
        ),
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
        if asset_id in {"item_icons", "wexp_icons"}:
            continue
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
