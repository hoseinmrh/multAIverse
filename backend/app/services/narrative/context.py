import re
from collections.abc import Sequence

from app.models import Event, LifeStateSnapshot, PersonProfile, Scenario, Universe
from app.models.enums import EventStatus
from app.services.narrative.schemas import (
    GeneratedEvent,
    NarrativeContext,
    NarrativeEventRecord,
    NarrativeState,
    ProfileNarrativeSummary,
    UniverseNarrativeSummary,
    UnresolvedDecision,
)
from app.services.simulation.state import SimulationState


def _event_key(title: str, year: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{year}-{slug[:90]}"


def _state_schema(state: LifeStateSnapshot | SimulationState) -> NarrativeState:
    skills = state.skills if isinstance(state, LifeStateSnapshot) else state.skills_dict()
    flags = state.active_flags
    normalized_skills: dict[str, int] = {}
    for name, value in skills.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Narrative skill score is not an integer: {name}")
        normalized_skills[name] = value
    return NarrativeState(
        year=state.year,
        age=state.age,
        location=state.location,
        career_title=state.career_title,
        career_level=state.career_level,
        monthly_income_eur=state.monthly_income_eur,
        net_worth_eur=state.net_worth_eur,
        health=state.health,
        relationships=state.relationships,
        research_impact=state.research_impact,
        reputation=state.reputation,
        freedom=state.freedom,
        stress=state.stress,
        happiness=state.happiness,
        discipline=state.discipline,
        creativity=state.creativity,
        chaos=state.chaos,
        skills=normalized_skills,
        active_flags=sorted(flags),
    )


def _record(event: Event | GeneratedEvent) -> NarrativeEventRecord:
    if isinstance(event, GeneratedEvent):
        return NarrativeEventRecord(
            event_key=event.event_key,
            year=event.year,
            title=event.title,
            description=event.description,
            category=event.category,
            importance=event.importance,
        )
    selected = next((choice.label for choice in event.choices if choice.selected), None)
    return NarrativeEventRecord(
        event_key=event.narrative_key or _event_key(event.title, event.year),
        year=event.year,
        title=event.title,
        description=event.description,
        category=event.category,
        importance=event.importance,
        selected_choice=selected,
    )


class NarrativeContextBuilder:
    """Build a bounded provider context without querying or modifying persistence."""

    def build(
        self,
        *,
        profile: PersonProfile,
        scenario: Scenario,
        universe: Universe,
        current_state: LifeStateSnapshot | SimulationState,
        previous_events: Sequence[Event | GeneratedEvent] = (),
        unresolved_events: Sequence[Event] = (),
        long_term_summary: str | None = None,
    ) -> NarrativeContext:
        records = [_record(event) for event in previous_events]
        major = [record for record in records if record.importance.value != "routine"][-3:]
        unresolved = [
            UnresolvedDecision(
                event_key=_event_key(event.title, event.year),
                title=event.title,
                description=event.description,
                choice_labels=[choice.label for choice in event.choices][:4],
            )
            for event in unresolved_events
            if event.status == EventStatus.PENDING and event.choices
        ][-3:]
        summary = long_term_summary or self._summarize_history(records, universe)
        return NarrativeContext(
            profile=ProfileNarrativeSummary(
                name=profile.name,
                age=current_state.age,
                location=profile.location,
                occupation=profile.occupation,
                education=profile.education,
                biography=profile.biography[:800],
                strengths=profile.strengths[:5],
                interests=profile.interests[:5],
                goals=profile.goals[:4],
                constraints=profile.constraints[:4],
            ),
            universe=UniverseNarrativeSummary(
                name=universe.name,
                slug=universe.slug,
                premise=universe.premise,
                starting_direction=universe.starting_direction,
                random_seed=universe.random_seed,
            ),
            current_state=_state_schema(current_state),
            last_major_events=major,
            previous_event_keys=[record.event_key for record in records[-40:]],
            unresolved_decisions=unresolved,
            long_term_summary=summary,
            simulation_mode=scenario.simulation_mode,
            current_year=current_state.year,
        )

    @staticmethod
    def _summarize_history(records: Sequence[NarrativeEventRecord], universe: Universe) -> str:
        if not records:
            return f"The {universe.name} path has just begun: {universe.starting_direction}"
        titles = "; ".join(record.title for record in records[-6:])
        return f"So far, the {universe.name} timeline has been shaped by: {titles}."[:1_500]
