from dataclasses import dataclass
from typing import Literal, cast

from app.models.enums import (
    ArtifactType,
    EventCategory,
    EventImportance,
    RiskLevel,
    SimulationMode,
)
from app.services.narrative.schemas import (
    AcademicAbstractContent,
    AccentColor,
    ArtifactContent,
    ArtifactMetadata,
    CompanyAnnouncementContent,
    DiaryEntryContent,
    EmailContent,
    FutureSelfReplyRequest,
    GeneratedArtifact,
    GeneratedChoice,
    GeneratedEvent,
    GeneratedFutureSelfProfile,
    GeneratedFutureSelfReply,
    GeneratedUniverseBranch,
    GeneratedYearSummary,
    NarrativeContext,
    NewsArticleContent,
    ProposedInitialState,
    SocialPostContent,
    SupportedArtifactType,
    UniverseBranchRequest,
    VisualTheme,
)
from app.services.simulation.randomness import SeededRandom
from app.services.simulation.schemas import DelayedEffectSpec, EffectPayload


@dataclass(frozen=True)
class _EventTemplate:
    key: str
    paths: frozenset[str]
    title: str
    description: str
    category: EventCategory
    importance: EventImportance = EventImportance.MAJOR
    base_weight: float = 1.0
    modes: frozenset[SimulationMode] | None = None


ALL_PATHS = frozenset({"industry", "research", "startup"})
SUPPORTED_ARTIFACTS: tuple[SupportedArtifactType, ...] = (
    ArtifactType.NEWS_ARTICLE,
    ArtifactType.ACADEMIC_ABSTRACT,
    ArtifactType.COMPANY_ANNOUNCEMENT,
    ArtifactType.DIARY_ENTRY,
    ArtifactType.EMAIL,
    ArtifactType.SOCIAL_MEDIA_POST,
)

EVENT_TEMPLATES = (
    _EventTemplate(
        "industry-leadership-charter",
        frozenset({"industry"}),
        "The mandate no one had written down",
        "A cross-functional AI programme is drifting, and the team asks {name} to define both "
        "its technical standard and its operating rhythm.",
        EventCategory.CAREER,
        base_weight=2.2,
    ),
    _EventTemplate(
        "industry-model-review",
        frozenset({"industry"}),
        "A model review changes the roadmap",
        "A careful evaluation uncovers a weakness in a flagship system just before a public "
        "commitment, creating a choice between speed and engineering credibility.",
        EventCategory.CRISIS,
        base_weight=1.3,
    ),
    _EventTemplate(
        "industry-research-window",
        frozenset({"industry"}),
        "A protected research window",
        "Leadership offers one quarter to turn an applied insight into publishable work, but "
        "delivery obligations will not disappear on their own.",
        EventCategory.RESEARCH,
        base_weight=1.4,
    ),
    _EventTemplate(
        "industry-equity-package",
        frozenset({"industry"}),
        "A compensation package with a long shadow",
        "A fictional scale-up proposes a higher salary and uncertain equity in exchange for a "
        "more demanding remit.",
        EventCategory.FINANCE,
    ),
    _EventTemplate(
        "industry-relocation",
        frozenset({"industry"}),
        "The team asks for a relocation",
        "The most influential collaborators are gathering in another city, forcing a trade-off "
        "between proximity to the work and the life already built in {location}.",
        EventCategory.RELATIONSHIP,
    ),
    _EventTemplate(
        "industry-mentor-sponsorship",
        frozenset({"industry"}),
        "A sponsor opens the executive room",
        "A respected technical director offers to sponsor {name} for a wider leadership role, "
        "provided the next difficult programme is delivered visibly.",
        EventCategory.OPPORTUNITY,
        base_weight=1.4,
    ),
    _EventTemplate(
        "research-field-trial",
        frozenset({"research"}),
        "The robot leaves the laboratory",
        "A partner lab offers a narrow field-test window for the autonomous system, before the "
        "team considers the safety evidence complete.",
        EventCategory.RESEARCH,
        base_weight=2.2,
    ),
    _EventTemplate(
        "research-industry-lab",
        frozenset({"research"}),
        "An industry lab makes a hybrid offer",
        "A fictional robotics institute proposes a joint appointment that brings resources and "
        "real deployments, while dividing attention from the thesis.",
        EventCategory.CAREER,
        base_weight=1.4,
    ),
    _EventTemplate(
        "research-grant-gap",
        frozenset({"research"}),
        "A grant gap threatens the experiment",
        "Equipment funding arrives below budget, leaving a choice between narrowing the study "
        "and finding an outside partner.",
        EventCategory.FINANCE,
    ),
    _EventTemplate(
        "research-authorship",
        frozenset({"research"}),
        "The authorship conversation",
        "A collaboration produces strong results and an uncomfortable disagreement about credit, "
        "ownership, and who carried the hardest part of the work.",
        EventCategory.RELATIONSHIP,
        base_weight=1.3,
    ),
    _EventTemplate(
        "research-keynote",
        frozenset({"research"}),
        "A last-minute conference invitation",
        "A speaker withdraws from a fictional autonomous-systems conference, giving {name} one "
        "week to turn unfinished findings into a public argument.",
        EventCategory.OPPORTUNITY,
        base_weight=1.5,
    ),
    _EventTemplate(
        "research-prototype-collapse",
        frozenset({"research"}),
        "The prototype fails before review",
        "The main robot develops an intermittent fault days before a milestone review, and the "
        "team cannot yet explain whether hardware or learning software is responsible.",
        EventCategory.CRISIS,
        base_weight=1.2,
    ),
    _EventTemplate(
        "startup-funding-room",
        frozenset({"startup"}),
        "The term sheet arrives after midnight",
        "A fictional seed fund offers enough runway to hire a small team, paired with milestones "
        "that would reshape the product and the founder's calendar.",
        EventCategory.STARTUP,
        base_weight=2.2,
    ),
    _EventTemplate(
        "startup-runway-cliff",
        frozenset({"startup"}),
        "The runway becomes a calendar",
        "Slower sales turn the company's cash balance into a visible deadline, forcing an early "
        "decision about costs, consulting work, or fundraising.",
        EventCategory.FINANCE,
        base_weight=1.5,
    ),
    _EventTemplate(
        "startup-cofounder-tension",
        frozenset({"startup"}),
        "The co-founder agreement is tested",
        "A fictional collaborator questions the product direction and the division of ownership, "
        "bringing a quiet disagreement into the open.",
        EventCategory.RELATIONSHIP,
        base_weight=1.3,
    ),
    _EventTemplate(
        "startup-enterprise-pilot",
        frozenset({"startup"}),
        "One customer could change the company",
        "A fictional manufacturer offers a paid pilot with a demanding deadline and requirements "
        "that could pull the product away from its broader vision.",
        EventCategory.OPPORTUNITY,
        base_weight=1.7,
    ),
    _EventTemplate(
        "startup-production-outage",
        frozenset({"startup"}),
        "The demo fails in front of the first believers",
        "A production incident interrupts a pivotal customer demonstration, making the recovery "
        "as important as the technical repair.",
        EventCategory.CRISIS,
        base_weight=1.2,
    ),
    _EventTemplate(
        "startup-founder-role",
        frozenset({"startup"}),
        "The company outgrows one founder's job",
        "Early traction creates more sales, hiring, and coordination work than product time, "
        "forcing {name} to decide what kind of founder to become.",
        EventCategory.CAREER,
        base_weight=1.4,
    ),
    _EventTemplate(
        "health-warning",
        ALL_PATHS,
        "The body files its own progress report",
        "Several weeks of poor recovery make the current pace impossible to dismiss, even as "
        "the year's most meaningful work accelerates.",
        EventCategory.HEALTH,
        base_weight=0.5,
    ),
    _EventTemplate(
        "relationship-anchor",
        ALL_PATHS,
        "An important relationship asks for presence",
        "Someone central to {name}'s life asks for more reliable time and attention, challenging "
        "the habit of treating connection as whatever remains after work.",
        EventCategory.RELATIONSHIP,
        base_weight=0.5,
    ),
    _EventTemplate(
        "chaos-coffee-machine",
        ALL_PATHS,
        "The coffee machine attracts venture capital",
        "A sensor-equipped coffee machine built during a sleepless hackathon becomes a fictional "
        "internet celebrity, and investors begin asking for a pitch deck that does not exist.",
        EventCategory.RANDOM,
        base_weight=7.0,
        modes=frozenset({SimulationMode.CHAOS}),
    ),
    _EventTemplate(
        "chaos-manifesto",
        ALL_PATHS,
        "The technical appendix becomes a manifesto",
        "A dense optimization appendix is shared without context and develops a fictional second "
        "life as a philosophy of decision-making.",
        EventCategory.RANDOM,
        base_weight=6.0,
        modes=frozenset({SimulationMode.CHAOS}),
    ),
)

MODE_OPENERS = {
    SimulationMode.REALISTIC: "Within the year's ordinary constraints",
    SimulationMode.CINEMATIC: "At a decisive and unusually public moment",
    SimulationMode.UTOPIAN: "With rare alignment between people, resources, and timing",
    SimulationMode.DARK: "Under mounting pressure and with no painless option",
    SimulationMode.CHAOS: "By a chain of improbable but internally consistent accidents",
}


class MockNarrativeProvider:
    """Offline, deterministic narrative templates with no persistence capabilities."""

    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]:
        defaults = ("Applied AI Leader", "Robotics Researcher", "Startup Founder")
        directions = tuple(request.branch_directions) or defaults[: request.number_of_branches]
        branches: list[GeneratedUniverseBranch] = []
        for index, direction in enumerate(directions):
            kind = self._branch_kind(direction, index)
            branches.append(self._branch(request, direction, kind, index))
        return tuple(branches)

    async def generate_significant_event(self, context: NarrativeContext) -> GeneratedEvent:
        path = self._path(context)
        used = set(context.previous_event_keys)
        candidates = [
            template
            for template in EVENT_TEMPLATES
            if path in template.paths
            and (template.modes is None or context.simulation_mode in template.modes)
            and template.key not in used
        ]
        priority_categories = self._priority_categories(context)
        prioritized = [
            template for template in candidates if template.category in priority_categories
        ]
        if prioritized:
            candidates = prioritized
        if not candidates:
            raise RuntimeError("Mock event catalogue exhausted for this timeline")
        weighted = [(template, self._event_weight(template, context)) for template in candidates]
        template = SeededRandom(context.universe.random_seed).weighted_choice(
            weighted,
            context.current_year + 1,
            context.simulation_mode.value,
            "mock-significant-event",
            *sorted(used),
        )
        rendered_description = template.description.format(
            name=context.profile.name,
            location=context.current_state.location,
        )
        description = f"{MODE_OPENERS[context.simulation_mode]}, {rendered_description}"
        return GeneratedEvent(
            event_key=template.key,
            year=context.current_year + 1,
            title=template.title,
            description=description,
            category=template.category,
            importance=template.importance,
            requires_choice=True,
            choices=self._choices(template, context),
            artifact_suggestions=self._artifact_suggestions(template.category),
            narrative_tags=[
                path,
                template.category.value,
                context.simulation_mode.value,
                "fictional",
            ],
        )

    async def generate_year_summary(
        self, context: NarrativeContext, event: GeneratedEvent
    ) -> GeneratedYearSummary:
        state = context.current_state
        pressure = "pressure stayed manageable" if state.stress < 70 else "pressure became costly"
        direction = self._direction_label(context)
        return GeneratedYearSummary(
            year=state.year,
            headline=f"{state.year}: {event.title}",
            overview=(
                f"In the {context.universe.name} timeline, {context.profile.name} spent the year "
                f"moving further toward {direction}. {event.description} By year's end, "
                f"{pressure}, "
                f"with happiness at {state.happiness} and stress at {state.stress}."
            ),
            key_developments=[
                event.title,
                f"Career level reached {state.career_level}",
                f"Net worth closed at €{state.net_worth_eur:,}",
            ],
            defining_tradeoff=self._tradeoff(event.category),
            closing_note=self._closing_note(context.simulation_mode, state.happiness),
            narrative_tags=[context.universe.slug, context.simulation_mode.value, str(state.year)],
        )

    async def generate_artifact(
        self,
        context: NarrativeContext,
        event: GeneratedEvent,
        artifact_type: ArtifactType | None = None,
    ) -> GeneratedArtifact:
        selected: ArtifactType | None = artifact_type
        if selected is None:
            options = event.artifact_suggestions or [ArtifactType.DIARY_ENTRY]
            selected = SeededRandom(context.universe.random_seed).choice(
                options, event.event_key, "artifact-type"
            )
        if selected not in SUPPORTED_ARTIFACTS:
            raise ValueError(f"Unsupported mock artifact type: {selected.value}")
        supported_type = selected
        date = f"{event.year}-09-15"
        name = context.profile.name
        title, content = self._artifact_content(supported_type, context, event, date, name)
        return GeneratedArtifact(
            artifact_type=supported_type,
            title=title,
            content=content,
            metadata=ArtifactMetadata(
                event_key=event.event_key,
                narrative_tags=[context.universe.slug, event.category.value, "fictional"],
            ),
        )

    async def generate_future_self_profile(
        self, context: NarrativeContext
    ) -> GeneratedFutureSelfProfile:
        state = context.current_state
        achievement = (
            context.last_major_events[-1].title
            if context.last_major_events
            else f"building a life as {state.career_title}"
        )
        regret = self._regret(context)
        temperament = SeededRandom(context.universe.random_seed).choice(
            ("measured and analytical", "warm but direct", "curious and quietly ambitious"),
            "future-self-personality",
        )
        return GeneratedFutureSelfProfile(
            name=context.profile.name,
            age=state.age,
            location=state.location,
            occupation=state.career_title,
            universe=context.universe.name,
            key_achievement=achievement,
            greatest_regret=regret,
            happiness=state.happiness,
            stress=state.stress,
            personality_summary=(
                f"{temperament}; shaped by the documented {context.universe.name} timeline and "
                f"inclined to discuss trade-offs without treating them as predictions."
            ),
        )

    async def generate_future_self_response(
        self, request: FutureSelfReplyRequest
    ) -> GeneratedFutureSelfReply:
        context = request.context
        question = request.message.casefold()
        recent = context.last_major_events[-1] if context.last_major_events else None
        reference = [recent.event_key] if recent else []
        event_clause = (
            f"The clearest example in my actual timeline is “{recent.title}.” "
            if recent
            else (
                "This timeline is still near its beginning, so I can only speak from the state "
                "it records. "
            )
        )
        tone: Literal["reflective", "hopeful", "candid", "wry", "somber"]
        if "regret" in question or "sacrifice" in question:
            content = f"{event_clause}My sharpest regret is {request.profile.greatest_regret}."
            tone = "candid"
        elif "proud" in question or "worth" in question:
            content = (
                f"{event_clause}I am proudest of {request.profile.key_achievement}. "
                f"Was it worth it? At happiness {request.profile.happiness} and stress "
                f"{request.profile.stress}, the honest answer is that the gains and costs coexist."
            )
            tone = "reflective"
        elif "avoid" in question:
            content = (
                f"{event_clause}Avoid treating every open door as an obligation. The recorded "
                f"stress level is {request.profile.stress}; protect health and relationships "
                "before "
                "ambition turns them into delayed maintenance."
            )
            tone = "candid"
        else:
            content = (
                f"{event_clause}The decision that mattered was repeatedly choosing what to "
                "protect, "
                f"not merely what to pursue. I ended up as {request.profile.occupation} in "
                f"{request.profile.location}, and I would tell my younger self to measure the path "
                "by its lived trade-offs, not by its title."
            )
            tone = "hopeful"
        return GeneratedFutureSelfReply(
            content=content,
            referenced_event_keys=reference,
            tone=tone,
        )

    @staticmethod
    def _branch_kind(direction: str, index: int) -> str:
        lowered = direction.casefold()
        if any(word in lowered for word in ("robot", "phd", "research")):
            return "research"
        if any(word in lowered for word in ("startup", "found", "company")):
            return "startup"
        if any(word in lowered for word in ("industry", "applied", "leader")):
            return "industry"
        return ("industry", "research", "startup")[index % 3]

    def _branch(
        self,
        request: UniverseBranchRequest,
        direction: str,
        kind: str,
        index: int,
    ) -> GeneratedUniverseBranch:
        definitions = {
            "industry": (
                "Applied AI Leader",
                "From research engineering to responsible AI leadership",
                "structured-grid",
                "#3B82F6",
                "AI Research Engineer",
                3_200,
                14_000,
                {"applied_ai": 72, "software_engineering": 76, "leadership": 38},
                ["industry_path", "masters_completed"],
            ),
            "research": (
                "Robotics Researcher",
                "A funded PhD in autonomous systems and optimization",
                "orbital-geometry",
                "#8B5CF6",
                "Robotics PhD Researcher",
                1_800,
                11_000,
                {"robotics": 64, "optimization": 73, "research": 70},
                ["phd_path", "funded_research", "masters_completed"],
            ),
            "startup": (
                "Startup Founder",
                "An ambitious return to building an AI product company",
                "energetic-particles",
                "#F59E0B",
                "AI Startup Founder",
                900,
                8_000,
                {"product": 52, "software_engineering": 74, "fundraising": 26},
                ["startup_path", "bootstrapping", "masters_completed"],
            ),
        }
        name, subtitle, motif, accent, career, income, worth, skills, flags = definitions[kind]
        if direction not in ("Applied AI Leader", "Robotics Researcher", "Startup Founder"):
            name = direction
        slug = "-".join(part for part in name.lower().replace("/", " ").split() if part)
        slug = "".join(character for character in slug if character.isalnum() or character == "-")
        mode_clause = {
            SimulationMode.REALISTIC: "through plausible progress and setbacks",
            SimulationMode.CINEMATIC: "through visible turning points and dramatic reversals",
            SimulationMode.UTOPIAN: "through unusually favorable but coherent opportunities",
            SimulationMode.DARK: "under persistent pressure and difficult trade-offs",
            SimulationMode.CHAOS: "through improbable but narratively consistent detours",
        }[request.simulation_mode]
        root = SeededRandom(request.scenario_seed)
        premise_verb = root.choice(("explores", "follows", "traces"), index, kind, "branch-verb")
        return GeneratedUniverseBranch(
            name=name,
            slug=slug,
            subtitle=subtitle,
            premise=(
                f"This fictional branch {premise_verb} {request.profile.name} choosing to "
                f"{direction.casefold()}, {mode_clause}."
            ),
            visual_theme=cast(VisualTheme, motif),
            accent_color=cast(AccentColor, accent),
            starting_direction=direction,
            proposed_initial_state=ProposedInitialState(
                location=request.profile.location,
                career_title=career,
                career_level={"industry": 36, "research": 29, "startup": 24}[kind],
                monthly_income_eur=income,
                net_worth_eur=worth,
                health=77 if kind != "startup" else 73,
                relationships=63 if kind == "industry" else 61 if kind == "research" else 59,
                research_impact=47 if kind == "industry" else 55 if kind == "research" else 44,
                reputation=42 if kind == "industry" else 39 if kind == "research" else 38,
                freedom=50 if kind == "industry" else 55 if kind == "research" else 70,
                stress=60 if kind == "industry" else 63 if kind == "research" else 72,
                happiness=69 if kind == "industry" else 70 if kind == "research" else 71,
                discipline=84 if kind != "research" else 86,
                creativity=79 if kind == "industry" else 82 if kind == "research" else 88,
                chaos=26 if kind == "industry" else 28 if kind == "research" else 55,
                skills=skills,
                active_flags=flags,
            ),
            narrative_tags=[kind, request.simulation_mode.value, "fictional"],
        )

    @staticmethod
    def _path(context: NarrativeContext) -> str:
        flags = set(context.current_state.active_flags)
        if "phd_path" in flags:
            return "research"
        if "startup_path" in flags:
            return "startup"
        return "industry"

    @staticmethod
    def _event_weight(template: _EventTemplate, context: NarrativeContext) -> float:
        state = context.current_state
        weight = template.base_weight
        if state.stress >= 75 and template.category in {EventCategory.HEALTH, EventCategory.CRISIS}:
            weight += 12
        if state.health <= 50 and template.category == EventCategory.HEALTH:
            weight += 15
        if state.net_worth_eur < 0 and template.category == EventCategory.FINANCE:
            weight += 14
        if state.relationships <= 45 and template.category == EventCategory.RELATIONSHIP:
            weight += 12
        if state.research_impact >= 65 and template.category == EventCategory.RESEARCH:
            weight += 4
        if context.simulation_mode == SimulationMode.DARK and template.category in {
            EventCategory.CRISIS,
            EventCategory.FINANCE,
            EventCategory.HEALTH,
        }:
            weight += 5
        if context.simulation_mode == SimulationMode.UTOPIAN and template.category in {
            EventCategory.OPPORTUNITY,
            EventCategory.RESEARCH,
            EventCategory.CAREER,
        }:
            weight += 5
        if (
            context.simulation_mode == SimulationMode.CINEMATIC
            and template.importance == EventImportance.MAJOR
        ):
            weight += 2
        return weight

    @staticmethod
    def _priority_categories(context: NarrativeContext) -> set[EventCategory]:
        state = context.current_state
        if context.simulation_mode == SimulationMode.CHAOS:
            return {EventCategory.RANDOM}
        if state.health <= 50:
            return {EventCategory.HEALTH, EventCategory.CRISIS}
        if state.stress >= 85:
            return {EventCategory.HEALTH, EventCategory.CRISIS}
        if state.net_worth_eur < 0:
            return {EventCategory.FINANCE, EventCategory.CRISIS}
        if state.relationships <= 35:
            return {EventCategory.RELATIONSHIP}
        if context.simulation_mode == SimulationMode.DARK:
            return {EventCategory.CRISIS, EventCategory.FINANCE, EventCategory.HEALTH}
        if context.simulation_mode == SimulationMode.UTOPIAN:
            return {
                EventCategory.OPPORTUNITY,
                EventCategory.RESEARCH,
                EventCategory.CAREER,
            }
        return set()

    def _choices(
        self, template: _EventTemplate, context: NarrativeContext
    ) -> list[GeneratedChoice]:
        category = template.category
        high_effects: dict[EventCategory, EffectPayload] = {
            EventCategory.CAREER: EffectPayload(
                stats={"career_level": 7, "reputation": 4, "stress": 6},
                finance={"monthly_income_delta_eur": 450},
                skill_changes={"leadership": 4},
            ),
            EventCategory.RESEARCH: EffectPayload(
                stats={"research_impact": 8, "reputation": 3, "stress": 6},
                skill_changes={"research": 4},
            ),
            EventCategory.STARTUP: EffectPayload(
                stats={"career_level": 6, "reputation": 4, "stress": 7, "freedom": -3},
                finance={"net_worth_delta_eur": 12_000},
                set_flags=["funded_startup"],
                skill_changes={"fundraising": 5},
            ),
            EventCategory.FINANCE: EffectPayload(
                stats={"stress": 4, "discipline": 3},
                finance={"monthly_income_delta_eur": 250, "net_worth_delta_eur": 2_500},
            ),
            EventCategory.HEALTH: EffectPayload(
                stats={"health": 8, "stress": -9, "freedom": 3, "career_level": -2}
            ),
            EventCategory.RELATIONSHIP: EffectPayload(
                stats={"relationships": 8, "happiness": 3, "stress": -3, "freedom": -2}
            ),
            EventCategory.OPPORTUNITY: EffectPayload(
                stats={"career_level": 5, "reputation": 5, "stress": 5},
                finance={"net_worth_delta_eur": -1_500},
            ),
            EventCategory.CRISIS: EffectPayload(
                stats={"discipline": 4, "reputation": 2, "stress": 7, "health": -2}
            ),
            EventCategory.RANDOM: EffectPayload(
                stats={"chaos": 10, "creativity": 5, "reputation": 4, "stress": 3},
                finance={"net_worth_delta_eur": 1_500},
            ),
        }
        measured_effects: dict[EventCategory, EffectPayload] = {
            EventCategory.CAREER: EffectPayload(
                stats={"career_level": 3, "freedom": 4, "stress": -3},
                skill_changes={"applied_ai": 3},
            ),
            EventCategory.RESEARCH: EffectPayload(
                stats={"research_impact": 4, "discipline": 3, "stress": -2}
            ),
            EventCategory.STARTUP: EffectPayload(
                stats={"freedom": 4, "stress": -2, "career_level": 2},
                finance={"net_worth_delta_eur": -2_000},
                skill_changes={"product": 4},
            ),
            EventCategory.FINANCE: EffectPayload(
                stats={"freedom": -2, "stress": -4},
                finance={"net_worth_delta_eur": -750},
            ),
            EventCategory.HEALTH: EffectPayload(stats={"health": 4, "stress": -5, "discipline": 2}),
            EventCategory.RELATIONSHIP: EffectPayload(
                stats={"relationships": 4, "stress": -2, "discipline": 2}
            ),
            EventCategory.OPPORTUNITY: EffectPayload(
                stats={"freedom": 4, "discipline": 2, "stress": -2}
            ),
            EventCategory.CRISIS: EffectPayload(
                stats={"stress": 3, "discipline": 3, "reputation": -1}
            ),
            EventCategory.RANDOM: EffectPayload(stats={"chaos": -2, "discipline": 3, "stress": -2}),
        }
        delayed: list[DelayedEffectSpec] = []
        delayed_categories = {
            EventCategory.CAREER,
            EventCategory.RESEARCH,
            EventCategory.STARTUP,
            EventCategory.OPPORTUNITY,
        }
        if category in delayed_categories:
            delayed = [
                DelayedEffectSpec(
                    trigger_after_years=2,
                    probability=0.45,
                    description="The commitment creates a later opening.",
                    effects=EffectPayload(
                        stats={"reputation": 4, "career_level": 3, "stress": 2},
                        set_flags=["recent_success"],
                    ),
                )
            ]
        high_label = {
            EventCategory.HEALTH: "Clear the calendar and recover",
            EventCategory.RELATIONSHIP: "Make a concrete commitment",
            EventCategory.CRISIS: "Lead the recovery in public",
            EventCategory.FINANCE: "Create financial room now",
        }.get(category, "Take the ambitious route")
        measured_label = {
            EventCategory.HEALTH: "Reduce the pace sustainably",
            EventCategory.RELATIONSHIP: "Renegotiate time honestly",
            EventCategory.CRISIS: "Stabilize before rebuilding",
            EventCategory.FINANCE: "Protect optionality and cut scope",
        }.get(category, "Choose the measured route")
        return [
            GeneratedChoice(
                label=high_label,
                description=(
                    f"Accept the sharper trade-off created by {template.title.casefold()} and "
                    "commit visible time and reputation to it."
                ),
                immediate_effects=high_effects[category],
                delayed_effects=delayed,
                risk_level=RiskLevel.HIGH,
            ),
            GeneratedChoice(
                label=measured_label,
                description=(
                    "Limit the immediate upside in order to preserve focus, health, and room to "
                    f"adapt within the {context.universe.name} path."
                ),
                immediate_effects=measured_effects[category],
                risk_level=RiskLevel.LOW,
            ),
        ]

    @staticmethod
    def _artifact_suggestions(category: EventCategory) -> list[SupportedArtifactType]:
        mapping: dict[EventCategory, list[SupportedArtifactType]] = {
            EventCategory.CAREER: [ArtifactType.EMAIL, ArtifactType.SOCIAL_MEDIA_POST],
            EventCategory.RESEARCH: [ArtifactType.ACADEMIC_ABSTRACT, ArtifactType.EMAIL],
            EventCategory.STARTUP: [ArtifactType.COMPANY_ANNOUNCEMENT, ArtifactType.DIARY_ENTRY],
            EventCategory.FINANCE: [ArtifactType.EMAIL, ArtifactType.DIARY_ENTRY],
            EventCategory.HEALTH: [ArtifactType.DIARY_ENTRY, ArtifactType.EMAIL],
            EventCategory.RELATIONSHIP: [ArtifactType.DIARY_ENTRY, ArtifactType.EMAIL],
            EventCategory.OPPORTUNITY: [ArtifactType.NEWS_ARTICLE, ArtifactType.EMAIL],
            EventCategory.CRISIS: [ArtifactType.NEWS_ARTICLE, ArtifactType.DIARY_ENTRY],
            EventCategory.RANDOM: [ArtifactType.SOCIAL_MEDIA_POST, ArtifactType.NEWS_ARTICLE],
        }
        return mapping[category]

    @staticmethod
    def _artifact_content(
        artifact_type: SupportedArtifactType,
        context: NarrativeContext,
        event: GeneratedEvent,
        date: str,
        name: str,
    ) -> tuple[str, ArtifactContent]:
        if artifact_type == ArtifactType.NEWS_ARTICLE:
            title = event.title
            return title, NewsArticleContent(
                publication_name="The Fictional Systems Review",
                headline=event.title,
                date=date,
                subheading=f"A turning point in the {context.universe.name} timeline.",
                body=(
                    f"In this fictional scenario, {name} confronted {event.title.casefold()}. "
                    f"The episode reflected a wider tension between ambition and sustainability."
                ),
                category=event.category.value,
            )
        if artifact_type == ArtifactType.ACADEMIC_ABSTRACT:
            title = f"Adaptive Decisions in {context.current_state.career_title} Systems"
            return title, AcademicAbstractContent(
                paper_title=title,
                authors=[name, "Elena Rossi (fictional)"],
                venue="Fictional Workshop on Adaptive Autonomous Systems",
                year=event.year,
                abstract=(
                    f"This fictional abstract frames the technical lessons surrounding "
                    f"{event.title.casefold()} as a reproducible systems problem."
                ),
                keywords=["adaptive systems", "decision-making", "simulation"],
            )
        if artifact_type == ArtifactType.COMPANY_ANNOUNCEMENT:
            title = "Northstar Machines announces a new chapter"
            return title, CompanyAnnouncementContent(
                company="Northstar Machines (fictional)",
                headline=title,
                date=date,
                announcement=(
                    f"The fictional company announced its response to {event.title.casefold()}, "
                    "emphasizing careful execution and transparent milestones."
                ),
                quote=f"“We are choosing durable learning over theatrical certainty,” said {name}.",
            )
        if artifact_type == ArtifactType.DIARY_ENTRY:
            title = f"Diary — {event.title}"
            return title, DiaryEntryContent(
                date=date,
                mood="restless but clear-eyed",
                entry=(
                    f"Today made {event.title.casefold()} feel real. I can see the upside, but I "
                    "can "
                    "also see what this path asks me to stop pretending is free."
                ),
            )
        if artifact_type == ArtifactType.EMAIL:
            title = f"Decision notes: {event.title}"
            return title, EmailContent(
                sender="Marta Bianchi (fictional collaborator)",
                recipient=name,
                subject=title,
                date=date,
                body=(
                    f"I wrote down the constraints around {event.title.casefold()}. Whatever you "
                    "choose, let us make the cost explicit and review it after six weeks."
                ),
            )
        title = f"A year shaped by {event.title.casefold()}"
        return title, SocialPostContent(
            platform="Professional Network (fictional)",
            author=name,
            date=date,
            content=(
                f"A lesson from {event.title.casefold()}: progress became more useful when the "
                "trade-offs were named instead of hidden."
            ),
            reactions=SeededRandom(context.universe.random_seed)
            .stream(event.event_key, "reactions")
            .randint(40, 1_200),
        )

    @staticmethod
    def _direction_label(context: NarrativeContext) -> str:
        return context.universe.starting_direction.rstrip(".").casefold()

    @staticmethod
    def _tradeoff(category: EventCategory) -> str:
        return {
            EventCategory.CAREER: (
                "Visibility and responsibility competed with protected craft time."
            ),
            EventCategory.RESEARCH: "Research ambition competed with rigor, recovery, and scope.",
            EventCategory.STARTUP: "Runway and speed competed with control and product clarity.",
            EventCategory.FINANCE: (
                "Financial security competed with flexibility and long-term upside."
            ),
            EventCategory.HEALTH: "Recovery competed with momentum, exposing that time was finite.",
            EventCategory.RELATIONSHIP: "Presence competed with professional intensity.",
            EventCategory.OPPORTUNITY: "A rare opening competed with focus on the existing path.",
            EventCategory.CRISIS: (
                "Fast recovery competed with honest diagnosis and sustainable repair."
            ),
            EventCategory.RANDOM: "Unexpected attention competed with every sensible priority.",
        }[category]

    @staticmethod
    def _closing_note(mode: SimulationMode, happiness: int) -> str:
        mode_note = {
            SimulationMode.REALISTIC: "The path remained plausible, mixed, and unfinished.",
            SimulationMode.CINEMATIC: "The year closed on a visible turning point.",
            SimulationMode.UTOPIAN: "Good conditions helped, but choices still carried costs.",
            SimulationMode.DARK: "Survival itself became a form of progress.",
            SimulationMode.CHAOS: "The absurdity remained coherent enough to become history.",
        }[mode]
        return f"{mode_note} Recorded happiness ended at {happiness}."

    @staticmethod
    def _regret(context: NarrativeContext) -> str:
        state = context.current_state
        candidates = {
            "not protecting relationships earlier": state.relationships,
            "treating recovery as optional for too long": state.health,
            "giving away too much freedom to urgent work": state.freedom,
        }
        return min(candidates, key=candidates.__getitem__)
