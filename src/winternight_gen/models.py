from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectSpec(StrictModel):
    id: str
    title: str
    level_id: str
    level_title: str
    objective: str
    loss: str


class MapSpec(StrictModel):
    id: str
    width: int = Field(ge=4, le=64)
    height: int = Field(ge=4, le=64)
    terrain_id: str


class UnitSpec(StrictModel):
    id: str
    name: str
    team: Literal["player", "enemy"]
    position: tuple[int, int]
    portrait: str
    class_id: str
    hp: int = Field(gt=0, le=99)
    strength: int = Field(ge=0, le=99)
    defense: int = Field(ge=0, le=99)


class SceneLine(StrictModel):
    speaker: str
    portrait: str
    position: Literal["left", "right"]
    text: str = Field(min_length=1, max_length=300)


class SceneSpec(StrictModel):
    id: str
    trigger: Literal["level_start", "level_end"]
    background: str
    lines: list[SceneLine] = Field(min_length=1)


class SceneSet(StrictModel):
    intro: SceneSpec
    outro: SceneSpec


class OutcomeSpec(StrictModel):
    event_id: str
    trigger: Literal["unit_death"]
    defeated_unit: str


class AssetSpec(StrictModel):
    provenance: Literal["programmatic_placeholder"]
    background: str
    portraits: list[str]
    tileset: str
    map_sprite: str


class MinimalSpec(StrictModel):
    schema_version: Literal["0.1"]
    project: ProjectSpec
    map: MapSpec
    units: list[UnitSpec] = Field(min_length=2)
    scenes: SceneSet
    victory: OutcomeSpec
    failure: OutcomeSpec
    assets: AssetSpec

    @model_validator(mode="after")
    def validate_references(self) -> MinimalSpec:
        unit_ids = [unit.id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("unit IDs must be unique")
        if {unit.team for unit in self.units} != {"player", "enemy"}:
            raise ValueError("minimal project requires at least one player and one enemy")
        if len({unit.position for unit in self.units}) != len(self.units):
            raise ValueError("unit positions must not overlap")
        for unit in self.units:
            x, y = unit.position
            if not (0 <= x < self.map.width and 0 <= y < self.map.height):
                raise ValueError(f"unit {unit.id} is outside map bounds")
            if unit.portrait not in self.assets.portraits:
                raise ValueError(f"unit {unit.id} references unknown portrait {unit.portrait}")
        for scene in (self.scenes.intro, self.scenes.outro):
            if scene.background != self.assets.background:
                raise ValueError(f"scene {scene.id} references unknown background")
            for line in scene.lines:
                if line.speaker not in unit_ids:
                    raise ValueError(f"scene {scene.id} references unknown speaker {line.speaker}")
                if line.portrait not in self.assets.portraits:
                    raise ValueError(f"scene {scene.id} references unknown portrait")
        if self.victory.defeated_unit not in unit_ids:
            raise ValueError("victory references an unknown unit")
        if self.failure.defeated_unit not in unit_ids:
            raise ValueError("failure references an unknown unit")
        return self


def load_spec(path: Path) -> MinimalSpec:
    return MinimalSpec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


# Full campaign contracts. MinimalSpec remains as the Phase 0 engine fixture.

CanonStatus = Literal["direct", "inferred", "gameplay_invention", "altered"]
Team = Literal["player", "enemy", "other"]

# Stats a unit spec may address by nid. CON and MOV are structural, so neither
# character growths nor mission stat bonuses tune them; only a class promotion
# moves them.
UNIT_STAT_NIDS = frozenset({"HP", "STR", "MAG", "SKL", "SPD", "LCK", "DEF", "RES"})
PROMOTION_STAT_NIDS = UNIT_STAT_NIDS | {"CON", "MOV"}


def _validate_stat_map(
    label: str,
    stats: dict[str, int],
    minimum: int,
    maximum: int,
    allowed: frozenset[str] = UNIT_STAT_NIDS,
) -> None:
    unknown = sorted(set(stats) - allowed)
    if unknown:
        raise ValueError(f"unknown stats in {label}: {unknown}")
    if any(not minimum <= value <= maximum for value in stats.values()):
        raise ValueError(f"{label} values must be between {minimum} and {maximum}")


class StoryBoundarySpec(StrictModel):
    last_allowed_beat: str
    ending_scene: str
    forbidden_terms: list[str] = Field(default_factory=list)


class CampaignConstraints(StrictModel):
    unique_map_layouts_max: int = Field(default=2, ge=1)
    expected_minutes: tuple[int, int]


class CampaignSpec(StrictModel):
    schema_version: Literal["0.2"]
    id: str
    title: str
    content_pack: str
    party_name: str
    party_leader: str
    chapter_order: list[str] = Field(min_length=1)
    entry_chapter: str
    story_boundary: StoryBoundarySpec
    constraints: CampaignConstraints


class CanonBibleBoundarySpec(StrictModel):
    final_beat: str
    final_scene: str
    excluded_topics: list[str] = Field(default_factory=list)


class CanonBibleSpec(StrictModel):
    schema_version: Literal["0.2"]
    id: str
    title: str
    scope_summary: str
    canon_principles: list[str] = Field(min_length=1)
    ending_boundary: CanonBibleBoundarySpec


class PromotionSpec(StrictModel):
    """One tier-2 class a tier-1 class may promote into.

    `stat_gains` carries the gains LT applies on promotion, which is also where
    a promoted class's higher constitution and movement live.
    """

    class_id: str
    class_name: str = Field(max_length=10)
    stat_gains: dict[str, int] = Field(default_factory=dict)
    additional_weapon_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def stat_gains_are_valid(self) -> PromotionSpec:
        _validate_stat_map("stat_gains", self.stat_gains, 0, 20, PROMOTION_STAT_NIDS)
        return self


class CombatSpec(StrictModel):
    class_id: str
    class_name: str = Field(max_length=10)
    level: int = Field(default=1, ge=1, le=20)
    hp: int = Field(gt=0, le=99)
    strength: int = Field(ge=0, le=99)
    magic: int = Field(ge=0, le=99)
    skill: int = Field(ge=0, le=99)
    speed: int = Field(ge=0, le=99)
    luck: int = Field(ge=0, le=99)
    defense: int = Field(ge=0, le=99)
    resistance: int = Field(ge=0, le=99)
    constitution: int = Field(ge=1, le=25)
    movement: int = Field(ge=1, le=15)
    growths: dict[str, int] = Field(default_factory=dict)
    weapon_type: str
    additional_weapon_types: list[str] = Field(default_factory=list)
    starting_items: list[str] = Field(default_factory=list)
    map_sprite: str = "graybox_human"
    ai: str | None = None
    promotions: list[PromotionSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def growths_are_valid(self) -> CombatSpec:
        _validate_stat_map("growths", self.growths, 0, 100)
        return self


class CharacterDefinition(StrictModel):
    id: str
    name: str
    description: str
    portrait: str
    named: bool = True
    narrative_constraints: list[str] = Field(default_factory=list)
    combat: CombatSpec


class CharacterCatalog(StrictModel):
    schema_version: Literal["0.2"]
    characters: list[CharacterDefinition]

    @model_validator(mode="after")
    def unique_ids(self) -> CharacterCatalog:
        ids = [character.id for character in self.characters]
        if len(ids) != len(set(ids)):
            raise ValueError("character IDs must be unique")
        return self

    @model_validator(mode="after")
    def promoted_classes_are_distinct(self) -> CharacterCatalog:
        # Each class compiles to exactly one LT Klass, so a promoted class may
        # not reuse a base class ID or be declared twice.
        base_ids = {character.combat.class_id for character in self.characters}
        promoted: list[str] = [
            promotion.class_id
            for character in self.characters
            for promotion in character.combat.promotions
        ]
        clashes = sorted(set(promoted) & base_ids)
        if clashes:
            raise ValueError(f"promoted class IDs collide with base classes: {clashes}")
        if len(promoted) != len(set(promoted)):
            raise ValueError("promoted class IDs must be unique")
        return self


class ItemDefinition(StrictModel):
    id: str
    name: str
    description: str
    kind: Literal["weapon", "healing", "healing_spell", "supply"]
    weapon_type: str | None = None
    min_range: int = Field(
        default=1,
        ge=0,
        le=10,
        description=(
            "Minimum targeting distance. Defaults to 1; author 0 on a healing "
            "item when its user must remain a legal target."
        ),
    )
    max_range: int = Field(default=1, ge=0, le=10)
    might: int = Field(default=0, ge=0, le=99)
    hit: int = Field(default=100, ge=0, le=200)
    uses: int = Field(default=1, ge=1, le=99)
    unbreakable: bool = Field(
        default=False,
        description=(
            "Omit LT's uses component entirely so the item never breaks and no "
            "menu renders a durability count. Cannot be combined with uses."
        ),
    )
    heal_amount: int = Field(default=0, ge=0, le=99)
    exp_on_use: int = Field(default=0, ge=0, le=100)
    map_target_cast_anim: str | None = None

    @model_validator(mode="after")
    def range_is_ordered(self) -> ItemDefinition:
        if self.min_range > self.max_range:
            raise ValueError("min_range cannot exceed max_range")
        # Compared against the default rather than model_fields_set so a
        # dump-and-revalidate round trip stays legal.
        if self.unbreakable and self.uses != 1:
            raise ValueError("unbreakable items cannot author uses")
        if self.kind != "weapon" and self.weapon_type is not None:
            raise ValueError("only weapons carry a weapon_type")
        return self


class AIProfileSpec(StrictModel):
    id: str
    behavior: Literal["pursue", "do_nothing", "patrol", "march"] = Field(
        description=(
            "AI behavior. march emits only Move_to toward destination and never "
            "emits an Attack behavior."
        )
    )
    destination: tuple[int, int] | None = Field(
        default=None,
        description="Required destination tile for patrol and non-attacking march AI.",
    )
    detection_radius: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def routed_ai_is_valid(self) -> AIProfileSpec:
        if self.behavior == "patrol":
            if self.destination is None or self.detection_radius is None:
                raise ValueError("patrol AI requires destination and detection_radius")
        elif self.behavior == "march":
            if self.destination is None:
                raise ValueError("march AI requires destination")
            if self.detection_radius is not None:
                raise ValueError("march AI does not accept a detection_radius")
        elif self.destination is not None or self.detection_radius is not None:
            raise ValueError("destination and detection_radius require patrol or march AI")
        return self


class ExperienceSpec(StrictModel):
    magnitude: float = Field(gt=0, le=100)
    curve: float = Field(gt=0, le=1)
    kill_multiplier: float = Field(gt=0, le=10)
    minimum: int = Field(ge=0, le=100)


class GameplaySpec(StrictModel):
    schema_version: Literal["0.2"]
    weapon_types: list[str]
    items: list[ItemDefinition]
    ai_profiles: list[AIProfileSpec]
    experience: ExperienceSpec

    @model_validator(mode="after")
    def unique_ids(self) -> GameplaySpec:
        item_ids = [item.id for item in self.items]
        ai_ids = [profile.id for profile in self.ai_profiles]
        if len(item_ids) != len(set(item_ids)) or len(ai_ids) != len(set(ai_ids)):
            raise ValueError("gameplay item and AI IDs must be unique")
        return self


class LocationDefinition(StrictModel):
    id: str
    name: str
    presentation: str
    map_template: str | None = None
    variants: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class LocationCatalog(StrictModel):
    schema_version: Literal["0.2"]
    locations: list[LocationDefinition]


class StoryBeatSpec(StrictModel):
    id: str
    canon_status: CanonStatus
    chronology: int = Field(ge=0)
    summary: str
    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    predecessors: list[str] = Field(default_factory=list)
    source_locator: str
    constraints: list[str] = Field(default_factory=list)


class StoryBeatCatalog(StrictModel):
    schema_version: Literal["0.2"]
    beats: list[StoryBeatSpec]

    @model_validator(mode="after")
    def graph_is_valid(self) -> StoryBeatCatalog:
        ids = [beat.id for beat in self.beats]
        if len(ids) != len(set(ids)):
            raise ValueError("story beat IDs must be unique")
        known = set(ids)
        for beat in self.beats:
            missing = set(beat.predecessors) - known
            if missing:
                raise ValueError(f"beat {beat.id} has unknown predecessors {sorted(missing)}")
        return self


class AdaptationDecision(StrictModel):
    id: str
    canon_status: CanonStatus
    decision: str
    source_beats: list[str] = Field(min_length=1)
    rationale: str
    canon_effect: str


class AdaptationRules(StrictModel):
    schema_version: Literal["0.2"]
    decisions: list[AdaptationDecision]


class TerrainLegendEntry(StrictModel):
    terrain_id: str
    name: str = Field(max_length=12)
    color: tuple[int, int, int]
    minimap: Literal[
        "Grass",
        "House",
        "Forest",
        "Thicket",
        "Floor",
        "Pillar",
        "Ruins",
        "Wall",
        "River",
        "Lava",
    ]
    platform: Literal[
        "Plains",
        "Road",
        "Forest",
        "Thicket",
        "Floor",
        "Pillar",
        "Ruins",
        "Wall",
        "House",
    ]
    movement_cost: int = Field(ge=1, le=99)
    blocks_movement: bool = False
    visual_style: Literal["default", "doorway", "doorstep"] = "default"


class MapLayerSpec(StrictModel):
    id: str
    initially_visible: bool = False
    foreground: bool = False
    tiles: dict[str, str] = Field(min_length=1)


class MapVariantSpec(StrictModel):
    id: str
    rows: list[str] = Field(min_length=4)
    lighting: Literal["day", "night", "firelit"]
    fog: bool = False
    fog_radius: int = Field(default=3, ge=1, le=10)
    layers: list[MapLayerSpec] = Field(default_factory=list)



class MapLayoutSpec(StrictModel):
    schema_version: Literal["0.2"]
    id: str
    width: int = Field(ge=8, le=64)
    height: int = Field(ge=8, le=64)
    legend: dict[str, TerrainLegendEntry]
    variants: list[MapVariantSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_grid(self) -> MapLayoutSpec:
        variant_ids = [variant.id for variant in self.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError(f"map {self.id} variant IDs must be unique")
        for variant in self.variants:
            layer_ids = [layer.id for layer in variant.layers]
            if len(layer_ids) != len(set(layer_ids)):
                raise ValueError(f"map {self.id}/{variant.id} layer IDs must be unique")
            if len(variant.rows) != self.height:
                raise ValueError(f"map {self.id}/{variant.id} row count does not match height")
            for row in variant.rows:
                if len(row) != self.width:
                    raise ValueError(f"map {self.id}/{variant.id} row width is invalid")
                unknown = set(row) - set(self.legend)
                if unknown:
                    raise ValueError(
                        f"map {self.id}/{variant.id} has unknown tiles {sorted(unknown)}"
                    )
            for layer in variant.layers:
                for coordinate, symbol in layer.tiles.items():
                    parts = coordinate.split(",")
                    if len(parts) != 2 or any(not part.isdigit() for part in parts):
                        raise ValueError(
                            f"map {self.id}/{variant.id}/{layer.id} has invalid "
                            f"coordinate {coordinate!r}"
                        )
                    x, y = (int(part) for part in parts)
                    if not (0 <= x < self.width and 0 <= y < self.height):
                        raise ValueError(
                            f"map {self.id}/{variant.id}/{layer.id} coordinate "
                            f"{coordinate!r} is out of bounds"
                        )
                    if symbol not in self.legend:
                        raise ValueError(
                            f"map {self.id}/{variant.id}/{layer.id} has unknown tile "
                            f"{symbol!r}"
                        )
        return self


class MissionMapRef(StrictModel):
    template: str
    variant: str
    seed: int


class ObjectiveSpec(StrictModel):
    type: Literal["tutorial", "escape", "defend_rescue", "search_escape"]
    display_text: str = Field(
        description=(
            "Initial map banner and persistent Win Conditions text. Separate LT "
            "display lines with commas; each banner line is at most 30 characters "
            "and each persistent Objective-screen line is at most 16 characters."
        )
    )
    unit: str | None = None
    region: str | None = None
    survive_turns: int | None = Field(default=None, ge=1)
    rescue_count: int | None = Field(default=None, ge=1)


class FailureCondition(StrictModel):
    type: Literal["unit_death"]
    unit: str | None = None
    turn: int | None = Field(default=None, ge=1)
    active_until_flag: str | None = None
    failure_scene: str | None = Field(
        default=None,
        description=(
            "Optional scene ID played before lose_game when this failure condition fires."
        ),
    )


class MissionUnitSpec(StrictModel):
    id: str
    character: str
    team: Team
    position: tuple[int, int] | None
    group: str | None = None
    starts_on_map: bool = True
    ai: str | None = None
    items: list[str] = Field(default_factory=list)
    role: Literal["combatant", "civilian", "objective"] = "combatant"
    level: int | None = Field(default=None, ge=1, le=20)
    stat_bonus: dict[str, int] = Field(default_factory=dict)
    phase_inert: bool = False

    @model_validator(mode="after")
    def stat_bonuses_are_valid(self) -> MissionUnitSpec:
        _validate_stat_map("stat_bonus", self.stat_bonus, -20, 20)
        return self

    @model_validator(mode="after")
    def phase_inert_excludes_players(self) -> MissionUnitSpec:
        if self.phase_inert and self.team == "player":
            raise ValueError("player units cannot be phase-inert")
        return self


class RegionSpec(StrictModel):
    id: str
    position: tuple[int, int]
    size: tuple[int, int] = (1, 1)
    region_type: Literal["normal", "event", "fog", "vision"] = "event"
    sub_id: str | None = None
    only_once: bool = False
    interrupt_move: bool = False
    highlight: str | None = None
    required_flags: list[str] = Field(default_factory=list)
    allowed_units: list[str] = Field(default_factory=list)
    starts_active: bool = True


class ReinforcementSpec(StrictModel):
    id: str
    turn: int | None = Field(default=None, ge=2)
    unit_ids: list[str] = Field(min_length=1)


class EventTriggerSpec(StrictModel):
    type: Literal[
        "level_start",
        "level_end",
        "turn_start",
        "enemy_turn_start",
        "unit_wait",
        "unit_death",
        "combat_start",
        "combat_end",
        "region_interact",
        "talk",
        "call",
    ]
    turn: int | None = Field(default=None, ge=1)
    unit: str | None = None
    unit2: str | None = None
    region: str | None = None
    item: str | None = None

    @model_validator(mode="after")
    def item_requires_combat_trigger(self) -> EventTriggerSpec:
        if self.item and self.type not in {"combat_start", "combat_end"}:
            raise ValueError("trigger item requires combat_start or combat_end")
        return self


class UnitInRegionSpec(StrictModel):
    unit: str = Field(description="Mission unit ID whose current position is tested.")
    region: str = Field(
        description=(
            "Mission region ID tested through game.level.regions so deactivated "
            "regions cannot match."
        )
    )


class TriggerUnitInRegionSpec(StrictModel):
    team: Team
    region: str


class LevelVarCompareSpec(StrictModel):
    name: str = Field(min_length=1)
    op: Literal["ge", "le", "eq"]
    value: int = Field(strict=True)


class EventConditionSpec(StrictModel):
    all_flags: list[str] = Field(default_factory=list)
    not_all_flags: list[str] = Field(default_factory=list)
    any_flags: list[str] = Field(default_factory=list)
    flag_false: str | None = None
    turn_at_least: int | None = Field(default=None, ge=1)
    turn_at_most: int | None = Field(
        default=None,
        ge=1,
        description="Matches only while the current turn is at or below this turn.",
    )
    unit_dead: str | None = None
    unit_in_region: UnitInRegionSpec | None = Field(
        default=None,
        description=(
            "Matches while the named unit occupies an active level region; "
            "deactivated regions never match."
        ),
    )
    trigger_unit_in_region: TriggerUnitInRegionSpec | None = Field(
        default=None,
        description=(
            "Matches when the triggering unit belongs to the named team and occupies "
            "an active level region."
        ),
    )
    trigger_unit_team: Team | None = None
    level_var_compare: LevelVarCompareSpec | None = Field(
        default=None,
        description="Compares a numeric level variable to an authored integer.",
    )

    @model_validator(mode="after")
    def turn_window_is_ordered(self) -> EventConditionSpec:
        if (
            self.turn_at_least is not None
            and self.turn_at_most is not None
            and self.turn_at_least > self.turn_at_most
        ):
            raise ValueError("turn_at_least cannot exceed turn_at_most")
        return self


# LT locks these tag NIDs into every project (TagCatalog.default_tags); an unknown
# name would make LT's remove_tag command a silent no-op.
LT_UNIT_TAGS = frozenset(
    {
        "Lord",
        "Boss",
        "Required",
        "Mounted",
        "Flying",
        "Armor",
        "Dragon",
        "AutoPromote",
        "NoAutoPromote",
        "Convoy",
        "AdjConvoy",
        "Tile",
        "Blacklist",
        "ZeroMove",
        "Horse",
    }
)


# Characters that would break out of a single compiled LT event-script line.
UNSAFE_EVENT_SCRIPT_CHARACTERS = frozenset(";{}\n\r")


class EventActionSpec(StrictModel):
    type: Literal[
        "play_scene",
        "tutorial_text",
        "permadeath_choice",
        "set_flag",
        "increment_flag",
        "set_current_hp",
        "spawn_group",
        "remove_unit",
        "move_unit",
        "give_item",
        "equip_item",
        "remove_item",
        "change_team",
        "change_ai",
        "remove_tag",
        "script_combat",
        "start_forecast_lesson",
        "add_talk",
        "remove_talk",
        "mark_visited",
        "activate_region",
        "deactivate_region",
        "refresh_unit",
        "highlight_target",
        "show_layer",
        "hide_layer",
        "change_objective",
        "flash_objective",
        "set_fog",
        "skip_save",
        "pair_up",
        "separate",
        "win",
        "lose",
        "set_next_chapter",
    ] = Field(
        description=(
            "Event action. start_forecast_lesson uses target=<lesson id> from "
            "scripted_forecast_lessons; it spawns the lesson's sole inert target, "
            "lends and equips its item, shows its prompt, refreshes the actor, and "
            "highlights the target. permadeath_choice uses target=<unit id> and "
            "value=<display name> to explain permanent playable death and offer "
            "Restart or Continue. change_objective accepts target simple (30 "
            "characters per comma-separated banner line), win/loss (16 characters "
            "per persistent Objective-screen line), or both (simple plus win); its "
            "value may embed LT display expressions such as {v:level_var}, which "
            "are measured by rendered width. flash_objective takes no target or "
            "value and makes the persistent objective panel blink and settle back "
            "from an enlarged draw so a changed objective cannot be missed. "
            "pair_up maps target=follower and value=carrier to LT pair_up; separate "
            "maps target=carrier to LT separate. remove_tag maps target=unit and "
            "value=tag to LT remove_tag."
        )
    )
    target: str | None = Field(
        default=None,
        description=(
            "Action target. For start_forecast_lesson use a "
            "scripted_forecast_lessons id. For change_objective use simple, win, "
            "loss, or both; both updates the transient map banner and persistent "
            "Win Conditions."
        ),
    )
    value: str | int | bool | None = Field(
        default=None,
        description=(
            "Action value. change_objective strings use commas as display-line "
            "breaks: 30 characters per simple line and 16 per win/loss line."
        ),
    )

    @model_validator(mode="after")
    def action_arguments_are_supported(self) -> EventActionSpec:
        if self.type == "change_objective":
            if self.target not in {"simple", "win", "loss", "both"}:
                raise ValueError(
                    "change_objective target must be simple, win, loss, or both"
                )
            if not isinstance(self.value, str) or not self.value:
                raise ValueError("change_objective value must be a non-empty string")
        elif self.type == "tutorial_text":
            if not isinstance(self.value, str) or not self.value:
                raise ValueError("tutorial_text value must be a non-empty string")
            if UNSAFE_EVENT_SCRIPT_CHARACTERS.intersection(self.value):
                raise ValueError("tutorial_text contains unsafe event-script characters")
        elif self.type == "permadeath_choice":
            if (
                not self.target
                or not isinstance(self.value, str)
                or not self.value
                or UNSAFE_EVENT_SCRIPT_CHARACTERS.intersection(self.value)
            ):
                raise ValueError(
                    "permadeath_choice requires a safe target unit and display name"
                )
            if len(f"{self.value} died and is gone as a playable unit.") > 56:
                raise ValueError("permadeath_choice display name exceeds the text box")
        elif self.type == "script_combat":
            commands = str(self.value or "").split(",")
            valid = {"hit1", "hit2", "crit1", "crit2", "miss1", "miss2", "--", "end"}
            if not commands or commands[-1] != "end" or any(
                command not in valid for command in commands
            ):
                raise ValueError("script_combat requires a valid combat script ending in end")
        elif self.type == "start_forecast_lesson":
            if not self.target or self.value is not None:
                raise ValueError(
                    "start_forecast_lesson requires target=<lesson id> and no value"
                )
        elif self.type == "flash_objective":
            if self.target is not None or self.value is not None:
                raise ValueError("flash_objective takes no target or value")
        elif self.type == "change_team" and self.value not in {"player", "enemy", "other"}:
            raise ValueError("change_team value must be player, enemy, or other")
        elif self.type == "remove_tag":
            if not self.target or self.value not in LT_UNIT_TAGS:
                raise ValueError(
                    "remove_tag requires target=<unit id> and a known LT tag value"
                )
        elif self.type == "move_unit":
            coordinates = str(self.value or "").split(",")
            if len(coordinates) != 2 or any(
                not coordinate.isdigit() for coordinate in coordinates
            ):
                raise ValueError("move_unit value must be an x,y position")
        elif self.type == "set_current_hp":
            if (
                not self.target
                or not isinstance(self.value, int)
                or isinstance(self.value, bool)
                or self.value <= 0
            ):
                raise ValueError(
                    "set_current_hp requires target=<unit id> and a positive integer value"
                )
        return self


class ScriptedForecastLessonSpec(StrictModel):
    id: str = Field(description="Stable lesson ID referenced by start_forecast_lesson.")
    actor: str = Field(description="Player mission-unit ID that performs the attack.")
    target: str = Field(
        description=(
            "Unarmed enemy mission-unit ID removed automatically after the authored miss."
        )
    )
    item: str = Field(
        description=(
            "Temporary weapon given and equipped at lesson start, then removed at completion."
        )
    )
    target_group: str = Field(
        description=(
            "Reinforcement group containing only target; start_forecast_lesson spawns it."
        )
    )
    outcome: Literal["miss"] = Field(
        default="miss",
        description=(
            "Authored combat outcome. Only miss is supported: the compiler emits "
            "set_combat_script;miss1,end, so no strike deals damage or grants a kill."
        ),
    )
    prompt: str = Field(
        min_length=1,
        max_length=320,
        description=(
            "One safe tutorial text box shown before control returns for real "
            "Attack, target-select, forecast, and confirm input."
        ),
    )
    completion_actions: list[EventActionSpec] = Field(
        min_length=1,
        description=(
            "Actions emitted after the forced miss, after the temporary item and "
            "target are removed; use these to continue the authored event chain."
        ),
    )

    @model_validator(mode="after")
    def prompt_is_event_safe(self) -> ScriptedForecastLessonSpec:
        if set(self.prompt) & set(";{}#\n\r"):
            raise ValueError("scripted forecast lesson prompt contains unsafe characters")
        if any(
            action.type in {"script_combat", "start_forecast_lesson"}
            for action in self.completion_actions
        ):
            raise ValueError(
                "scripted forecast completion_actions cannot start or script combat"
            )
        return self


class MissionEventSpec(StrictModel):
    id: str
    trigger: EventTriggerSpec
    condition: EventConditionSpec = Field(default_factory=EventConditionSpec)
    actions: list[EventActionSpec] = Field(min_length=1)
    only_once: bool = True
    priority: int = Field(default=20, ge=0, le=100)

    @model_validator(mode="after")
    def trigger_unit_condition_has_unit_context(self) -> MissionEventSpec:
        if (
            self.condition.trigger_unit_in_region or self.condition.trigger_unit_team
        ) and self.trigger.type not in {
            "unit_wait",
            "unit_death",
            "combat_start",
            "combat_end",
            "region_interact",
            "talk",
        }:
            raise ValueError(
                "a trigger-unit condition requires a trigger with unit context"
            )
        return self


class TargetPlaySpec(StrictModel):
    minimum_turns: int = Field(ge=1)
    maximum_turns: int = Field(ge=1)
    expected_minutes: tuple[int, int]


class GuidePathSpec(StrictModel):
    id: str
    points: list[tuple[int, int]] = Field(min_length=2)
    destination_region: str

    @model_validator(mode="after")
    def points_form_one_contiguous_path(self) -> GuidePathSpec:
        if len(set(self.points)) != len(self.points):
            raise ValueError(f"guide path {self.id} repeats a tile")
        if any(
            abs(x2 - x1) + abs(y2 - y1) != 1
            for (x1, y1), (x2, y2) in zip(self.points, self.points[1:], strict=False)
        ):
            raise ValueError(f"guide path {self.id} points must be tile-adjacent")
        for index, (x1, y1) in enumerate(self.points):
            if any(
                abs(x2 - x1) + abs(y2 - y1) == 1
                for x2, y2 in self.points[index + 2 :]
            ):
                raise ValueError(
                    f"guide path {self.id} has non-consecutive adjacent tiles"
                )
        return self


class MissionSpec(StrictModel):
    schema_version: Literal["0.2"]
    id: str
    title: str
    chapter_index: int = Field(ge=0)
    canon_status: CanonStatus
    source_beats: list[str] = Field(min_length=1)
    intro_scene: str
    outro_scene: str
    objective: ObjectiveSpec
    failure_conditions: list[FailureCondition] = Field(default_factory=list)
    map: MissionMapRef
    units: list[MissionUnitSpec] = Field(min_length=1)
    regions: list[RegionSpec] = Field(default_factory=list)
    guide_paths: list[GuidePathSpec] = Field(default_factory=list)
    reinforcements: list[ReinforcementSpec] = Field(default_factory=list)
    scripted_forecast_lessons: list[ScriptedForecastLessonSpec] = Field(
        default_factory=list,
        description=(
            "Guided one-attack lessons. Each is started exactly once with "
            "start_forecast_lesson; the compiler creates hidden combat-start and "
            "combat-end events that force miss1,end, remove the target, and run "
            "completion_actions."
        ),
    )
    events: list[MissionEventSpec] = Field(min_length=1)
    narrative_constraints: dict[str, bool | str | int]
    target_play: TargetPlaySpec

    @model_validator(mode="after")
    def validate_local_ids(self) -> MissionSpec:
        unit_ids = [unit.id for unit in self.units]
        region_ids = [region.id for region in self.regions]
        event_ids = [event.id for event in self.events]
        lesson_ids = [lesson.id for lesson in self.scripted_forecast_lessons]
        guide_ids = [guide.id for guide in self.guide_paths]
        for kind, ids in (
            ("unit", unit_ids),
            ("region", region_ids),
            ("event", event_ids),
            ("guide path", guide_ids),
            ("scripted forecast lesson", lesson_ids),
        ):
            if len(ids) != len(set(ids)):
                raise ValueError(f"mission {self.id} {kind} IDs must be unique")
        if len({unit.position for unit in self.units if unit.position}) != len(
            [unit for unit in self.units if unit.position]
        ):
            raise ValueError(f"mission {self.id} unit positions must not overlap")

        units_by_id = {unit.id: unit for unit in self.units}
        groups_by_id = {group.id: group for group in self.reinforcements}
        hidden_event_ids = {
            generated_id
            for lesson_id in lesson_ids
            for generated_id in (
                f"{lesson_id}__script",
                f"{lesson_id}__complete",
            )
        }
        if hidden_event_ids & set(event_ids):
            raise ValueError(
                f"mission {self.id} event IDs collide with scripted forecast events"
            )

        starts: list[str] = []
        for event in self.events:
            for action in event.actions:
                if action.type == "start_forecast_lesson":
                    starts.append(action.target)
                    if not event.only_once:
                        raise ValueError(
                            "start_forecast_lesson must belong to an only-once event"
                        )
        if len(starts) != len(set(starts)) or set(starts) != set(lesson_ids):
            raise ValueError(
                "each scripted forecast lesson must be started exactly once"
            )

        for lesson in self.scripted_forecast_lessons:
            actor = units_by_id.get(lesson.actor)
            target = units_by_id.get(lesson.target)
            group = groups_by_id.get(lesson.target_group)
            if actor is None or actor.team != "player":
                raise ValueError(
                    f"scripted forecast lesson {lesson.id} actor must be a player unit"
                )
            if (
                target is None
                or target.team != "enemy"
                or target.ai != "do_nothing"
                or target.starts_on_map
                or target.group != lesson.target_group
                or target.items
            ):
                raise ValueError(
                    f"scripted forecast lesson {lesson.id} target must be an off-map, "
                    "unarmed do_nothing enemy in its target_group"
                )
            if group is None or group.unit_ids != [lesson.target]:
                raise ValueError(
                    f"scripted forecast lesson {lesson.id} target_group must contain "
                    "only its target"
                )
        return self


class SceneCastSpec(StrictModel):
    character: str
    portrait: str
    position: Literal["left", "right", "center"]


class DialogueSceneBeat(StrictModel):
    type: Literal["dialogue"]
    speaker: str
    intent: str
    text: str = Field(min_length=1, max_length=320)


class ActionSceneBeat(StrictModel):
    type: Literal["action"]
    action: Literal[
        "sound",
        "show_portrait",
        "narration",
        "transition_close",
        "transition_open",
        "ending_card",
    ]
    asset: str | None = None
    text: str | None = Field(default=None, max_length=320)

    @model_validator(mode="after")
    def validate_action_payload(self) -> ActionSceneBeat:
        if self.action in {"sound", "show_portrait", "ending_card"} and not self.asset:
            raise ValueError(f"{self.action} requires an asset")
        if self.action == "narration" and not self.text:
            raise ValueError("narration requires text")
        return self


SceneBeat = Annotated[DialogueSceneBeat | ActionSceneBeat, Field(discriminator="type")]


class SceneSpecV2(StrictModel):
    schema_version: Literal["0.2"]
    id: str
    chapter: str
    canon_status: CanonStatus
    source_beats: list[str] = Field(min_length=1)
    trigger: EventTriggerSpec
    background: str
    cast: list[SceneCastSpec] = Field(default_factory=list)
    beats: list[SceneBeat] = Field(min_length=1)

    @model_validator(mode="after")
    def dialogue_remains_visible(self) -> SceneSpecV2:
        transition_closed = False
        for beat in self.beats:
            if isinstance(beat, ActionSceneBeat):
                if beat.action == "transition_close":
                    transition_closed = True
                elif beat.action == "transition_open":
                    transition_closed = False
                elif transition_closed and beat.action == "narration":
                    raise ValueError(
                        f"scene {self.id} cannot place narration behind a closed transition"
                    )
            elif transition_closed:
                raise ValueError(
                    f"scene {self.id} cannot place dialogue behind a closed transition"
                )
        return self


class SceneFile(StrictModel):
    schema_version: Literal["0.2"]
    scenes: list[SceneSpecV2] = Field(min_length=1)


class AssetManifestEntry(StrictModel):
    id: str
    type: Literal["portrait", "background", "tileset", "map_sprite", "ui", "reference"]
    subject_id: str
    variant: str
    provenance: Literal["programmatic_placeholder", "ai_generated", "original", "licensed"]
    source_path: str | None = None
    processed_path: str | None = None
    stand_processed_path: str | None = None
    move_processed_path: str | None = None
    prompt: str | None = None
    reference_ids: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    seed: int | None = None
    source_hash: str | None = None
    output_hash: str | None = None
    stand_output_hash: str | None = None
    move_output_hash: str | None = None
    source_grid: tuple[int, int] | None = None
    source_cell: tuple[int, int] | None = None
    processing_profile: Literal["standard", "dark_wounded"] = "standard"
    processing_version: str
    approval_status: Literal["placeholder", "pending", "approved", "rejected"]
    license_note: str

    @model_validator(mode="after")
    def validate_provenance(self) -> AssetManifestEntry:
        if (self.source_grid is None) != (self.source_cell is None):
            raise ValueError("source_grid and source_cell must be provided together")
        if self.source_grid and self.source_cell:
            columns, rows = self.source_grid
            column, row = self.source_cell
            if columns < 1 or rows < 1:
                raise ValueError("source_grid dimensions must be positive")
            if not (0 <= column < columns and 0 <= row < rows):
                raise ValueError("source_cell is outside source_grid")
        if self.provenance == "ai_generated" and self.approval_status == "approved":
            required = {
                "source_path": self.source_path,
                "prompt": self.prompt,
                "provider": self.provider,
                "model": self.model,
                "source_hash": self.source_hash,
            }
            if self.type == "map_sprite":
                required.update(
                    stand_processed_path=self.stand_processed_path,
                    move_processed_path=self.move_processed_path,
                    stand_output_hash=self.stand_output_hash,
                    move_output_hash=self.move_output_hash,
                )
            elif self.type != "reference":
                required["output_hash"] = self.output_hash
            missing = sorted(name for name, value in required.items() if not value)
            if missing:
                raise ValueError(f"approved AI asset {self.id} lacks provenance fields {missing}")
        if self.provenance in {"original", "licensed"} and not self.source_path:
            raise ValueError(f"sourced asset {self.id} requires source_path")
        if self.type == "tileset" and self.provenance != "programmatic_placeholder":
            raise ValueError(
                f"{self.type} asset {self.id} currently supports programmatic_placeholder only"
            )
        if self.type == "map_sprite" and self.provenance not in {
            "programmatic_placeholder",
            "ai_generated",
        }:
            raise ValueError(
                f"map_sprite asset {self.id} supports programmatic_placeholder "
                "or ai_generated provenance"
            )
        return self


class AssetManifestSpec(StrictModel):
    schema_version: Literal["0.2"]
    assets: list[AssetManifestEntry]

    @model_validator(mode="after")
    def unique_ids(self) -> AssetManifestSpec:
        ids = [asset.id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("asset IDs must be unique")
        return self


class CampaignBundle(StrictModel):
    campaign: CampaignSpec
    canon_bible: CanonBibleSpec
    characters: CharacterCatalog
    gameplay: GameplaySpec
    locations: LocationCatalog
    story_beats: StoryBeatCatalog
    adaptation_rules: AdaptationRules
    maps: list[MapLayoutSpec]
    missions: list[MissionSpec]
    scenes: list[SceneSpecV2]
    asset_manifest: AssetManifestSpec

    @model_validator(mode="after")
    def validate_cross_references(self) -> CampaignBundle:
        character_by_id = {
            character.id: character for character in self.characters.characters
        }
        character_ids = set(character_by_id)
        item_by_id = {item.id: item for item in self.gameplay.items}
        item_ids = set(item_by_id)
        ai_ids = {profile.id for profile in self.gameplay.ai_profiles}
        location_ids = {location.id for location in self.locations.locations}
        beat_by_id = {beat.id: beat for beat in self.story_beats.beats}
        map_by_id = {layout.id: layout for layout in self.maps}
        mission_by_id = {mission.id: mission for mission in self.missions}
        scene_by_id = {scene.id: scene for scene in self.scenes}
        asset_ids = {asset.id for asset in self.asset_manifest.assets}
        asset_by_id = {asset.id: asset for asset in self.asset_manifest.assets}

        if self.canon_bible.id != self.campaign.id:
            raise ValueError("canon bible ID must match campaign ID")
        canon_boundary = self.canon_bible.ending_boundary
        campaign_boundary = self.campaign.story_boundary
        if (
            canon_boundary.final_beat != campaign_boundary.last_allowed_beat
            or canon_boundary.final_scene != campaign_boundary.ending_scene
            or set(canon_boundary.excluded_topics) != set(campaign_boundary.forbidden_terms)
        ):
            raise ValueError("canon bible boundary must match campaign story boundary")

        for asset in self.asset_manifest.assets:
            unresolved_references = set(asset.reference_ids) - asset_ids
            if unresolved_references:
                raise ValueError(
                    f"asset {asset.id} references unknown assets {sorted(unresolved_references)}"
                )

        if self.campaign.chapter_order != [
            mission.id
            for mission in sorted(self.missions, key=lambda mission: mission.chapter_index)
        ]:
            raise ValueError("campaign chapter order must match mission chapter indexes")
        if self.campaign.entry_chapter not in mission_by_id:
            raise ValueError("campaign entry chapter is unknown")
        if self.campaign.entry_chapter != self.campaign.chapter_order[0]:
            raise ValueError("campaign entry chapter must be first in chapter order")
        entry_player_units = {
            unit.id
            for unit in mission_by_id[self.campaign.entry_chapter].units
            if unit.team == "player"
        }
        if self.campaign.party_leader not in entry_player_units:
            raise ValueError("campaign party leader must be a player unit in the entry chapter")
        map_layout_count = len({mission.map.template for mission in self.missions})
        if map_layout_count > self.campaign.constraints.unique_map_layouts_max:
            raise ValueError("campaign exceeds unique tactical map layout budget")
        campaign_minimum, campaign_maximum = self.campaign.constraints.expected_minutes
        authored_minimum = sum(mission.target_play.expected_minutes[0] for mission in self.missions)
        authored_maximum = sum(mission.target_play.expected_minutes[1] for mission in self.missions)
        if authored_minimum < campaign_minimum or authored_maximum > campaign_maximum:
            raise ValueError(
                "mission duration ranges exceed campaign duration contract: "
                f"campaign={self.campaign.constraints.expected_minutes}, "
                f"missions=({authored_minimum}, {authored_maximum})"
            )

        for beat in self.story_beats.beats:
            if set(beat.characters) - character_ids:
                raise ValueError(f"beat {beat.id} references unknown characters")
            if set(beat.locations) - location_ids:
                raise ValueError(f"beat {beat.id} references unknown locations")
        for character in self.characters.characters:
            if set(character.combat.starting_items) - item_ids:
                raise ValueError(f"character {character.id} references unknown items")
            if character.combat.ai and character.combat.ai not in ai_ids:
                raise ValueError(f"character {character.id} references unknown AI")
            if (
                character.portrait not in asset_by_id
                or asset_by_id[character.portrait].type != "portrait"
            ):
                raise ValueError(f"character {character.id} references a non-portrait asset")
            if (
                character.combat.map_sprite not in asset_by_id
                or asset_by_id[character.combat.map_sprite].type != "map_sprite"
            ):
                raise ValueError(f"character {character.id} references a non-map-sprite asset")
        for decision in self.adaptation_rules.decisions:
            if set(decision.source_beats) - set(beat_by_id):
                raise ValueError(f"adaptation {decision.id} references unknown beats")

        for mission in self.missions:
            if set(mission.source_beats) - set(beat_by_id):
                raise ValueError(f"mission {mission.id} references unknown beats")
            if mission.intro_scene not in scene_by_id or mission.outro_scene not in scene_by_id:
                raise ValueError(f"mission {mission.id} has unknown intro or outro scene")
            if mission.map.template not in map_by_id:
                raise ValueError(f"mission {mission.id} references unknown map")
            layout = map_by_id[mission.map.template]
            variant_ids = {variant.id for variant in layout.variants}
            if mission.map.variant not in variant_ids:
                raise ValueError(f"mission {mission.id} references unknown map variant")
            for unit in mission.units:
                if unit.character not in character_ids:
                    raise ValueError(f"mission {mission.id} unit {unit.id} has unknown character")
                if unit.position:
                    x, y = unit.position
                    if not (0 <= x < layout.width and 0 <= y < layout.height):
                        raise ValueError(f"mission {mission.id} unit {unit.id} is out of bounds")
                if set(unit.items) - item_ids:
                    raise ValueError(f"mission {mission.id} unit {unit.id} has unknown items")
                if unit.ai and unit.ai not in ai_ids:
                    raise ValueError(f"mission {mission.id} unit {unit.id} has unknown AI")
            for region in mission.regions:
                x, y = region.position
                width, height = region.size
                if x < 0 or y < 0 or x + width > layout.width or y + height > layout.height:
                    raise ValueError(f"mission {mission.id} region {region.id} is out of bounds")
            unit_ids = {unit.id for unit in mission.units}
            for reinforcement in mission.reinforcements:
                if set(reinforcement.unit_ids) - unit_ids:
                    raise ValueError(f"mission {mission.id} reinforcement references unknown units")
            units_by_id = {unit.id: unit for unit in mission.units}
            for lesson in mission.scripted_forecast_lessons:
                if lesson.item not in item_by_id:
                    raise ValueError(
                        f"mission {mission.id} scripted forecast lesson {lesson.id} "
                        "references an unknown item"
                    )
                item = item_by_id[lesson.item]
                if item.kind != "weapon":
                    raise ValueError(
                        f"mission {mission.id} scripted forecast lesson {lesson.id} "
                        "requires a weapon item"
                    )
                actor = units_by_id[lesson.actor]
                actor_combat = character_by_id[actor.character].combat
                actor_items = {*actor_combat.starting_items, *actor.items}
                if lesson.item in actor_items:
                    raise ValueError(
                        f"mission {mission.id} scripted forecast lesson {lesson.id} "
                        "item must be temporary"
                    )
                usable_weapon_types = {
                    actor_combat.weapon_type,
                    *actor_combat.additional_weapon_types,
                }
                if item.weapon_type not in usable_weapon_types:
                    raise ValueError(
                        f"mission {mission.id} scripted forecast lesson {lesson.id} "
                        "item is incompatible with its actor"
                    )
                target = units_by_id[lesson.target]
                target_combat = character_by_id[target.character].combat
                if target_combat.starting_items:
                    raise ValueError(
                        f"mission {mission.id} scripted forecast lesson {lesson.id} "
                        "target character must be unarmed"
                    )

        for scene in self.scenes:
            if scene.chapter not in mission_by_id:
                raise ValueError(f"scene {scene.id} references unknown chapter")
            if set(scene.source_beats) - set(beat_by_id):
                raise ValueError(f"scene {scene.id} references unknown beats")
            if (
                scene.background not in asset_by_id
                or asset_by_id[scene.background].type != "background"
            ):
                raise ValueError(f"scene {scene.id} references a non-background asset")
            for cast in scene.cast:
                if cast.character not in character_ids or cast.portrait not in asset_ids:
                    raise ValueError(f"scene {scene.id} has unknown cast or portrait")
                if asset_by_id[cast.portrait].type != "portrait":
                    raise ValueError(f"scene {scene.id} cast references a non-portrait asset")
            speakers = {cast.character for cast in scene.cast}
            for beat in scene.beats:
                if isinstance(beat, DialogueSceneBeat) and beat.speaker not in speakers:
                    raise ValueError(f"scene {scene.id} dialogue speaker is not in cast")
                if isinstance(beat, ActionSceneBeat) and beat.action == "show_portrait":
                    if not beat.asset or beat.asset not in {
                        member.portrait for member in scene.cast
                    }:
                        raise ValueError(f"scene {scene.id} show_portrait asset is not in cast")

        boundary = self.campaign.story_boundary
        if boundary.last_allowed_beat not in beat_by_id:
            raise ValueError("campaign boundary beat is unknown")
        if boundary.ending_scene not in scene_by_id:
            raise ValueError("campaign ending scene is unknown")
        ending_scene = scene_by_id[boundary.ending_scene]
        if boundary.last_allowed_beat not in ending_scene.source_beats:
            raise ValueError("ending scene does not include the boundary beat")
        boundary_chronology = beat_by_id[boundary.last_allowed_beat].chronology
        later_beats = sorted(
            beat.id for beat in self.story_beats.beats if beat.chronology > boundary_chronology
        )
        if later_beats:
            raise ValueError(f"story beats exceed campaign boundary: {later_beats}")
        if ending_scene.chapter != self.campaign.chapter_order[-1]:
            raise ValueError("campaign ending scene is not in the final chapter")
        final_mission = mission_by_id[self.campaign.chapter_order[-1]]
        outro_calls = [
            action.target
            for event in final_mission.events
            if event.trigger.type == "level_end"
            for action in event.actions
            if action.type == "play_scene"
        ]
        if boundary.ending_scene not in outro_calls:
            raise ValueError("campaign ending scene is not called by the final outro")
        ending_index = outro_calls.index(boundary.ending_scene)
        for scene_id in outro_calls[ending_index + 1 :]:
            scene = scene_by_id[scene_id]
            if any(isinstance(beat, DialogueSceneBeat) for beat in scene.beats) or any(
                not isinstance(beat, ActionSceneBeat) or beat.action != "ending_card"
                for beat in scene.beats
            ):
                raise ValueError(f"story-bearing scene {scene_id} follows campaign ending scene")
        all_dialogue = " ".join(
            beat.text.lower()
            for scene in self.scenes
            for beat in scene.beats
            if isinstance(beat, DialogueSceneBeat)
        )
        forbidden = [term for term in boundary.forbidden_terms if term.lower() in all_dialogue]
        if forbidden:
            raise ValueError(f"dialogue crosses story boundary with forbidden terms {forbidden}")
        return self


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_campaign_bundle(root: Path) -> CampaignBundle:
    scene_paths = sorted((root / "design/scenes").rglob("*.yaml"))
    scene_files = [SceneFile.model_validate(_read_yaml(path)) for path in scene_paths]
    map_paths = sorted((root / "design/maps").glob("*.yaml"))
    mission_paths = sorted((root / "design/missions").glob("*.yaml"))
    return CampaignBundle(
        campaign=CampaignSpec.model_validate(_read_yaml(root / "design/campaign.yaml")),
        canon_bible=CanonBibleSpec.model_validate(_read_yaml(root / "source/canon_bible.yaml")),
        characters=CharacterCatalog.model_validate(_read_yaml(root / "source/characters.yaml")),
        gameplay=GameplaySpec.model_validate(_read_yaml(root / "design/gameplay.yaml")),
        locations=LocationCatalog.model_validate(_read_yaml(root / "source/locations.yaml")),
        story_beats=StoryBeatCatalog.model_validate(_read_yaml(root / "source/story_beats.yaml")),
        adaptation_rules=AdaptationRules.model_validate(
            _read_yaml(root / "source/adaptation_rules.yaml")
        ),
        maps=[MapLayoutSpec.model_validate(_read_yaml(path)) for path in map_paths],
        missions=[MissionSpec.model_validate(_read_yaml(path)) for path in mission_paths],
        scenes=[scene for scene_file in scene_files for scene in scene_file.scenes],
        asset_manifest=AssetManifestSpec.model_validate(
            _read_yaml(root / "design/asset_manifest.yaml")
        ),
    )
