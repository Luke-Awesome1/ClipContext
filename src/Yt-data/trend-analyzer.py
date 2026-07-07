import os
import json
import re
import pandas as pd
import isodate
from googleapiclient.discovery import build
from google import genai
from google.genai import types
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Initialize config
INPUT_COST_PER_M = 0.30
OUTPUT_COST_PER_M = 2.50

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyCcCZZlkkolUiIokUJ0k_bVhwpCRESMYOA")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6KgMYtGDUewqeobDIKl4KfIWa1iDX0Q4InZOmnPQoFAFw"))


def get_channel_id(handle: str) -> str:
    if not handle.startswith('@'):
        handle = '@' + handle
    request = youtube.search().list(part="snippet", q=handle, type="channel", maxResults=1)
    response = request.execute()
    items = response.get('items', [])
    if not items:
        raise ValueError(f"Profile {handle} could not be found.")
    return items[0]['snippet']['channelId']


def fetch_creator_trends_and_export(handle: str, target_count: int = 30) -> list:
    """Loops through multiple search pages to capture short-form data rows and saves instantly."""
    try:
        channel_id = get_channel_id(handle)
    except Exception as e:
        print(f"⚠️ Channel Tracking Fault: {e}")
        return []

    valid_clips = []
    next_page_token = None
    clean_filename = f"raw_trends_{handle.replace('@', '').strip().lower()}_v2.json"

    while len(valid_clips) < target_count:
        search_request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            order="viewCount",
            maxResults=50,
            pageToken=next_page_token
        )
        search_response = search_request.execute()
        video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if 'videoId' in item['id']]

        if not video_ids:
            break

        stats_request = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
        stats_response = stats_request.execute()

        for video in stats_response.get('items', []):
            raw_duration = video['contentDetails']['duration']
            duration_seconds = isodate.parse_duration(raw_duration).total_seconds()

            if 30 <= duration_seconds <= 120:
                raw_title = video['snippet']['title']
                raw_description = video['snippet']['description']

                # --- FIX: Scan BOTH Title and Description for Hashtags ---
                hashtags_in_title = re.findall(r"#\w+", raw_title)
                hashtags_in_desc = re.findall(r"#\w+", raw_description)

                # Merge into a single unique list (removes duplicates)
                all_hashtags = list(set(hashtags_in_title + hashtags_in_desc))

                # --- FIX: Clean the Title and Description by stripping the hashtags out ---
                clean_title_text = re.sub(r"#\w+", "", raw_title).strip()
                clean_description_text = re.sub(r"#\w+", "", raw_description).strip()

                if len(valid_clips) < target_count:
                    valid_clips.append({
                        "video_id": video['id'],
                        "raw_title": raw_title,
                        "clean_title": clean_title_text,  # Clean title for layout tracking
                        "raw_description": raw_description,
                        "clean_description": clean_description_text,
                        "extracted_hashtags": all_hashtags,  # Guaranteed to capture both areas now!
                        "views": int(video['statistics'].get('viewCount', 0)),
                        "likes": int(video['statistics'].get('likeCount', 0)),
                        "comments": int(video['statistics'].get('commentCount', 0)),
                        "duration": duration_seconds
                    })

        # --- CRITICAL FIX: SOLIDIFY AT EACH PAGE STEP ---
        # This overwrites the file progressively, guaranteeing the disk state matches memory
        with open(clean_filename, 'w', encoding='utf-8') as f:
            json.dump(valid_clips, f, indent=4, ensure_ascii=False)
        print(f"💾 File checkpoint synchronized: Saved {len(valid_clips)} items to {clean_filename}")

        next_page_token = search_response.get('nextPageToken')
        if not next_page_token:
            break

    print(f"✅ Pipeline Completed: Final structured data written to: {clean_filename}")
    return valid_clips

def categorize_trends(clips_list: list) -> pd.DataFrame:
    df = pd.DataFrame(clips_list)
    if df.empty or len(df) < 3:
        return df
    df['like_ratio'] = df['likes'] / (df['views'] + 1)
    df['comment_ratio'] = df['comments'] / (df['views'] + 1)

    X = df[['views', 'like_ratio', 'comment_ratio']]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)
    return df


# =====================================================================
# 🧠 EXTRACT STRUCTURAL LAYOUT SEQUENCING BLUEPRINT
# =====================================================================
def extract_structural_blueprint_prompt(handle: str, clustered_df: pd.DataFrame) -> str:
    """Analyzes high-performing data points to outline exact element preceding rules."""
    if clustered_df.empty:
        return "Insufficient data rows to evaluate structural sequencing layers."

    # Isolate only items inside the statistically highest performing cluster tier
    top_cluster_id = clustered_df.groupby('cluster_id')['views'].mean().idxmax()
    top_performing_subset = clustered_df[clustered_df['cluster_id'] == top_cluster_id].head(5)

    raw_data_dump = ""
    for idx, row in top_performing_subset.iterrows():
        # Inside extract_structural_blueprint_prompt loop:
        raw_data_dump += f"CLEAN TITLE: {row['clean_title']}\n"
        raw_data_dump += f"CLEAN DESCRIPTION TEXT:\n{row['clean_description']}\n"
        raw_data_dump += f"CAPTURED HASHTAGS: {', '.join(row['extracted_hashtags'])}\n"

    system_instruction = """
    You are an expert technical prompt compiler. Your job is to analyze the high-performing short-form video metrics provided and map out a strict sequencing rule template.
    You will format your output as an explicit, copy-pasteable instruction manual that can be directly passed into a downstream text generation LLM.

    Analyze the sequencing layouts and output exactly this structure:

    # 📋 DOWNSTREAM MODEL INFERENCE REGULATION ENGINE

    ## 🏷️ TITLE ARCHITECTURE & PRECEDING SEQUENCING FORMULA
    Detail what component precedes what in the titles. Use exact syntactic matching rules, such as:
    `[CAPITALIZATION RULE] -> [EMOJI POSITIONING] -> [CONTEXT FILTERS IN PARENTHESES OR BRACKETS]`
    State the exact sequencing order rules derived from the winning cluster data.

    ## 📝 DESCRIPTION SEQUENCING PIPELINE
    Outline down-the-page layout layout parameters. Define exactly what lines appear first, middle, and trailing:
    - Block 1: Hook Sentence structure (precedes all other text blocks).
    - Block 2: Informational Body Context / Link placement (precedes hashtags).
    - Block 3: Hashtag Array block positioning.

    ## 🔍 HASHTAG DENSITY & IN-LINE MIXING CONVENTIONS
    State whether hashtags are appended cleanly at the bottom lines or integrated within active sentences. Outline dense tag categorization counts (e.g., General Topic tags vs Niche Game Title tags).
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Target Creator Context Handle: {handle}\nTop Performance Rows Data:\n{raw_data_dump}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1
        )
    )

    usage = response.usage_metadata
    net_cost = ((usage.prompt_token_count / 1_000_000) * INPUT_COST_PER_M) + (
                (usage.candidates_token_count / 1_000_000) * OUTPUT_COST_PER_M)
    print(f"📥 Current Prompt Telemetry Execution Cost: ${net_cost:.6f} USD\n")

    return response.text


if __name__ == "__main__":
    test_creator_target = "SuperSilva_01"

    # This loop now scans pages until it fetches a full pool of 30 accurate short-form pieces
    raw_video_matches = fetch_creator_trends_and_export(test_creator_target, target_count=30)

    if raw_video_matches:
        processed_matrix = categorize_trends(raw_video_matches)

        # Build the structured, sequence-aware template prompt out of your data clusters
        downstream_llm_blueprint = extract_structural_blueprint_prompt(test_creator_target, processed_matrix)
        print(downstream_llm_blueprint)