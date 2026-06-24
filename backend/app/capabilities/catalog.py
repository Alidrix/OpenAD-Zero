from functools import lru_cache
from pathlib import Path
from typing import get_args

import yaml
from pydantic import ValidationError

from app.capabilities.schemas import Capability, CapabilityMode, CapabilityStatus

CATALOG_PATH = Path(__file__).with_name("capabilities.yml")
REQUIRED_FIELDS = set(Capability.model_fields)
VALID_STATUSES = set(get_args(CapabilityStatus))
VALID_MODES = set(get_args(CapabilityMode))

class CapabilityCatalogError(RuntimeError):
    pass

@lru_cache(maxsize=1)
def load_capabilities() -> list[Capability]:
    if not CATALOG_PATH.exists():
        raise CapabilityCatalogError(f"Capability catalog not found: {CATALOG_PATH}")
    try:
        raw = yaml.safe_load(CATALOG_PATH.read_text())
    except yaml.YAMLError as exc:
        raise CapabilityCatalogError(f"Invalid capability catalog YAML: {exc}") from exc
    if not isinstance(raw, list):
        raise CapabilityCatalogError("Capability catalog must contain a YAML list.")
    capabilities: list[Capability] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        try:
            capability = Capability.model_validate(item)
        except ValidationError as exc:
            raise CapabilityCatalogError(f"Invalid capability entry at index {index}: {exc}") from exc
        if capability.id in seen:
            raise CapabilityCatalogError(f"Duplicate capability id: {capability.id}")
        seen.add(capability.id)
        capabilities.append(capability)
    return capabilities

# Backward compatible alias for older tests/modules.
def list_capabilities() -> list[Capability]:
    return load_capabilities()

def get_capability(capability_id: str) -> Capability | None:
    return next((c for c in load_capabilities() if c.id == capability_id), None)

def list_categories() -> list[str]:
    return sorted({c.category for c in load_capabilities()})

def list_statuses() -> list[str]:
    return sorted({c.status for c in load_capabilities()})

def creates_manual_card_only(capability: Capability | None) -> bool:
    return bool(capability and capability.execution == "manual_card" and capability.status in {"manual_only", "planned", "lab_only"})
