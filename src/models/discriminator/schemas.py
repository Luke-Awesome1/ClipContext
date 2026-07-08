from pydantic import BaseModel, Field, model_validator


class RankedCandidate(BaseModel):
    id: int
    rank: int
    score: int = Field(ge=0, le=100)
    reason: str


class DiscriminatorResult(BaseModel):
    """Independent ranking of each candidate pool.

    Titles, descriptions, and hashtag sets are independent candidate pools —
    ranking candidate id 3 first in `titles` does not imply any pairing with
    the id-3 entry in `descriptions` or `hashtags`.
    """

    titles: list[RankedCandidate]
    descriptions: list[RankedCandidate]
    hashtags: list[RankedCandidate]

    @model_validator(mode="after")
    def validate_ranks(self) -> "DiscriminatorResult":
        for pool_name in ("titles", "descriptions", "hashtags"):
            pool = getattr(self, pool_name)

            if len(pool) != 10:
                raise ValueError(
                    f"Expected exactly 10 ranked {pool_name}, "
                    f"received {len(pool)}"
                )

            ranks = sorted(item.rank for item in pool)

            if ranks != list(range(1, 11)):
                raise ValueError(
                    f"Ranked {pool_name} must use ranks 1 through 10 "
                    "with no duplicates"
                )

        return self
