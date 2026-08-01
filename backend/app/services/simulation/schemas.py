from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class SimulationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FinanceEffects(SimulationSchema):
    monthly_income_delta_eur: int = 0
    net_worth_delta_eur: int = 0


class EffectPayload(SimulationSchema):
    stats: dict[str, int] = Field(default_factory=dict)
    finance: FinanceEffects = Field(default_factory=FinanceEffects)
    set_flags: list[str] = Field(default_factory=list)
    remove_flags: list[str] = Field(default_factory=list)
    skill_changes: dict[str, int] = Field(default_factory=dict)

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
    stats: dict[str, int] = Field(default_factory=dict)
    skills: dict[str, int] = Field(default_factory=dict)
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
