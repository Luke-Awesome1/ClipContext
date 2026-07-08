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

# =====================================================================
# ⚙️ CONFIGURATION & CLIENT INITIALIZATION
# =====================================================================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyCcCZZlkkolUiIokUJ0k_bVhwpCRESMYOA")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA2NddDnD5ZBsOGxtkV0OopbSNfbeDLoYg")

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# =====================================================================
# 🔍 STEP 1: DYNAMIC KEYWORD GENERATOR FROM THE NEW SUMMARY STRUCTURE
# =====================================================================
def generate_keywords_from_summary(json_path: str = "video_context.json") -> str:
    """Reads the new context JSON format and utilizes Gemini to extract clean search phrases."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            context_data = json.load(f)

        summary = context_data.get("multimodal_summary", "")
        core_msg = context_data.get("core_message", "")
        combined_context = f"Summary: {summary}\nCore Message: {core_msg}"

        system_instruction = """
        You are a search engine optimization (SEO) keyword extraction engine. 
        Your task is to read a video's summary and extract a single, high-volume, 
        broad 2-to-4 word search query that can be used on YouTube to find top trending, 
        highly viewed videos on the exact same generic technology or concept.

        CRITICAL RULES:
        1. Stripped Constraints: Completely remove personal names (e.g., Ayushman, Jinxie), specific tool names (e.g., ClipContext), or event names (e.g., AMD hackathon).
        2. Clean Output: Return ONLY the raw search string. No quotation marks, no bullet points, no introductory text.
        """

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Analyze this raw context data to extract a broad YouTube search phrase:\n\n{combined_context}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )

        search_query = response.text.strip().replace('"', '')
        print(f"📡 Dynamic SEO Query Extracted from Summary: '{search_query}'")
        return search_query

    except FileNotFoundError:
        print(f"⚠️ Context file not found at {json_path}. Falling back to default query.")
        return "AI video analysis"


# =====================================================================
# 🌍 STEP 2: WORLDWIDE DATA ACQUISITION PIPELINE (SHORTS ONLY)
# =====================================================================
def fetch_worldwide_trends(search_query: str, target_count: int = 30) -> list:
    """Queries the global YouTube charts using keywords and enforces short-form video constraints."""
    valid_clips = []
    next_page_token = None

    print(f"🚀 Scraping global short-form pool for query: '{search_query}'...")

    while len(valid_clips) < target_count:
        search_request = youtube.search().list(
            part="id,snippet",
            q=search_query,
            type="video",
            order="viewCount",
            videoDuration="short",
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

                hashtags_in_title = re.findall(r"#\w+", raw_title)
                hashtags_in_desc = re.findall(r"#\w+", raw_description)
                all_hashtags = list(set(hashtags_in_title + hashtags_in_desc))

                clean_title = re.sub(r"#\w+", "", raw_title).strip()
                clean_desc = re.sub(r"#\w+", "", raw_description).strip()

                if len(valid_clips) < target_count:
                    valid_clips.append({
                        "video_id": video['id'],
                        "raw_title": raw_title,
                        "clean_title": clean_title,
                        "raw_description": raw_description,
                        "clean_description": clean_desc,
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
# 📊 STEP 3: K-MEANS INTERACTION MATRIX CLUSTERING
# =====================================================================
def categorize_trends(clips_list: list) -> pd.DataFrame:
    """Normalizes engagement ratios and groups global matches into 3 mathematical performance tiers."""
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
# 🧬 STEP 4: EXTRACTION ENGINE FOR SYNTAX, SEO & TITLE ADJECTIVES PAYLOAD
# =====================================================================
def compile_syntax_payload(clustered_df: pd.DataFrame, file_prefix: str):
    """Isolates the alpha performance group to reverse-engineer syntax layouts, tags, and title hooks."""
    if clustered_df.empty:
        print("❌ Insufficient data to compile strategy profile payload.")
        return

    top_cluster_id = clustered_df.groupby('cluster_id')['views'].mean().idxmax()
    top_subset = clustered_df[clustered_df['cluster_id'] == top_cluster_id].head(5)

    raw_data_dump = ""
    for idx, row in top_subset.iterrows():
        raw_data_dump += f"\n[VIRAL SAMPLE]\nTITLE: {row['clean_title']}\nDESC: {row['clean_description']}\nTAGS: {row['extracted_hashtags']}\n"

    system_instruction = """
    You are a linguistic pattern extractor. Analyze the winning viral metadata text blocks and return a raw JSON payload with exactly three keys:
    1. "syntax_blueprint": Explicitly details sequencing layouts across titles, descriptions, and hashtags (e.g., sequencing order rules, line-break formatting choices, capitalization rules).
    2. "seo_vocabulary": Array list of high-impact tags, core topic descriptions, metadata phrases, and system keywords optimized for search visibility.
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

    syntax_filename = f"syntax/w_syntax.json"
    with open(syntax_filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"🧬 Strategy Syntax File Created (3 Keys Split) -> {syntax_filename}")


# =====================================================================
# 🚀 ROUTING ENGINE RUNTIME
# =====================================================================
if __name__ == "__main__":
    context_json_input = "video_context.json"

    search_query_term = generate_keywords_from_summary(context_json_input)
    raw_video_matches = fetch_worldwide_trends(search_query=search_query_term, target_count=30)

    if raw_video_matches:
        processed_matrix = categorize_trends(raw_video_matches)
        safe_slug = search_query_term.replace(' ', '_').lower()

        trends_filename = f"trends/w_trends.json"
        processed_matrix.to_json(trends_filename, orient="records", indent=4)
        print(f"📊 Historical Trends Telemetry File Created -> {trends_filename}")

        compile_syntax_payload(processed_matrix, safe_slug)

        print("\n✅ Worldwide Processing Pipeline Completed with separate Adjectives payload allocation.")