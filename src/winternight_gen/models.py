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


class StoryBoundarySpec(StrictModel):
    last_allowed_beat: str
    ending_scene: str
    forbidden_terms: list[str] = Field(default_factory=list)


class CampaignConstraints(StrictModel):
    unique_map_layouts_max: int = Field(default=2, ge=1)
    expected_minutes: tuple[int, int]
    original_dialogue_only: bool = True


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


class CombatSpec(StrictModel):
    class_id: str
    class_name: str
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
    weapon_type: str
    additional_weapon_types: list[str] = Field(default_factory=list)
    starting_items: list[str] = Field(default_factory=list)
    map_sprite: str = "graybox_human"
    ai: str | None = None


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


class ItemDefinition(StrictModel):
    id: str
    name: str
    description: str
    kind: Literal["weapon", "healing", "supply"]
    weapon_type: str | None = None
    min_range: int = Field(default=1, ge=1, le=10)
    max_range: int = Field(default=1, ge=1, le=10)
    might: int = Field(default=0, ge=0, le=99)
    hit: int = Field(default=100, ge=0, le=200)
    uses: int = Field(default=1, ge=1, le=99)
    heal_amount: int = Field(default=0, ge=0, le=99)


class AIProfileSpec(StrictModel):
    id: str
    behavior: Literal["pursue", "do_nothing"]


class GameplaySpec(StrictModel):
    schema_version: Literal["0.2"]
    weapon_types: list[str]
    items: list[ItemDefinition]
    ai_profiles: list[AIProfileSpec]

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
    provenance: str
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
    dialogue_policy: Literal["original_paraphrase_only"]
    decisions: list[AdaptationDecision]


class TerrainLegendEntry(StrictModel):
    terrain_id: str
    name: str
    color: tuple[int, int, int]
    movement_cost: int = Field(ge=1, le=99)
    blocks_movement: bool = False


class MapVariantSpec(StrictModel):
    id: str
    rows: list[str] = Field(min_length=4)
    lighting: Literal["day", "night", "firelit"]
    fog: bool = False
    fog_radius: int = Field(default=3, ge=1, le=10)


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
        return self


class MissionMapRef(StrictModel):
    template: str
    variant: str
    seed: int


class ObjectiveSpec(StrictModel):
    type: Literal["tutorial", "escape", "defend_rescue", "search_escape"]
    display_text: str
    unit: str | None = None
    region: str | None = None
    survive_turns: int | None = Field(default=None, ge=1)
    rescue_count: int | None = Field(default=None, ge=1)


class FailureCondition(StrictModel):
    type: Literal["unit_death"]
    unit: str | None = None
    turn: int | None = Field(default=None, ge=1)
    active_until_flag: str | None = None


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
    survival_floor: Literal[1] | None = None


class RegionSpec(StrictModel):
    id: str
    position: tuple[int, int]
    size: tuple[int, int] = (1, 1)
    region_type: Literal["normal", "event", "fog", "vision"] = "event"
    sub_id: str | None = None
    only_once: bool = False
    interrupt_move: bool = False
    highlight: str | None = None


class ReinforcementSpec(StrictModel):
    id: str
    turn: int = Field(ge=2)
    unit_ids: list[str] = Field(min_length=1)


class EventTriggerSpec(StrictModel):
    type: Literal[
        "level_start",
        "level_end",
        "turn_start",
        "unit_wait",
        "unit_death",
        "combat_start",
        "region_interact",
        "talk",
        "call",
    ]
    turn: int | None = Field(default=None, ge=1)
    unit: str | None = None
    unit2: str | None = None
    region: str | None = None


class EventConditionSpec(StrictModel):
    all_flags: list[str] = Field(default_factory=list)
    not_all_flags: list[str] = Field(default_factory=list)
    any_flags: list[str] = Field(default_factory=list)
    flag_false: str | None = None
    turn_at_least: int | None = Field(default=None, ge=1)
    unit_dead: str | None = None


class EventActionSpec(StrictModel):
    type: Literal[
        "play_scene",
        "set_flag",
        "increment_flag",
        "spawn_group",
        "remove_unit",
        "give_item",
        "equip_item",
        "add_talk",
        "remove_talk",
        "mark_visited",
        "show_layer",
        "change_objective",
        "set_fog",
        "skip_save",
        "win",
        "lose",
        "set_next_chapter",
    ]
    target: str | None = None
    value: str | int | bool | None = None


class MissionEventSpec(StrictModel):
    id: str
    trigger: EventTriggerSpec
    condition: EventConditionSpec = Field(default_factory=EventConditionSpec)
    actions: list[EventActionSpec] = Field(min_length=1)
    only_once: bool = True
    priority: int = Field(default=20, ge=0, le=100)


class TargetPlaySpec(StrictModel):
    minimum_turns: int = Field(ge=1)
    maximum_turns: int = Field(ge=1)
    expected_minutes: tuple[int, int]


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
    failure_conditions: list[FailureCondition] = Field(min_length=1)
    map: MissionMapRef
    units: list[MissionUnitSpec] = Field(min_length=1)
    regions: list[RegionSpec] = Field(default_factory=list)
    reinforcements: list[ReinforcementSpec] = Field(default_factory=list)
    events: list[MissionEventSpec] = Field(min_length=1)
    narrative_constraints: dict[str, bool | str | int]
    target_play: TargetPlaySpec

    @model_validator(mode="after")
    def validate_local_ids(self) -> MissionSpec:
        unit_ids = [unit.id for unit in self.units]
        region_ids = [region.id for region in self.regions]
        event_ids = [event.id for event in self.events]
        for kind, ids in (("unit", unit_ids), ("region", region_ids), ("event", event_ids)):
            if len(ids) != len(set(ids)):
                raise ValueError(f"mission {self.id} {kind} IDs must be unique")
        if len({unit.position for unit in self.units if unit.position}) != len(
            [unit for unit in self.units if unit.position]
        ):
            raise ValueError(f"mission {self.id} unit positions must not overlap")
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
        "narration",
        "transition_close",
        "transition_open",
        "ending_card",
    ]
    asset: str | None = None
    text: str | None = Field(default=None, max_length=320)


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
    prompt: str | None = None
    reference_ids: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    seed: int | None = None
    source_hash: str | None = None
    output_hash: str | None = None
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
            if self.type != "reference":
                required["output_hash"] = self.output_hash
            missing = sorted(name for name, value in required.items() if not value)
            if missing:
                raise ValueError(f"approved AI asset {self.id} lacks provenance fields {missing}")
        if self.provenance in {"original", "licensed"} and not self.source_path:
            raise ValueError(f"sourced asset {self.id} requires source_path")
        if (
            self.type in {"map_sprite", "ui", "tileset"}
            and self.provenance != "programmatic_placeholder"
        ):
            raise ValueError(
                f"{self.type} asset {self.id} currently supports "
                "programmatic_placeholder only"
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
        character_ids = {character.id for character in self.characters.characters}
        item_ids = {item.id for item in self.gameplay.items}
        ai_ids = {profile.id for profile in self.gameplay.ai_profiles}
        location_ids = {location.id for location in self.locations.locations}
        beat_by_id = {beat.id: beat for beat in self.story_beats.beats}
        map_by_id = {layout.id: layout for layout in self.maps}
        mission_by_id = {mission.id: mission for mission in self.missions}
        scene_by_id = {scene.id: scene for scene in self.scenes}
        asset_ids = {asset.id for asset in self.asset_manifest.assets}
        asset_by_id = {asset.id: asset for asset in self.asset_manifest.assets}

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
