# Direct video-generation APIs (as of 2026-10-11): Luma (Ray 3.2), Pika, PixVerse (V6 / C1), Higgsfield

Research method note: direct network egress from this environment was blocked; official pages were read through a fetch proxy (TinyFish). All figures below are quoted from the pages as fetched on 2026-10-11 unless marked otherwise. Third-party sources are labelled "(third-party)".

Use-case lens throughout: ~10 clips per episode, each ~6 s, 9:16 vertical, image-to-video, ≥1080x1920, negative prompt wanted, no text in frame, no audio needed, realistic 1890s Central Asian / Kyrgyz people in traditional dress (unnamed, not real identifiable individuals).

## Q1. Luma AI — which API, models, endpoint, auth, async pattern

### Takeaway
Luma's current first-party video API is the **Luma Agents API** (`https://agents.lumalabs.ai/v1`, Bearer `luma-api-*` key) with a single video model, **`ray-3.2`**; Ray 3, Ray 2, Ray 2 Flash, Ray 2 Relaxed, Ray 3 Reference and Ray 3 Refiner are being retired, and the old Dream Machine API (`api.lumalabs.ai/dream-machine/v1`) is legacy. Pattern is submit → poll (no webhook on the new API) → download from a presigned URL that expires in 1 hour.

### Cited Findings
- The legacy docs site now carries a banner "Looking for the latest Luma API? Create and manage API access in the Luma API Platform... visit the Luma Agents API documentation." — [docs.lumalabs.ai/docs/video-generation](https://docs.lumalabs.ai/docs/video-generation)
- Luma Agents API: "provides access to Luma's image and video models — uni-1 and uni-1-max for images, Ray 3.2 for video — through a single async REST surface." Base URL `https://agents.lumalabs.ai/v1`; endpoints `POST /v1/generations` and `GET /v1/generations/{generation_id}`. Auth: `Authorization: Bearer $LUMA_AGENTS_API_KEY`; keys begin `luma-api-`. SDKs: `pip install luma-agents`, `npm install luma-agents`, Go, CLI. — [docs.agents.lumalabs.ai (Quickstart)](https://docs.agents.lumalabs.ai/)
- Supported model ids: "`uni-1`, `uni-1-max`, and `ray-3.2`"; `ray-3.2` accepts `type` values `video`, `video_edit`, `video_reframe`. — [Error handling](https://docs.agents.lumalabs.ai/guides/error-handling); [Models](https://docs.agents.lumalabs.ai/guides/model)
- Migration guide: "Move legacy Luma video integrations to Ray 3.2 ... retiring models: Ray 3, Ray 2, Ray 2 Flash, Ray 2 Relaxed, Ray 3 Reference, Ray 3 Refiner." "legacy identifiers are not accepted by the new API." Legacy `callback_url` maps to "Poll `GET /v1/generations/{id}`" — i.e. the new API has no callback/webhook. — [Migration guide](https://docs.agents.lumalabs.ai/guides/videos/migration/)
- Legacy Dream Machine API (still documented): `POST https://api.lumalabs.ai/dream-machine/v1/generations`, models `ray-2`, `ray-flash-2`, `keyframes.frame0/frame1` with `{"type":"image","url":...}`, resolution "540p, 720p, 1080, 4k", optional `callback_url` (POST, retried max 3 times, 5 s timeout). — [docs.lumalabs.ai/docs/video-generation](https://docs.lumalabs.ai/docs/video-generation) (legacy; page "Updated 2 months ago")
- Generation states: `queued`, `processing`, `completed`, `failed`. Output: `output[].url` presigned MP4; "Presigned URLs expire after 1 hour"; re-poll mints a fresh URL. Suggested polling: 30 s initial wait, 5 s interval, 10-minute hard deadline; "a 5s/720p generation typically completes in well under two minutes." — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- No cancel endpoint; no staging/sandbox environment; no free tier. — [FAQ](https://docs.agents.lumalabs.ai/guides/faq/)
- Marketing page: "1080p output across the model", multi-keyframe "up to 16 keyframes" (docs say 1–64 — see Q2). — [lumalabs.ai/api](https://lumalabs.ai/api)

### Inferences
- Any new integration should target `agents.lumalabs.ai/v1` + `ray-3.2`; building on `ray-2`/`api.lumalabs.ai` now means a forced migration soon.
- Because there is no webhook, a bot-side poller (like the existing xAI script pattern) is needed.

### Gaps
- Exact retirement date for legacy Ray models: the guide says to use "the retirement date in [your deprecation] message"; no public date found.
- Whether 4K (offered on legacy Ray 2 docs) survives anywhere: Ray 3.2 docs list only 360p/540p/720p/1080p.

## Q2. Luma Ray 3.2 — image-to-video, resolutions/9:16, durations/fps, negative prompt/seed, audio

### Takeaway
Ray 3.2 does i2v via `video.start_frame` / `video.end_frame` (URL, base64, or file_id) or multi-keyframes; resolutions 360p/540p/720p/1080p, aspect ratios include `9:16`; durations are only `5s` or `10s` at 24 fps (no 6 s); **no negative prompt, no seed, no audio**. Critically, `start_frame`/`end_frame` are rejected with `10s`, so a single-image i2v clip is 5 s unless you use the `keyframes` route.

### Cited Findings
- I2V: "Pass an image as `video.start_frame`, `video.end_frame`, or both... a publicly accessible `url`, inline base64 `data` with `media_type`, or a `file_id` from the Files API." Image limits: "max 50 MB and 8000 px per side". — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- Multi-keyframe: `video.keyframes` (1–64 ImageRefs) + `video.keyframe_indexes` in the "`duration × 24fps` grid: `5s → 0–120`, `10s → 0–240`"; a single anchor at index 0 is equivalent to `start_frame`; this path "lifts those anchors' restrictions: arbitrary frame positions, `duration: "10s"`, and `hdr: true` are all supported." — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- `aspect_ratio` values: `9:16`, `3:4`, `1:1`, `4:3`, `16:9`, `21:9`; "When omitted, the model selects a ratio based on the prompt and anchor frames." — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- `video.resolution`: `360p` (draft, SDR only), `540p`, `720p` (default), `1080p`. `video.duration`: `5s` (default), `10s` — "`10s` is rejected with `hdr`, `start_frame`, or `end_frame`". — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- Vertical 1080p restriction exists for **reframe** only: "Only vertical targets (`9:16`, `3:4`) at `1080p` are not yet available" for `video_reframe`. — [Error handling](https://docs.agents.lumalabs.ai/guides/error-handling)
- Prompt 1–6,000 characters. — [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/)
- "Does the API support negative prompts? No. There is no parameter." "Not deterministically. Each generation uses a different random seed and there is no public parameter." — [FAQ](https://docs.agents.lumalabs.ai/guides/faq/)
- Output formats: "Video output is delivered as MP4"; HDR MP4 + optional EXR (ACES2065-1). No audio parameter or audio output is documented anywhere in the model capability matrix. — [Models](https://docs.agents.lumalabs.ai/guides/model)
- Third-party listing of Ray 3.2 (Replicate) agrees: 5 s or 10 s, 540p/720p/1080p, same six aspect ratios, "10s clips support text-to-video only — no `start_image`, `end_image`". — [Replicate luma/ray-3.2](https://replicate.com/luma/ray-3.2) (third-party)

### Inferences
- For a 6 s target: generate 5 s with `start_frame` (cheapest), or 10 s via `keyframes:[img], keyframe_indexes:[0]` and trim with FFmpeg (3× cost). Neither gives native 6 s.
- 9:16 + 1080p for generation (`type:"video"`) is not documented as restricted (only reframe is), so 1080x1920 output is plausible, but the exact pixel dimensions are not stated.
- "No text in frame" must be expressed positively in the prompt (Luma explicitly recommends positive phrasing) since there is no negative prompt.
- Silent output is the default (no audio), which fits the use case.

### Gaps
- Exact output pixel dimensions for `9:16` @ `1080p` (assumed 1080x1920, not confirmed in docs).
- fps is inferred as 24 from the keyframe-index grid; no explicit "fps" spec found.

## Q3. Luma — pricing, rate limits, moderation, watermark, account availability

### Takeaway
Ray 3.2 pay-as-you-go: **$0.30 per 5 s at 720p, $1.20 per 5 s at 1080p** (10 s: $0.90 / $3.60), no minimum, no free tier, prepaid via Stripe; rate limits are per-client RPM + concurrent jobs shown in the dashboard. Moderation is always-on and explicitly blocks "deepfakes of real people"; generic historical people should pass but named figures/real-person reference photos are a known false-positive trigger.

### Cited Findings
- Ray 3.2 SDR video generation (`type:"video"`, T2V/I2V/interpolation): 360p $0.06 / 5 s, $0.18 / 10 s; 540p $0.15 / $0.45; **720p $0.30 / $0.90; 1080p $1.20 / $3.60**. HDR (5 s only) 720p $0.60, 1080p $2.40; HDR+EXR 720p $0.90, 1080p $3.60. "Video rates are subject to change ahead of general availability." — [Pricing](https://docs.agents.lumalabs.ai/guides/pricing)
- Same table on the marketing page (540p/720p/1080p: $0.15/$0.30/$1.20 per 5 s; $0.45/$0.90/$3.60 per 10 s); "HDR output is 2× SDR pricing"; "No minimum commitment"; "Rate limits apply, no latency SLA." — [lumalabs.ai/api](https://lumalabs.ai/api)
- Pay-as-you-go: "No minimum spend, no contract." Provisioned Throughput for video: "contact sales". Failed async generations with `content_moderated` / `generation_failed` / `output_not_found` are refunded. — [Pricing](https://docs.agents.lumalabs.ai/guides/pricing)
- Rate limits: "Requests per minute (RPM)" (sliding 60 s window) and "Concurrent jobs"; "Your specific RPM and concurrent-job limits depend on your plan and are visible in the Luma platform dashboard"; HTTP 429 with `Retry-After`; polling GET is not counted against the generation RPM. — [Rate limits](https://docs.agents.lumalabs.ai/guides/rate-limits/)
- Legacy Dream Machine API "Build" tier: Ray video 10 concurrent generations, 20 create requests/min; usage limit $5,000/month. — [docs.lumalabs.ai/docs/rate-limits](https://docs.lumalabs.ai/docs/rate-limits) (legacy API; may not apply to Agents API)
- Signup/billing: "Create an account at platform.lumalabs.ai, generate a key"; "Is there a free tier? No."; auto-reload "Stripe charges your default payment method". — [FAQ](https://docs.agents.lumalabs.ai/guides/faq/)
- Moderation: blocks CSAM, sexual content, "Non-consensual intimate imagery and deepfakes of real people", graphic violence, self-harm, hateful content, infringing imagery; "Moderation runs on inputs... and outputs"; "cannot be disabled"; false positives from "named public figures... and reference images depicting real people." — [FAQ](https://docs.agents.lumalabs.ai/guides/faq/)
- Optional `user_id` on POST is forwarded "so trust & safety issues can be attributed to a specific end user". — [Quickstart](https://docs.agents.lumalabs.ai/)

### Inferences
- Episode cost (10 clips × 5 s, 1080p, 1 take each): **$12.00**; at 720p $3.00. A 6 s clip via the 10 s keyframe route at 1080p would be $36 per episode.
- A generated (AI) source still of an unnamed 1890s Kyrgyz herder is not a "real person", so it should normally pass; using archival photographs of real, identifiable people as start frames carries moderation risk.

### Gaps
- No statement found on visible/invisible watermarking (C2PA, etc.) of API output.
- No statement found on country restrictions or KYC for API signup (only "account" + Stripe card).
- Default RPM/concurrency numbers for Agents API pay-as-you-go not published (dashboard only).

## Q4. Pika — is there a first-party API? Models, parameters, pricing

### Takeaway
As of Oct 2026 Pika **does have a first-party API**: the **Pika API Club** (launched 2026-08-05) at `api.dev.pika.art`, `X-API-Key` header, $10/month membership + pay-as-you-go. It serves Pika's own **Pika 2.5** (i2v with `negative_prompt` and `seed`, 720p/1080p, 5 or 10 s) plus 100+ resold third-party models. Before that (from Dec 2025), Pika 2.2 was available to developers only via fal.ai, which still hosts it.

### Cited Findings
- "Today, we're introducing the Pika API Club: a membership platform that gives builders access to 100+ leading video, image, audio, and LLM models through one API" — dated "August 5, 2026"; models include "Seedance 2.0, MiniMax H3, Kling 3.0, Veo 3.1, Grok Imagine Video, and Pika 2.5". — [pika.art/blog/pika-api-club](https://pika.art/blog/pika-api-club)
- Membership: "$10/month unlocks member (wholesale) pricing. New members get a $10 credit toward their first month... model usage is pay-as-you-go... cancel anytime." Commercial use: "All API outputs are licensed for commercial use under your Pika API agreement." Support: api@pika.art. — [dev.pika.art](https://dev.pika.art/)
- Pika 2.5 i2v endpoint: `POST https://api.dev.pika.art/v1/media/pika/pika-2.5/image-to-video`; poll `GET https://api.dev.pika.art/v1/media/jobs/{request_id}`; `GET .../{request_id}/content` returns the output URL; `DELETE` erases stored media. Auth: "Send your key in the X-API-Key header." Body fields: `image` (required, URL), `prompt`, `negative_prompt`, `seed`, `resolution` (enum), `duration_s` (enum). Local files: `POST /v1/media/uploads` with `content_type`, `size_bytes` → PUT to `upload_url` (expires 5 min). 429 returns failed-job envelope with `Retry-After`; `Idempotency-Key` header supported. — [dev.pika.art Pika 2.5 i2v](https://dev.pika.art/models/pika/pika-2.5/image-to-video)
- Playground snippet: "Turn photos into ... videos in up to 1080p... Duration (seconds). Default: 5. 5 10." — [Pika 2.5 Playground](https://dev.pika.art/models/pika/pika-2.5/image-to-video/playground) (search snippet)
- Pika API pricing (member rates, "include 5% platform fee", recorded 10.6.26): **Pika 2.5 Image to Video: 720p $0.04/sec; "720p 5s" $0.04/sec; 1080p $0.06/sec; "1080p 5s" $0.09/sec**; Text to Video 720p 5s $0.04/sec, 1080p 5s $0.09/sec; Pika 2.5 Keyframe i2v 720p $0.04/sec, 1080p $0.06/sec; all marked "Only on Pika" (not on fal/Runway/Higgsfield). — [dev.pika.art/pricing](https://dev.pika.art/pricing)
- fal.ai partnership (Dec 2025): "Pika ... has partnered with fal to bring its powerful Model 2.2 ... Pikaframes ... Pikascenes"; "high-quality 1080p". — [blog.fal.ai](https://blog.fal.ai/pika-api-is-now-powered-by-fal/)
- fal endpoint `fal-ai/pika/v2.2/image-to-video`: `image_url` (required, first frame), `prompt`, `seed`, `negative_prompt` (default ""), `resolution` enum `720p`, `1080p` (default 720p), `duration` enum `5`, `10`; auth `FAL_KEY`; queue submit with optional `webhookUrl`, status, result. — [fal.ai Pika 2.2 i2v API](https://fal.ai/models/fal-ai/pika/v2.2/image-to-video/api)
- A third-party page dated Sep 2026 still claims "Is there an official Pika Labs API? Not a first-party one on pika.art. Access is through fal.ai" — contradicted by Pika's own API Club pages. — [flux-1.ai](https://flux-1.ai/pika-labs-api/) (third-party, outdated); contradicted by [pika.art/blog/pika-api-club](https://pika.art/blog/pika-api-club)

### Inferences
- Pika 2.5 i2v at 1080p, 5 s: either $0.30 (at $0.06/s) or $0.45 (at $0.09/s) — the pricing table lists both "1080p" and "1080p 5s" rows and it is unclear which applies; 10 clips ≈ $3.00–$4.50 plus the $10/month fee.
- 6 s is not a supported value (5 or 10 only); trim from 10 s or accept 5 s.
- Pika 2.5 i2v has no `aspect_ratio` field in the documented body; framing presumably follows the input image (so a 1080x1920 still should give 9:16) — not confirmed.

### Gaps
- Exact accepted enum values of `resolution` / `duration_s` (rendered as blank on the fetched page; 720p/1080p and 5/10 come from pricing and playground snippet).
- Audio: no audio parameter on Pika 2.5 i2v; whether output carries audio is not stated.
- Output pixel dimensions, fps, watermark, moderation policy for real people, rate-limit numbers, country/KYC restrictions: not found.
- fal.ai price for Pika 2.2 not retrieved.

## Q5. PixVerse — first-party platform API (V6, C1, legacy V5.x)

### Takeaway
PixVerse has a mature first-party API (`https://app-api.pixverse.ai/openapi/v2/`, headers `API-KEY` + unique `Ai-trace-id`). Current models are **`v6`** (2026-03-29) and **`c1`** (2026-04-07): i2v with any **integer duration 1–15 s** (so native 6 s), quality 360p/540p/720p/1080p, `seed`, `negative_prompt`, optional audio via `generate_audio_switch`, polling or signed webhooks. It is the cheapest direct option found for 6 s 1080p i2v.

### Cited Findings
- "All endpoints are under `https://app-api.pixverse.ai/openapi/v2/`. Every request uses two headers: `API-KEY` (your key) and `Ai-trace-id` (a fresh UUID per request — reusing the same value returns the previous result instead of triggering a new generation)." Responses `{ErrCode, ErrMsg, Resp}`; "poll the get-status endpoint every 3–5s until `status=1`". — [PixVerse-api-llm.txt](https://docs.platform.pixverse.ai/pixverse-api-llm-txt-2109771m0)
- I2V flow: upload `POST /openapi/v2/image/upload` (multipart `image` or `image_url`; "maximum dimensions 10000 pixels", "less than 20MB", png/webp/jpeg/jpg) → returns `img_id`; then `POST /openapi/v2/video/img/generate` with `img_id`, `prompt`, `model`, `duration`, `quality`, `motion_mode`, `negative_prompt`, `seed`. — [Upload Image](https://docs.platform.pixverse.ai/upload-image-13016631e0); [Image-to-Video generation](https://docs.platform.pixverse.ai/image-to-video-generation-13016633e0); [llm.txt](https://docs.platform.pixverse.ai/pixverse-api-llm-txt-2109771m0)
- V6 parameters: `model:"v6"`, `prompt` ≤5000 chars, `duration` int 1–15 ("1080p supports up to 15s"), `quality` "360p","540p","720p","1080p", `aspect_ratio` supported for t2v/fusion only ("❌" for i2v), `generate_audio_switch` boolean, `generate_multi_clip_switch`, `img_id` (i2v), `first_frame_img`/`last_frame_img` (transition endpoint), `image_references` (fusion), `seed` 0–2147483647. — [V6](https://docs.platform.pixverse.ai/v6-2056814m0)
- C1: same shape (`model:"c1"`), 1–15 s, up to 1080p, `generate_audio_switch`, no video extension; "Cinematic quality, reference-based generation, action scenes". — [C1](https://docs.platform.pixverse.ai/c1-2067883m0); [Capability matrix](https://docs.platform.pixverse.ai/capability-matrix-2144288m0)
- Negative prompt length: error 400018/400019 "Prompt/negative prompt length exceeds 2048 characters limit." Status response includes `negative_prompt`, `outputWidth`, `outputHeight`, `seed`. — [Error codes](https://docs.platform.pixverse.ai/error-codes-796041m0); [Get Video Generation Status](https://docs.platform.pixverse.ai/get-video-generation-status-13016632e0)
- Status codes: "1: Generation successful; 5: Generating; 7: Contents moderation failed; 8: Generation failed" (6 = deleted per llm.txt). — [Get Video Generation Status](https://docs.platform.pixverse.ai/get-video-generation-status-13016632e0)
- Webhooks: create a `webhook_id` in the dashboard and add it to the generation request; POST with `Webhook-Timestamp`, `Webhook-Nonce`, `Webhook-Signature` (Base64 HMAC-SHA256); must answer HTTP 200 body `ok`; retries 2 s → 4 h (8 attempts). Supported for `video/img/generate`, `video/transition/generate`, etc. — [Webhook integration](https://docs.platform.pixverse.ai/webhook-integration-1905378m0)
- Credits per second — V6: 720p **9** (no audio) / 12 (audio); 1080p **18** / 23. C1: 720p 10 / 13; 1080p 19 / 24. Legacy V5.6 (per clip): 1080p 5 s 75 / 150. — [Pricing](https://docs.platform.pixverse.ai/pricing-796039m0)
- Credit purchase: $10 → 2,000 credits; $50 → 10,000; $100 → 20,000; $500 → 100,000; $2000 → 400,000; $5000 → 1,000,000. Memberships: Essential $100 / 22,250 monthly credits; Scale $1,500 / 360,000; Business $6,000 / 1,636,365. Page also says "$1 = 5 videos (v6, 720p, 5s, no audio)" and "$10 → 59 videos" — inconsistent with 45 credits per such clip at 200 credits/$ (would be ≈4.4 videos per $1). — [Pricing](https://docs.platform.pixverse.ai/pricing-796039m0)
- Concurrency by membership: Free 3, Essential 15, Scale 20, Business 25. — [Rate limit](https://docs.platform.pixverse.ai/rate-limit-796040m0)
- "API memberships are separate from PixVerse Web (app.pixverse.ai) Membership... API credits cannot be used with the PixVerse Web"; subscribe at platform.pixverse.ai/billing with payment details; upgrades/downgrades "Not supporting yet". — [Subscribe API plans](https://docs.platform.pixverse.ai/how-to-subscribe-api-plans-882969m0)
- Moderation errors: 500054 "Image maybe contains inappropriate content"; 500063 video/image/text moderation failed ("text you entered contains sensitive information"). — [Error codes](https://docs.platform.pixverse.ai/error-codes-796041m0)
- Changelog: v6 2026-03-29; c1 2026-04-07; V6 reference-to-video `reference_mode:"omni"` 2026-07-26; Upscale 2026-06-16; latest entry 2026-09-24. — [Changelogs](https://docs.platform.pixverse.ai/changelogs-906383m0)
- PixVerse states ISO/IEC 27001 (DNV) certification and SOC 2 controls. — [pixverse.ai/en/developers](https://pixverse.ai/en/developers)

### Inferences
- Cost per 6 s 1080p i2v clip, no audio: V6 = 108 credits ≈ **$0.54** (at $0.005/credit top-up price; ≈$0.49 on Essential membership); C1 = 114 credits ≈ $0.57. 720p V6: 54 credits ≈ $0.27. Per episode (10 clips): ≈ $5.40 at 1080p V6. Equivalent ≈ $0.09/s at 1080p, $0.045/s at 720p.
- Set `generate_audio_switch: false` explicitly to get the cheaper no-audio rate (default on the direct API not stated; Higgsfield's wrapper defaults audio to true).
- Because i2v has no `aspect_ratio`, the 9:16 framing must come from the uploaded still; a 1080x1920 input at `quality:"1080p"` should yield 9:16 1080p, confirmable via `outputWidth/outputHeight`.
- The Free tier (concurrency 3) suggests sign-up without a paid plan is possible, but generation needs purchased credits.

### Gaps
- Whether API output carries a visible watermark: not stated in API docs (third-party claims say paid web plans remove it; not verified for API).
- Exact output pixel dimensions and fps for 1080p 9:16 not documented.
- Content policy specifics on realistic historical/ethnic depictions, real-person likeness: only generic moderation error codes found.
- KYC / country restrictions for API billing: not found.
- Default value of `generate_audio_switch` on V6/C1 direct API.

## Q6. Higgsfield — first-party API? Which models it resells

### Takeaway
Higgsfield launched a self-serve **first-party API** (`https://api.higgsfield.ai`, `Authorization: Key <KEY_ID>:<KEY_SECRET>`, console.higgsfield.ai) in Sept 2026. It is mainly an **aggregator/reseller**: 67 video catalog entries across 22 families (Kling, Seedance, Wan, Happy Horse, MiniMax/Hailuo, LTX-2.5, PixVerse V6, Grok Imagine Video) plus a few own models (Genjutsu, Cinema Studio 4.0, DoP; Soul image models). Pricing is USD per second per model; PixVerse V6 via Higgsfield starts at $0.115/s, roughly 2.5× PixVerse's direct 720p rate.

### Cited Findings
- "Higgsfield provides one integration point for generative media models. Submit a request to a model endpoint, then poll for the result or receive a webhook." Response: `status: "queued"`, `request_id`, `status_url`, `cancel_url`. "Output files are available for at least seven days." — [docs.higgsfield.ai](https://docs.higgsfield.ai/docs)
- Auth: "`Authorization: Key YOUR_KEY_ID:YOUR_KEY_SECRET`"; legacy `hf-api-key` / `hf-secret` headers still accepted; "Do not use a Bearer token". — [Authentication](https://docs.higgsfield.ai/docs/authentication); [FAQ](https://docs.higgsfield.ai/docs/help/faq)
- Video catalog (22 families, 67 entries): Higgsfield Genjutsu; ByteDance Seedance 2.0, Seedance 2.5; Kling 2.5 Turbo, 2.6, 2.6 Motion Control, 3.0 (Standard/Pro/4K/Turbo), 3.0 Motion Control, Kling O3, Kling Omni; Alibaba Happy Horse 1.0, HappyHorse 1.1, Wan 3.0, Wan 3.0 Prime, Wan 2.6, Wan 2.7; Higgsfield Cinema Studio 4.0; Lightricks LTX-2.5; MiniMax H3, Hailuo 2.3; PixVerse V6; xAI Grok Imagine Video 1.5. — [Video Generation API](https://docs.higgsfield.ai/docs/models/video-generation)
- Not in the catalog: no Luma, no Pika, no Veo, no Sora models listed. — [Video Generation API](https://docs.higgsfield.ai/docs/models/video-generation)
- Blog (2026-09-16): "self-serve API ... more than 50 current video and image generation models with pay-as-you-go billing in US dollars. There is no subscription"; "The API is a separate product from the higgsfield.ai website"; "Creating a key unlocks 20 concurrent requests"; account "personal and company use". Starting rates: Kling 2.5 $0.042/s; Kling 2.6 $0.07/s; Seedance 2.5 $0.0738/s; Kling 3.0 $0.112/s; **PixVerse 6 $0.115/s**; MiniMax H3 $0.13/s; LTX 2.5 Pro $0.17/s; Wan 3.0 $0.20/s; Grok Imagine Video 1.5 $0.25/s; Seedance 2.0 $0.9332/s; DoP $0.125/generation. — [higgsfield.ai/blog/higgsfield-api](https://higgsfield.ai/blog/higgsfield-api); [higgsfield.ai/blog/generate-ai-videos-higgsfield-api](https://higgsfield.ai/blog/generate-ai-videos-higgsfield-api)
- Docs describe billing in "account credits" with an estimate endpoint (`POST /estimate/<model-path>` returns `{"credits":"1.500","usd":"0.094"}` — illustrative); "Credits expire one year after they are added"; failed and `nsfw` requests not charged; queued requests cancellable and refunded. — [Billing and retention](https://docs.higgsfield.ai/docs/concepts/billing-and-retention)
- Rate limits: concurrency per account/model, visible in console; example error "Maximum number of concurrent requests (4) has been reached" returned as HTTP 400; no `Retry-After` headers. — [Rate limits](https://docs.higgsfield.ai/docs/concepts/rate-limits) (example "4" conflicts with blog's "20 concurrent requests")
- PixVerse V6 via Higgsfield: `POST https://api.higgsfield.ai/pixverse/v6/image-to-video`; fields `image_url` (required), `end_image_url`, `prompt` 1–5000, `duration` number 1–15 (default 5, fractional allowed), `resolution` "360p"/"540p"/"720p"/"1080p" (default 720p), `generate_audio` (default **true**), `negative_prompt` 1–2048, `seed` 0–2147483647; "This endpoint has no aspect_ratio parameter; framing comes from the input image"; `Idempotency-Key` header. — [PixVerse V6 — Image to video](https://docs.higgsfield.ai/docs/models/pixverse-v6/image-to-video)
- Webhooks: "Pass an HTTPS endpoint in the query parameter when submitting"; must respond within 10 s; retries up to two hours; duplicates possible. Uploads: presigned upload URL (expires 1 h). — [Webhooks](https://docs.higgsfield.ai/docs/how-to/webhooks); [File uploads](https://docs.higgsfield.ai/docs/concepts/file-uploads)
- Moderation: "NSFW ... indicates that either your input parameters or the generated output did not pass our content moderation system... Content policy rules and restrictions may vary depending on the specific model being used." — [FAQ](https://docs.higgsfield.ai/docs/help/faq)

### Inferences
- For PixVerse V6 specifically, going direct to PixVerse is cheaper (~$0.045/s 720p, ~$0.09/s 1080p no audio) than Higgsfield's "starting" $0.115/s; Higgsfield's value is one key for many models (Kling 3.0, Seedance, Wan, etc.).
- Remember to send `generate_audio:false` through Higgsfield (default true).
- Moderation through Higgsfield = Higgsfield's layer + the upstream model's policy.

### Gaps
- Per-resolution Higgsfield price for PixVerse V6 at 1080p (only "starting rate" published in fetched pages; full price list is on the console/pricing page, not fetched).
- Exact webhook query-parameter name (stripped from the fetched page).
- KYC/country restrictions, watermarking: not found.

## Q7. Cross-provider fit for the use case (6 s, 9:16, ≥1080x1920, i2v, negative prompt, no text, ~10 clips)

### Takeaway
Only **PixVerse (V6/C1, direct or via Higgsfield)** natively supports a 6 s duration with a negative prompt and seed at 1080p i2v; **Pika 2.5** has negative prompt + seed at 1080p but only 5/10 s; **Luma Ray 3.2** has no negative prompt, no seed, and single-image i2v is fixed at 5 s, though it is the only one with HDR/EXR and multi-keyframe control.

### Cited Findings
- PixVerse V6 i2v: duration 1–15 int, 1080p, `negative_prompt`, `seed`, audio switch; 18 credits/s at 1080p no audio. — [V6](https://docs.platform.pixverse.ai/v6-2056814m0); [Pricing](https://docs.platform.pixverse.ai/pricing-796039m0)
- Pika 2.5 i2v: `negative_prompt`, `seed`, up to 1080p, durations 5/10; $0.06–$0.09/s at 1080p plus $10/mo. — [Pika 2.5 i2v](https://dev.pika.art/models/pika/pika-2.5/image-to-video); [Pika pricing](https://dev.pika.art/pricing)
- Luma Ray 3.2: no negative prompt or seed; `start_frame` rejected with 10 s; $1.20 per 5 s at 1080p. — [FAQ](https://docs.agents.lumalabs.ai/guides/faq/); [Video generation](https://docs.agents.lumalabs.ai/guides/videos/generation/); [Pricing](https://docs.agents.lumalabs.ai/guides/pricing)

### Inferences
- Approximate per-episode cost (10 clips, 1 take each, 1080p, no audio): PixVerse V6 direct ≈ $5.40 (6 s); Pika 2.5 ≈ $3.00–$4.50 (5 s) + $10/mo membership; Luma Ray 3.2 = $12.00 (5 s); Higgsfield PixVerse V6 ≥ $6.90 (6 s × $0.115/s starting rate, likely higher at 1080p). Retakes multiply these.
- All three direct APIs accept an image by public URL; PixVerse requires a prior upload to get `img_id`; Pika and Higgsfield offer presigned uploads; Luma also accepts base64 inline.
- "No text in frame": use `negative_prompt` ("text, captions, subtitles, watermark, logo, letters") on PixVerse/Pika; on Luma state it positively in the prompt.

### Gaps
- None of the four providers' docs (as fetched) state watermark policy for API output or KYC/country restrictions; treat as unverified and check during signup.
- No provider explicitly addresses depictions of specific ethnic/historical groups; only generic "real person / deepfake / public figure" rules (Luma) and generic NSFW/moderation codes (PixVerse, Higgsfield) were found.
