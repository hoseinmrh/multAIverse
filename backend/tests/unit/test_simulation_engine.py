from dataclasses import FrozenInstanceError, replace

import pytest
from pydantic import ValidationError

from app.models.enums import SimulationMode
from app.services.simulation import (
    DueEffectInput,
    EffectPayload,
    SeededRandom,
    SimulationEngine,
    SimulationState,
    apply_effects,
    calculate_burnout_risk,
    calculate_finances,
    calculate_happiness,
    calculate_momentum,
    clamp_score,
    derive_seed,
)


def sample_state(**changes: object) -> SimulationState:
    state = SimulationState(
        year=2026,
        age=25,
        location="Milan",
        career_title="Engineer",
        career_level=45,
        monthly_income_eur=3_000,
        net_worth_eur=12_000,
        health=75,
        relationships=65,
        research_impact=45,
        reputation=42,
        freedom=55,
        stress=58,
        happiness=68,
        discipline=82,
        creativity=78,
        chaos=30,
        skills=(("applied_ai", 70), ("leadership", 40), ("software_engineering", 75)),
        active_flags=frozenset({"industry_path"}),
    )
    return replace(state, **changes)  # type: ignore[arg-type]


def test_seeded_random_streams_are_stable_and_namespaced() -> None:
    first = [SeededRandom(90210).stream(2028, "events").random() for _ in range(3)]
    second = [SeededRandom(90210).stream(2028, "events").random() for _ in range(3)]

    assert first == second
    assert derive_seed(90210, 2028, "events") == derive_seed(90210, 2028, "events")
    assert derive_seed(90210, 2028, "events") != derive_seed(90210, 2028, "finance")


def test_simulation_state_is_deeply_immutable() -> None:
    state = sample_state()

    with pytest.raises(FrozenInstanceError):
        state.stress = 1  # type: ignore[misc]
    with pytest.raises(AttributeError):
        state.active_flags.add("changed")  # type: ignore[attr-defined]

    assert state.skills == (("applied_ai", 70), ("leadership", 40), ("software_engineering", 75))


def test_effects_are_clamped_capped_and_use_diminishing_returns() -> None:
    state = sample_state(health=98, stress=95, net_worth_eur=10)
    changed = apply_effects(
        state,
        EffectPayload(
            stats={"health": 500, "relationships": -500, "stress": 500},
            finance={"monthly_income_delta_eur": -99_999, "net_worth_delta_eur": -999_999},
            skill_changes={"leadership": 500},
        ),
    )

    assert changed.health == 100
    assert changed.relationships >= 0
    assert changed.stress == 100
    assert changed.monthly_income_eur == 0
    assert changed.net_worth_eur == -99_990
    assert changed.skill("leadership") == 100
    assert clamp_score(-1_000) == 0
    assert clamp_score(1_000) == 100

    calm_penalty = apply_effects(sample_state(stress=50), EffectPayload(stats={"health": -10}))
    stressed_penalty = apply_effects(sample_state(stress=90), EffectPayload(stats={"health": -10}))
    assert stressed_penalty.health < calm_penalty.health


def test_effect_schema_rejects_unknown_or_malformed_fields() -> None:
    with pytest.raises(ValidationError, match="Unknown statistics"):
        EffectPayload.model_validate({"stats": {"luck": 12}})
    with pytest.raises(ValidationError):
        EffectPayload.model_validate({"finance": {"monthly_income_eur": 100}})
    with pytest.raises(ValidationError):
        EffectPayload.model_validate({"stats": {"stress": "many"}})


def test_probabilistic_delayed_effects_resolve_at_zero_and_one_probability() -> None:
    engine = SimulationEngine()
    state = sample_state()
    due = (
        DueEffectInput(
            key="certain",
            trigger_year=2027,
            probability=1.0,
            effects=EffectPayload(set_flags=["certain_consequence"]),
        ),
        DueEffectInput(
            key="impossible",
            trigger_year=2027,
            probability=0.0,
            effects=EffectPayload(set_flags=["impossible_consequence"]),
        ),
    )

    prepared = engine.prepare_year(
        state,
        universe_seed=1234,
        mode=SimulationMode.REALISTIC,
        due_effects=due,
    )

    assert "certain_consequence" in prepared.state_before_significant_event.active_flags
    assert "impossible_consequence" not in prepared.state_before_significant_event.active_flags
    assert [resolution.occurred for resolution in prepared.delayed_resolutions] == [True, False]


def test_happiness_is_nonlinear_and_high_income_cannot_override_distress() -> None:
    balanced = sample_state(monthly_income_eur=2_500, stress=25, health=85, relationships=85)
    wealthy_but_distressed = sample_state(
        monthly_income_eur=25_000,
        stress=98,
        health=30,
        relationships=25,
        freedom=20,
        active_flags=frozenset({"industry_path", "project:a", "project:b", "project:c"}),
    )

    assert calculate_happiness(balanced) > calculate_happiness(wealthy_but_distressed)


def test_burnout_risk_combines_stress_health_constraints_and_projects() -> None:
    low_risk = sample_state(stress=45, health=80, freedom=75, active_flags=frozenset())
    high_risk = sample_state(
        stress=94,
        health=35,
        freedom=20,
        discipline=92,
        active_flags=frozenset({"project:a", "project:b", "project:c"}),
    )

    assert calculate_burnout_risk(low_risk) < 20
    assert calculate_burnout_risk(high_risk) > 75


def test_financial_calculation_updates_income_savings_assets_and_debt() -> None:
    solvent = calculate_finances(sample_state(), career_momentum=80)
    indebted = calculate_finances(
        sample_state(net_worth_eur=-20_000, stress=90, active_flags=frozenset({"startup_path"})),
        career_momentum=20,
    )

    assert solvent.monthly_income_eur > 3_000
    assert solvent.net_worth_eur > 12_000
    assert solvent.annual_net_worth_change_eur == solvent.net_worth_eur - 12_000
    assert indebted.annual_net_worth_change_eur < solvent.annual_net_worth_change_eur


def test_momentum_responds_to_career_research_and_startup_inputs() -> None:
    base = sample_state()
    research_state = replace(
        base,
        research_impact=80,
        skills=(("research", 90), ("robotics", 85), ("optimization", 82)),
        active_flags=frozenset({"phd_path", "funded_research"}),
    )
    startup_state = replace(
        base,
        reputation=75,
        net_worth_eur=100_000,
        skills=(("product", 90), ("software_engineering", 90), ("fundraising", 85)),
        active_flags=frozenset({"startup_path", "strong_team"}),
    )

    assert calculate_momentum(research_state).research > calculate_momentum(base).research
    assert (
        calculate_momentum(startup_state, market_timing=90).startup
        > calculate_momentum(startup_state, market_timing=10).startup
    )


def test_yearly_advancement_is_reproducible_and_advances_age_and_year() -> None:
    engine = SimulationEngine()
    state = sample_state()

    first = engine.prepare_year(state, universe_seed=4455, mode=SimulationMode.CINEMATIC)
    second = engine.prepare_year(state, universe_seed=4455, mode=SimulationMode.CINEMATIC)
    first_result = engine.finalize_year(
        first,
        first.significant_event.choices[0].effects
        if first.significant_event.requires_choice
        else None,
    )
    second_result = engine.finalize_year(
        second,
        second.significant_event.choices[0].effects
        if second.significant_event.requires_choice
        else None,
    )

    assert first == second
    assert first_result == second_result
    assert first_result.state.year == 2027
    assert first_result.state.age == 26


def test_yearly_total_changes_are_capped_and_prolonged_stress_harms_health() -> None:
    engine = SimulationEngine()
    previous = sample_state(
        stress=95,
        health=75,
        active_flags=frozenset({"industry_path", "system:high_stress_last_year"}),
    )
    prepared = engine.prepare_year(
        previous,
        universe_seed=88,
        mode=SimulationMode.REALISTIC,
    )
    result = engine.finalize_year(
        prepared,
        EffectPayload(stats={"career_level": 100, "research_impact": 100, "stress": -100}),
    )

    assert result.state.health < previous.health
    assert abs(result.state.career_level - previous.career_level) <= 25
    assert abs(result.state.research_impact - previous.research_impact) <= 25
    assert abs(result.state.stress - previous.stress) <= 25
