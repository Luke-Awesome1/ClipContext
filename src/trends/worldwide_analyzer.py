import json
import os
import re
from pathlib import Path

import isodate
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Import your unified Fireworks client utility and model targets
from src.ai.fireworks.client import get_fireworks_client

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# MiniMax model identifier configured on your Fireworks layer
MINIMAX_MODEL_ID = "accounts/fireworks/models/minimax-m3"


def get_youtube_client():
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "YOUTUBE_API_KEY environment variable is not set"
        )

    return build(
        "youtube",
        "v3",
        developerKey=YOUTUBE_API_KEY,
    )


def generate_keywords_from_summary(context_path: Path) -> str:
    with context_path.open("r", encoding="utf-8") as file:
        context_data = json.load(file)

    summary = context_data.get("multimodal_summary", "")
    core_message = context_data.get("core_message", "")

    combined_context = (
        f"Summary: {summary}\n"
        f"Core Message: {core_message}"
    )

    system_instruction = """
You are a search engine optimization keyword extraction engine.

Read the video's semantic context and extract one broad,
high-volume 2-to-4 word YouTube search query representing
the generic technology, subject, or concept.

Rules:
1. Remove personal names.
2. Remove specific product or tool names.
3. Remove event and hackathon names.
4. Return only the raw search phrase.
5. Do not use quotation marks.
6. Do not add commentary.
""".strip()

    # Access unified Fireworks wrapper engine
    fw_client = get_fireworks_client()

    response = fw_client.chat.completions.create(
        model=MINIMAX_MODEL_ID,
        messages=[
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": f"Extract a broad YouTube search phrase from this context:\n\n{combined_context}",
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        extra_body={"reasoning_effort": "low"},
    )

    # Extract clean text from structured choice array
    raw_content = response.choices[0].message.content.strip()

    # If MiniMax encapsulates its simple response pattern inside a dictionary key, pull it out
    try:
        parsed_json = json.loads(raw_content)
        if isinstance(parsed_json, dict):
            # Extract whatever primary text string it generated inside the mandatory root
            raw_content = next(iter(parsed_json.values()))
    except Exception:
        pass

    search_query = str(raw_content).strip().replace('"', "")

    print(f"Dynamic worldwide SEO query: '{search_query}'")
    return search_query


def fetch_worldwide_trends(search_query: str, target_count: int = 30) -> list:
    youtube = get_youtube_client()

    valid_clips = []
    next_page_token = None

    print(f"Scraping global short-form pool for: '{search_query}'...")

    while len(valid_clips) < target_count:
        search_request = youtube.search().list(
            part="id,snippet",
            q=search_query,
            type="video",
            order="viewCount",
            videoDuration="short",
            maxResults=50,
            pageToken=next_page_token,
        )

        search_response = search_request.execute()

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if "videoId" in item["id"]
        ]

        if not video_ids:
            break

        stats_request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids),
        )

        stats_response = stats_request.execute()

        for video in stats_response.get("items", []):
            raw_duration = video["contentDetails"]["duration"]
            duration_seconds = isodate.parse_duration(raw_duration).total_seconds()

            if not 30 <= duration_seconds <= 120:
                continue

            raw_title = video["snippet"]["title"]
            raw_description = video["snippet"]["description"]

            all_hashtags = list(
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
                    "extracted_hashtags": all_hashtags,
                    "views": int(video["statistics"].get("viewCount", 0)),
                    "likes": int(video["statistics"].get("likeCount", 0)),
                    "comments": int(video["statistics"].get("commentCount", 0)),
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


def compile_syntax_payload(clustered_df: pd.DataFrame, syntax_path: Path) -> None:
    if clustered_df.empty:
        raise RuntimeError(
            "No worldwide trend data available to generate syntax"
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

Analyze the winning viral metadata samples.

Return one JSON object with exactly these keys:
1. syntax_blueprint
2. seo_vocabulary
3. adjectives

syntax_blueprint must describe title, description, and hashtag structural patterns.
seo_vocabulary must contain topic and search vocabulary observed in the samples.
adjectives must contain tone, emotion, and stylistic descriptors observed in the samples.
""".strip()

    fw_client = get_fireworks_client()

    response = fw_client.chat.completions.create(
        model=MINIMAX_MODEL_ID,
        messages=[
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": f"Analyze these viral source patterns and construct the syntax profile:\n\n{raw_data_dump}",
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
        extra_body={"reasoning_effort": "low"},
    )

    raw_content = response.choices[0].message.content.strip()

    # Bulletproof layer to unpack nested string dictionary structures automatically
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

    print(f"Worldwide syntax created -> {syntax_path}")


def run_worldwide_analysis(
    context_path: Path,
    trends_path: Path,
    syntax_path: Path,
    target_count: int = 30,
) -> None:
    search_query = generate_keywords_from_summary(context_path=context_path)

    raw_video_matches = fetch_worldwide_trends(
        search_query=search_query,
        target_count=target_count,
    )

    if not raw_video_matches:
        raise RuntimeError(
            "Worldwide analyzer found no matching YouTube videos"
        )

    processed_matrix = categorize_trends(raw_video_matches)

    trends_path.parent.mkdir(parents=True, exist_ok=True)
    processed_matrix.to_json(
        trends_path,
        orient="records",
        indent=4,
    )

    print(f"Worldwide trends created -> {trends_path}")

    compile_syntax_payload(
        clustered_df=processed_matrix,
        syntax_path=syntax_path,
    )

