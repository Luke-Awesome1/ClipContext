# Demo Script (3 minutes)

A timed narration for a live/recorded demo. Run through
[DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) beforehand — this script assumes
the AMD notebook, tunnel, and OAuth test users are already confirmed
working; it does not cover pre-flight setup.

Say the words in *italics* roughly as written; everything else is a
stage direction.

---

## 0:00 – 0:20 — The problem

*"Creators spend real time after editing writing titles, descriptions,
and hashtags — usually disconnected from what the video actually shows
and says, and from what's actually working on the platform right now.
ClipContext fixes that."*

Open the landing page. Let it load fully before continuing.

## 0:20 – 0:40 — Upload

Upload a short (30s–2min) test video. Optionally type a YouTube creator
handle.

*"I'll upload a short clip — under two minutes, which is the sweet spot
for Shorts/TikTok/Reels. Everything after this happens automatically."*

## 0:40 – 1:20 — Processing (narrate over the progress stages)

*"Under the hood, everything up through frame scanning and transcription
runs locally — free, no API calls. Only the multimodal understanding step
and the two AI generation stages make paid or GPU inference calls. That's
the core efficiency bet: don't send a whole video to an expensive model
when most of its frames are redundant."*

Let it reach Results. If it's running long, this is a natural place to
cut in a recording.

## 1:20 – 1:50 — Grounded understanding + AMD evidence

Point at the VideoContext / "AI Understanding" card.

*"This is the canonical understanding of the video — topic, core message,
what's actually said and shown. Every generated title, description, and
hashtag has to be consistent with this; nothing gets invented."*

Point at the AMD GPU inference badge, if present for this run.

*"This candidate set was generated on an AMD GPU — ROCm and vLLM, running
[model name from the badge/status endpoint]. If that badge isn't showing,
this stage fell back to Fireworks automatically for this run — that
fallback and the honest audit trail behind it are themselves part of the
submission, not a thing to hide."*

## 1:50 – 2:20 — Ranked candidates

Switch between Titles / Descriptions / Hashtags tabs.

*"Ten independently-generated candidates in each pool, each one taking a
genuinely different angle — a question, a bold claim, a curiosity gap, a
number-led hook — not ten rewordings of the same idea. A second AI pass
ranks each pool independently against the video's ground truth and real
trend data, with a reason for every score."*

Select a title, description, and hashtag set (or accept the top-ranked
defaults).

## 2:20 – 2:45 — YouTube upload

Click Connect YouTube if not already connected, complete consent, then
Upload with privacy set to **Private**.

*"And this isn't just a copy-paste tool — with one click, the analyzed
video uploads straight to the creator's own channel with the picks they
just made."*

Confirm the upload succeeds (video id/URL returned); don't wait for
YouTube-side processing to finish on camera.

## 2:45 – 3:00 — Close

*"Local-first preprocessing, evidence-grounded generation, independent
ranking, and real AMD GPU inference with a truthful audit trail — that's
ClipContext."*

---

## If you have more time (extended walkthrough)

- Show `GET /api/providers/status` in a terminal/browser tab to prove AMD
  reachability live, not just trust the badge.
- Open **My Artifacts** (requires ClipContext login) to show saved results
  persist independently of the original job.
- Mention the fallback architecture explicitly: *"If the AMD notebook
  goes down mid-demo, the app keeps working — it falls back to Fireworks
  automatically and says so honestly in the audit trail, it doesn't
  silently claim AMD ran something it didn't."*

## If something breaks live

See [DEMO_CHECKLIST.md § If something goes wrong live](DEMO_CHECKLIST.md#if-something-goes-wrong-live)
for specific recovery moves per failure mode (AMD badge missing, OAuth
"access blocked", processing stall). The short version: narrate the
failure honestly and move on rather than live-debugging on camera — a
previously completed job's results page, kept open in another tab, is
the fastest recovery path for any mid-demo stall.
