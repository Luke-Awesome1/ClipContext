from pydantic import BaseModel, Field


class KeyMoment(BaseModel):
    start_time: float
    end_time: float

    spoken_content: str
    visual_content: str

    significance: str


class VideoContext(BaseModel):
    topic: str

    content_type: str

    core_message: str

    transcript_summary: str

    visual_summary: str

    multimodal_summary: str

    key_moments: list[KeyMoment] = Field(
        default_factory=list
    )

    key_entities: list[str] = Field(
        default_factory=list
    )

    visible_text: list[str] = Field(
        default_factory=list
    )

    emotional_arc: str

    visual_style: str

    technical_level: str

    target_audience_signals: list[str] = Field(
        default_factory=list
    )

    captionable_details: list[str] = Field(
        default_factory=list
    )

    uncertainties: list[str] = Field(
        default_factory=list
    )