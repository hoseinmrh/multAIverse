from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.enums import UniverseStatus
from app.schemas import LifeStateSnapshotCreate, PersonProfileCreate, UniverseCreate


def test_snapshot_schema_rejects_out_of_range_statistics() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 100"):
        LifeStateSnapshotCreate(
            universe_id=uuid4(),
            year=2026,
            age=25,
            location="Milan",
            career_title="Engineer",
            career_level=30,
            monthly_income_eur=2_000,
            net_worth_eur=5_000,
            health=101,
            relationships=60,
            research_impact=40,
            reputation=35,
            freedom=50,
            stress=55,
            happiness=65,
            discipline=80,
            creativity=75,
            chaos=25,
        )


def test_universe_schema_forbids_unknown_fields_and_validates_slug() -> None:
    valid_data = {
        "scenario_id": uuid4(),
        "name": "Applied AI Leader",
        "slug": "applied-ai-leader",
        "subtitle": "A path",
        "premise": "A grounded fictional premise.",
        "visual_theme": {"accent": "blue"},
        "starting_direction": "Remain in industry.",
        "current_year": 2026,
        "current_age": 25,
        "random_seed": 42,
        "status": UniverseStatus.ACTIVE,
    }
    assert UniverseCreate.model_validate(valid_data).slug == "applied-ai-leader"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        UniverseCreate.model_validate({**valid_data, "simulation_result": "unvalidated"})

    with pytest.raises(ValidationError, match="String should match pattern"):
        UniverseCreate.model_validate({**valid_data, "slug": "Not Safe"})


def test_profile_schema_rejects_a_start_before_birth() -> None:
    with pytest.raises(ValidationError, match="starting_year must not be earlier"):
        PersonProfileCreate(
            name="Impossible Profile",
            birth_year=2027,
            starting_year=2026,
            starting_age=0,
            location="Milan",
            occupation="Student",
            education="School",
        )
