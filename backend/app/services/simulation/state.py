import math
from dataclasses import dataclass, replace

from app.services.simulation.balance import DEFAULT_BALANCE, SimulationBalance
from app.services.simulation.schemas import ChoiceRequirements, EffectPayload


def clamp_score(value: int | float, balance: SimulationBalance = DEFAULT_BALANCE) -> int:
    return round(max(balance.score_min, min(balance.score_max, value)))


def clamp_change(value: int, limit: int) -> int:
    return max(-limit, min(limit, value))


@dataclass(frozen=True)
class SimulationState:
    year: int
    age: int
    location: str
    career_title: str
    career_level: int
    monthly_income_eur: int
    net_worth_eur: int
    health: int
    relationships: int
    research_impact: int
    reputation: int
    freedom: int
    stress: int
    happiness: int
    discipline: int
    creativity: int
    chaos: int
    skills: tuple[tuple[str, int], ...]
    active_flags: frozenset[str]

    def skill(self, name: str) -> int:
        return dict(self.skills).get(name, 0)

    def skills_dict(self) -> dict[str, int]:
        return dict(self.skills)


@dataclass(frozen=True)
class MomentumScores:
    career: int
    research: int
    startup: int


@dataclass(frozen=True)
class FinancialResult:
    monthly_income_eur: int
    net_worth_eur: int
    annual_net_worth_change_eur: int


def _modifier(current: int, change: int, stress: int, balance: SimulationBalance) -> int:
    bounded = clamp_change(change, balance.max_effect_stat_change)
    if bounded > 0:
        scale = max(
            balance.minimum_positive_modifier_scale,
            1.0 - (current / balance.score_max) * balance.diminishing_returns_strength,
        )
        bounded = round(bounded * scale)
    elif bounded < 0 and stress >= balance.high_stress_threshold:
        bounded = round(bounded * balance.prolonged_stress_penalty_scale)
    return clamp_score(current + bounded, balance)


def apply_effects(
    state: SimulationState,
    effects: EffectPayload,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> SimulationState:
    scores = {
        "career_level": state.career_level,
        "health": state.health,
        "relationships": state.relationships,
        "research_impact": state.research_impact,
        "reputation": state.reputation,
        "freedom": state.freedom,
        "stress": state.stress,
        "happiness": state.happiness,
        "discipline": state.discipline,
        "creativity": state.creativity,
        "chaos": state.chaos,
    }
    for field_name, change in effects.stats.items():
        scores[field_name] = _modifier(scores[field_name], change, state.stress, balance)

    income_delta = clamp_change(
        effects.finance.monthly_income_delta_eur,
        balance.max_monthly_income_effect_eur,
    )
    net_worth_delta = clamp_change(
        effects.finance.net_worth_delta_eur,
        balance.max_net_worth_effect_eur,
    )
    skills = state.skills_dict()
    for skill_name, change in effects.skill_changes.items():
        skills[skill_name] = clamp_score(skills.get(skill_name, 0) + change, balance)
    flags = set(state.active_flags)
    flags.difference_update(effects.remove_flags)
    flags.update(effects.set_flags)
    return replace(
        state,
        career_level=scores["career_level"],
        monthly_income_eur=max(0, state.monthly_income_eur + income_delta),
        net_worth_eur=state.net_worth_eur + net_worth_delta,
        health=scores["health"],
        relationships=scores["relationships"],
        research_impact=scores["research_impact"],
        reputation=scores["reputation"],
        freedom=scores["freedom"],
        stress=scores["stress"],
        happiness=scores["happiness"],
        discipline=scores["discipline"],
        creativity=scores["creativity"],
        chaos=scores["chaos"],
        skills=tuple(sorted(skills.items())),
        active_flags=frozenset(flags),
    )


def requirements_met(state: SimulationState, requirements: ChoiceRequirements) -> bool:
    if any(getattr(state, name) < minimum for name, minimum in requirements.stats.items()):
        return False
    if any(state.skill(name) < minimum for name, minimum in requirements.skills.items()):
        return False
    if not set(requirements.required_flags).issubset(state.active_flags):
        return False
    return not set(requirements.forbidden_flags).intersection(state.active_flags)


def calculate_burnout_risk(
    state: SimulationState,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> int:
    stress_risk = (
        max(0, state.stress - balance.high_stress_threshold) * balance.burnout_stress_weight
    )
    health_risk = (
        max(0, balance.low_health_threshold - state.health) * balance.burnout_health_weight
    )
    discipline_constraint = (
        max(0, state.discipline - state.freedom) * balance.burnout_constraint_weight
    )
    active_projects = sum(1 for flag in state.active_flags if flag.startswith("project:"))
    project_risk = float(max(0, active_projects - balance.burnout_project_threshold + 1))
    project_risk *= balance.burnout_project_weight
    return clamp_score(stress_risk + health_risk + discipline_constraint + project_risk, balance)


def _income_security(monthly_income_eur: int, balance: SimulationBalance) -> float:
    relative = (
        monthly_income_eur - balance.income_security_midpoint_eur
    ) / balance.income_security_span_eur
    return 50.0 + 50.0 * math.tanh(relative)


def calculate_happiness(
    state: SimulationState,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> int:
    purpose = clamp_score(
        balance.purpose_career_weight * state.career_level
        + balance.purpose_research_weight * state.research_impact
        + balance.purpose_creativity_weight * state.creativity
        + balance.purpose_reputation_weight * state.reputation,
        balance,
    )
    stability = clamp_score(100 - state.chaos, balance)
    weighted = (
        state.health * balance.happiness_health_weight
        + state.relationships * balance.happiness_relationship_weight
        + state.freedom * balance.happiness_freedom_weight
        + purpose * balance.happiness_purpose_weight
        + _income_security(state.monthly_income_eur, balance) * balance.happiness_financial_weight
        + stability * balance.happiness_stability_weight
    )
    stress_penalty = balance.happiness_stress_penalty * (state.stress / 100) ** 2
    burnout_penalty = calculate_burnout_risk(state, balance) * balance.happiness_burnout_penalty
    return clamp_score(weighted - stress_penalty - burnout_penalty, balance)


def _skill_average(state: SimulationState, names: tuple[str, ...]) -> float:
    available = [state.skill(name) for name in names if state.skill(name) > 0]
    return sum(available) / len(available) if available else 0.0


def calculate_momentum(
    state: SimulationState,
    *,
    market_timing: int = 50,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> MomentumScores:
    career_skill = _skill_average(
        state,
        ("applied_ai", "software_engineering", "leadership", "robotics", "research"),
    )
    opportunity = (
        balance.opportunity_reputation_weight * state.reputation
        + balance.opportunity_relationship_weight * state.relationships
    )
    career = balance.career_skill_weight * career_skill
    career += balance.career_opportunity_weight * opportunity
    career += balance.career_discipline_weight * state.discipline
    career += balance.career_level_weight * state.career_level
    if "recent_success" in state.active_flags:
        career += balance.recent_success_momentum_bonus

    research_skill = _skill_average(state, ("research", "robotics", "optimization"))
    focus = clamp_score(state.discipline - max(0, state.stress - 60) // 2)
    network = (state.relationships + state.reputation) / 2
    research = balance.research_impact_weight * state.research_impact
    research += balance.research_focus_weight * focus
    research += balance.research_network_weight * network
    research += balance.research_skill_weight * research_skill
    if "funded_research" in state.active_flags:
        research += balance.institutional_support_bonus

    execution = _skill_average(state, ("product", "software_engineering", "fundraising"))
    capital = clamp_score(50 + state.net_worth_eur / 2_000)
    team_quality = (
        balance.strong_team_quality
        if "strong_team" in state.active_flags
        else balance.default_team_quality
    )
    startup = balance.startup_execution_weight * execution
    startup += balance.startup_network_weight * network
    startup += balance.startup_capital_weight * capital
    startup += balance.startup_reputation_weight * state.reputation
    startup += balance.startup_team_weight * team_quality
    startup += balance.startup_creativity_weight * state.creativity
    startup += balance.startup_timing_weight * clamp_score(market_timing)
    return MomentumScores(
        career=clamp_score(career),
        research=clamp_score(research),
        startup=clamp_score(startup),
    )


def calculate_finances(
    state: SimulationState,
    career_momentum: int,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> FinancialResult:
    growth_rate = balance.annual_income_growth_base
    growth_rate += career_momentum * balance.annual_income_growth_per_career_point
    growth_rate = min(balance.maximum_annual_income_growth, growth_rate)
    new_income = max(0, round(state.monthly_income_eur * (1 + growth_rate)))

    savings_rate = balance.base_savings_rate
    savings_rate += (state.discipline / 100) * balance.discipline_savings_modifier
    savings_rate -= (state.stress / 100) * balance.stress_savings_penalty
    if "startup_path" in state.active_flags:
        savings_rate -= balance.startup_savings_penalty
    savings_rate = max(
        balance.minimum_savings_rate, min(balance.maximum_savings_rate, savings_rate)
    )
    annual_savings = round(new_income * 12 * savings_rate)
    asset_change = round(
        state.net_worth_eur
        * (
            balance.positive_net_worth_return
            if state.net_worth_eur >= 0
            else balance.negative_net_worth_interest
        )
    )
    annual_change = annual_savings + asset_change
    return FinancialResult(
        monthly_income_eur=new_income,
        net_worth_eur=state.net_worth_eur + annual_change,
        annual_net_worth_change_eur=annual_change,
    )
