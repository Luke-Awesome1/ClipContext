from src.youtube.metadata import build_upload_body


def test_hashtags_are_appended_to_description():
    body = build_upload_body(
        title="My Video",
        description="A cool video.",
        hashtags=["#AI", "#VideoAnalysis"],
        privacy_status="private",
        made_for_kids=False,
    )

    assert body["snippet"]["description"] == "A cool video.\n\n#AI #VideoAnalysis"


def test_tags_strip_leading_hash_and_dedupe_case_insensitively():
    body = build_upload_body(
        title="My Video",
        description="Desc",
        hashtags=["#AI", "ai", "#VideoAnalysis", "  ", "#AI"],
        privacy_status="private",
        made_for_kids=False,
    )

    assert body["snippet"]["tags"] == ["AI", "VideoAnalysis"]


def test_empty_hashtags_produce_no_malformed_tags_or_trailing_blank_line():
    body = build_upload_body(
        title="My Video",
        description="Just a description.",
        hashtags=[],
        privacy_status="unlisted",
        made_for_kids=True,
    )

    assert body["snippet"]["tags"] == []
    assert body["snippet"]["description"] == "Just a description."


def test_status_fields_map_privacy_and_made_for_kids():
    body = build_upload_body(
        title="My Video",
        description="Desc",
        hashtags=[],
        privacy_status="public",
        made_for_kids=True,
    )

    assert body["status"] == {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": True,
    }


def test_title_and_description_are_truncated_to_youtube_limits():
    body = build_upload_body(
        title="x" * 200,
        description="y" * 6000,
        hashtags=[],
        privacy_status="private",
        made_for_kids=False,
    )

    assert len(body["snippet"]["title"]) == 100
    assert len(body["snippet"]["description"]) == 5000
