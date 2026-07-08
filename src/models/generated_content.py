from pydantic import BaseModel, model_validator


class TextCandidate(BaseModel):
    id: int
    text: str


class HashtagCandidate(BaseModel):
    id: int
    tags: list[str]


class GeneratedContent(BaseModel):
    titles: list[TextCandidate]
    descriptions: list[TextCandidate]
    hashtags: list[HashtagCandidate]

    @model_validator(mode="after")
    def validate_candidate_counts(self) -> "GeneratedContent":
        if len(self.titles) != 10:
            raise ValueError(
                f"Expected exactly 10 titles, "
                f"received {len(self.titles)}"
            )

        if len(self.descriptions) != 10:
            raise ValueError(
                f"Expected exactly 10 descriptions, "
                f"received {len(self.descriptions)}"
            )

        if len(self.hashtags) != 10:
            raise ValueError(
                f"Expected exactly 10 hashtag sets, "
                f"received {len(self.hashtags)}"
            )

        expected_ids = list(range(1, 11))

        title_ids = [
            candidate.id
            for candidate in self.titles
        ]

        description_ids = [
            candidate.id
            for candidate in self.descriptions
        ]

        hashtag_ids = [
            candidate.id
            for candidate in self.hashtags
        ]

        if title_ids != expected_ids:
            raise ValueError(
                "Title IDs must be integers from 1 through 10 "
                "in ascending order"
            )

        if description_ids != expected_ids:
            raise ValueError(
                "Description IDs must be integers from 1 through 10 "
                "in ascending order"
            )

        if hashtag_ids != expected_ids:
            raise ValueError(
                "Hashtag IDs must be integers from 1 through 10 "
                "in ascending order"
            )

        return self