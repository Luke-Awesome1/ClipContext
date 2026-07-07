from pydantic import BaseModel, Field


class VisualWindowAnalysis(BaseModel):
    description: str

    subjects: list[str] = Field(
        default_factory=list
    )

    actions: list[str] = Field(
        default_factory=list
    )

    objects: list[str] = Field(
        default_factory=list
    )

    visible_text: list[str] = Field(
        default_factory=list
    )

    setting: str

    visual_mood: str