from dataclasses import dataclass, replace
from typing import cast

from app.models.enums import SimulationMode
from app.services.simulation.balance import DEFAULT_BALANCE, SimulationBalance
from app.services.simulation.events import SystemEventDefinition, path_flag, select_events
from app.services.simulation.randomness import SeededRandom
from app.services.simulation.schemas import EffectPayload
from app.services.simulation.state import (
    MomentumScores,
    SimulationState,
    apply_effects,
    calculate_finances,
    calculate_happiness,
    calculate_momentum,
)


@dataclass(frozen=True)
class DueEffectInput:
    key: str
    trigger_year: int
    probability: float
    effects: EffectPayload


@dataclass(frozen=True)
class DelayedResolution:
    key: str
    occurred: bool


@dataclass(frozen=True)
class PreparedYear:
    previous_state: SimulationState
    state_before_significant_event: SimulationState
    routine_event: SystemEventDefinition
    significant_event: SystemEventDefinition
    momenta: MomentumScores
    delayed_resolutions: tuple[DelayedResolution, ...]
    annual_net_worth_change_eur: int


@dataclass(frozen=True)
class YearResult:
    state: SimulationState
    summary: str
    momenta: MomentumScores
    delayed_resolutions: tuple[DelayedResolution, ...]
    annual_net_worth_change_eur: int


class SimulationEngine:
    """Pure deterministic yearly transition engine with no persistence dependencies."""

    def __init__(self, balance: SimulationBalance = DEFAULT_BALANCE) -> None:
        self.balance = balance

    def prepare_year(
        self,
        state: SimulationState,
        *,
        universe_seed: int,
        mode: SimulationMode,
        due_effects: tuple[DueEffectInput, ...] = (),
    ) -> PreparedYear:
        target_year = state.year + 1
        working = replace(state, year=target_year, age=state.age + 1)
        working, delayed_resolutions = self._apply_due_effects(
            working,
            universe_seed=universe_seed,
            due_effects=due_effects,
        )
        working = self._apply_baseline(working, state)
        market_timing = (
            SeededRandom(universe_seed)
            .stream(target_year, "market-timing")
            .randint(self.balance.score_min, self.balance.score_max)
        )
        momenta = calculate_momentum(
            working,
            market_timing=market_timing,
            balance=self.balance,
        )
        working = self._apply_path_progression(
            working,
            universe_seed=universe_seed,
            mode=mode,
            momenta=momenta,
        )
        finances = calculate_finances(working, momenta.career, self.balance)
        working = replace(
            working,
            monthly_income_eur=finances.monthly_income_eur,
            net_worth_eur=finances.net_worth_eur,
        )
        routine, significant = select_events(
            working,
            universe_seed,
            mode,
            momenta,
            self.balance,
        )
        working = apply_effects(working, routine.effects, self.balance)
        return PreparedYear(
            previous_state=state,
            state_before_significant_event=working,
            routine_event=routine,
            significant_event=significant,
            momenta=momenta,
            delayed_resolutions=delayed_resolutions,
            annual_net_worth_change_eur=finances.annual_net_worth_change_eur,
        )

    def finalize_year(
        self,
        prepared: PreparedYear,
        significant_effects: EffectPayload | None = None,
    ) -> YearResult:
        effects = significant_effects or prepared.significant_event.effects
        final_state = apply_effects(
            prepared.state_before_significant_event,
            effects,
            self.balance,
        )
        final_state = self._cap_yearly_score_changes(prepared.previous_state, final_state)
        final_state = replace(final_state, happiness=calculate_happiness(final_state, self.balance))
        final_state = self._cap_yearly_score_changes(prepared.previous_state, final_state)
        occurred = sum(resolution.occurred for resolution in prepared.delayed_resolutions)
        summary = (
            f"{final_state.year}: {prepared.routine_event.title}. "
            f"{prepared.significant_event.title}. "
            f"Career, research, and startup momentum were "
            f"{prepared.momenta.career}, {prepared.momenta.research}, and "
            f"{prepared.momenta.startup}; {occurred} delayed consequence(s) occurred."
        )
        return YearResult(
            state=final_state,
            summary=summary,
            momenta=prepared.momenta,
            delayed_resolutions=prepared.delayed_resolutions,
            annual_net_worth_change_eur=prepared.annual_net_worth_change_eur,
        )

    def _apply_due_effects(
        self,
        state: SimulationState,
        *,
        universe_seed: int,
        due_effects: tuple[DueEffectInput, ...],
    ) -> tuple[SimulationState, tuple[DelayedResolution, ...]]:
        rng = SeededRandom(universe_seed)
        working = state
        resolutions: list[DelayedResolution] = []
        for due in sorted(due_effects, key=lambda effect: (effect.trigger_year, effect.key)):
            occurred = rng.chance(
                due.probability,
                state.year,
                "delayed-effect",
                due.trigger_year,
                due.key,
            )
            if occurred:
                working = apply_effects(working, due.effects, self.balance)
            resolutions.append(DelayedResolution(key=due.key, occurred=occurred))
        return working, tuple(resolutions)

    def _apply_baseline(
        self,
        state: SimulationState,
        previous_state: SimulationState,
    ) -> SimulationState:
        effects = EffectPayload(stats={"stress": -self.balance.yearly_stress_recovery})
        working = apply_effects(state, effects, self.balance)
        flags = set(working.active_flags)
        was_high = "system:high_stress_last_year" in previous_state.active_flags
        if previous_state.stress >= self.balance.high_stress_threshold:
            flags.add("system:high_stress_last_year")
        else:
            flags.discard("system:high_stress_last_year")
        working = replace(working, active_flags=frozenset(flags))
        if was_high and previous_state.stress >= self.balance.extreme_stress_threshold:
            working = apply_effects(
                working,
                EffectPayload(stats={"health": -self.balance.extreme_stress_health_penalty}),
                self.balance,
            )
        return working

    def _apply_path_progression(
        self,
        state: SimulationState,
        *,
        universe_seed: int,
        mode: SimulationMode,
        momenta: MomentumScores,
    ) -> SimulationState:
        path = path_flag(state)
        if path == "phd_path":
            momentum = momenta.research
            success = EffectPayload(
                stats={
                    "research_impact": self.balance.career_success_gain,
                    "reputation": self.balance.success_reputation_gain,
                }
            )
            setback = EffectPayload(
                stats={
                    "research_impact": self.balance.progression_setback_penalty,
                    "stress": self.balance.progression_setback_stress,
                }
            )
        elif path == "startup_path":
            momentum = momenta.startup
            success = EffectPayload(
                stats={
                    "career_level": self.balance.career_success_gain,
                    "reputation": self.balance.success_reputation_gain + 1,
                },
                finance={"monthly_income_delta_eur": self.balance.startup_success_income_eur},
            )
            setback = EffectPayload(
                stats={
                    "career_level": self.balance.progression_setback_penalty,
                    "stress": self.balance.progression_setback_stress + 1,
                },
                finance={"net_worth_delta_eur": self.balance.startup_setback_net_worth_eur},
            )
        else:
            momentum = momenta.career
            success = EffectPayload(
                stats={
                    "career_level": self.balance.career_success_gain,
                    "reputation": self.balance.success_reputation_gain,
                },
                finance={"monthly_income_delta_eur": self.balance.industry_success_income_eur},
            )
            setback = EffectPayload(
                stats={
                    "career_level": max(-1, self.balance.progression_setback_penalty),
                    "stress": self.balance.progression_setback_stress,
                }
            )

        probability = self.balance.momentum_random_floor
        probability += (momentum / 100) * (
            self.balance.momentum_random_ceiling - self.balance.momentum_random_floor
        )
        mode_balance = self.balance.mode[mode]
        probability *= mode_balance.positive_outcome_modifier
        probability = max(
            self.balance.momentum_random_floor,
            min(self.balance.momentum_random_ceiling, probability),
        )
        succeeded = SeededRandom(universe_seed).chance(
            probability,
            state.year,
            "path-progression",
            path,
        )
        return apply_effects(state, success if succeeded else setback, self.balance)

    def _cap_yearly_score_changes(
        self,
        previous: SimulationState,
        current: SimulationState,
    ) -> SimulationState:
        limit = self.balance.max_yearly_total_stat_change

        def capped(field_name: str) -> int:
            old_value = cast(int, getattr(previous, field_name))
            new_value = cast(int, getattr(current, field_name))
            return max(old_value - limit, min(old_value + limit, new_value))

        return replace(
            current,
            career_level=capped("career_level"),
            health=capped("health"),
            relationships=capped("relationships"),
            research_impact=capped("research_impact"),
            reputation=capped("reputation"),
            freedom=capped("freedom"),
            stress=capped("stress"),
            happiness=capped("happiness"),
            discipline=capped("discipline"),
            creativity=capped("creativity"),
            chaos=capped("chaos"),
        )
