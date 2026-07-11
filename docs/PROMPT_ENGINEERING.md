# Prompt Design

Every prompt ClipContext sends to a model, where it lives, and the
reasoning behind its current wording. Useful reading before changing any
of them — a lot of the phrasing here exists to avoid a specific,
previously-observed failure mode, not because it reads nicely.

## Where every prompt lives

| # | File | Used for | Consumed by |
|---|------|----------|-------------|
| 1 | `src/prompts/content_generation.py` | System prompt for title/description/hashtag generation | `src/ai/content_generator.py` → Fireworks / AMD vLLM |
| 2 | `src/ai/content_generator.py` (`build_generation_prompt`) | User prompt wrapping VIDEO_CONTEXT + PLATFORM_SYNTAX | same |
| 3 | `src/models/discriminator/d_prompt.txt` | System prompt for ranking generated candidates | `src/models/discriminator/discriminator.py` |
| 4 | `src/ai/context_builder.py` (`build_video_context`) | Fuses transcript + visual timeline into the canonical `VideoContext` | Fireworks Kimi (multimodal) |
| 5 | `src/ai/fireworks/multimodal.py` (`build_visual_content`) | Per-window visual-fact extraction (primary vision path) | Fireworks Kimi |
| 6 | `src/ai/vision/gemma.py` (`build_visual_prompt`) | Per-window visual-fact extraction (Gemini fallback vision path) | Gemini |
| 7 | `src/trends/trend_analyzer.py` (`compile_creator_syntax`) | Extracts creator-specific style profile from their top clips | MiniMax (Fireworks) |
| 8 | `src/trends/worldwide_analyzer.py` (`compile_syntax_payload`) | Extracts global style profile from top clips in the video's niche | MiniMax (Fireworks) |
| 9 | `src/trends/worldwide_analyzer.py` (`generate_keywords_from_summary`) | Derives the YouTube search query used to gather #8's samples | MiniMax (Fireworks) |

---

## Why content generation reads the full `VideoContext`

`src/pipeline/runner.py` calls `generate_content()` with
`paths["video_context"]` — the full canonical `VideoContext` object,
including `transcript_summary`, `visual_summary`, `key_moments`,
`key_entities`, `visible_text`, `emotional_arc`, `visual_style`,
`technical_level`, `target_audience_signals`, `captionable_details`, and
`uncertainties`. This matters because a copywriter (human or model) can't
produce a specific, hook-worthy title from just a topic string and a
one-line summary — it needs the concrete details those fields carry. The
discriminator stage reads the same full object for the same reason: it's
scoring candidates against ground truth, and a thin context makes that
scoring meaningless.

This is also why the context-fusion prompt (`context_builder.py`, below)
and the two vision prompts matter: their output is the only raw material
content generation and ranking ever see. A vague `visual_summary` or a
generic `key_moments` entry is a permanent loss of specificity two stages
downstream, not a shortcut.

---

## 1–2. Content generation (system + user prompt)

**Diversity via fixed lanes, not vibes.** Each of the 10 titles, 10
descriptions, and 10 hashtag sets is assigned a fixed strategic lane by
id — titles get named angles (question, bold statement, curiosity gap,
comparison, list, story, technical, emotional, search-optimized,
creator-voice); hashtags get named strategies (broad, niche,
platform-native, entity-driven, audience-driven, balanced, trend-aligned,
tone, content-type, minimal). Asking a model to just "be creative and
diverse" ten times in a row reliably produces synonym-swapped
near-duplicates; assigning each id a structurally different job doesn't.
Each lane includes an explicit escape hatch — reinterpret the lane's
*spirit* rather than fabricating a fact to force it (e.g. no invented
statistic to satisfy a "list/number-led" title if the video has no
numbers) — so structural diversity never comes at the cost of grounding.

**Descriptions are short, on purpose.** Real short-form (Shorts/TikTok/
Reels-style) video descriptions run 1-3 sentences — viewers don't tap
"Show more" to read an essay. All 10 description lanes carry an explicit
word-count ceiling (~40 words for 9 of the 10 lanes, ~60 for the one lane
allowed to run denser), and are instructed to treat
`PLATFORM_SYNTAX.syntax_blueprint`'s observed description length/structure
— extracted from real high-performing videos, see §7–9 below — as the
target to hit, not a floor to exceed. The lane descriptions themselves
(immediate value-drop, narrative beat, structured breakdown, interactive
hook, SEO opener, deep intel, open-loop suspense, casual BTS, viewer
takeaway, brief execution) are each a different structural bet, but none
of them are allowed to become a paragraph-long editorial.

**Field names are schema-exact.** The output schema example uses
`titles` / `descriptions` / `hashtags`, matching `GeneratedContent`
exactly — a mismatched key here would silently get overridden under
strict JSON-schema mode but actively mislead the model's own
self-consistency, and would break outright under a `json_object` fallback
path.

**Self-check before returning.** The prompt ends with an explicit,
silent pre-return checklist (structural diversity across all 10 in each
pool, grounding in `VIDEO_CONTEXT`, description length discipline, JSON
validity) with an explicit instruction never to expose the checklist or
any reasoning in the final output — a self-critique pass without
chain-of-thought leakage into user-facing content.

**The user prompt** (`build_generation_prompt`) explicitly tells the
model to use `key_moments`, `visible_text`, `key_entities`, and
`target_audience_signals` — "not just topic and core_message" — since
those fields are exactly the ones a thin prompt tends to ignore in favor
of the two most generic fields available.

---

## 3. Discriminator (ranking) prompt

**Explicit, weighted criteria, not just "which one's better."** Every
candidate pool is scored against: accuracy (against
`ground_truth_video_context`, with overclaiming penalized even if it
would "perform well"), CTR/hook strength, SEO/search intent (cross-
referenced against `historical_performance_benchmarks`), clarity,
platform fit, originality, and audience relevance — plus pool-specific
criteria (title structural diversity, description above-the-fold
strength, hashtag broad/niche balance). Evaluation criteria that lean only
on "excitement" or "hook" language, with nothing about accuracy or
originality, produce rankings that reward whichever candidate oversells
hardest.

**Scoring discipline.** The prompt explicitly demands real spread across
the 0–100 range and specific, non-generic `reason` text ("cite the actual
candidate," not "great hook") — without this, models reliably cluster
every candidate in a tight 92–98 band, which makes the rank useless as a
downstream selection signal since nothing is actually being discriminated
between.

**Field names are schema-exact**, matching `DiscriminatorResult`
(`titles` / `descriptions` / `hashtags`) — same rationale as content
generation above, and on a file that already allows one repair-retry
attempt on schema mismatch (`MAX_REPAIR_ATTEMPTS = 1` in
`src/ai/providers/orchestrator.py`), so a wrong key here silently burns a
retry on every single run.

---

## 4. Context fusion (`context_builder.py`)

Builds the canonical `VideoContext` — the direct input to both content
generation and ranking (see above), so its specificity sets a hard ceiling
on everything downstream. The prompt frames this explicitly: a copywriter
will only ever see this object, never the transcript or the video itself,
so a vague summary here is a permanent information loss, not an
efficiency.

Field-specific guidance: `captionable_details` should aim for 3–5
concrete/vivid/numeric entries rather than one polished sentence;
`target_audience_signals` should name a specific audience instead of
"general viewers"; `emotional_arc` should describe a progression (e.g.
"curiosity → tension → relief") rather than a single static mood word,
with an explicit escape hatch to say the tone is flat if that's genuinely
what the evidence shows.

---

## 5–6. Vision prompts (`fireworks/multimodal.py`, `vision/gemma.py`)

Both per-window visual-analysis prompts (Fireworks Kimi primary path,
Gemini fallback path) carry the same instruction: prefer a specific,
concrete visual detail over a generic label whenever the frames support
one, and explicitly name anything visually notable (a sharp reaction, a
reveal, high-impact on-screen text, a striking composition). All
anti-hallucination rules apply equally (no inferred speech/intent, no
inventing events between frames, no identifying people without visible
evidence) — the specificity instruction only raises the bar within those
constraints. Generic visual-timeline entries like "a person talking" are
the most common upstream cause of generic-feeling final titles/
descriptions, since nothing downstream can invent specificity that wasn't
captured here.

---

## 7–9. Trend / syntax extraction prompts

`trend_analyzer.py`'s creator-syntax extraction and
`worldwide_analyzer.py`'s global-syntax extraction both require
`syntax_blueprint` to separately describe title/description/hashtag
structural patterns (typical length, opening pattern, CTA habits, tag
count and broad/niche mix) rather than one undifferentiated "recurring
patterns" blob, and both explicitly forbid asserting a pattern present in
only one sample. `adjectives` is scoped to words describing *how* the
samples actually sound (e.g. "urgent," "deadpan," "earnest") rather than
generic praise ("engaging," "great"), since generic praise gives
content generation nothing to actually act on when it's told to "match the
tone in adjectives."

The search-query prompt (`generate_keywords_from_summary`) — which
determines the comparison set that becomes both
`historical_performance_benchmarks` and the worldwide `PLATFORM_SYNTAX`
input — targets a broad/narrow sweet spot rather than only "broad,
high-volume": a query that's too broad pulls in irrelevant benchmark
videos, which pollutes both the discriminator's benchmarks and the style
profile content generation leans on.

---

## Changing a prompt

If you change a prompt in a way that's a deliberate improvement (not a
typo fix), update this doc's relevant section to explain what changed and
why — it's meant to stay current as the project's reference for prompt
design decisions, not a one-time writeup. Run `make test` after any prompt
change (`.venv/bin/python -m pytest tests/ -q`); prompts aren't otherwise
covered by static analysis, so the test suite is what catches an
accidental schema-shape regression.
