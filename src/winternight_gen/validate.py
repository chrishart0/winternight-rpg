from __future__ import annotations

from pathlib import Path

from .models import (
    AssetManifestSpec,
    CampaignBundle,
    CampaignSpec,
    CanonBibleSpec,
    GameplaySpec,
    MapLayoutSpec,
    MinimalSpec,
    MissionSpec,
    SceneSpecV2,
    load_campaign_bundle,
    load_spec,
)
from .semantic_validation import validate_campaign_semantics


def validate_spec(path: Path) -> MinimalSpec:
    return load_spec(path)


def export_schema(path: Path) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(MinimalSpec.model_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_campaign(root: Path) -> CampaignBundle:
    bundle = load_campaign_bundle(root)
    validate_campaign_semantics(bundle)
    return bundle


def export_campaign_schemas(directory: Path) -> None:
    import json

    directory.mkdir(parents=True, exist_ok=True)
    schemas = {
        "campaign.schema.json": CampaignSpec,
        "canon_bible.schema.json": CanonBibleSpec,
        "mission.schema.json": MissionSpec,
        "scene.schema.json": SceneSpecV2,
        "asset.schema.json": AssetManifestSpec,
        "map.schema.json": MapLayoutSpec,
        "gameplay.schema.json": GameplaySpec,
    }
    for filename, model in schemas.items():
        (directory / filename).write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
