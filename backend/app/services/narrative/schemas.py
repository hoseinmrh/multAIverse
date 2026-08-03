from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    ArtifactType,
    EventCategory,
    EventImportance,
    RiskLevel,
    SimulationMode,
)
from app.services.simulation.schemas import (
    NORMALIZED_STATS,
    ChoiceRequirements,
    DelayedEffectSpec,
    EffectPayload,
)


class NarrativeSchema(BaseModel):
    """Closed, immutable contract shared by every narrative provider."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


ShortText = Annotated[str, Field(min_length=1, max_length=240)]
Paragraph = Annotated[str, Field(min_length=1, max_length=2_000)]
Score = Annotated[int, Field(ge=0, le=100)]


def _finance_effect_fields() -> list[Literal["monthly_income_delta_eur", "net_worth_delta_eur"]]:
    return ["monthly_income_delta_eur", "net_worth_delta_eur"]


class ProfileNarrativeSummary(NarrativeSchema):
    name: ShortText
    age: Annotated[int, Field(ge=0, le=130)]
    location: ShortText
    occupation: ShortText
    education: Annotated[str, Field(min_length=1, max_length=500)]
    biography: Annotated[str, Field(max_length=800)] = ""
    strengths: list[ShortText] = Field(default_factory=list, max_length=5)
    interests: list[ShortText] = Field(default_factory=list, max_length=5)
    goals: list[ShortText] = Field(default_factory=list, max_length=4)
    constraints: list[ShortText] = Field(default_factory=list, max_length=4)


class UniverseNarrativeSummary(NarrativeSchema):
    name: ShortText
    slug: Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")]
    premise: Paragraph
    starting_direction: Annotated[str, Field(min_length=1, max_length=800)]
    random_seed: int


class NarrativeState(NarrativeSchema):
    year: Annotated[int, Field(gt=1900, le=2200)]
    age: Annotated[int, Field(ge=0, le=130)]
    location: ShortText
    career_title: ShortText
    career_level: Score
    monthly_income_eur: Annotated[int, Field(ge=0)]
    net_worth_eur: int
    health: Score
    relationships: Score
    research_impact: Score
    reputation: Score
    freedom: Score
    stress: Score
    happiness: Score
    discipline: Score
    creativity: Score
    chaos: Score
    skills: dict[str, Score] = Field(default_factory=dict)
    active_flags: list[ShortText] = Field(default_factory=list, max_length=30)


class NarrativeEventRecord(NarrativeSchema):
    event_key: Annotated[str, Field(min_length=1, max_length=120)]
    year: Annotated[int, Field(gt=1900, le=2200)]
    title: ShortText
    description: Paragraph
    category: EventCategory
    importance: EventImportance
    selected_choice: ShortText | None = None


class UnresolvedDecision(NarrativeSchema):
    event_key: Annotated[str, Field(min_length=1, max_length=120)]
    title: ShortText
    description: Paragraph
    choice_labels: list[ShortText] = Field(min_length=1, max_length=4)


class AllowedEffectFields(NarrativeSchema):
    stats: list[str] = Field(
        default_factory=lambda: sorted(NORMALIZED_STATS),
        min_length=len(NORMALIZED_STATS),
        max_length=len(NORMALIZED_STATS),
    )
    finance: list[Literal["monthly_income_delta_eur", "net_worth_delta_eur"]] = Field(
        default_factory=_finance_effect_fields,
        min_length=2,
        max_length=2,
    )
    flags: bool = True
    skills: bool = True

    @model_validator(mode="after")
    def validate_stat_allowlist(self) -> Self:
        if set(self.stats) != NORMALIZED_STATS:
            raise ValueError("Allowed narrative statistics must match the simulation allowlist")
        return self


class NarrativeContext(NarrativeSchema):
    profile: ProfileNarrativeSummary
    universe: UniverseNarrativeSummary
    current_state: NarrativeState
    last_major_events: list[NarrativeEventRecord] = Field(default_factory=list, max_length=3)
    previous_event_keys: list[str] = Field(default_factory=list, max_length=40)
    unresolved_decisions: list[UnresolvedDecision] = Field(default_factory=list, max_length=3)
    long_term_summary: Annotated[str, Field(min_length=1, max_length=1_500)]
    simulation_mode: SimulationMode
    current_year: Annotated[int, Field(gt=1900, le=2200)]
    allowed_effect_fields: AllowedEffectFields = Field(default_factory=AllowedEffectFields)

    @model_validator(mode="after")
    def validate_year_alignment(self) -> Self:
        if self.current_year != self.current_state.year:
            raise ValueError("Context year must match the current state year")
        return self


class UniverseBranchRequest(NarrativeSchema):
    profile: ProfileNarrativeSummary
    decision_question: Annotated[str, Field(min_length=1, max_length=1_000)]
    scenario_seed: int
    simulation_mode: SimulationMode
    number_of_branches: Annotated[int, Field(ge=1, le=3)] = 3
    branch_directions: list[ShortText] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_directions(self) -> Self:
        if self.branch_directions and len(self.branch_directions) != self.number_of_branches:
            raise ValueError("Custom branch directions must match number_of_branches")
        return self


class ProposedInitialState(NarrativeSchema):
    location: ShortText
    career_title: ShortText
    career_level: Score
    monthly_income_eur: Annotated[int, Field(ge=0)]
    net_worth_eur: int
    health: Score
    relationships: Score
    research_impact: Score
    reputation: Score
    freedom: Score
    stress: Score
    happiness: Score
    discipline: Score
    creativity: Score
    chaos: Score
    skills: dict[str, Score]
    active_flags: list[ShortText]


VisualTheme = Literal["structured-grid", "orbital-geometry", "energetic-particles"]
AccentColor = Literal["#3B82F6", "#8B5CF6", "#F59E0B"]


class GeneratedUniverseBranch(NarrativeSchema):
    name: ShortText
    slug: Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")]
    subtitle: ShortText
    premise: Paragraph
    visual_theme: VisualTheme
    accent_color: AccentColor
    starting_direction: Annotated[str, Field(min_length=1, max_length=800)]
    proposed_initial_state: ProposedInitialState
    narrative_tags: list[ShortText] = Field(min_length=1, max_length=8)


class GeneratedChoice(NarrativeSchema):
    label: Annotated[str, Field(min_length=1, max_length=180)]
    description: Paragraph
    immediate_effects: EffectPayload = Field(default_factory=EffectPayload)
    delayed_effects: list[DelayedEffectSpec] = Field(default_factory=list, max_length=3)
    requirements: ChoiceRequirements = Field(default_factory=ChoiceRequirements)
    risk_level: RiskLevel = RiskLevel.MEDIUM


SupportedArtifactType = Literal[
    ArtifactType.NEWS_ARTICLE,
    ArtifactType.ACADEMIC_ABSTRACT,
    ArtifactType.COMPANY_ANNOUNCEMENT,
    ArtifactType.DIARY_ENTRY,
    ArtifactType.EMAIL,
    ArtifactType.SOCIAL_MEDIA_POST,
]


class GeneratedEvent(NarrativeSchema):
    event_key: Annotated[str, Field(min_length=1, max_length=120)]
    year: Annotated[int, Field(gt=1900, le=2200)]
    title: Annotated[str, Field(min_length=1, max_length=220)]
    description: Paragraph
    category: EventCategory
    importance: EventImportance
    requires_choice: bool
    choices: list[GeneratedChoice] = Field(default_factory=list, max_length=4)
    automatic_effects: EffectPayload | None = None
    artifact_suggestions: list[SupportedArtifactType] = Field(default_factory=list, max_length=2)
    narrative_tags: list[ShortText] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_resolution_shape(self) -> Self:
        if self.requires_choice:
            if len(self.choices) < 2:
                raise ValueError("A decision event must provide at least two choices")
            if self.automatic_effects is not None:
                raise ValueError("A decision event cannot provide automatic effects")
        elif self.choices or self.automatic_effects is None:
            raise ValueError("An automatic event must provide effects and no choices")
        return self


class GeneratedYearSummary(NarrativeSchema):
    year: Annotated[int, Field(gt=1900, le=2200)]
    headline: ShortText
    overview: Paragraph
    key_developments: list[ShortText] = Field(min_length=1, max_length=4)
    defining_tradeoff: Annotated[str, Field(min_length=1, max_length=500)]
    closing_note: Annotated[str, Field(min_length=1, max_length=500)]
    narrative_tags: list[ShortText] = Field(min_length=1, max_length=8)


class NewsArticleContent(NarrativeSchema):
    publication_name: ShortText
    headline: ShortText
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    subheading: Annotated[str, Field(min_length=1, max_length=500)]
    body: Paragraph
    category: ShortText


class AcademicAbstractContent(NarrativeSchema):
    paper_title: ShortText
    authors: list[ShortText] = Field(min_length=1, max_length=8)
    venue: ShortText
    year: Annotated[int, Field(gt=1900, le=2200)]
    abstract: Paragraph
    keywords: list[ShortText] = Field(min_length=2, max_length=8)


class CompanyAnnouncementContent(NarrativeSchema):
    company: ShortText
    headline: ShortText
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    announcement: Paragraph
    quote: Annotated[str, Field(min_length=1, max_length=600)]


class DiaryEntryContent(NarrativeSchema):
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    mood: ShortText
    entry: Paragraph


class EmailContent(NarrativeSchema):
    sender: ShortText
    recipient: ShortText
    subject: ShortText
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    body: Paragraph


class SocialPostContent(NarrativeSchema):
    platform: ShortText
    author: ShortText
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    content: Paragraph
    reactions: Annotated[int, Field(ge=0, le=10_000_000)]


ArtifactContent = (
    NewsArticleContent
    | AcademicAbstractContent
    | CompanyAnnouncementContent
    | DiaryEntryContent
    | EmailContent
    | SocialPostContent
)


class ArtifactMetadata(NarrativeSchema):
    is_fictional: Literal[True] = True
    event_key: Annotated[str, Field(min_length=1, max_length=120)]
    narrative_tags: list[ShortText] = Field(default_factory=list, max_length=8)


class GeneratedArtifact(NarrativeSchema):
    artifact_type: SupportedArtifactType
    title: ShortText
    content: ArtifactContent
    metadata: ArtifactMetadata

    @model_validator(mode="after")
    def validate_content_type(self) -> Self:
        expected: dict[ArtifactType, type[NarrativeSchema]] = {
            ArtifactType.NEWS_ARTICLE: NewsArticleContent,
            ArtifactType.ACADEMIC_ABSTRACT: AcademicAbstractContent,
            ArtifactType.COMPANY_ANNOUNCEMENT: CompanyAnnouncementContent,
            ArtifactType.DIARY_ENTRY: DiaryEntryContent,
            ArtifactType.EMAIL: EmailContent,
            ArtifactType.SOCIAL_MEDIA_POST: SocialPostContent,
        }
        if not isinstance(self.content, expected[self.artifact_type]):
            raise ValueError("Artifact content does not match artifact_type")
        return self


class GeneratedFutureSelfProfile(NarrativeSchema):
    name: ShortText
    age: Annotated[int, Field(ge=0, le=130)]
    location: ShortText
    occupation: ShortText
    universe: ShortText
    key_achievement: Annotated[str, Field(min_length=1, max_length=500)]
    greatest_regret: Annotated[str, Field(min_length=1, max_length=500)]
    happiness: Score
    stress: Score
    personality_summary: Annotated[str, Field(min_length=1, max_length=800)]
    fictional_character: Literal[True] = True


class FutureSelfMessage(NarrativeSchema):
    role: Literal["user", "future_self"]
    content: Annotated[str, Field(min_length=1, max_length=2_000)]


class FutureSelfReplyRequest(NarrativeSchema):
    context: NarrativeContext
    profile: GeneratedFutureSelfProfile
    message: Annotated[str, Field(min_length=1, max_length=2_000)]
    conversation_history: list[FutureSelfMessage] = Field(default_factory=list, max_length=12)


class GeneratedFutureSelfReply(NarrativeSchema):
    content: Paragraph
    referenced_event_keys: list[str] = Field(default_factory=list, max_length=3)
    tone: Literal["reflective", "hopeful", "candid", "wry", "somber"]
    fictional_character: Literal[True] = True
