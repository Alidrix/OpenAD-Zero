from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.recommendations.models import V2RecommendationRule, V2SafeTemplate
from app.recommendations.safety import validate_policy, validate_template
from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS

ROOT = Path(__file__).resolve().parents[3]
CATALOG_DIR = ROOT / "command-catalog" / "v2"


class CatalogLoadError(ValueError):
    pass


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_catalog(
    catalog_dir: Path = CATALOG_DIR,
) -> tuple[list[V2SafeTemplate], list[V2RecommendationRule], dict]:
    templates_raw = _load_yaml(catalog_dir / "templates.safe.yml") or []
    rules_raw = _load_yaml(catalog_dir / "recommendation_rules.yml") or []
    policy = _load_yaml(catalog_dir / "safety_policy.yml") or {}
    validate_policy(policy)

    templates = [V2SafeTemplate.model_validate(item) for item in templates_raw]
    seen: set[str] = set()
    for template in templates:
        if template.id in seen:
            raise CatalogLoadError(f"Duplicate V2 template id: {template.id}")
        seen.add(template.id)
        if template.template_ref not in COMMAND_TEMPLATE_DEFINITIONS:
            raise CatalogLoadError(f"Unknown template_ref: {template.template_ref}")
        validate_template(template, policy)

    rules = [V2RecommendationRule.model_validate(item) for item in rules_raw]
    template_ids = {template.id for template in templates}
    for rule in rules:
        if rule.recommend.template_id not in template_ids:
            raise CatalogLoadError(
                f"Rule references unknown template_id: {rule.recommend.template_id}"
            )
        if not rule.recommend.reason:
            raise CatalogLoadError(f"Rule requires a recommendation reason: {rule.id}")

    return templates, rules, policy


@lru_cache(maxsize=1)
def get_catalog() -> tuple[list[V2SafeTemplate], list[V2RecommendationRule], dict]:
    return load_catalog()
