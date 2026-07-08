import os
import re
import json
from pathlib import Path

import isodate
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.ai.fireworks.client import get_fireworks_client, MINMAX_ID

load_dotenv()


def get_youtube_client():
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY environment variable is not set"
        )

    return build(
        "youtube",
        "v3",
        developerKey=api_key,
    )


def get_channel_id(handle: str) -> str:
    youtube = get_youtube_client()

    if not handle.startswith("@"):
        handle = "@" + handle

    try:
        request = youtube.channels().list(
            part="id",
            forHandle=handle,
            maxResults=1,
        )

        response = request.execute()
        items = response.get("items", [])

        if items:
            return items[0]["id"]

        search_request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1,
        )

        search_response = search_request.execute()
        search_items = search_response.get("items", [])

        if not search_items:
            raise ValueError(
                f"Creator {handle} could not be found on YouTube"
            )

        return search_items[0]["snippet"]["channelId"]

    except HttpError as error:
        raise RuntimeError(
            "YouTube API request failed while resolving the creator "
            f"channel (status {error.resp.status}). This may be a quota "
            "or configuration issue with YOUTUBE_API_KEY."
        ) from error


def fetch_creator_trends(handle: str, target_count: int = 30) -> list:
    youtube = get_youtube_client()
    channel_id = get_channel_id(handle)

    valid_clips = []
    next_page_token = None

    print(f"Scraping creator short-form pool for: {handle}...")

    while len(valid_clips) < target_count:
        try:
            search_request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                type="video",
                order="viewCount",
                maxResults=50,
                pageToken=next_page_token,
            )

            search_response = search_request.execute()
        except HttpError as error:
            raise RuntimeError(
                "YouTube API request failed while fetching creator videos "
                f"(status {error.resp.status}). This may be a quota or "
                "configuration issue with YOUTUBE_API_KEY."
            ) from error

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if "videoId" in item["id"]
        ]

        if not video_ids:
            break

        try:
            stats_request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids),
            )

            stats_response = stats_request.execute()
        except HttpError as error:
            raise RuntimeError(
                "YouTube API request failed while fetching video "
                f"statistics (status {error.resp.status})."
            ) from error

        for video in stats_response.get("items", []):
            content_details = video.get("contentDetails", {})
            raw_duration = content_details.get("duration")

            if not raw_duration:
                continue

            duration_seconds = isodate.parse_duration(raw_duration).total_seconds()

            if not 30 <= duration_seconds <= 120:
                continue

            snippet = video.get("snippet", {})
            statistics = video.get("statistics", {})

            raw_title = snippet.get("title", "")
            raw_description = snippet.get("description", "")

            hashtags = list(
                set(
                    re.findall(r"#\w+", raw_title)
                    + re.findall(r"#\w+", raw_description)
                )
            )

            clean_title = re.sub(r"#\w+", "", raw_title).strip()
            clean_description = re.sub(r"#\w+", "", raw_description).strip()

            valid_clips.append(
                {
                    "video_id": video["id"],
                    "raw_title": raw_title,
                    "clean_title": clean_title,
                    "raw_description": raw_description,
                    "clean_description": clean_description,
                    "extracted_hashtags": hashtags,
                    "views": int(statistics.get("viewCount", 0)),
                    "likes": int(statistics.get("likeCount", 0)),
                    "comments": int(statistics.get("commentCount", 0)),
                    "duration": duration_seconds,
                }
            )

            if len(valid_clips) >= target_count:
                break

        next_page_token = search_response.get("nextPageToken")
        if not next_page_token:
            break

    return valid_clips


def categorize_trends(clips_list: list) -> pd.DataFrame:
    dataframe = pd.DataFrame(clips_list)

    if dataframe.empty:
        return dataframe

    dataframe["like_ratio"] = dataframe["likes"] / (dataframe["views"] + 1)
    dataframe["comment_ratio"] = dataframe["comments"] / (dataframe["views"] + 1)

    if len(dataframe) < 3:
        dataframe["cluster_id"] = 0
        return dataframe

    features = dataframe[["views", "like_ratio", "comment_ratio"]]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    kmeans = KMeans(
        n_clusters=min(3, len(dataframe)),
        random_state=42,
        n_init=10,
    )

    dataframe["cluster_id"] = kmeans.fit_predict(scaled_features)
    return dataframe


def compile_creator_syntax(clustered_df: pd.DataFrame, syntax_path: Path) -> None:
    if clustered_df.empty:
        raise RuntimeError(
            "No creator trend data available to generate syntax"
        )

    top_cluster_id = (
        clustered_df.groupby("cluster_id")["views"].mean().idxmax()
    )

    top_subset = clustered_df[
        clustered_df["cluster_id"] == top_cluster_id
    ].head(5)

    raw_data_dump = ""
    for _, row in top_subset.iterrows():
        raw_data_dump += (
            "\n[VIRAL SAMPLE]\n"
            f"TITLE: {row['clean_title']}\n"
            f"DESC: {row['clean_description']}\n"
            f"TAGS: {row['extracted_hashtags']}\n"
        )

    system_instruction = """
You are a linguistic pattern extractor.

Analyze the creator's highest-performing metadata samples.

Return one JSON object with exactly these keys:
1. syntax_blueprint
2. seo_vocabulary
3. adjectives

Extract recurring structural patterns from titles, descriptions, and hashtags.
""".strip()

    # Get the unified Fireworks client wrapper
    fw_client = get_fireworks_client()

    # Call MiniMax using OpenAI compatibility structures matching discriminator.py
    response = fw_client.chat.completions.create(
        model=MINMAX_ID,
        messages=[
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": f"Analyze these viral source patterns and construct the syntax profile:\n\n{raw_data_dump}",
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
        extra_body={
            "reasoning_effort": "low"  # Forces lightning-fast output without nested string anomalies
        },
    )

    # Extract content using OpenAI schema choices array
    raw_content = response.choices[0].message.content.strip()

    # Bulletproof unpacking filter layer to prevent frontend crashes
    try:
        parsed_json = json.loads(raw_content)
        if isinstance(parsed_json, dict) and len(parsed_json.keys()) == 1:
            root_key = list(parsed_json.keys())[0]
            if isinstance(parsed_json[root_key], str):
                raw_content = parsed_json[root_key]
    except Exception:
        pass

    syntax_path.parent.mkdir(parents=True, exist_ok=True)

    with syntax_path.open("w", encoding="utf-8") as file:
        file.write(raw_content)


def run_creator_analysis(
    handle: str,
    trends_path: Path,
    syntax_path: Path,
    target_count: int = 30,
) -> None:
    raw_video_matches = fetch_creator_trends(
        handle=handle,
        target_count=target_count,
    )

    if not raw_video_matches:
        raise RuntimeError(
            "Creator analyzer found no matching short-form videos"
        )

    processed_matrix = categorize_trends(raw_video_matches)

    trends_path.parent.mkdir(parents=True, exist_ok=True)
    processed_matrix.to_json(
        trends_path,
        orient="records",
        indent=4,
    )

    compile_creator_syntax(
        clustered_df=processed_matrix,
        syntax_path=syntax_path,
    )

    print(f"Creator trends created -> {trends_path}")
    print(f"Creator syntax created -> {syntax_path}")