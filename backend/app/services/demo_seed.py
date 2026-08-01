from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import LifeStateSnapshot, PersonProfile, Scenario, Universe
from app.models.enums import SimulationMode, UniverseStatus
from app.repositories import (
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)

DEMO_PROFILE_ID = UUID("10000000-0000-4000-8000-000000000001")
DEMO_SCENARIO_ID = UUID("20000000-0000-4000-8000-000000000001")
APPLIED_AI_UNIVERSE_ID = UUID("30000000-0000-4000-8000-000000000001")
ROBOTICS_UNIVERSE_ID = UUID("30000000-0000-4000-8000-000000000002")
STARTUP_UNIVERSE_ID = UUID("30000000-0000-4000-8000-000000000003")


@dataclass(frozen=True)
class DemoSeedResult:
    profile_id: UUID
    scenario_id: UUID
    universe_ids: tuple[UUID, UUID, UUID]


@dataclass(frozen=True)
class UniverseSeedDefinition:
    id: UUID
    name: str
    slug: str
    subtitle: str
    premise: str
    accent: str
    motif: str
    starting_direction: str
    random_seed: int
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
    skills: dict[str, object]
    active_flags: list[str]


UNIVERSE_DEFINITIONS = (
    UniverseSeedDefinition(
        id=APPLIED_AI_UNIVERSE_ID,
        name="Applied AI Leader",
        slug="applied-ai-leader",
        subtitle="From research engineering to responsible AI leadership",
        premise=(
            "Hosein remains in industry and develops toward an AI research engineering "
            "leadership role."
        ),
        accent="#3B82F6",
        motif="structured-grid",
        starting_direction="Build applied AI systems and grow into technical leadership.",
        random_seed=202_601,
        career_title="AI Research Engineer",
        career_level=36,
        monthly_income_eur=3_200,
        net_worth_eur=14_000,
        health=77,
        relationships=63,
        research_impact=47,
        reputation=42,
        freedom=50,
        stress=60,
        happiness=69,
        discipline=84,
        creativity=79,
        chaos=26,
        skills={"applied_ai": 72, "software_engineering": 76, "leadership": 38},
        active_flags=["industry_path", "masters_completed"],
    ),
    UniverseSeedDefinition(
        id=ROBOTICS_UNIVERSE_ID,
        name="Robotics Researcher",
        slug="robotics-researcher",
        subtitle="A funded PhD in autonomous systems and optimization",
        premise=(
            "Hosein accepts a funded robotics PhD and focuses on optimization, learning, "
            "and autonomous systems."
        ),
        accent="#8B5CF6",
        motif="orbital-geometry",
        starting_direction="Pursue rigorous robotics research through a funded PhD.",
        random_seed=202_602,
        career_title="Robotics PhD Researcher",
        career_level=29,
        monthly_income_eur=1_800,
        net_worth_eur=11_000,
        health=76,
        relationships=61,
        research_impact=55,
        reputation=39,
        freedom=55,
        stress=63,
        happiness=70,
        discipline=86,
        creativity=82,
        chaos=28,
        skills={"robotics": 64, "optimization": 73, "research": 70},
        active_flags=["phd_path", "funded_research", "masters_completed"],
    ),
    UniverseSeedDefinition(
        id=STARTUP_UNIVERSE_ID,
        name="Startup Founder",
        slug="startup-founder",
        subtitle="An ambitious return to building an AI product company",
        premise=(
            "Hosein returns full-time to building an AI product company and attempts to "
            "raise funding."
        ),
        accent="#F59E0B",
        motif="energetic-particles",
        starting_direction="Build an AI product company and seek an initial funding round.",
        random_seed=202_603,
        career_title="AI Startup Founder",
        career_level=24,
        monthly_income_eur=900,
        net_worth_eur=8_000,
        health=73,
        relationships=59,
        research_impact=44,
        reputation=38,
        freedom=70,
        stress=72,
        happiness=71,
        discipline=83,
        creativity=88,
        chaos=55,
        skills={"product": 52, "software_engineering": 74, "fundraising": 26},
        active_flags=["startup_path", "bootstrapping", "masters_completed"],
    ),
)


class DemoSeedService:
    """Create the stable demo graph exactly once inside one transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.profiles = PersonProfileRepository(session)
        self.scenarios = ScenarioRepository(session)
        self.universes = UniverseRepository(session)
        self.snapshots = LifeStateSnapshotRepository(session)

    def seed(self) -> DemoSeedResult:
        with self.session.begin():
            self._seed_profile()
            self._seed_scenario()
            for definition in UNIVERSE_DEFINITIONS:
                self._seed_universe(definition)

        return DemoSeedResult(
            profile_id=DEMO_PROFILE_ID,
            scenario_id=DEMO_SCENARIO_ID,
            universe_ids=(
                APPLIED_AI_UNIVERSE_ID,
                ROBOTICS_UNIVERSE_ID,
                STARTUP_UNIVERSE_ID,
            ),
        )

    def _seed_profile(self) -> None:
        if self.profiles.get(DEMO_PROFILE_ID) is not None:
            return
        self.profiles.add(
            PersonProfile(
                id=DEMO_PROFILE_ID,
                name="Hosein",
                birth_year=2001,
                starting_year=2026,
                starting_age=25,
                location="Milan",
                occupation="Part-time AI and R&D engineer",
                education="MSc student in Computer Science and Engineering",
                biography=(
                    "A fictionalized early-career engineer balancing advanced study, applied "
                    "AI work, research ambitions, and entrepreneurial experiments."
                ),
                strengths=[
                    "Strong technical background",
                    "Research experience",
                    "Software engineering experience",
                    "High academic performance",
                    "Entrepreneurial interest",
                    "Adaptability",
                    "International experience",
                ],
                weaknesses=[
                    "Risk of overcommitting",
                    "Difficulty protecting focused time",
                ],
                interests=[
                    "Artificial intelligence",
                    "Robotics",
                    "Research",
                    "Startups",
                    "Quantum-inspired optimization",
                    "Fitness",
                    "Travel",
                ],
                goals=[
                    "Finish the master's degree",
                    "Build meaningful technical work",
                    "Choose a sustainable post-graduation path",
                ],
                constraints=[
                    "Finishing a master's degree",
                    "Limited time",
                    "Competing professional and academic priorities",
                    "Financial uncertainty",
                    "Risk of taking on too many projects",
                    "Decisions about where to live after graduation",
                ],
                starting_stats={
                    "career_level": 30,
                    "health": 78,
                    "relationships": 64,
                    "research_impact": 48,
                    "reputation": 36,
                    "freedom": 52,
                    "stress": 58,
                    "happiness": 68,
                    "discipline": 84,
                    "creativity": 80,
                    "chaos": 30,
                },
            )
        )

    def _seed_scenario(self) -> None:
        if self.scenarios.get(DEMO_SCENARIO_ID) is not None:
            return
        self.scenarios.add(
            Scenario(
                id=DEMO_SCENARIO_ID,
                profile_id=DEMO_PROFILE_ID,
                title="After Graduation",
                decision_question="What should Hosein prioritize after graduation?",
                description=(
                    "Explore three fictional paths through applied AI leadership, robotics "
                    "research, and startup building."
                ),
                number_of_universes=3,
                simulation_mode=SimulationMode.REALISTIC,
                seed=202_600,
            )
        )

    def _seed_universe(self, definition: UniverseSeedDefinition) -> None:
        if self.universes.get(definition.id) is None:
            self.universes.add(
                Universe(
                    id=definition.id,
                    scenario_id=DEMO_SCENARIO_ID,
                    name=definition.name,
                    slug=definition.slug,
                    subtitle=definition.subtitle,
                    premise=definition.premise,
                    visual_theme={"accent": definition.accent, "motif": definition.motif},
                    starting_direction=definition.starting_direction,
                    current_year=2026,
                    current_age=25,
                    random_seed=definition.random_seed,
                    status=UniverseStatus.ACTIVE,
                )
            )

        if self.snapshots.latest(definition.id) is not None:
            return
        self.snapshots.add(
            LifeStateSnapshot(
                universe_id=definition.id,
                year=2026,
                age=25,
                location="Milan",
                career_title=definition.career_title,
                career_level=definition.career_level,
                monthly_income_eur=definition.monthly_income_eur,
                net_worth_eur=definition.net_worth_eur,
                health=definition.health,
                relationships=definition.relationships,
                research_impact=definition.research_impact,
                reputation=definition.reputation,
                freedom=definition.freedom,
                stress=definition.stress,
                happiness=definition.happiness,
                discipline=definition.discipline,
                creativity=definition.creativity,
                chaos=definition.chaos,
                skills=definition.skills,
                active_flags=definition.active_flags,
            )
        )
