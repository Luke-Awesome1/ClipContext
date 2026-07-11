# Prompt Engineering Audit — ClipContext

Full audit and rewrite of every AI prompt in the repo. Scope was
intentionally narrow: **prompt text and prompt-input data only** — no
pipeline stages, APIs, schemas, frontend, backend routing, deployment, or
model providers changed. All 112 existing tests pass unmodified after
these edits (`.venv/bin/python -m pytest tests/ -q`).

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

Every prompt in the repo lives in one of these nine places — none were
missed (verified by grepping for `system_prompt`, `f"""` prompt blocks,
and `role.*system` patterns across `src/`).

---

## The highest-leverage fix: content generation was seeing 4 fields, not 15

Before touching any prompt wording, the audit found the real bottleneck:
`src/pipeline/runner.py` was calling `generate_content()` with
`paths["caption_context"]` — a file `_save_caption_context()` builds by
keeping only 4 fields off the full `VideoContext`:

```python
caption_context = {
    "topic": context.topic,
    "content_type": context.content_type,
    "multimodal_summary": context.multimodal_summary,
    "core_message": context.core_message,
}
```

`transcript_summary`, `visual_summary`, `key_moments`, `key_entities`,
`visible_text`, `emotional_arc`, `visual_style`, `technical_level`,
`target_audience_signals`, `captionable_details`, and `uncertainties` were
all computed by the context-fusion stage and then discarded before
content generation ever saw them — the discriminator stage, by contrast,
already reads `paths["video_context"]` (the full object). No amount of
prompt rewriting can produce a specific, hook-worthy title if the model
was only ever told the topic and a one-line summary.

**Fix** (`src/pipeline/runner.py`): `generate_content()` now reads
`paths["video_context"]` (the full `VideoContext`) instead of
`paths["caption_context"]`. `caption_context.json` is untouched and still
written/used exactly as before by the worldwide-trends keyword step — this
only changes which already-computed file content generation reads. One
line, no schema change, no new pipeline stage.

This is why the `context_builder.py`, `multimodal.py`, and `gemma.py`
prompt improvements below matter now in a way they didn't before: their
output was previously dead weight for content generation and is now the
primary raw material for it.

---

## 1–2. Content generation (system + user prompt)

**Old system prompt problems:**
- No mechanism forcing the 10 titles/descriptions/hashtag-sets apart —
  relied entirely on vague instructions ("Ensure every single title
  explores a completely unique linguistic frame"), which in practice
  produces synonym-swapped convergence.
- Output schema example used the key `"hashtag_sets"` while the actual
  Pydantic schema (`GeneratedContent`) requires `"hashtags"` — a real
  correctness bug. Under strict JSON-schema mode this is silently
  overridden by the schema, but it actively misleads the model's own
  self-consistency and would break outright under the `json_object`
  fallback path some providers use.
- User prompt (`build_generation_prompt`) never told the model to
  actually use the richer context fields, even before the starvation bug
  above — it just dumped the JSON and said "generate exactly 10 of each."

**New system prompt:**
- Assigns a **fixed strategy per candidate id** — 10 named lanes for
  titles (question, bold statement, curiosity gap, comparison, list,
  story, technical, emotional, search-optimized, creator-voice), 10 fixed
  description formats (short hook, long-form editorial, structured,
  conversational+CTA, SEO-forward, technical, cliffhanger, authentic,
  benefit-driven, minimalist), and 10 hashtag strategies (broad, niche,
  platform-native, entity-driven, audience-driven, balanced, trend-
  aligned, tone, content-type, minimal). This is the single biggest
  diversity lever: instead of asking the model to *feel* diverse, it is
  structurally forced into 10 different lanes, with an explicit escape
  hatch ("reinterpret the lane's spirit... never invent a fact to force
  it") so it doesn't fabricate details when a lane doesn't fit.
- Fixed the `hashtag_sets` → `hashtags` mismatch.
- Added an explicit, silent pre-return checklist (diversity check,
  length-variance check between the minimalist and long-form description,
  JSON validity) with an explicit instruction never to expose it — this
  is a self-critique pass without chain-of-thought leakage.
- Added negative instructions specific to the failure modes actually
  observed conceptually in template-y AI output: no shared opening
  words/clauses across titles, no throat-clearing openers in
  descriptions, no tag repeated across more than half the hashtag sets.

**New user prompt:** explicitly tells the model to use `key_moments`,
`visible_text`, `key_entities`, and `target_audience_signals` "not just
topic and core_message" — reinforcing the system prompt now that those
fields actually arrive.

**Expected improvement:** meaningfully different title/description/
hashtag *structures* per candidate (not just reworded), fewer JSON
validation retries from the field-name fix, and grounding in specific
video details instead of generic topic-level statements.

---

## 1b. Follow-up fix: description candidates were essay-length

**Problem:** two of the 10 fixed description lanes (id 2 "Narrative
Journey" and id 3 "Structured Value Breakdown") explicitly instructed
"immersive, multi-paragraph editorial" and "three distinct paragraphs"
output. Real short-form (Shorts/TikTok/Reels-style) video descriptions run
1-3 sentences — the model was following those two lanes' instructions
correctly, but the instructions themselves didn't match how real
descriptions on this content type actually look, and had nothing to do
with the length/structure signal already sitting in
`PLATFORM_SYNTAX.syntax_blueprint` (extracted from real high-performing
videos, see [§7–9](#7-9-trend--syntax-extraction-prompts) below) — the
prompt never told the model to treat that signal as a length ceiling.

**Fix** (`src/prompts/content_generation.py`): rewrote all 10 description
lanes with an explicit word-count ceiling (~40 words for 9 of the 10
lanes, ~60 words for the one lane — id 6 — allowed to run denser), an
explicit instruction that `PLATFORM_SYNTAX`'s observed description
length/structure is the target to hit rather than a floor to exceed, and
replaced the two paragraph-format lanes with short, single/double-sentence
equivalents that keep the same *strategic* intent (narrative beat,
structured breakdown) without the essay length. Updated the pre-return
self-check accordingly. No schema or pipeline change — prompt text only;
all 112 tests still pass.

---

## 3. Discriminator (ranking) prompt

**Old prompt problems:**
- Output schema used `ranked_titles` / `ranked_descriptions` /
  `ranked_hashtag_sets` while `DiscriminatorResult` requires `titles` /
  `descriptions` / `hashtags` — same class of bug as content generation,
  and on the same file that already forces one repair-retry attempt on
  schema mismatch (`MAX_REPAIR_ATTEMPTS = 1` in
  `src/ai/providers/orchestrator.py`), i.e. this was silently burning a
  retry (or failing outright under `json_object` fallback) on every run.
- Evaluation criteria leaned heavily on "excitement" and "hook" language
  without explicitly requiring accuracy, originality, or search-intent
  alignment as scored dimensions — the mission brief for this audit
  explicitly calls out "avoid ranking purely based on excitement."
- No instruction about score *spread* — nothing stopped the model from
  clustering every candidate at 92–98, which makes rank meaningless as a
  downstream selection signal.

**New prompt:**
- Fixed the field-name mismatch.
- Explicit criteria list applied to every pool: accuracy (against
  `ground_truth_video_context`, with overclaiming penalized even if it
  would "perform well"), CTR/hook strength, SEO/search intent (cross-
  referenced against `historical_performance_benchmarks`), clarity,
  platform fit, originality, audience relevance — plus pool-specific
  criteria (title structural diversity, description above-the-fold
  strength, hashtag broad/niche balance).
- Explicit scoring-discipline section demanding real spread across the
  0–100 range and specific, non-generic `reason` text ("cite the actual
  candidate," not "great hook").

**Expected improvement:** fewer wasted repair-retries from the schema
mismatch, rankings that reward accuracy and originality instead of just
surface excitement, and scores that are actually useful as a selection
signal instead of a tight cluster near 95.

---

## 4. Context fusion (`context_builder.py`)

This builds the canonical `VideoContext` — now the direct input to
content generation (see the connectivity fix above), so its quality
matters far more than it did before this audit.

**Changes:** no JSON schema changes. Added a "downstream use" framing
telling the model explicitly that a copywriter will only ever see this
object, never the transcript or video itself — so vague summaries here
are a permanent information loss, not an efficiency. Added field-specific
guidance: `captionable_details` should aim for 3–5 concrete/vivid/numeric
entries rather than one polished sentence; `target_audience_signals`
should name a specific audience instead of "general viewers"; `emotional_
arc` should describe a progression (e.g. "curiosity → tension → relief")
rather than a single static mood word, with an explicit escape hatch to
say the tone is flat if that's genuinely what the evidence shows.

**Expected improvement:** richer raw material specifically in the fields
the new content-generation prompt was written to lean on (`key_moments`,
`captionable_details`, `target_audience_signals`, `emotional_arc`).

---

## 5–6. Vision prompts (`fireworks/multimodal.py`, `vision/gemma.py`)

**Changes:** both per-window visual-analysis prompts (Fireworks Kimi
primary path, Gemini fallback path) gained the same instruction: prefer a
specific, concrete visual detail over a generic label whenever the frames
support one, and explicitly name anything visually notable (a sharp
reaction, a reveal, high-impact on-screen text, a striking composition).
All existing anti-hallucination rules (no inferred speech/intent, no
inventing events between frames, no identifying people without visible
evidence) are unchanged — this only raises the specificity bar within
those constraints.

**Expected improvement:** visual timeline entries that feed
`context_builder.py` with more usable, specific evidence instead of
generic descriptions like "a person talking," which is where the
"generic, templated" complaint about final outputs often actually
originates upstream.

---

## 7–9. Trend / syntax extraction prompts

**Changes** (`trend_analyzer.py` creator syntax, `worldwide_analyzer.py`
global syntax, `worldwide_analyzer.py` search-query extraction):
- Both syntax-extraction prompts now explicitly require
  `syntax_blueprint` to separately describe title/description/hashtag
  structural patterns (previously just "extract recurring structural
  patterns" with no breakdown), and explicitly instruct not inventing a
  pattern present in only one sample.
- `adjectives` now explicitly excludes generic praise words ("engaging,"
  "great") in favor of words describing *how* the samples actually sound.
- The search-query prompt (which determines what "viral" comparison set
  `historical_performance_benchmarks` and the worldwide syntax profile
  are built from) now explicitly targets the broad/narrow sweet spot
  instead of only "broad, high-volume" — a query that's too broad pulls
  in irrelevant benchmark videos, which pollutes both the discriminator's
  benchmarks and the content-generation `PLATFORM_SYNTAX` input.

**Expected improvement:** a `PLATFORM_SYNTAX` object (`syntax_blueprint`,
`seo_vocabulary`, `adjectives`) that is actually differentiated per
format and grounded in real recurring patterns, rather than a generic
tone summary — which is the style reference the new content-generation
prompt explicitly leans on per-lane (e.g. lane 10 titles and lane 8
descriptions are defined as "matching the tone in adjectives").

---

## Validation performed

- **Static:** every edited module re-imports and its prompt-builder
  functions render without error (`build_generation_prompt`,
  `load_system_instruction`, etc.), confirmed via `.venv/bin/python -c`.
- **Schema-name regression check:** grepped both rewritten prompts to
  confirm the old mismatched keys (`hashtag_sets`, `ranked_titles`,
  `ranked_descriptions`, `ranked_hashtag_sets`) are gone and the
  Pydantic-exact keys (`titles`, `descriptions`, `hashtags`) are present.
- **Full test suite:** `.venv/bin/python -m pytest tests/ -q` → 112
  passed, 0 failed, no changes needed to any test.

**Not performed:** a live end-to-end pipeline run against a real video.
Doing that consumes real Fireworks/AMD API usage and requires a sample
video and (for the AMD path) the notebook/tunnel to be up. If you want a
real before/after comparison on an actual video ahead of the demo, say so
and I'll run one job through the pipeline and diff the generated
titles/descriptions/hashtags and discriminator scores against a prior
run's output.
