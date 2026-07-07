# ClipContext — Agent Instructions

## Read before modifying code

Before writing or changing any code:

1. Read `PROJECT_STATE.md`.
2. Read `ARCHITECTURE.md`.
3. Read `TASKS.md`.
4. Inspect the repository tree.
5. Inspect all files relevant to the requested module.
6. Do not redesign working modules unless the current task explicitly requires it.
7. Do not make paid AI inference calls unless explicitly instructed.
8. Do not delete caches or `outputs/fireworks_budget.json`.
9. Do not guess model IDs or API capabilities. Verify provider documentation when necessary.
10. Preserve Pydantic model contracts unless a schema migration is explicitly discussed.

## Project

ClipContext is a web application for content creators.

A creator uploads a short video, approximately 30 seconds to 2 minutes.

ClipContext analyses the video's speech and visual content using a compute-efficient sparse multimodal pipeline.

It generates platform-ready titles, captions, descriptions, and hashtags in four styles:

* Professional
* Dry / Sarcastic
* Tech Humour
* Relatable Humour

The generated content will eventually be adapted using:

* the creator's historical YouTube content
* current content trends

## Core USP

Do not send a complete video wholesale to a multimodal model when most frames are temporally redundant.

ClipContext performs local sparse temporal context extraction before paid multimodal inference.

Current pipeline:

Raw video
→ validation
→ local audio extraction
→ local transcription
→ 1 FPS local frame scan
→ local visual quality scoring
→ local perceptual diversity selection
→ 5-second temporal windows
→ global sparse frame budget
→ multimodal semantic understanding
→ canonical VideoContext
→ creator/trend adaptation
→ multi-style content generation

The current test clip is approximately 37.9 seconds.

Approximately 1,137 source frames exist at 30 FPS.

38 candidate frames are locally scanned at 1 FPS.

The current sparse budget selects a maximum of 12 frames for VLM inference.

The purpose is to reduce redundant multimodal inference while preserving important temporal evidence.

## Current technology

Python 3.13 virtual environment.

Local video processing:

* OpenCV
* FFmpeg/audio extraction code already present

Speech:

* local transcription implementation in `src/ai/transcriber.py`

Schemas:

* Pydantic

Google vision fallback:

* Gemini through Google AI Studio
* previously tested successfully

AMD/Fireworks:

* Fireworks AI credits are available
* Kimi K2.5 is currently being tested
* model ID currently tested:
  `accounts/fireworks/models/kimi-k2p5`

Fireworks OpenAI-compatible endpoint:
`https://api.fireworks.ai/inference/v1`

## Current Fireworks problem

Two sparse multimodal Kimi K2.5 requests have failed with HTTP 500 INTERNAL_SERVER_ERROR.

Failed request IDs:

* `chatcmpl-2304429a1b16473c8298fd29a7f986f6`
* `chatcmpl-420ce40eff204cf48a2b8c121ccccda6`

The first request contained approximately 24 images.

The second architecture reduced the global sparse budget to 12 images and removed `response_format`.

The 12-image request also returned HTTP 500.

Do not retry the full multimodal request blindly.

The next diagnostic is a one-image Kimi K2.5 vision smoke test in `smoke_test_kimi.py`.

Diagnostic sequence:

1 image
→ if successful, test 4 images
→ then 8 images
→ then 12 images

If the one-image request also returns HTTP 500, stop debugging the full video pipeline.

In that case, use Gemini as the visual observation provider and use Fireworks for text-based semantic fusion and generation.

## Current working pipeline

The following components have already worked:

### Video validation

A 37.894966-second H.264 1920×1080 test video is accepted.

### Audio extraction

Audio is extracted to:

`data/audio/test.wav`

### Candidate frame extraction

The video is scanned at 1 FPS.

38 candidate frames are produced.

Frames are resized to a maximum width of 768 pixels.

Each candidate receives a local visual quality score based on:

* brightness
* edge density
* contrast

### Perceptual diversity selection

Frames are selected using:

* quality score
* grayscale thumbnail visual difference

The objective is:

high visual information
+
different visual information

### Temporal alignment

The video is divided into 5-second windows.

Transcript segments are aligned using:

* strict speech
* boundary context speech

Strict speech uses transcript segment midpoint ownership.

Context speech includes overlapping transcript segments.

### Sparse frame budget

The current global VLM frame budget is 12.

Every temporal window receives one representative frame first.

Remaining frame capacity is allocated to higher-priority windows.

### Gemini visual understanding

The previous Gemini implementation successfully produced temporal visual observations.

Observed test-video content included:

* silhouetted person near a city-facing window
* office scenes
* visible distress/body posture
* on-screen text:
  `this is my ultimate dream`
* on-screen text:
  `I believe it's yours too`
* silhouetted backpacked figure in a mountainous valley
* closing abstract logo graphic

### Test transcript

The current test transcript is approximately:

“I don't know what that dream is that you have. I don't care how disappointing it might have been as you've been working toward that dream. That that dream that you're holding in your mind that it's possible.”

## Canonical output

The multimodal understanding layer must return `VideoContext`.

See:

`src/models/video_context.py`

Important fields include:

* topic
* content_type
* core_message
* transcript_summary
* visual_summary
* multimodal_summary
* key_moments
* key_entities
* visible_text
* emotional_arc
* visual_style
* technical_level
* target_audience_signals
* captionable_details
* uncertainties

`captionable_details` must contain specific evidence-grounded hooks for downstream content generation.

`uncertainties` must contain interpretations that are plausible but not established.

## Evidence rules

Speech is evidence of what is said.

Frames are evidence of what is visually shown.

Do not identify people without explicit evidence.

Do not convert visual metaphor into literal fact.

Do not invent causal relationships between scenes.

Do not claim an outcome occurred unless shown or spoken.

Preserve clearly readable important on-screen text.

Prefer specific concrete observations over generic descriptions.

## Cost constraints

The project has approximately $50 in Fireworks hackathon credits.

Credits must last through development and future demos.

Avoid unnecessary inference.

Cache expensive intermediate outputs.

Do not delete caches unless explicitly instructed.

The local development budget guard is stored in:

`outputs/fireworks_budget.json`

The local tracker is an estimate and is not authoritative billing data.

Current target architecture should require very few paid calls per fresh video.

Warm-path target:

1 multimodal/context understanding call
+
1 multi-style generation call

Creator and trend profiles should be cached.

## Team ownership

Ayushman owns:

* `src/video/**`
* `src/ai/transcriber.py`
* `src/ai/temporal_alignment.py`
* multimodal pipeline
* backend/API integration

Frontend collaborator owns:

* `frontend/**`

Creator/trend intelligence collaborator owns:

* `src/ai/creator/**`
* `src/ai/trends/**`

Do not create cross-module imports that tightly couple creator/trend intelligence to video processing.

Expected contracts:

`process_video(video_path) -> VideoContext`

`analyse_creator_voice(past_content) -> CreatorVoiceProfile`

`analyse_trend_patterns(trend_content) -> TrendProfile`

`generate_content(video_context, creator_profile, trend_profile) -> GenerationResult`

## Hackathon

Project is for the lablab.ai AMD Developer Hackathon ACT II.

Track:

Track 3 — Unicorn / Open Innovation.

AMD compute usage must be demonstrated.

Submission requires:

* GitHub repository URL
* demo video
* slide deck

Hosted demo is optional but recommended.

The repository and slide deck are important because automated pre-screening does not inspect the demo video.

The product should explicitly demonstrate its AMD/Fireworks compute path.

Do not make unsupported claims about the exact accelerator used by a request. Verify Fireworks usage/billing metadata if accelerator evidence is required.

## Immediate priority

The immediate task is not frontend development.

The immediate task is:

1. Run the one-image Kimi vision smoke test once.
2. Determine whether Kimi vision works through this Fireworks account/API path.
3. If successful, identify the safe multi-image payload threshold.
4. If unsuccessful, restore Gemini as the visual provider.
5. Use Fireworks Kimi for text semantic fusion.
6. Build a stable `process_video(video_path) -> VideoContext` boundary.
7. Build caption/title/description/hashtag generation.
8. Expose a backend API for the frontend collaborator.

Always report which files you intend to modify before making architectural changes.
