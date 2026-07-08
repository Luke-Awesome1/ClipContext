import pytest
from pydantic import ValidationError

from src.models.discriminator.schemas import DiscriminatorResult, RankedCandidate
from src.models.generated_content import GeneratedContent


def _titles(n=10):
    return [{"id": i, "text": f"Title {i}"} for i in range(1, n + 1)]


def _descriptions(n=10):
    return [{"id": i, "text": f"Description {i}"} for i in range(1, n + 1)]


def _hashtags(n=10):
    return [{"id": i, "tags": [f"#tag{i}"]} for i in range(1, n + 1)]


def _ranked(n=10):
    return [
        {"id": i, "rank": i, "score": 100 - i, "reason": "because"}
        for i in range(1, n + 1)
    ]


def test_generated_content_requires_exactly_ten_of_each():
    GeneratedContent.model_validate(
        {
            "titles": _titles(),
            "descriptions": _descriptions(),
            "hashtags": _hashtags(),
        }
    )


def test_generated_content_rejects_wrong_title_count():
    with pytest.raises(ValidationError):
        GeneratedContent.model_validate(
            {
                "titles": _titles(9),
                "descriptions": _descriptions(),
                "hashtags": _hashtags(),
            }
        )


def test_generated_content_rejects_non_sequential_ids():
    titles = _titles()
    titles[0]["id"] = 99

    with pytest.raises(ValidationError):
        GeneratedContent.model_validate(
            {
                "titles": titles,
                "descriptions": _descriptions(),
                "hashtags": _hashtags(),
            }
        )


def test_discriminator_result_accepts_independent_pools():
    result = DiscriminatorResult.model_validate(
        {
            "titles": _ranked(),
            "descriptions": _ranked(),
            "hashtags": _ranked(),
        }
    )

    assert result.titles[0].rank == 1
    # Pools are independent — ids need not line up across pools.
    assert [c.id for c in result.titles] == [c.id for c in result.descriptions]


def test_discriminator_result_rejects_duplicate_ranks():
    ranked = _ranked()
    ranked[1]["rank"] = 1  # duplicate rank 1

    with pytest.raises(ValidationError):
        DiscriminatorResult.model_validate(
            {
                "titles": ranked,
                "descriptions": _ranked(),
                "hashtags": _ranked(),
            }
        )


def test_ranked_candidate_score_must_be_within_bounds():
    with pytest.raises(ValidationError):
        RankedCandidate.model_validate(
            {"id": 1, "rank": 1, "score": 150, "reason": "too high"}
        )
