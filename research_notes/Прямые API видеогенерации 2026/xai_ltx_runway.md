# Direct video generation APIs: xAI Grok Imagine, Lightricks LTX API, Runway API (as of 2026-10-11)

Audience: a US-based individual developer (see section 4). Method note: docs.x.ai, docs.ltx.io and docs.dev.runwayml.com are blocked by the egress proxy of this environment, so the pages were read through the TinyFish fetch tool (rendered official pages, fetched 2026-10-11). Every fact below comes from an official page unless it is marked as third-party. Page "last updated" dates are given where the page shows one. Target use case: a 6 s, 9:16 image-to-video clip at ≥1080x1920, with a negative prompt and no text in frame, about 10 clips per episode.

## 1. xAI — Grok Imagine Video (grok-imagine-video-1.5, -1.5-lite, grok-imagine-video)

### Takeaway
xAI currently sells three video models: `grok-imagine-video-1.5` (native 1080p, $0.25/s at 1080p), `grok-imagine-video-1.5-lite` (1080p upscaled from 720p, $0.14/s) and the older `grok-imagine-video` (720p max; it is the only one that does editing and extension). Image-to-video always matches the input image's aspect ratio and the docs say `aspect_ratio` is **ignored**, not that it stretches the frame. Audio is on by default and is turned off with `generate_audio: false`. No negative prompt, seed or fps parameter is documented.

### Cited Findings
**Endpoint, auth, async pattern**
- REST base `https://api.x.ai/v1`. Submit with `POST /v1/videos/generations`. The response is `{"request_id": "..."}`. Poll `GET /v1/videos/{request_id}`. Auth header is `Authorization: Bearer $XAI_API_KEY`. Statuses are `pending` / `done` / `failed` (examples also check `expired`). When done, the response is `{"status":"done","video":{"url":"https://vidgen.x.ai/.../video.mp4","duration":8,"respect_moderation":true},"model":"grok-imagine-video-1.5"}` — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- "Videos are returned as temporary URLs… download/process it promptly if you need to keep a copy." No exact expiry time is stated — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- Editing and extension use their own endpoints: `/v1/videos/edits` and `/v1/videos/extensions`. Generation typically "takes up to several minutes". The SDK's default poll timeout is 10 min — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- Outputs can be persisted to the Files API, which can also create a permanent public URL — [xAI Imagine overview (updated 2026-10-08)](https://docs.x.ai/developers/model-capabilities/imagine)

**Models and capabilities** (from the table on the Video Overview page, updated 2026-10-08)
- `grok-imagine-video-1.5`: T2V and I2V "Up to 1080p, native". Up to 14 reference images (reference-to-video capped at 720p and 15 s). Up to 3 voice references. First and last frame. Up to 4 keyframes. Duration 1–15 s. Resolution 480p/720p/1080p. Price 480p $0.08/s, 720p $0.14/s, 1080p $0.25/s — [xAI Video Overview](https://docs.x.ai/developers/model-capabilities/video/overview)
- `grok-imagine-video-1.5-lite` (labelled "New"): T2V and I2V "Up to 1080p, upscaled from 720p". No references, first/last frame or keyframes. Duration 1–15 s. Price 480p $0.02/s, 720p $0.03/s, 1080p $0.14/s — [xAI Video Overview](https://docs.x.ai/developers/model-capabilities/video/overview)
- `grok-imagine-video` (classic): up to 720p (480p $0.05/s, 720p $0.07/s). Video editing (source ≤ 8.7 s). Extension (+2–10 s). Up to 7 reference images. It rejects `last_frame` and `keyframes` — [xAI Video Overview](https://docs.x.ai/developers/model-capabilities/video/overview); [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- The pricing page confirms the same per-second rates and adds input charges: $0.01/img of image input for 1.5 and 1.5-lite. For classic it is $0.01/s of video input and $0.002/img — [xAI Pricing](https://docs.x.ai/developers/pricing)
- On 1.5 and 1.5-lite, text-to-video runs internally as text-to-image followed by image-to-video — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)

**Image-to-video input and aspect ratio (checks the claim in CLAUDE.md)**
- The image is passed as `"image": {"url": "..."}`. The value can be a public URL, a base64 data URI (`data:image/jpeg;base64,...`) or a Files API `file_id`. "Sending `image` alone is image-to-video". Adding `last_frame`, `keyframes` or `reference_images` turns the request into reference-to-video with that image pinned as the first frame — [xAI Image-to-Video (updated 2026-09-21)](https://docs.x.ai/developers/model-capabilities/video/image-to-video)
- Quote: "Image-to-video output always matches the input image's aspect ratio; `aspect_ratio` is ignored." — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation); the overview says the same thing ("The output always matches the still's aspect ratio; `aspect_ratio` is ignored") — [xAI Video Overview](https://docs.x.ai/developers/model-capabilities/video/overview)
- Allowed `aspect_ratio` values for T2V are `1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9, 5:2`, default `16:9`. `resolution` takes `480p` (default), `720p` or `1080p` — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- Image input limits for xAI image-input models: max 20 MiB, jpg/jpeg or png only — [xAI Models](https://docs.x.ai/developers/models)

**Audio, duration and other knobs**
- `duration` runs from 1 to 15 s with a default of 8 — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- "Generated videos include an audio track by default". Passing `"generate_audio": false` requests a silent video — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- The video generation docs do not document a negative prompt, seed, fps or prompt-enhancement parameter (I searched the full page for these terms) — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)

**Rate limits, billing, moderation**
- Video RPS by tier for all three video models is T0 10, T1 20, T2 39, T3 79, T4 158. These numbers were parsed from a concatenated table cell ("10203979158"). Tiers depend on cumulative spend since 2026-01-01 (T1 $50, T2 $250, T3 $1,000, T4 $5,000). However, "Rate limit tiers apply to text, embedding, and voice models. For increases to Imagine API limits, contact sales@x.ai" — [xAI Rate Limits](https://docs.x.ai/developers/rate-limits)
- Rate-limit and auth errors come back synchronously as HTTP errors (429). Failed jobs return `error.code`, one of `invalid_argument` (this includes "content blocked by moderation"), `permission_denied`, `failed_precondition`, `service_unavailable` or `internal_error` — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- The response includes `respect_moderation`. The SDK example prints "Video filtered by moderation" when it is false — [xAI Video Generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- "When your request is deemed to be in violation of our usage guideline… we will still charge for the generation". A $0.05 fee applies to violations caught before generation, but that line is stated for the Responses API — [xAI Pricing](https://docs.x.ai/developers/pricing)
- Generated media "is subject to content policy review and is not used for training" — [xAI Imagine overview](https://docs.x.ai/developers/model-capabilities/imagine)
- Watermark (third-party, low confidence): one blog says Grok outputs carry a watermark. A directory listing says exports are watermark-free. Both sources most likely describe the consumer Grok app, not the API — [elser.ai](https://www.elser.ai/blog/grok-ai-video-limits); [creati.ai](https://creati.ai/ai-tools/grokimagine-ai/)

**Via Runway (alternative route to the same models)**
- Runway resells `grok_imagine_1_5`: 480p 10, 720p 16, 1080p 29 credits/s, plus 1 credit per image (start frame included). It also resells `grok_imagine_1_5_lite`: 2 / 3 / 14 credits/s plus 1 credit for the start frame. At $0.01/credit — [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/)
- On Runway, `grok_imagine_1_5` I2V takes `resolution` (`480p`/`720p`/`1080p`), `duration` 1–15 and an optional `promptText` (max 2500 characters), and "Output aspect ratio follows the input image". Only the `first` frame position is supported — [Runway API reference](https://docs.dev.runwayml.com/api.md); [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)

### Inferences
- The CLAUDE.md note "aspect_ratio is not passed for image-to-video, otherwise xAI stretches the frame" is **not corroborated** by current docs, which say the parameter is ignored. The stretching was either seen on an older model or build, or it came from the input image's own ratio. Omitting the parameter is still harmless and is the safest choice. To get 1080x1920 you have to supply a 9:16 source image and set `resolution: "1080p"`.
- Cost for this use case (6 s, 1080p I2V) on direct xAI: 1.5 = 6 × $0.25 + $0.01 = **$1.51/clip, about $15.10 per 10-clip episode**. 1.5-lite = 6 × $0.14 + $0.01 = **$0.85/clip, about $8.50/episode**. Via Runway the cost is about $1.75 and $0.85 respectively, so direct xAI is cheaper for 1.5.
- Because there is no negative prompt, "no text in frame" has to be handled in the positive prompt and in the source image.
- 1.5 renders 1080p natively, while lite upscales from 720p. For ≥1080x1920 at full detail, 1.5 is the honest choice.

### Gaps
- Exact pixel dimensions of 1080p 9:16 output (presumably 1080x1920, but the docs do not say), output fps, and the codec are not documented.
- The expiry time of the `vidgen.x.ai` URL is not stated, only "temporary".
- Minimum prepaid top-up, KYC and country restrictions for console.x.ai were not found in the pages read.
- Watermark or C2PA for API output: no official statement found.
- No official policy text was found on realistic depictions of non-famous historical people. Only the general "content policy review" applies.
- The Imagine concurrency limit (as opposed to RPS) is not stated.

## 2. Lightricks — LTX API (ltx-2-5-fast / ltx-2-5-pro / ltx-2-3-fast / ltx-2-3-pro)

### Takeaway
The LTX API (`https://api.ltx.io`, Bearer key, async V2 jobs) offers LTX-2.5 and LTX-2.3 in Fast and Pro variants. All four support 9:16 at `1080x1920` and up to `2160x3840` (4K). Durations are fixed values of 6/8/10 s (Fast also has 12–20 s at ≤1080p 24/25 fps), and fps is 24/25/48/50. The API exposes **no negative prompt, seed, CFG/guidance or steps parameters**. Audio is generated by default and turned off with `generate_audio: false`. LTX-2 (`ltx-2-fast`/`ltx-2-pro`) was removed on 2026-08-16. Price for 1080x1920: $0.06–$0.17/s depending on model.

### Cited Findings
**Host, auth, async**
- Host `https://api.ltx.io` since 2026-07-21. The old `https://api.ltx.video` "keep working unchanged" — [LTX API Changelog](https://docs.ltx.io/api-changelog)
- Auth header is `Authorization: Bearer YOUR_API_KEY`. A bad key returns 401 `authentication_error` — [LTX Authentication](https://docs.ltx.io/authentication)
- Async V2 flow: `POST /v2/image-to-video` returns `202` with `id` and `created_at`. Poll `GET /v2/image-to-video/{id}` and download from `result.video_url`. Statuses are `pending`, `processing`, `completed` and `failed`. Recommended polling interval is ≥5 s with jitter — [LTX Image-to-Video reference](https://docs.ltx.io/api-documentation/api-reference/async-video-generation/submit-image-to-video); [LTX Async Jobs](https://docs.ltx.io/async-jobs)
- Retention: "Job status is available for up to 24 hours after the job reaches a terminal state… Output URLs expire independently of job status. Download or re-host outputs as soon as you observe `completed`" — [LTX Async Jobs](https://docs.ltx.io/async-jobs)
- The V1 sync endpoints (`/v1/text-to-video`, `/v1/image-to-video`, …) stop working after 2026-10-26 23:59 UTC. `/v1/upload` remains — [LTX API Changelog (2026-09-24)](https://docs.ltx.io/api-changelog)

**Image-to-video request fields** (`POST /v2/image-to-video`)
- `image_uri` (required, first frame). `prompt` (required, ≤5000 characters). `model` (required). `duration` (integer or `null`, required; `null` means automatic duration on 2.5). `resolution` (required, e.g. `"1080x1920"`). `fps` (default 24). `generate_audio` (default `true`). `last_frame_uri` (optional; interpolates first→last). `camera_motion` (enum) — [LTX Image-to-Video reference](https://docs.ltx.io/api-documentation/api-reference/async-video-generation/submit-image-to-video)
- `camera_motion` options: `dolly_in`, `dolly_out`, `dolly_left`, `dolly_right`, `jib_up`, `jib_down`, `static`, `focus_shift` — [LTX API Changelog (2026-01-01)](https://docs.ltx.io/api-changelog)
- Image input methods: HTTPS URL (max 15 MB, 10 s fetch timeout, no redirects, domain names only), data URI (max 7 MB encoded), or a cloud upload via `v1/upload` that returns `ltx://uploads/...` (200 MB cap; upload URL valid 1 h, file kept 24 h). Formats: PNG, JPEG, WEBP — [LTX Input Formats](https://docs.ltx.io/input-formats)
- The request schema has no negative prompt, seed, guidance/CFG or steps field. The only fields are the ones listed above — [LTX Image-to-Video reference](https://docs.ltx.io/api-documentation/api-reference/async-video-generation/submit-image-to-video)

**Models, resolutions, durations, fps**
- LTX-2.5: `ltx-2-5-fast` for speed and low cost, `ltx-2-5-pro` for higher fidelity. "Both produce portrait and landscape video up to 4K." The page describes the release as including "a Diffusion Video Decoder…, native multi-shot scenes, and a better distilled model" — [LTX-2.5](https://docs.ltx.io/models/ltx-2-5)
- LTX-2.5 support matrix: **Fast** 720p and 1080p at 24/25 fps → 6, 8, 10, 12, 14, 16, 18, 20 s; at 48/50 fps → 6, 8, 10 s; 1440p and 4K → 6, 8, 10 s. **Pro** at every resolution (720p–4K) and 24/25/48/50 fps → 6, 8, 10 s — [LTX-2.5](https://docs.ltx.io/models/ltx-2-5)
- Resolution strings, 16:9 / 9:16: 720p `1280x720`/`720x1280`, 1080p `1920x1080`/`1080x1920`, 1440p `2560x1440`/`1440x2560`, 4K `3840x2160`/`2160x3840`. LTX-2.3 has the same matrix and the same resolutions — [LTX-2.5](https://docs.ltx.io/models/ltx-2-5); [LTX-2.3](https://docs.ltx.io/models/ltx-2-3)
- `ltx-2-5-pro` gained 1440p, 4K and 48 fps on 2026-09-02. At launch (2026-08-11) Pro was 720p/1080p only — [LTX API Changelog](https://docs.ltx.io/api-changelog). The "Supported Models" overview page still says "up to 4K on Fast, up to 1080p on Pro… 48 fps on Fast", which is **stale** and contradicted by the changelog and the LTX-2.5 page — [LTX Supported Models](https://docs.ltx.io/models)
- Automatic duration means sending `"duration": null`, and the field itself is still required. On prepaid accounts, credits for the maximum possible duration are held until the job finishes. It cannot be combined with `last_frame_uri` — [LTX-2.5](https://docs.ltx.io/models/ltx-2-5)
- On LTX-2.3, audio-to-video, retake and extend require `ltx-2-3-pro`. LTX-2.5 supports T2V, I2V and A2V but not retake or extend — [LTX-2.3](https://docs.ltx.io/models/ltx-2-3); [LTX-2.5](https://docs.ltx.io/models/ltx-2-5)
- LTX-2 (`ltx-2-fast`, `ltx-2-pro`) was removed on 2026-08-16. Requests for those models now return an error — [LTX API Changelog](https://docs.ltx.io/api-changelog)

**Pricing** (per second of output, I2V; T2V is identical)
- `ltx-2-5-fast`: 720p $0.09, 1080p (`1080x1920`) $0.13, 1440p $0.19, 4K $0.30 — [LTX Pricing](https://docs.ltx.io/pricing)
- `ltx-2-5-pro`: 720p $0.12, 1080p $0.17, 1440p $0.25, 4K $0.39 — [LTX Pricing](https://docs.ltx.io/pricing)
- `ltx-2-3-fast`: 720p $0.03, 1080p $0.06, 1440p $0.12, 4K $0.24 — [LTX Pricing](https://docs.ltx.io/pricing)
- `ltx-2-3-pro`: 720p $0.04, 1080p $0.08, 1440p $0.16, 4K $0.32 — [LTX Pricing](https://docs.ltx.io/pricing)
- Billing is prepaid credits. Auto top-up requires at least one previous credit purchase; the threshold can be set from $10 to $10,000 and the top-up amount from $5 to $2,500 — [LTX Auto Top-Up](https://docs.ltx.io/auto-top-up)

**Limits, errors, moderation**
- Default concurrency is 2 simultaneous generations; ask sales for more. There is also a limit on queued async jobs. Exceeding either returns 429 (`rate_limit_error` / `concurrency_limit_error`, with `Retry-After`) — [LTX Rate Limits](https://docs.ltx.io/rate-limits)
- Errors: 402 `insufficient_funds_error`, 403 `permission_error`, 422 `content_filtered_error` ("Content rejected by safety filters"), 529 `overloaded_error` — [LTX Error Handling](https://docs.ltx.io/errors)

### Inferences
- For 6 s 1080x1920 I2V: `ltx-2-5-pro` $1.02/clip (**$10.20 per 10 clips**), `ltx-2-5-fast` $0.78 ($7.80), `ltx-2-3-pro` $0.48 ($4.80), `ltx-2-3-fast` $0.36 ($3.60). 6 s is the minimum allowed duration, so it fits exactly.
- With the default concurrency of 2, a 10-clip episode runs in about 5 waves.
- The hosted API cannot be told to use the full (non-distilled) model, a negative prompt or CFG. The LTX-2.5 page's mention of "a better distilled model" suggests distillation is part of the hosted pipeline, probably at least for Fast, but which checkpoint Fast and Pro run is not documented. This matches the project's reason for running its own Runpod endpoint (`--model dev` with a negative prompt). The hosted API trades those controls for 4K, 48/50 fps and native audio.
- "No text in frame" can only be enforced through the prompt and the source image.

### Gaps
- Output URL lifetime is not specified, only "expire independently".
- The minimum first purchase amount and the KYC/country rules for console.ltx.io were not found.
- No content policy specific to realistic historical people was found, nor anything about watermarking or C2PA.
- The queue limit value and the exact model checkpoint (distilled vs full) behind Fast and Pro are not documented.

## 3. Runway API — Gen-4.5, Gen-4 Turbo, Aleph 2.0 (plus resold third-party models)

### Takeaway
Runway API (`https://api.dev.runwayml.com`, `Authorization: Bearer`, required `X-Runway-Version: 2024-11-06`) bills $0.01 per credit with a $10 minimum purchase. Its first-party video models (**Gen-4.5** at 12 cr/s = $0.12/s and **Gen-4 Turbo** at 5 cr/s = $0.05/s) top out at **720x1280** for portrait image-to-video. Neither has a negative prompt or audio. Both accept `seed`, and moderation of public figures can be relaxed with `publicFigureThreshold`. Aleph 2.0 is video-to-video editing, not image-to-video. To get 1080x1920 on Runway you have to use resold third-party models (Grok Imagine, WAN 3.0, Seedance, HappyHorse, Veo 3.1…) or a paid upscale step.

### Cited Findings
**Host, auth, async**
- Base URL `https://api.dev.runwayml.com`. Header `Authorization: Bearer <key>`. Required on every request: `X-Runway-Version: 2024-11-06`. The SDKs `@runwayml/sdk` and `runwayml` read `RUNWAYML_API_SECRET` — [Runway AI context primer](https://docs.dev.runwayml.com/ai-context.md); [Runway Getting Started](https://docs.dev.runwayml.com/guides/using-the-api/)
- Submit with `POST /v1/image_to_video`, which returns `{id}`. Poll `GET /v1/tasks/{id}` ("should not expect updates more frequent than once every five seconds"). Statuses are `PENDING`, `THROTTLED`, `RUNNING`, `SUCCEEDED`, `FAILED` and `CANCELLED`. `DELETE /v1/tasks/{id}` cancels or deletes a task — [Runway API reference](https://docs.dev.runwayml.com/api.md)
- Output URLs "will expire within 24-48 hours; fetch the task again to get fresh URLs" — [Runway API reference](https://docs.dev.runwayml.com/api.md); [Runway Outputs](https://docs.dev.runwayml.com/assets/outputs/)

**Gen-4.5 image-to-video (`model: "gen4.5"`)**
- Fields: `promptText` (required, ≤1000 characters). `promptImage` (string, or an array of `{uri, position: "first"}`). `seed` (0–4294967295). `ratio` (required): one of `1280:720`, `720:1280`, `1104:832`, `960:960`, `832:1104`, `1584:672`. `duration` integer 2–10 (required). `contentModeration.publicFigureThreshold` set to `auto` or `low`. `outputFormat`: `mp4` (default H.264), `prores`, `png_sequence`, HDR profiles. `proresProfile` — [Runway API reference](https://docs.dev.runwayml.com/api.md)
- Per the inputs guide, Gen-4.5 I2V supports "Landscape `1280:720` `1584:672` `1104:832`, Portrait `720:1280` `832:1104` `672:1584` and Square `960:960`". The guide adds `672:1584`, which the generated API reference does not list (minor conflict). Gen-4.5 T2V is limited to `1280:720`/`720:1280` — [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)
- Prompt-image aspect ratio must be between 0.5 and 2 for Gen-4.5 (0.5–2.358 for Gen-4 Turbo). If the input does not match `ratio`, it is center-cropped — [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)
- The gen4.5 and gen4_turbo schemas have no `audio` or `negativePrompt` field. In Runway's I2V reference, `negativePrompt` appears only for `veo3.1` and `veo3.1_fast` (≤1000 characters, together with `audio` default `true` and `seed`) — [Runway API reference](https://docs.dev.runwayml.com/api.md)
- Pricing: `gen4.5` 12 credits/s, `gen4_turbo` 5 credits/s. Credits cost $0.01. ProRes/PNG output adds 5 cr/s and HDR profiles add 20 cr/s (Gen-4.5 and Aleph 2.0 only) — [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/)

**Gen-4 Turbo (`gen4_turbo`)**
- `promptText` is optional (≤1000). `promptImage` takes position `first` only. `seed`. `ratio` is one of `1280:720`, `720:1280`, `1104:832`, `832:1104`, `960:960`, `1584:672`. `duration` 2–10. `contentModeration.publicFigureThreshold` — [Runway API reference](https://docs.dev.runwayml.com/api.md)

**Aleph 2.0 (`aleph2`) and newer models**
- Aleph 2.0 is "Runway's flagship in-context video editing model with keyframe-guided control" at $0.28/s (28 cr/s, 56-credit minimum). It "preserves the input video's resolution (up to 1080p). Input videos must be 2–30 seconds and 30 FPS or lower." It is not an image-to-video model — [Runway Models](https://docs.dev.runwayml.com/guides/models/); [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/); [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)
- The current Runway catalog lists 44 models. The first-party video models are Gen-4.5, Gen-4 Turbo, Aleph 2.0 and Act-Two. I found no "Gen-5" or newer first-party video model. Third-party models resold through the same API include `seedance2_5`, `seedance2`, `wan3`, `wan3_prime`, `hailuo3`, `h3_max`, `grok_imagine_1_5`, `grok_imagine_1_5_lite`, `happyhorse_1_0`, `veo3.1`, `veo3.1_fast`, `gemini_omni_flash` and `gemini_omni_flash_1.1` — [Runway Models](https://docs.dev.runwayml.com/guides/models/)
- Resold models that offer 1080x1920 or 1080p I2V: `wan3` has a `ratio` that includes `1080:1920` and `auto_1080p`, an `audio` boolean and 2–30 s; it costs 20 cr/s at 1080p — [Runway API reference](https://docs.dev.runwayml.com/api.md); [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/). `happyhorse_1_0` I2V takes `resolution` `720P`/`1080P` and follows the image's aspect ratio; it costs 30 cr/s at 1080p — [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)
- Video upscale with `magnific_video_upscaler_creative` is billed per output frame: $0.007/frame at 720p/1k, $0.009 at 2k, $0.012 at 4k — [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/)

**Image input**
- `promptImage` accepts an HTTPS URL (≤16 MB; no redirects; the server must answer HEAD with a correct `Content-Type`), a data URI (≤5 MB encoded, about 3.3 MB binary), or a `runway://` ephemeral upload (≤200 MB, valid 24 h). Formats: JPEG, PNG, WebP. GIF is not supported — [Runway Inputs](https://docs.dev.runwayml.com/assets/inputs/)

**Billing, tiers, limits**
- "A minimum payment of $10 (at $0.01 per credit) is required to get started." Credits are bought per project in the developer portal. Sales tax may apply — [Runway Setup](https://docs.dev.runwayml.com/guides/setup/); [Runway Pricing](https://docs.dev.runwayml.com/guides/pricing/)
- Usage tiers are per model and per project. Tier 1 (new account): max concurrency 1–2, max 50–200 generations/day, $100/month spend cap. Tier 2 is reached right after $50 purchased (concurrency 3, $500/month). Tier 3 after $100 (concurrency 5). Tier 4 after $1,000 (10). Tier 5 after $5,000 (20). The Tier 1 cells list several values for different model groups, and the scrape did not show which value belongs to Gen-4.5 — [Runway Usage Tiers](https://docs.dev.runwayml.com/usage/tiers/)
- Tasks over the concurrency limit wait as `THROTTLED` and are queued automatically. There is "no maximum requests-per-minute limit". Going over the daily generation cap returns 429 — [Runway Usage Tiers](https://docs.dev.runwayml.com/usage/tiers/)

**Moderation**
- Moderation evaluates both the image and the text prompt. A moderated task returns `"status":"FAILED"` with `failure` and `failureCode`. "Moderated generations have the same credit cost as successful generations". Too many moderated requests lead to account suspension. The default is `auto`; `contentModeration.publicFigureThreshold: "low"` makes it "less strict about preventing generations that include recognizable public figures" — [Runway Content Moderation](https://docs.dev.runwayml.com/api-details/moderation/)
- A search snippet of an older Runway page says moderated generations are refunded. That conflicts with the current page, which says they are charged — [Runway usage/moderation (older page, per search snippet)](https://docs.dev.runwayml.com/usage/moderation); vs [Runway Content Moderation](https://docs.dev.runwayml.com/api-details/moderation/)

### Inferences
- Gen-4.5 I2V at the best portrait size (720x1280) for 6 s costs 72 credits = **$0.72/clip, $7.20 per 10 clips**. Gen-4 Turbo costs $0.30/clip. Neither reaches 1080x1920 natively, so the ≥1080x1920 requirement means either a paid upscale (Magnific "1k" at 6 s × 24 fps (fps assumed) × $0.007 ≈ $1.01) or a resold third-party model.
- Gen-4.5 has no negative prompt and no audio, so it suits silent b-roll, and "no text" has to go in the positive prompt.
- Runway's publicFigure setting is aimed at recognizable celebrities. Anonymous 1890s Kyrgyz people in traditional dress do not obviously fall under public-figure rules. The real risk is the generic image/text classifier, and moderated attempts are still charged and count toward suspension.

### Gaps
- Gen-4.5 and Gen-4 Turbo output fps and bitrate are not stated in the pages read.
- Which Tier 1 concurrency value (1 or 2) applies to Gen-4.5 is ambiguous in the scraped table.
- Supported billing countries and KYC: nothing found (search turned up no Runway-specific source).
- The categories of blocked content live in a Help Center FAQ that I did not read. Watermarking and C2PA for API outputs are not mentioned anywhere in the developer docs I read.

## 4. Availability for a US-based individual developer (signup, KYC, payment, region)

Correction from the coordinator: the developer is an individual based in the USA, not in Central Asia. The Central Asian aspect matters only for the subject matter of the clips (1890s Kyrgyz people), not for account access.

### Takeaway
All three providers are US companies or serve the US directly, and all use self-serve signup with prepaid credits on a card. None of the pages I read mentions business verification, KYC or an organization requirement for an individual. For a US individual the practical differences are the minimum first purchase (Runway $10; xAI and LTX not stated), US sales tax (explicitly mentioned by Runway), and the default concurrency (LTX 2, Runway Tier 1 is 1–2, xAI video has RPS limits and Imagine increases go through sales).

### Cited Findings
- xAI: "Sign up for an account at console.x.ai, then load it with credits to start using the API." Then create an API key on the API Keys page and use it as `XAI_API_KEY` — [xAI Quickstart (updated 2026-09-25)](https://docs.x.ai/developers/quickstart)
- xAI: rate-limit tier qualification is based on "total revenue received through prepaid credit purchases or successfully fulfilled invoices". Tier 1 starts at $50 cumulative spend, but tiers cover text, embedding and voice; Imagine limit increases go through sales@x.ai — [xAI Rate Limits](https://docs.x.ai/developers/rate-limits)
- xAI: a US regional endpoint (US inference, 1.1x token price) currently covers only `grok-4.7` and `grok-4.6`. It does not apply to video, and a US user does not need it for Imagine — [xAI Pricing](https://docs.x.ai/developers/pricing)
- xAI: the platform advertises SOC 2 Type II, GDPR, data residency and SSO/RBAC for enterprise. These are not requirements for an individual — [xAI Imagine overview](https://docs.x.ai/developers/model-capabilities/imagine)
- LTX: "Sign in to the Developer Console to create your API key" (console.ltx.io). Credits are prepaid. Auto top-up needs an existing payment method and at least one prior purchase (threshold $10–$10,000, top-up $5–$2,500). Postpaid/invoiced accounts exist ("Postpaid accounts hold nothing and are invoiced"). Enterprise plans go through sales — [LTX Quick Start](https://docs.ltx.io/quickstart); [LTX Auto Top-Up](https://docs.ltx.io/auto-top-up); [LTX-2.5](https://docs.ltx.io/models/ltx-2-5); [LTX Pricing](https://docs.ltx.io/pricing)
- Runway: sign up in the developer portal, create a project, then create an API key (shown once). "A minimum payment of $10 (at $0.01 per credit) is required to get started" — [Runway Setup](https://docs.dev.runwayml.com/guides/setup/)
- Runway: payment methods are added "through Stripe". Autobilling recharge must be at least 1,000 credits ($10), the balance is checked hourly, and "sales tax may be applied to the charge depending on your location". A new project starts at Tier 1 with a $100/month spend cap. It reaches Tier 2 immediately after $50 has been purchased, and Tier 3 after $100 — [Runway Autobilling](https://docs.dev.runwayml.com/usage/autobilling/); [Runway Usage Tiers](https://docs.dev.runwayml.com/usage/tiers/)
- Runway: the API is also sold through AWS Marketplace, an alternative way to pay for US users with AWS billing — [Runway docs navigation (Usage & Billing → AWS Marketplace)](https://docs.dev.runwayml.com/usage/aws-marketplace/)

### Inferences
- For a US individual, signup on all three should be a card-only self-serve flow. Budgeting the minimum spend: Runway $10 up front (plus applicable state sales tax). xAI and LTX require a prepaid purchase whose minimum the docs do not state.
- Runway's Tier 1 cap of $100/month and concurrency of 1–2 are enough for about 10 clips per episode. Buying $50–$100 lifts concurrency to 3–5 immediately.
- On LTX, automatic duration holds credits for the maximum duration. With fixed `duration: 6` this does not apply, so a small prepaid balance is enough.

### Gaps
- Minimum first credit purchase on console.x.ai and on console.ltx.io: not stated in the docs read.
- Whether xAI or LTX charges US sales tax: not stated.
- No explicit KYC or identity-verification statement was found for any of the three. Terms of Service pages (x.ai/legal, Runway and LTX terms) were not read, so lists of supported countries and age requirements remain unverified. For a US resident, country restrictions are very unlikely to apply, but that is an inference.
