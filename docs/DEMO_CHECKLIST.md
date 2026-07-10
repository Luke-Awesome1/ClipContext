# ClipContext — Demo Checklist (2–5 minutes)

Run through once, end to end, before recording/presenting — do not skip
straight to the click order without a rehearsal, since AMD reachability and
YouTube OAuth Testing-mode restrictions are both stateful.

## Before you start

- [ ] AMD notebook: `amd/start_vllm.sh` running with
      `AMD_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct` in its own `tmux` session
      (survives a dropped terminal); `amd/smoke_test.py` passed against
      `localhost:8000` (see `amd/README.md`).
- [ ] AMD notebook: `cloudflared tunnel --url http://localhost:8000`
      running in a second `tmux` session — the notebook has no direct
      public port, so this tunnel is required. Note the current
      `https://*.trycloudflare.com` URL; it's ephemeral and changes on
      every `cloudflared` restart, so re-check it's still the one the
      backend has, not a stale one from an earlier session.
- [ ] Backend host (Railway) has `AMD_VLLM_BASE_URL` set to that tunnel
      URL + `/v1`, `AMD_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct`,
      `AMD_VLLM_API_KEY` matching what the vLLM server was started with,
      and `CONTENT_GENERATION_PROVIDER=amd_vllm` — restarted after setting
      them. `DISCRIMINATOR_PROVIDER` intentionally left unset (defaults to
      Fireworks) to keep the demo to one AMD wait.
- [ ] `curl <backend>/api/providers/status` shows
      `"reachable": true` for `amd_vllm` — check this shortly before
      presenting, not hours earlier, since both the notebook and the tunnel
      are time-boxed.
- [ ] The Google account you'll log in with is added as a Test user on the
      OAuth consent screen (required while it's in Testing mode).
- [ ] A short (30s–2min) test video is ready locally.

## Click/run order

1. **Landing page** — open the deployed frontend URL. Confirm it loads with
   no console errors.
2. **Upload** — upload the test video. Optionally enter a YouTube creator
   handle to show creator-specific trend analysis (skip if you want the
   faster worldwide-only path).
3. **Processing** — let the progress stages play through
   (validating → audio → frames → transcribing → temporal alignment →
   visual analysis → context generation → trends → content generation →
   ranking). Narrate: "everything before context generation runs locally
   and free; only the multimodal understanding and the two AMD-eligible
   stages make paid/GPU inference calls."
4. **Results — multimodal understanding** — point at the "VideoContext
   Signals" card (topic / content type / core message / multimodal
   summary). This is the grounded evidence every generated candidate is
   required to be consistent with.
5. **Results — AMD inference evidence** — point at the small "AMD GPU
   inference" badge(s) at the bottom of that same card (only present when
   `provider_used == "amd_vllm"` for that stage in this actual run — if a
   badge is missing, AMD fell back to Fireworks for that stage; check
   `/api/providers/status` before continuing rather than presenting a
   fallback as AMD execution).
6. **Results — ranked candidates** — switch between the Titles /
   Descriptions / Hashtags tabs. Point out the rank/score/reason on each
   candidate and that the three pools are ranked independently.
7. **Select** a title, description, and hashtag set (or accept the
   top-ranked defaults).
8. **Save artifact** — click Save Results (requires ClipContext Google
   login — sign in if not already). Confirm the save succeeds.
9. **My Artifacts** — navigate to `/artifacts`, open the saved artifact,
   confirm the full generated content and selection are present.
10. **Connect YouTube** — click Connect YouTube, complete the Google
    consent screen, confirm it returns to `/results?youtube=connected` and
    shows the connected channel's name.
11. **Private upload** — confirm privacy is set to **Private** (the
    default), click Upload, watch the real upload progress, confirm a
    video id/URL is returned.
12. **View on YouTube** — click through and confirm the video exists on the
    channel (still processing on YouTube's side is fine to show — the
    point is the upload succeeded).

## If something goes wrong live

- **AMD badge missing** — say so plainly ("this stage fell back to
  Fireworks this run") rather than skipping past it; the fallback
  architecture and honest audit trail are themselves part of the technical
  submission.
- **YouTube OAuth fails with "access blocked"** — the Google account isn't
  on the Testing-mode Test users list; switch to an account that is, or
  narrate the flow from a previous successful run instead of live-debugging
  Google Cloud Console on camera.
- **Processing stalls on visual analysis** — Fireworks Kimi vision rate
  limit or a truncated response; this is unrelated to the AMD integration
  (it's the vision stage) — have a previously completed job's results page
  ready as a fallback to keep the demo moving.
