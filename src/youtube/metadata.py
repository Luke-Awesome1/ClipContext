"""Builds a YouTube `videos.insert` request body from ClipContext selections.

Deliberately does not touch generated_content.json — this is a separate,
throwaway request payload assembled fresh for each upload.
"""

from src.youtube.constants import (
    DEFAULT_CATEGORY_ID,
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
)


def _normalize_tags(hashtags: list[str]) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []

    for tag in hashtags:
        stripped = tag.lstrip("#").strip()

        if not stripped:
            continue

        key = stripped.lower()

        if key in seen:
            continue

        seen.add(key)
        tags.append(stripped)

    return tags


def _hashtag_line(hashtags: list[str]) -> str:
    clean = []

    for tag in hashtags:
        stripped = tag.strip()

        if not stripped:
            continue

        clean.append(stripped if stripped.startswith("#") else f"#{stripped}")

    return " ".join(clean)


def build_upload_body(
    title: str,
    description: str,
    hashtags: list[str],
    privacy_status: str,
    made_for_kids: bool,
) -> dict:
    hashtag_line = _hashtag_line(hashtags)
    base_description = description.rstrip()

    if hashtag_line:
        full_description = (
            f"{base_description}\n\n{hashtag_line}" if base_description else hashtag_line
        )
    else:
        full_description = base_description

    return {
        "snippet": {
            "title": title.strip()[:MAX_TITLE_LENGTH],
            "description": full_description[:MAX_DESCRIPTION_LENGTH],
            "tags": _normalize_tags(hashtags),
            "categoryId": DEFAULT_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
