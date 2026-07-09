"""Shared constants for the YouTube OAuth / upload feature.

Limits below follow the current official YouTube Data API v3 documentation
for the `videos` resource (`snippet.title`, `snippet.description`).
"""

MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000

# "People & Blogs" — a sensible default category so the hackathon UI does
# not need to build a full category selector. videos.insert requires a
# categoryId; this one is broadly valid across regions.
DEFAULT_CATEGORY_ID = "22"

# 8MB chunks: bounded memory, well above the resumable-upload protocol's
# 256KB-multiple requirement, without buffering the whole file.
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024

MAX_UPLOAD_RETRIES = 8
RETRIABLE_HTTP_STATUS_CODES = {500, 502, 503, 504}

OAUTH_STATE_TTL_SECONDS = 10 * 60
SESSION_COOKIE_NAME = "cc_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
