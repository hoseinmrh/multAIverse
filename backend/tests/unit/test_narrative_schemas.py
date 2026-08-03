import pytest
from pydantic import ValidationError

from app.models.enums import (
    ArtifactType,
    EventCategory,
    EventImportance,
    RiskLevel,
    SimulationMode,
)
from app.services.narrative.schemas import (
    GeneratedChoice,
    GeneratedEvent,
    NarrativeState,
    ProfileNarrativeSummary,
    UniverseBranchRequest,
)
from app.services.simulation.schemas import EffectPayload


def test_generated_event_contract_is_closed_and_resolution_shape_is_strict() -> None:
    choice = GeneratedChoice(
        label="Commit",
        description="Commit to the work with an explicit review point.",
        immediate_effects=EffectPayload(stats={"career_level": 4}),
        risk_level=RiskLevel.MEDIUM,
    )
    second = GeneratedChoice(
        label="Protect focus",
        description="Decline the expansion and preserve focused time.",
        immediate_effects=EffectPayload(stats={"freedom": 3}),
        risk_level=RiskLevel.LOW,
    )
    event = GeneratedEvent(
        event_key="career-window",
        year=2027,
        title="A career window",
        description="A fictional team proposes a wider technical mandate.",
        category=EventCategory.CAREER,
        importance=EventImportance.MAJOR,
        requires_choice=True,
        choices=[choice, second],
        artifact_suggestions=[ArtifactType.EMAIL],
        narrative_tags=["career", "fictional"],
    )

    assert event.model_dump(mode="json")["category"] == "career"
    with pytest.raises(ValidationError, match="at least two choices"):
        GeneratedEvent(
            event_key="invalid",
            year=2027,
            title="Invalid decision",
            description="This event has too few choices.",
            category=EventCategory.CAREER,
            importance=EventImportance.MAJOR,
            requires_choice=True,
            choices=[choice],
            narrative_tags=["invalid"],
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        GeneratedEvent.model_validate({**event.model_dump(), "provider_command": "write-db"})


def test_generated_effects_reuse_simulation_allowlist() -> None:
    with pytest.raises(ValidationError, match="Unknown statistics"):
        GeneratedChoice(
            label="Invalid",
            description="Try to bypass the deterministic engine.",
            immediate_effects=EffectPayload(stats={"secret_power": 100}),
        )


def test_key_value_wire_entries_validate_into_engine_maps() -> None:
    effects = EffectPayload.model_validate(
        {
            "stats": [{"key": "career_level", "value": 4}],
            "skill_changes": [{"key": "negotiation", "value": 3}],
        }
    )

    assert effects.stats == {"career_level": 4}
    assert effects.skill_changes == {"negotiation": 3}
    with pytest.raises(ValidationError):
        EffectPayload.model_validate(
            {
                "stats": [
                    {"key": "stress", "value": 2},
                    {"key": "stress", "value": 3},
                ]
            }
        )


def test_context_state_and_branch_request_are_bounded() -> None:
    with pytest.raises(ValidationError):
        NarrativeState(
            year=2026,
            age=25,
            location="Milan",
            career_title="Engineer",
            career_level=101,
            monthly_income_eur=1_000,
            net_worth_eur=0,
            health=70,
            relationships=70,
            research_impact=70,
            reputation=70,
            freedom=70,
            stress=70,
            happiness=70,
            discipline=70,
            creativity=70,
            chaos=20,
            skills={},
            active_flags=[],
        )

    profile = ProfileNarrativeSummary(
        name="Hosein",
        age=25,
        location="Milan",
        occupation="Engineer",
        education="MSc",
    )
    with pytest.raises(ValidationError, match="must match"):
        UniverseBranchRequest(
            profile=profile,
            decision_question="What next?",
            scenario_seed=1,
            simulation_mode=SimulationMode.REALISTIC,
            number_of_branches=3,
            branch_directions=["Industry", "Research"],
        )
