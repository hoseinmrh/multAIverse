from dataclasses import dataclass, field

from app.models.enums import SimulationMode


@dataclass(frozen=True)
class ModeBalance:
    """Mode-specific probability and outcome tuning owned by the engine."""

    positive_outcome_modifier: float
    setback_modifier: float
    volatility: float


@dataclass(frozen=True)
class SimulationBalance:
    """Central balance configuration; formulas do not carry hidden magic numbers."""

    score_min: int = 0
    score_max: int = 100
    skill_min: int = 0
    skill_max: int = 100
    max_effect_stat_change: int = 18
    max_yearly_total_stat_change: int = 25
    max_monthly_income_effect_eur: int = 5_000
    max_net_worth_effect_eur: int = 100_000
    diminishing_returns_strength: float = 0.55
    minimum_positive_modifier_scale: float = 0.25
    high_stress_threshold: int = 80
    extreme_stress_threshold: int = 90
    prolonged_stress_penalty_scale: float = 1.25
    yearly_stress_recovery: int = 4
    extreme_stress_health_penalty: int = 7
    low_health_threshold: int = 45
    burnout_project_threshold: int = 2
    burnout_stress_weight: float = 1.8
    burnout_health_weight: float = 1.3
    burnout_constraint_weight: float = 0.8
    burnout_project_weight: float = 12.0
    happiness_health_weight: float = 0.24
    happiness_relationship_weight: float = 0.25
    happiness_freedom_weight: float = 0.19
    happiness_purpose_weight: float = 0.20
    happiness_financial_weight: float = 0.06
    happiness_stability_weight: float = 0.06
    happiness_stress_penalty: float = 24.0
    happiness_burnout_penalty: float = 0.12
    purpose_career_weight: float = 0.36
    purpose_research_weight: float = 0.28
    purpose_creativity_weight: float = 0.20
    purpose_reputation_weight: float = 0.16
    income_security_midpoint_eur: int = 2_000
    income_security_span_eur: int = 4_000
    annual_income_growth_base: float = 0.015
    annual_income_growth_per_career_point: float = 0.00045
    maximum_annual_income_growth: float = 0.10
    base_savings_rate: float = 0.14
    discipline_savings_modifier: float = 0.08
    stress_savings_penalty: float = 0.06
    startup_savings_penalty: float = 0.10
    positive_net_worth_return: float = 0.02
    negative_net_worth_interest: float = 0.05
    minimum_savings_rate: float = -0.20
    maximum_savings_rate: float = 0.40
    momentum_random_floor: float = 0.08
    momentum_random_ceiling: float = 0.92
    significant_choice_probability: float = 0.78
    opportunity_reputation_weight: float = 0.60
    opportunity_relationship_weight: float = 0.40
    career_skill_weight: float = 0.34
    career_opportunity_weight: float = 0.24
    career_discipline_weight: float = 0.24
    career_level_weight: float = 0.18
    recent_success_momentum_bonus: int = 6
    research_impact_weight: float = 0.28
    research_focus_weight: float = 0.22
    research_network_weight: float = 0.18
    research_skill_weight: float = 0.22
    institutional_support_bonus: int = 10
    startup_execution_weight: float = 0.26
    startup_network_weight: float = 0.14
    startup_capital_weight: float = 0.12
    startup_reputation_weight: float = 0.10
    startup_team_weight: float = 0.14
    startup_creativity_weight: float = 0.10
    startup_timing_weight: float = 0.14
    strong_team_quality: int = 70
    default_team_quality: int = 40
    career_success_gain: int = 4
    success_reputation_gain: int = 2
    progression_setback_penalty: int = -2
    progression_setback_stress: int = 3
    industry_success_income_eur: int = 180
    startup_success_income_eur: int = 250
    startup_setback_net_worth_eur: int = -2_000
    mode: dict[SimulationMode, ModeBalance] = field(
        default_factory=lambda: {
            SimulationMode.REALISTIC: ModeBalance(1.0, 1.0, 1.0),
            SimulationMode.CINEMATIC: ModeBalance(1.08, 1.05, 1.25),
            SimulationMode.UTOPIAN: ModeBalance(1.18, 0.78, 0.85),
            SimulationMode.DARK: ModeBalance(0.82, 1.28, 1.10),
            SimulationMode.CHAOS: ModeBalance(1.0, 1.0, 1.65),
        }
    )


DEFAULT_BALANCE = SimulationBalance()
