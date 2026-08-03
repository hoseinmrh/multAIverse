from typing import Annotated, Any, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, WithJsonSchema, model_validator

NORMALIZED_STATS = frozenset(
    {
        "career_level",
        "health",
        "relationships",
        "research_impact",
        "reputation",
        "freedom",
        "stress",
        "happiness",
        "discipline",
        "creativity",
        "chaos",
    }
)


def _key_value_entries_to_dict(value: Any) -> Any:
    """Accept the array shape required by OpenAI Structured Outputs."""

    if not isinstance(value, list):
        return value
    result: dict[str, int] = {}
    for entry in value:
        if not isinstance(entry, dict):
            return value
        key = entry.get("key")
        item_value = entry.get("value")
        if not isinstance(key, str) or not isinstance(item_value, int) or key in result:
            return value
        result[key] = item_value
    return result


def _key_value_array_schema(
    *, value_minimum: int | None = None, value_maximum: int | None = None
) -> dict[str, object]:
    value_schema: dict[str, object] = {"type": "integer"}
    if value_minimum is not None:
        value_schema["minimum"] = value_minimum
    if value_maximum is not None:
        value_schema["maximum"] = value_maximum
    return {
        "type": "array",
        "maxItems": 20,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "key": {"type": "string", "minLength": 1, "maxLength": 120},
                "value": value_schema,
            },
            "required": ["key", "value"],
        },
    }


IntMap = Annotated[
    dict[str, int],
    BeforeValidator(_key_value_entries_to_dict),
    WithJsonSchema(_key_value_array_schema()),
]
ScoreMap = Annotated[
    dict[str, Annotated[int, Field(ge=0, le=100)]],
    BeforeValidator(_key_value_entries_to_dict),
    WithJsonSchema(_key_value_array_schema(value_minimum=0, value_maximum=100)),
]


class SimulationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FinanceEffects(SimulationSchema):
    monthly_income_delta_eur: int = 0
    net_worth_delta_eur: int = 0


class EffectPayload(SimulationSchema):
    stats: IntMap = Field(default_factory=dict)
    finance: FinanceEffects = Field(default_factory=FinanceEffects)
    set_flags: list[str] = Field(default_factory=list)
    remove_flags: list[str] = Field(default_factory=list)
    skill_changes: IntMap = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_effect_fields(self) -> Self:
        unknown_stats = set(self.stats).difference(NORMALIZED_STATS)
        if unknown_stats:
            raise ValueError(f"Unknown statistics: {', '.join(sorted(unknown_stats))}")
        if any(not name.strip() for name in (*self.set_flags, *self.remove_flags)):
            raise ValueError("Flag names must not be empty")
        if any(not name.strip() for name in self.skill_changes):
            raise ValueError("Skill names must not be empty")
        return self


class DelayedEffectSpec(SimulationSchema):
    trigger_after_years: int = Field(ge=1, le=50)
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str = Field(min_length=1, max_length=500)
    effects: EffectPayload


class PersistedDelayedEffect(SimulationSchema):
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    effects: EffectPayload


class ChoiceRequirements(SimulationSchema):
    stats: ScoreMap = Field(default_factory=dict)
    skills: ScoreMap = Field(default_factory=dict)
    required_flags: list[str] = Field(default_factory=list)
    forbidden_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_requirements(self) -> Self:
        unknown_stats = set(self.stats).difference(NORMALIZED_STATS)
        if unknown_stats:
            raise ValueError(f"Unknown required statistics: {', '.join(sorted(unknown_stats))}")
        if any(value < 0 or value > 100 for value in (*self.stats.values(), *self.skills.values())):
            raise ValueError("Required scores must be between 0 and 100")
        return self
