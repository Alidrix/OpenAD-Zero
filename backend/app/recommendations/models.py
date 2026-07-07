from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class V2SafeTemplate(BaseModel):
    id: str
    tool_id: str
    name: str
    description: str
    category: str
    risk_level: str
    mode: str
    requires_human_approval: bool
    requires_terms_acceptance: bool
    template_ref: str
    expected_inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    recommendation_signals: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class V2RuleWhen(BaseModel):
    signals: list[str] = Field(default_factory=list)


class V2RuleRecommendation(BaseModel):
    template_id: str
    reason: str
    priority: str = 'low'


class V2RecommendationRule(BaseModel):
    id: str
    when: V2RuleWhen
    recommend: V2RuleRecommendation


class V2Recommendation(BaseModel):
    recommendation_id: str
    template_id: str
    name: str
    reason: str
    priority: str
    risk_level: str
    mode: str
    requires_human_approval: bool
    safety_notes: list[str]


class V2CommandPreview(BaseModel):
    template_id: str
    tool_id: str
    name: str
    argv_preview: list[str]
    required_params: list[str]
    missing_params: list[str]
    safety_notes: list[str]
    risk_level: str
    mode: str
    executable: bool = False
    automatic_execution_allowed: bool = False


class V2PreviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    template_id: str
    params: dict[str, str] = Field(default_factory=dict)
