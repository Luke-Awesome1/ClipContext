from pydantic import BaseModel, Field


class VisualEvent(BaseModel):
    start_time: float
    end_time: float
    description: str


class VideoContext(BaseModel):
    transcript: str

    topic: str
    content_type: str

    visual_summary: str

    visual_events: list[VisualEvent] = Field(
        default_factory=list
    )

    key_entities: list[str] = Field(
        default_factory=list
    )

    emotional_tone: str

    technical_level: str

    core_message: str