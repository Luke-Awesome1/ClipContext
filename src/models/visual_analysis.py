from pydantic import BaseModel, Field


class VisualEvent(BaseModel):
    start_time: float
    end_time: float
    description: str

    visible_text: list[str] = Field(
        default_factory=list
    )

    entities: list[str] = Field(
        default_factory=list
    )


class VisualAnalysis(BaseModel):
    visual_summary: str

    setting: str

    visual_style: str

    events: list[VisualEvent] = Field(
        default_factory=list
    )

    recurring_entities: list[str] = Field(
        default_factory=list
    )

    visual_tone: str