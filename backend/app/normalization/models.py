from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NormalizationResult:
    scan_id: str
    source_type: str | None = None
    source_id: str | None = None
    assets_created: int = 0
    services_created: int = 0
    findings_created: int = 0
    signals_created: int = 0
    ad_objects_created: int = 0
    ad_relations_created: int = 0
    attack_paths_created: int = 0
    credential_risks_created: int = 0
    diagnostics_created: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def merge(self, other: NormalizationResult) -> NormalizationResult:
        for k in (
            'assets_created',
            'services_created',
            'findings_created',
            'signals_created',
            'ad_objects_created',
            'ad_relations_created',
            'attack_paths_created',
            'credential_risks_created',
            'diagnostics_created',
        ):
            setattr(self, k, getattr(self, k) + getattr(other, k))
        self.errors += other.errors
        self.warnings += other.warnings
        return self

    def as_dict(self):
        return self.__dict__.copy()
