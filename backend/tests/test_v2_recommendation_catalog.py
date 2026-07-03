from pathlib import Path

import pytest
import yaml

from app.recommendations.catalog_loader import CatalogLoadError, load_catalog
from app.recommendations.safety import CatalogSafetyError


def test_catalog_loads_templates_rules_and_policy():
    templates, rules, policy = load_catalog()
    assert {template.id for template in templates}
    assert {rule.id for rule in rules}
    assert policy["v2_current_execution_policy"]["automatic_execution"] is False


def test_catalog_rejects_unknown_template_ref(tmp_path: Path):
    catalog = tmp_path
    catalog.joinpath("templates.safe.yml").write_text(
        yaml.safe_dump(
            [
                {
                    "id": "bad",
                    "tool_id": "bad",
                    "name": "Bad",
                    "description": "Bad ref",
                    "category": "discovery",
                    "risk_level": "low",
                    "mode": "preview_only",
                    "requires_human_approval": True,
                    "requires_terms_acceptance": False,
                    "template_ref": "missing_template",
                    "expected_inputs": [],
                    "expected_outputs": [],
                    "recommendation_signals": [],
                    "safety_notes": [],
                }
            ]
        )
    )
    catalog.joinpath("recommendation_rules.yml").write_text("[]\n")
    catalog.joinpath("safety_policy.yml").write_text(
        Path("command-catalog/v2/safety_policy.yml").read_text()
    )
    with pytest.raises(CatalogLoadError, match="Unknown template_ref"):
        load_catalog(catalog)


def test_catalog_rejects_blocked_category(tmp_path: Path):
    catalog = tmp_path
    catalog.joinpath("templates.safe.yml").write_text(
        yaml.safe_dump(
            [
                {
                    "id": "bad",
                    "tool_id": "bad",
                    "name": "Bad",
                    "description": "Bad category",
                    "category": "password_spraying",
                    "risk_level": "high",
                    "mode": "gated_high_risk",
                    "requires_human_approval": True,
                    "requires_terms_acceptance": True,
                    "template_ref": "kerbrute_passwordspray_safe_preview",
                    "expected_inputs": [],
                    "expected_outputs": [],
                    "recommendation_signals": [],
                    "safety_notes": [],
                }
            ]
        )
    )
    catalog.joinpath("recommendation_rules.yml").write_text("[]\n")
    catalog.joinpath("safety_policy.yml").write_text(
        Path("command-catalog/v2/safety_policy.yml").read_text()
    )
    with pytest.raises(CatalogSafetyError, match="Blocked"):
        load_catalog(catalog)
