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
from dotenv import load_dotenv

# =====================================================================
# ⚙️ CONFIGURATION & CLIENT INITIALIZATION
# =====================================================================

load_dotenv()
# =====================================================================
# ⚙️ CONFIGURATION & CLIENT INITIALIZATION
# =====================================================================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def get_channel_id(handle: str) -> str:
    if not handle.startswith('@'):
        handle = '@' + handle
    request = youtube.search().list(part="snippet", q=handle, type="channel", maxResults=1)
    response = request.execute()
    items = response.get('items', [])
    if not items:
        raise ValueError(f"Profile {handle} could not be found.")
    return items[0]['snippet']['channelId']


# =====================================================================
# 🌍 STEP 1: SPECIFIC CREATOR DATA ACQUISITION PIPELINE
# =====================================================================
def fetch_creator_trends_and_export(handle: str, target_count: int = 30) -> list:
    """Loops through multiple search pages to capture target creator short-form data rows."""
    try:
        channel_id = get_channel_id(handle)
    except Exception as e:
        print(f"⚠️ Channel Tracking Fault: {e}")
        return []

    valid_clips = []
    next_page_token = None

    print(f"🚀 Scraping short-form pool for creator: {handle}...")

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

            # Enforce strict short-form temporal bounds
            if 30 <= duration_seconds <= 120:
                raw_title = video['snippet']['title']
                raw_description = video['snippet']['description']

                # Scan BOTH Title and Description for Hashtags
                hashtags_in_title = re.findall(r"#\w+", raw_title)
                hashtags_in_desc = re.findall(r"#\w+", raw_description)
                all_hashtags = list(set(hashtags_in_title + hashtags_in_desc))

                # Clean text fields by stripping out embedded hashtags
                clean_title_text = re.sub(r"#\w+", "", raw_title).strip()
                clean_description_text = re.sub(r"#\w+", "", raw_description).strip()

                if len(valid_clips) < target_count:
                    valid_clips.append({
                        "video_id": video['id'],
                        "raw_title": raw_title,
                        "clean_title": clean_title_text,
                        "raw_description": raw_description,
                        "clean_description": clean_description_text,
                        "extracted_hashtags": all_hashtags,
                        "views": int(video['statistics'].get('viewCount', 0)),
                        "likes": int(video['statistics'].get('likeCount', 0)),
                        "comments": int(video['statistics'].get('commentCount', 0)),
                        "duration": duration_seconds
                    })

        next_page_token = search_response.get('nextPageToken')
        if not next_page_token:
            break

    return valid_clips


# =====================================================================
# 📊 STEP 2: K-MEANS INTERACTION MATRIX CLUSTERING
# =====================================================================
def categorize_trends(clips_list: list) -> pd.DataFrame:
    """Normalizes engagement ratios and segments matches into 3 mathematical performance tiers."""
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
# 🧬 STEP 3: EXTRACTION ENGINE FOR SYNTAX & SEO ADJECTIVES PAYLOAD
# =====================================================================
def compile_syntax_payload(clustered_df: pd.DataFrame, file_prefix: str):
    """Isolates the alpha performance group to reverse-engineer syntax layouts and vocabulary hooks."""
    if clustered_df.empty:
        print("❌ Insufficient data to compile strategy profile payload.")
        return

    top_cluster_id = clustered_df.groupby('cluster_id')['views'].mean().idxmax()
    top_performing_subset = clustered_df[clustered_df['cluster_id'] == top_cluster_id].head(5)

    raw_data_dump = ""
    for idx, row in top_performing_subset.iterrows():
        raw_data_dump += f"\n[VIRAL SAMPLE]\nTITLE: {row['clean_title']}\nDESC: {row['clean_description']}\nTAGS: {row['extracted_hashtags']}\n"

    system_instruction = """
    You are a linguistic pattern extractor. Analyze the winning viral metadata text blocks and return a raw JSON payload with exactly two keys:
    1. "syntax_blueprint": Explicitly details sequencing layouts across titles, descriptions, and hashtags (e.g., sequencing order rules, line-break formatting choices, capitalization rules).
    2. "seo_vocabulary": Array list of energetic, click-driving adjectives, sensory verbs, and descriptive terms consistently found across these titles and content.
    3. "adjectives": Read the titles and description to tell words that describe the tone and emotion of the video and captures the vibe to create a related title and description.

    Ensure your output is a single clean JSON object block. Do not add any conversational prose, markdown symbols like ```json, or opening/closing commentary.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=raw_data_dump,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    # Saved inside the same active workspace path directory
    syntax_filename = f"syntax/yt_syntax.json"
    with open(syntax_filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"🧬 Strategy Syntax File Created -> {syntax_filename}")


# =====================================================================
# 🚀 ROUTING ENGINE RUNTIME
# =====================================================================
if __name__ == "__main__":
    test_creator_target = "Thinknomyofficial"
    safe_slug = test_creator_target.replace('@', '').strip().lower()

    # Scrape the specific target creator
    raw_video_matches = fetch_creator_trends_and_export(test_creator_target, target_count=30)

    if raw_video_matches:
        # Run K-Means Clustering on engagement data
        processed_matrix = categorize_trends(raw_video_matches)

        # Saves trending historical timeline records directly to local workspace root
        trends_filename = f"trends/yt_trends.json"
        processed_matrix.to_json(trends_filename, orient="records", indent=4)
        print(f"📊 Historical Trends Telemetry File Created -> {trends_filename}")

        # Process and build layout architecture styles directly to local workspace root
        compile_syntax_payload(processed_matrix, safe_slug)

        print("\n✅ Creator Pipeline Processing Completed.")