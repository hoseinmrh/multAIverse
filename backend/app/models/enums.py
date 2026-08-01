from enum import StrEnum


class SimulationMode(StrEnum):
    REALISTIC = "realistic"
    CINEMATIC = "cinematic"
    UTOPIAN = "utopian"
    DARK = "dark"
    CHAOS = "chaos"


class UniverseStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EventCategory(StrEnum):
    CAREER = "career"
    EDUCATION = "education"
    FINANCE = "finance"
    RESEARCH = "research"
    STARTUP = "startup"
    HEALTH = "health"
    RELATIONSHIP = "relationship"
    SOCIAL = "social"
    TRAVEL = "travel"
    OPPORTUNITY = "opportunity"
    CRISIS = "crisis"
    RANDOM = "random"
    CROSSOVER = "crossover"


class EventImportance(StrEnum):
    ROUTINE = "routine"
    NOTABLE = "notable"
    MAJOR = "major"


class EventType(StrEnum):
    NARRATIVE = "narrative"
    DECISION = "decision"
    MILESTONE = "milestone"


class EventStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"


class EventSource(StrEnum):
    SEEDED = "seeded"
    SYSTEM = "system"
    MOCK = "mock"
    OPENAI = "openai"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArtifactType(StrEnum):
    NEWS_ARTICLE = "news_article"
    DIARY_ENTRY = "diary_entry"
    LINKEDIN_UPDATE = "linkedin_update"
    ACADEMIC_ABSTRACT = "academic_abstract"
    COMPANY_ANNOUNCEMENT = "company_announcement"
    EMAIL = "email"
    TEXT_CONVERSATION = "text_conversation"
    CONFERENCE_INVITATION = "conference_invitation"
    REJECTION_LETTER = "rejection_letter"
    AWARD = "award"
    FINANCIAL_SNAPSHOT = "financial_snapshot"
    CALENDAR_ENTRY = "calendar_entry"
    SOCIAL_MEDIA_POST = "social_media_post"
    FUTURE_SELF_NOTE = "future_self_note"


class MessageRole(StrEnum):
    USER = "user"
    FUTURE_SELF = "future_self"
    SYSTEM = "system"
