from dataclasses import dataclass

from app.models.enums import EventCategory, EventImportance, RiskLevel, SimulationMode
from app.services.simulation.balance import DEFAULT_BALANCE, SimulationBalance
from app.services.simulation.randomness import SeededRandom
from app.services.simulation.schemas import ChoiceRequirements, DelayedEffectSpec, EffectPayload
from app.services.simulation.state import MomentumScores, SimulationState


@dataclass(frozen=True)
class ChoiceDefinition:
    label: str
    description: str
    effects: EffectPayload
    delayed_effects: tuple[DelayedEffectSpec, ...] = ()
    requirements: ChoiceRequirements = ChoiceRequirements()
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass(frozen=True)
class SystemEventDefinition:
    key: str
    title: str
    description: str
    category: EventCategory
    importance: EventImportance
    effects: EffectPayload = EffectPayload()
    choices: tuple[ChoiceDefinition, ...] = ()

    @property
    def requires_choice(self) -> bool:
        return bool(self.choices)


ROUTINE_EVENTS = (
    SystemEventDefinition(
        key="steady-practice",
        title="A year of deliberate practice",
        description="Protected practice time compounds into stronger technical judgment.",
        category=EventCategory.EDUCATION,
        importance=EventImportance.ROUTINE,
        effects=EffectPayload(stats={"discipline": 2}, skill_changes={"software_engineering": 2}),
    ),
    SystemEventDefinition(
        key="community-connections",
        title="Professional community deepens",
        description="Several small collaborations strengthen the surrounding network.",
        category=EventCategory.SOCIAL,
        importance=EventImportance.ROUTINE,
        effects=EffectPayload(stats={"relationships": 3, "reputation": 1}),
    ),
    SystemEventDefinition(
        key="recovery-season",
        title="A season of recovery",
        description="A quieter stretch creates room for health and perspective.",
        category=EventCategory.HEALTH,
        importance=EventImportance.ROUTINE,
        effects=EffectPayload(stats={"health": 3, "stress": -3}),
    ),
    SystemEventDefinition(
        key="unexpected-expense",
        title="An unexpected expense",
        description="A necessary expense tests the year's financial buffer.",
        category=EventCategory.FINANCE,
        importance=EventImportance.ROUTINE,
        effects=EffectPayload(finance={"net_worth_delta_eur": -1_200}),
    ),
)


PATH_DECISIONS: dict[str, tuple[SystemEventDefinition, ...]] = {
    "industry_path": (
        SystemEventDefinition(
            key="leadership-offer",
            title="A technical leadership opening",
            description="A growing applied-AI team needs someone to own a difficult programme.",
            category=EventCategory.CAREER,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Lead the programme",
                    description="Accept wider responsibility and a demanding delivery horizon.",
                    effects=EffectPayload(
                        stats={"career_level": 7, "reputation": 5, "stress": 6},
                        finance={"monthly_income_delta_eur": 450},
                        skill_changes={"leadership": 5},
                        set_flags=["project:ai_programme"],
                    ),
                    delayed_effects=(
                        DelayedEffectSpec(
                            trigger_after_years=2,
                            probability=0.55,
                            description="The programme earns wider recognition.",
                            effects=EffectPayload(
                                stats={"career_level": 5, "reputation": 6, "stress": 2},
                                set_flags=["recent_success"],
                                remove_flags=["project:ai_programme"],
                            ),
                        ),
                    ),
                    requirements=ChoiceRequirements(stats={"discipline": 55}),
                    risk_level=RiskLevel.HIGH,
                ),
                ChoiceDefinition(
                    label="Stay deeply technical",
                    description="Protect specialist focus and decline the management track.",
                    effects=EffectPayload(
                        stats={"research_impact": 4, "freedom": 4, "stress": -3},
                        skill_changes={"applied_ai": 5},
                    ),
                    risk_level=RiskLevel.LOW,
                ),
            ),
        ),
        SystemEventDefinition(
            key="international-role",
            title="An international role appears",
            description="A partner lab offers a role spanning product delivery and research.",
            category=EventCategory.OPPORTUNITY,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Take the international assignment",
                    description="Trade stability for visibility and a broader network.",
                    effects=EffectPayload(
                        stats={"career_level": 5, "reputation": 5, "stress": 4, "freedom": -2},
                        finance={"monthly_income_delta_eur": 300, "net_worth_delta_eur": -2_000},
                        set_flags=["living_abroad"],
                    ),
                    risk_level=RiskLevel.MEDIUM,
                ),
                ChoiceDefinition(
                    label="Build influence from the current team",
                    description="Use existing trust to improve systems closer to home.",
                    effects=EffectPayload(
                        stats={"relationships": 4, "career_level": 3, "stress": -2}
                    ),
                    risk_level=RiskLevel.LOW,
                ),
            ),
        ),
    ),
    "phd_path": (
        SystemEventDefinition(
            key="research-collaboration",
            title="A difficult research collaboration",
            description="A partner lab proposes an ambitious autonomous-systems study.",
            category=EventCategory.RESEARCH,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Commit to the collaboration",
                    description="Pursue the high-upside study alongside existing obligations.",
                    effects=EffectPayload(
                        stats={"research_impact": 7, "reputation": 3, "stress": 7},
                        set_flags=["project:robotics_collaboration"],
                        skill_changes={"robotics": 4},
                    ),
                    delayed_effects=(
                        DelayedEffectSpec(
                            trigger_after_years=2,
                            probability=0.45,
                            description="The collaboration opens an applied research opportunity.",
                            effects=EffectPayload(
                                stats={"career_level": 5, "reputation": 4, "stress": 3},
                                set_flags=["startup_opportunity", "recent_success"],
                                remove_flags=["project:robotics_collaboration"],
                            ),
                        ),
                    ),
                    requirements=ChoiceRequirements(skills={"research": 55}),
                    risk_level=RiskLevel.HIGH,
                ),
                ChoiceDefinition(
                    label="Protect the thesis core",
                    description="Narrow the scope and preserve sustained focus.",
                    effects=EffectPayload(
                        stats={"discipline": 3, "stress": -4, "research_impact": 3}
                    ),
                    risk_level=RiskLevel.LOW,
                ),
            ),
        ),
        SystemEventDefinition(
            key="conference-deadline",
            title="A pivotal conference deadline",
            description="Promising results arrive just before a major submission window closes.",
            category=EventCategory.RESEARCH,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Push for submission",
                    description="Attempt the deadline with a concentrated final sprint.",
                    effects=EffectPayload(
                        stats={"research_impact": 6, "stress": 8, "health": -2},
                        skill_changes={"research": 3},
                    ),
                    risk_level=RiskLevel.HIGH,
                ),
                ChoiceDefinition(
                    label="Develop the work carefully",
                    description="Choose rigor and sustainability over this submission cycle.",
                    effects=EffectPayload(stats={"health": 3, "stress": -4, "research_impact": 2}),
                    risk_level=RiskLevel.LOW,
                ),
            ),
        ),
    ),
    "startup_path": (
        SystemEventDefinition(
            key="funding-term-sheet",
            title="A funding term sheet",
            description="A fictional seed fund offers capital with an aggressive growth plan.",
            category=EventCategory.STARTUP,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Accept the funding",
                    description="Gain runway while accepting demanding milestones.",
                    effects=EffectPayload(
                        stats={"career_level": 6, "reputation": 5, "stress": 7, "freedom": -4},
                        finance={"net_worth_delta_eur": 18_000},
                        set_flags=["funded_startup", "project:fundraising_growth"],
                        remove_flags=["bootstrapping"],
                        skill_changes={"fundraising": 6},
                    ),
                    delayed_effects=(
                        DelayedEffectSpec(
                            trigger_after_years=1,
                            probability=0.50,
                            description="The funded growth experiment finds a repeatable market.",
                            effects=EffectPayload(
                                stats={"career_level": 7, "reputation": 6, "stress": 4},
                                finance={"monthly_income_delta_eur": 1_000},
                                set_flags=["product_market_fit", "recent_success"],
                                remove_flags=["project:fundraising_growth"],
                            ),
                        ),
                    ),
                    requirements=ChoiceRequirements(skills={"fundraising": 20}),
                    risk_level=RiskLevel.HIGH,
                ),
                ChoiceDefinition(
                    label="Keep bootstrapping",
                    description="Preserve control and search for customers at a measured pace.",
                    effects=EffectPayload(
                        stats={"freedom": 4, "stress": -2, "career_level": 2},
                        finance={"net_worth_delta_eur": -2_500},
                        skill_changes={"product": 4},
                    ),
                    risk_level=RiskLevel.MEDIUM,
                ),
            ),
        ),
        SystemEventDefinition(
            key="enterprise-pilot",
            title="A make-or-break enterprise pilot",
            description="A large fictional customer offers a narrow window to prove the product.",
            category=EventCategory.OPPORTUNITY,
            importance=EventImportance.MAJOR,
            choices=(
                ChoiceDefinition(
                    label="Reorient around the pilot",
                    description="Concentrate the company on winning the reference customer.",
                    effects=EffectPayload(
                        stats={"career_level": 5, "stress": 8, "reputation": 3},
                        set_flags=["project:enterprise_pilot"],
                        skill_changes={"product": 4},
                    ),
                    risk_level=RiskLevel.HIGH,
                ),
                ChoiceDefinition(
                    label="Protect the broader roadmap",
                    description=(
                        "Decline dependency on one customer and continue product discovery."
                    ),
                    effects=EffectPayload(
                        stats={"freedom": 4, "creativity": 3, "stress": -2},
                        finance={"net_worth_delta_eur": -1_500},
                    ),
                    risk_level=RiskLevel.MEDIUM,
                ),
            ),
        ),
    ),
}


AUTOMATIC_SIGNIFICANT_EVENTS = (
    SystemEventDefinition(
        key="earned-recognition",
        title="Work earns quiet recognition",
        description="Consistent output leads to an unsolicited professional opportunity.",
        category=EventCategory.OPPORTUNITY,
        importance=EventImportance.NOTABLE,
        effects=EffectPayload(stats={"reputation": 4, "career_level": 3}),
    ),
    SystemEventDefinition(
        key="difficult-setback",
        title="A plan fails under real constraints",
        description="A promising effort misses its goal and forces a careful reset.",
        category=EventCategory.CRISIS,
        importance=EventImportance.NOTABLE,
        effects=EffectPayload(stats={"stress": 5, "reputation": -3, "discipline": 2}),
    ),
)


def path_flag(state: SimulationState) -> str:
    for candidate in ("industry_path", "phd_path", "startup_path"):
        if candidate in state.active_flags:
            return candidate
    return "industry_path"


def select_events(
    state: SimulationState,
    universe_seed: int,
    mode: SimulationMode,
    momenta: MomentumScores,
    balance: SimulationBalance = DEFAULT_BALANCE,
) -> tuple[SystemEventDefinition, SystemEventDefinition]:
    rng = SeededRandom(universe_seed)
    routine = rng.choice(ROUTINE_EVENTS, state.year, "routine")
    mode_balance = balance.mode[mode]
    choice_probability = balance.significant_choice_probability / mode_balance.volatility
    if rng.chance(choice_probability, state.year, "requires-choice"):
        decisions = PATH_DECISIONS[path_flag(state)]
        return routine, rng.choice(decisions, state.year, "decision")

    strongest = max(momenta.career, momenta.research, momenta.startup) / 100
    success_weight = max(0.1, strongest * mode_balance.positive_outcome_modifier)
    setback_weight = max(0.1, (1.0 - strongest) * mode_balance.setback_modifier)
    significant = rng.weighted_choice(
        (
            (AUTOMATIC_SIGNIFICANT_EVENTS[0], success_weight),
            (AUTOMATIC_SIGNIFICANT_EVENTS[1], setback_weight),
        ),
        state.year,
        "automatic-significant",
    )
    return routine, significant
