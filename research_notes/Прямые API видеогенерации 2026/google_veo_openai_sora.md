# Google Veo (Gemini API and Vertex AI / "Gemini Enterprise Agent Platform") and OpenAI Sora 2: first-party video API facts as of October 2026

Research date: 2026-10-11. Direct HTTP from the dev container to ai.google.dev / platform.openai.com is blocked by the egress proxy, so official pages were fetched through a remote fetcher (TinyFish), and each was read in full or grep-searched. "Last updated" stamps are given where the page showed one. The user is a **US-based individual developer** (coordinator correction); region notes are written for the US.

**Headline findings (read first):**
1. **OpenAI Sora 2 / Sora 2 Pro are no longer available by API.** OpenAI shut down the Videos API and every `sora-2*` model on **2026-09-24** and named no replacement. Everything about Sora below is historical.
2. **Google now offers two video model families.** One is **Veo 3.1** (Standard / Fast / Lite, plus deprecated Veo 3). The other is the new **Gemini Omni Flash** (`gemini-omni-1.1-flash`, GA on the paid tier). Google now calls Omni Flash the *default* video model. No "Veo 4" exists in any official doc I fetched.
3. **Veo 3.1 cannot do 6 s at 1080p.** On every Veo 3.1 tier, both 1080p and 4k require `durationSeconds = "8"`. A 6 s clip at ≥1080×1920 therefore means either generating 8 s and trimming, or using Gemini Omni Flash, where 1080p is *upscaled*.
4. **The Gemini API has no free tier for Veo or Omni.** Tier 1, the new paid account, also has a **spend-based rate limit of $10 per rolling 10 minutes**. That allows only about three 8 s 1080p Veo 3.1 Standard clips per 10 minutes.

---

## 1. Official endpoints, API style, auth, and which models are offered

### Takeaway
Gemini API Veo uses `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:predictLongRunning`. You authenticate with the `x-goog-api-key` header and poll the operation it returns. Vertex Veo uses the same predictLongRunning pattern on `us-central1-aiplatform.googleapis.com`, with `Authorization: Bearer <OAuth token>`, and polls with `:fetchPredictOperation`. Gemini Omni Flash uses a different API, the **Interactions API** (`/v1beta/interactions`). The OpenAI Videos API (`api.openai.com/v1/videos`, Bearer auth) was shut down on 2026-09-24.

### Cited Findings
**Google: what is offered**
- The Gemini API "offers two models for generating video, Gemini Omni Flash and Veo." It says "Use Gemini Omni Flash as your default model for video generation… Use Veo 3.1 for specific capabilities like scene extension, last-frame control, or integration with legacy pipelines." (page last updated 2026-06-30) — [Gemini API: Video generation](https://ai.google.dev/gemini-api/docs/video)
- Gemini API Veo model list: **Veo 3.1 Preview** (latest update Jan 2026), **Veo 3.1 Fast Preview** (Jan 2026), **Veo 3.1 Lite Preview** (Mar 2026), **Veo 3 (Deprecated)** and **Veo 3 Fast (Deprecated)** (Jul 2025). All Veo 3.1 tiers have "Status: Preview". — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- The Gemini API code samples use the model ID `veo-3.1-generate-preview`. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- A developer forum post also cites `veo-3.1-lite-generate-preview` as a working Gemini API model ID (third-party/forum). — [Google AI dev forum, Jan 2026](https://discuss.ai.google.dev/t/veo-3-api-generate-audio-parameter-not-supported-last-frame-limitations/119206)
- Vertex model IDs are `veo-3.1-generate-001` (GA, released 2025-11-17, retirement "November 17, 2026 or later"), `veo-3.1-fast-generate-001` (GA, same dates) and `veo-3.1-lite-generate-001` (Preview, released 2026-04-02). Vertex marks retirement dates with this footnote: "Models may remain accessible through the Gemini API after these dates." (page last updated 2026-10-10) — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- Vertex has been rebranded "Gemini Enterprise Agent Platform". Docs now redirect to `docs.cloud.google.com/gemini-enterprise-agent-platform/...`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Gemini Omni Flash is model `gemini-omni-1.1-flash`. It is described as "Our next-generation video generation and editing model, now generally available to developers on the paid tier of the Gemini API." A `gemini-omni-flash-preview` also exists. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- On Vertex, the Omni model ID listed for image-to-video is `gemini-omni-1.1-flash-preview`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)

**Google: endpoints and auth**
- Gemini API REST sample: `BASE_URL="https://generativelanguage.googleapis.com/v1beta"`, then `curl "${BASE_URL}/models/veo-3.1-generate-preview:predictLongRunning" -H "x-goog-api-key: $GEMINI_API_KEY"` with body `{"instances":[{"prompt":…}],"parameters":{…}}`. Polling is `GET ${BASE_URL}/${operation_name}` until `.done == true`. The video URI is at `.response.generateVideoResponse.generatedSamples[0].video.uri`, and you download it with `curl -L -H "x-goog-api-key: …"`. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Vertex Veo submit is `POST https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/publishers/google/models/MODEL_ID:predictLongRunning` with `-H "Authorization: Bearer $(gcloud auth print-access-token)"`. You poll with `POST …/MODEL_ID:fetchPredictOperation` and body `{"operationName": "projects/…/operations/OPERATION_ID"}`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Gemini API Omni Flash is `POST https://generativelanguage.googleapis.com/v1beta/interactions?key=$API_KEY` with body `{"model":"gemini-omni-1.1-flash","input":"…","response_format":{"type":"video","aspect_ratio":"9:16"}}`. — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Vertex Omni is `POST https://aiplatform.googleapis.com/v1beta1/projects/PROJECT_ID/locations/global/interactions` with `Authorization: Bearer TOKEN`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)

**OpenAI**
- "The Sora 2 models and Videos API were shut down on September 24, 2026 and are no longer available. No one-to-one replacement API is available. This guide is retained for historical reference." — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)
- Deprecations page (notice dated 2026-03-24): shutdown on 2026-09-24 of the "Videos API", `sora-2`, `sora-2-pro`, `sora-2-2025-10-06`, `sora-2-2025-12-08` and `sora-2-pro-2025-10-06`. The recommended replacement is "—". — [OpenAI Deprecations](https://platform.openai.com/docs/deprecations)
- Historical API shape: `POST https://api.openai.com/v1/videos` with `-H "Authorization: Bearer $OPENAI_API_KEY"`, sent as multipart or JSON. Fields were `model`, `prompt`, `size`, `seconds` and `input_reference`. Other endpoints: `GET /videos/{id}`, `GET /videos/{id}/content`, `/v1/videos/extensions`, `/v1/videos/edits` and `/v1/videos/characters`. — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)
- The openai.com/api/pricing page now renders only ChatGPT Business seat pricing. No Sora pricing was present when fetched. — [openai.com/api/pricing](https://openai.com/api/pricing/)

### Inferences
- For a new integration in October 2026, only Google offers a first-party API among the two providers. OpenAI is out.
- The Gemini API Fast model ID is probably `veo-3.1-fast-generate-preview`, following the pattern of the Standard and Lite IDs. The ID cell was empty in the fetched copy of the page, so confirm it with `models.list` before use.
- Veo 3.1 on the Gemini API is still labelled **Preview** after about a year. Preview models carry stricter rate limits ("Rate limits are more restricted for experimental and preview models" — [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).

### Gaps
- The exact Gemini API model ID for Veo 3.1 Fast was not captured; the page rendered it in a tab that the fetcher dropped.
- I found no official statement on whether Gemini Omni Flash on the Gemini API is synchronous or async by default. The docs mention `background`, `store` and `stream` flags, and an asynchronous section exists on Vertex.

---

## 2. Image-to-video: first frame, last frame, reference images, and how images are passed

### Takeaway
All Veo 3.1 tiers accept a first-frame `image` and an optional `lastFrame` for interpolation. Veo 3.1 Standard and Fast, but not Lite, also accept up to 3 `referenceImages` ("asset"). On the Gemini API, images go inline as base64 (`inlineData {mimeType, data}`). On Vertex they go as `bytesBase64Encoded` + `mimeType` (JPEG/PNG, max 20 MB). Omni Flash takes images as base64 parts in an `input` array, and you set their roles with `<FIRST_FRAME>`/`<LAST_FRAME>`/`<IMAGE_REF_N>` tags.

### Cited Findings
- Gemini API parameter table: `image` is "An initial image to animate". `lastFrame` is "The final image for an interpolation video… Must be used in combination with the `image` parameter" and is supported on Veo 3.1, 3.1 Fast and 3.1 Lite. `referenceImages`, "Up to three images to be used as style and content references", is supported on Veo 3.1 and 3.1 Fast and is "n/a" on Lite. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Gemini API REST shapes: `"image": {"inlineData": {"mimeType": "image/png", "data": "<base64>"}}` and `"lastFrame": {"inlineData": {...}}` inside `instances[0]`. For references: `"referenceImages": [{"image": {"inlineData": {...}}, "referenceType": "asset"}]`. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- "Veo uses the input image as the initial frame." With reference images: "Provide up to three asset images of a single person, character, or product. Veo preserves the subject's appearance in the output video." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- On Vertex, `INPUT_IMAGE` is "A base64-encoded string… For best quality, we recommend that the input image's resolution be 720p (1280 x 720 pixels) or higher, and have an aspect ratio of either 16:9 or 9:16. Images of other aspect ratios or sizes may be resized or centrally cropped". MIME types are `image/jpeg` and `image/png` only. The `resizeMode` parameter takes `"crop"` or `"pad"`. The body shape is `"image": {"bytesBase64Encoded": "...", "mimeType": "..."}`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- On Vertex, the "Image-to-video maximum input image size" is 20 MB. Veo 3.1 Standard/Fast list "Text to video, image to video, from first and last frame: Supported" and "Use reference images: Asset images Supported". For Veo 3.1 Lite, the Vertex page says reference images are "Not supported". The same page lists image as "Not supported" in Lite's modality row while listing image-to-video as supported under capabilities, which is an internal inconsistency on the page. — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- On Vertex, "reference image to video only supports 8 seconds" (Veo 3.1). — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- Forum report (Jan 2026, Vertex `veo-3.1-fast-generate-001`): using `last_frame` with a 4 s duration returned "Your use case is currently not supported". This is unofficial and anecdotal. — [Google AI dev forum](https://discuss.ai.google.dev/t/veo-3-api-generate-audio-parameter-not-supported-last-frame-limitations/119206)
- Omni Flash (Gemini API): images are passed as `{"type": "image", "data": "<base64>", "mime_type": "image/jpeg"}` items in `input`. "Depending on your prompt, the model will decide how to use the image". You can force the behavior with `video_config.task` = `image_to_video` / `text_to_video` / `reference_to_video` / `edit` / `extend`. Role tags are `<FIRST_FRAME>`, `<LAST_FRAME>`, `<IMAGE_REF_N>` and `<VIDEO_REF_N>`. First/last-frame interpolation is supported. — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- On Vertex, Omni takes the image as `{"type":"image","uri":"gs://…","mime_type":"image/png"}`, a Cloud Storage URI. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Sora (historical): "an input image, which acts as **the first frame of your video**". The image was passed as `input_reference`, either a multipart upload or JSON `{file_id | image_url}`. "The image must match the target video's resolution (`size`)." Accepted types were JPEG, PNG and WebP. There was no last-frame option. — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- For a 9:16 first frame on Veo, supply the image already at 9:16 and ≥720×1280. Otherwise Vertex will crop or pad it, and the Gemini API probably behaves the same way, though that is undocumented.
- The Gemini API Veo docs show only inline base64 for images, with no URL or file-upload form. A ~1080×1920 PNG adds a few MB to the JSON request.

### Gaps
- I found no official statement of a maximum input-image size or accepted MIME types for the Gemini API, as opposed to Vertex.
- Whether Vertex Veo also accepts `gcsUri` for input images was not shown in the fetched page.

---

## 3. Resolutions, 9:16, and 1080×1920

### Takeaway
Veo 3.1 Standard and Fast output 720p (default), 1080p or 4k. Lite outputs 720p or 1080p. Both 9:16 and 16:9 are supported, but **1080p and 4k require an 8 s duration**, and video extension is 720p only. Unlike old Veo 3, Veo 3.1 does not restrict 1080p to 16:9. Omni Flash offers 360p, 720p (default), 1080p and 4k, but 1080p and 4k are documented as **upscaled**.

### Cited Findings
- Gemini API `resolution` values for Veo 3.1 and 3.1 Fast: `"720p"` (default), `"1080p"` (only supports 8s duration), `"4k"` (only supports 8s duration), and `"720p"` only for extension. Veo 3.1 Lite: `"720p"` (default) and `"1080p"` (only supports 8s duration). — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Gemini API `aspectRatio`: `"16:9"` (default) or `"9:16"` for all of Veo 3.1, Fast, Lite and Veo 3. The model-features table lists resolution as "720p, 1080p (8s length only), 4k (8s length only)" for Veo 3.1/Fast, but "720p & 1080p (16:9 only)" for **Veo 3 & Veo 3 Fast**. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Third-party LiteLLM docs state "1080p (Veo 3.1 only, 16:9 aspect ratio only)". This conflicts with the current official table, which puts the 16:9-only limit on Veo 3, not 3.1. — [LiteLLM docs (third-party)](https://docs.litellm.ai/docs/providers/gemini/videos); contradicted by [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Google blog (Jan 13, 2026): Veo 3.1 added native portrait mode for "Ingredients to Video", generating full-frame vertical video rather than cropping from landscape, plus "crisp 1080p". This comes from a search-result summary; I did not fetch the blog page itself. — [Google blog: Veo 3.1 Gemini API](https://blog.google/innovation-and-ai/technology/developers-tools/veo-3-1-gemini-api/)
- Vertex, per model: Veo 3.1 supports aspect ratios 9:16 and 16:9, output resolutions 720p, 1080p and 4K, and input resolutions 720p and 1080p. Veo 3.1 Fast and Lite list output resolutions of 720p and 1080p only; no 4K is listed on the Vertex page for Fast. — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- This conflicts with Vertex pricing, which lists 4k SKUs for Veo 3.1 Fast ($0.30/s with audio). Both are official Vertex pages. — [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Omni Flash `resolution` (inside `response_format`) takes `360p`, `720p` (default), `1080p` "1080p output (upscaled)" or `4k` "4K output (upscaled)". `aspect_ratio` is `"9:16"` or `"16:9"`, with 16:9 the default. — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- On Vertex, `gemini-omni-flash-preview` "only supports `720p`", while `gemini-omni-1.1-flash-preview` supports 360p, 720p, 1080p and 4k. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Sora (historical): "Use `sora-2-pro` when you need 1080p exports in `1920x1080` or `1080x1920`." — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- "1080p" at 9:16 almost certainly means 1080×1920 output, but no fetched Google page states the pixel dimensions explicitly. Verify with ffprobe on the first output.
- For the Omni Flash 1080p option, expect upscaled 720p (≈720×1280 → 1080×1920) rather than native 1080p detail.

### Gaps
- No official pixel dimensions are published for Veo 3.1 9:16 1080p or 4k output.

---

## 4. Durations and frame rate

### Takeaway
Veo 3.1 (all tiers) offers 4, 6 or 8 s at 24 fps. Exactly 8 s is required for 1080p, 4k, reference images and extension. Omni Flash offers 3–10 s (documented on Vertex) at 24 fps, judging by the 24 fps reference in its prompt guide. Sora historically offered up to 20 s.

### Cited Findings
- Gemini API `durationSeconds`: `"4"`, `"6"` or `"8"`. It "Must be "8" when using extension, reference images or with 1080p and 4k resolutions" for Veo 3.1/Fast, and "Must be "8" when using reference images or with 1080p" for Lite. Frame rate is **24fps** for every model. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- On Vertex, Veo 3.1 video lengths are "4, 6, or 8 seconds; reference image to video only supports 8 seconds". The frame rate is "24 FPS" and the MIME type is `video/mp4`. Vertex `DURATION` takes "Veo 3 models: `4`, `6`, or `8`. The default is `8`." — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate); [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Vertex Omni `DURATION`: "Allowed strings are integers between `3` and `10`, followed by "s" for seconds. For example, `"10s"`." — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Omni extension "can extend videos by 10s, up to a total length of 40s". The prompt guide mentions "12 frames at 24fps". — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Sora (historical): "Both `sora-2` and `sora-2-pro` support `16`- and `20`-second generations". Examples used `seconds: "8"`. Extensions could add up to 20 s each, to a maximum of 120 s. — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- Six seconds is a native Veo 3.1 option only at 720p. At 1080p you pay for 8 s and trim.

### Gaps
- The Gemini API Omni page (as fetched) did not show a `duration` field in the visible prose. Whether `response_format.duration` works on the Gemini API, as it does on Vertex, needs a test call.

---

## 5. Negative prompt, seed, and prompt enhancement

### Takeaway
Vertex Veo documents `negativePrompt` and `seed` (uint32). The current Gemini API Veo parameter table **does not list** `negativePrompt` and mentions `seed` only as "available, doesn't guarantee determinism". Gemini Omni Flash explicitly does **not** support negative prompts. I found no prompt-enhancement toggle (`enhancePrompt`) in the current official pages.

### Cited Findings
- Vertex optional `parameters`: `"aspectRatio"`, `"negativePrompt"` ("A string value that describes content that you want to prevent the model from generating"), `"personGeneration"`, `"resolution"`, `"sampleCount"` (1–4) and `"seed"`. The seed is "An uint32 value… Specifying a seed number with your request without changing other parameters guides the model to produce the same videos. The accepted range of values is `0`-`4294967295`." — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- The Gemini API Veo parameter table lists only `prompt`, `image`, `lastFrame`, `referenceImages`, `video`, `aspectRatio`, `durationSeconds`, `personGeneration` and `resolution`. It adds: "Note that the seed parameter is also available for Veo 3 models. It doesn't guarantee determinism, but slightly improves it." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Omni Flash: "System instructions, temperature, `top_p`, stop sequences, and negative prompts are not supported (you can put your negatives in the regular prompt: e.g., "Do not do X")." The prompt guide suggests "No dialogue", "No extra sound effects", and so on. — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Omni Flash renders text well and readably, and the docs encourage prompting for text. This is the opposite of what this use case needs; suppress it by prompting for "no text". — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Sora (historical): the documented request fields had no negative-prompt or seed parameter. — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- On the Gemini API, `negativePrompt` may still be accepted, since earlier Veo docs and SDKs had it, but it is not documented as of October 2026. Test it, and if it is rejected, fall back to "no text, no captions, no subtitles" wording in the main prompt. Vertex is the path where `negativePrompt` is officially documented.

### Gaps
- Whether the Gemini API currently accepts `negativePrompt` for `veo-3.1-*-preview` is unconfirmed.
- I found no current official documentation of `enhancePrompt`, a prompt-rewriter toggle, for Veo 3.1 on either surface.

---

## 6. Audio generation and disabling it

### Takeaway
On the **Gemini API**, Veo 3.1 audio is "Always on" and priced only as "video with audio". On **Vertex**, separate cheaper "Video generation" (no audio) SKUs exist, roughly 20–50% less. That implies audio can be disabled there, but the parameter name was not documented in the pages I fetched. Omni Flash always generates an audio track unless you prompt otherwise.

### Cited Findings
- Gemini API model-features table: "Audio: Natively generates audio with video. ✔️ Always on" for Veo 3.1, 3.1 Fast, 3.1 Lite and Veo 3. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Gemini API pricing lists only "video with audio price (default)" rows for Veo 3.1 Standard, Fast and Lite. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Vertex pricing has separate rows. Veo 3.1 "Video + Audio generation" costs $0.40 (720p, 1080p) and $0.60 (4k); "Video generation" costs $0.20 (720p, 1080p) and $0.40 (4k). Veo 3.1 Fast with audio is $0.10/$0.12/$0.30 versus video-only $0.08/$0.10/$0.25 (720p/1080p/4k). Veo 3.1 Lite with audio is $0.05/$0.08 versus video-only $0.03/$0.05 (720p/1080p). — [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Forum (Jan 2026, unofficial): on Vertex, `generate_audio=False` returned "generate_audio parameter is not supported in Gemini API". The error likely came from the SDK being pointed at the Gemini API backend. A second user reported that on the public Gemini API, `generateAudio` was rejected for `veo-3.1-generate-preview` and `veo-3.1-lite-generate-preview`. That user also saw outputs with no audio track, which contradicts the docs' "Always on". — [Google AI dev forum](https://discuss.ai.google.dev/t/veo-3-api-generate-audio-parameter-not-supported-last-frame-limitations/119206)
- Gemini API: "Veo 3.1 will sometimes block a video from generating because of safety filters or other processing issues with the audio. You will not be charged if your video is blocked from generating." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Omni Flash: "By default the model will try to generate an appropriate audio track for a video." Omni pricing is "for video outputs (with audio)". — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni); [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

### Inferences
- If the pipeline discards generated audio, as a narrated episode with its own voiceover would, Vertex video-only SKUs halve the Veo 3.1 Standard cost. The parameter is very likely `generateAudio: false` on Vertex; verify it, because the forum thread shows confusion.
- On the Gemini API you pay the "with audio" price regardless, and can strip audio with FFmpeg.

### Gaps
- The exact Vertex parameter for disabling audio is not shown in the official pages fetched. The `turn-off-audio` doc URL I tried returned 404.

---

## 7. Pricing, free tier, and rate limits for a new paid account

### Takeaway
**Gemini API, per second, with audio, paid tier only, no free tier:**

| Model | 720p | 1080p | 4k |
|---|---|---|---|
| Veo 3.1 Standard | $0.40 | $0.40 | $0.60 |
| Veo 3.1 Fast | $0.10 | $0.12 | $0.30 |
| Veo 3.1 Lite | $0.05 | $0.08 | n/a |

**Vertex** charges the same with-audio prices and adds cheaper video-only SKUs. **Omni Flash** is billed by output tokens: about $0.10/s at 720p and, by calculation, about $0.152/s at 1080p. A new Gemini API paid project (Tier 1) is capped at **$10 of spend per rolling 10 minutes** and has a **$250 billing-tier cap**.

### Cited Findings
- Gemini API: "Veo 3.1 Standard video with audio price (default) | Not available | $0.40 (720p and 1080p) $0.60 (4k)". "Veo 3.1 Fast… $0.10 (720p) $0.12 (1080p) $0.30 (4k)". "Veo 3.1 Lite… $0.05 (720p) $0.08 (1080p) (4k output not supported)". The Free Tier column reads "Not available". — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Gemini API Omni Flash (`gemini-omni-1.1-flash`): input costs $1.50 per 1M tokens and output $17.50 per 1M tokens of video. "Billing is based on total output token consumption, calculated at a rate of 5,792 tokens per second of 720p video. Under Standard pricing, this equates to an effective price of approximately $0.10 per second." Free tier: "Not available". — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Vertex Omni: "1931 tokens per second of 360p video, 5792 tokens per second of 720p video, 8688 tokens per second of 1080p video, and 17376 tokens per second of 4k video for video outputs (with audio)". The video output price is $17.50 per 1M tokens. Input images cost 1120 tokens each. — [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Vertex Veo prices are labelled "$X / 1 count". The values match the Gemini API's per-second prices. The video-only rows are Veo 3.1 at $0.20 (720p/1080p) and $0.40 (4k), Fast at $0.08/$0.10/$0.25, and Lite at $0.03/$0.05. — [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Gemini API paid tier: "Batch API (50% cost reduction)" is listed as a general paid-tier feature. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Gemini API usage tiers: **Free** requires an "Active project or free trial". **Tier 1** requires you to "Set up and link an active billing account" and has a $250 billing-tier cap. **Tier 2** requires "Paid $100 + 3 days from first successful payment" and has a $2,000 cap. **Tier 3** requires "Paid $1,000 + 30 days" and has a cap of $20,000–$100,000+. — [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- Spend-based rate limits per rolling 10 minutes: Tier 1 **$10**, Tier 2 $50, Tier 3 $200. Exceeding the limit returns `429 RESOURCE_EXHAUSTED`. "Rate limits are applied per project, not per API key." Per-model RPM/RPD values are not published on the page; the docs say "can be viewed in Google AI Studio". "Rate limits are more restricted for experimental and preview models." — [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- Vertex Veo 3.1 consumption options: "Provisioned Throughput Supported · Batch inference Not supported · Pay-as-you-go Not supported · Fixed quota Supported". The quota is "Regional online prediction requests per base model per minute per base model: 50", though the page renders the unit as "tokens per minute". The only region is `us-central1`. — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- Sora (historical, third-party, since the official page is gone): sora-2 cost $0.10/s at 720p. sora-2-pro cost $0.30/s at 720p, $0.50/s at 1024×1792 (or 1792×1024), and $0.70/s at 1080p. — [CostGoat (third-party)](https://costgoat.com/pricing/sora); [aifreeapi (third-party)](https://www.aifreeapi.com/en/posts/cheapest-sora-2-api). The earlier $0.10/$0.30/$0.50 table is at [eesel.ai (third-party, 2025)](https://www.eesel.ai/blog/sora-2-in-the-api-pricing).

### Inferences
- **Cost per 6 s, 9:16 clip at ≥1080p.** Veo 3.1 bills an 8 s render because 1080p requires it.
  - Gemini API: Standard 8×$0.40 = **$3.20**, Fast 8×$0.12 = **$0.96**, Lite 8×$0.08 = **$0.64**.
  - Vertex video-only: Standard $1.60, Fast $0.80, Lite $0.40.
  - Omni Flash at 1080p (upscaled), 6 s: 6×8688×$17.50/1M ≈ **$0.91**. At 720p, 6 s: ≈ $0.61.
- **Per episode of about 10 clips, first takes only:**
  - Veo 3.1 Standard: about $32 on the Gemini API, or $16 video-only on Vertex.
  - Fast: about $9.60, or $8 on Vertex.
  - Lite: about $6.40, or $4 on Vertex.
  - Omni 1080p: about $9.10.
  - Rerolls multiply these numbers.
- **The Tier 1 spend limit throttles batch rendering.** $10 per 10 minutes allows only about 3 Veo 3.1 Standard 1080p clips, about 10 Fast clips, or about 15 Lite clips per 10-minute window. An episode of 10 Standard clips takes about 40 minutes or more on Tier 1. Tier 2 arrives after $100 spent plus 3 days.
- On Vertex, the model page says "Pay-as-you-go: Not supported" for Veo 3.1, which seems to require fixed quota or Provisioned Throughput. This may be a rendering artifact of the rebranded page. Treat Vertex self-serve access as unverified until tested.

### Gaps
- Per-model RPM/RPD for Veo on the Gemini API is not published; it appears only in AI Studio for the project.
- Whether Batch (50% off) applies to Veo or Omni video on the Gemini API was not confirmed.
- The exact meaning of Vertex's "count" unit (presumably per second) is not spelled out on the fetched page. The per-second interpretation rests on the values matching the Gemini API's per-second prices.

---

## 8. Async job pattern, retention, and output format

### Takeaway
Veo works as follows: submit to predictLongRunning, receive an operation `name`, poll until `done: true`, then download the MP4 from `generatedSamples[0].video.uri` with the API key. Generated files are **deleted after 2 days**. Latency runs from 11 s to 6 min. Vertex can write output directly to `gs://` via `storageUri`. Omni Flash returns base64 MP4 inline, or a URI if you request `delivery:"uri"`. Sora used queued → in_progress → completed and offered 1-hour download URLs.

### Cited Findings
- "When you send a request to the API, it starts a long-running job and immediately returns an `operation` object. You must then poll until the video is ready, which is indicated by the `done` status being true." The samples poll every 10 s. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- "Request latency: Min: 11 seconds; Max: 6 minutes (during peak hours)." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- "Video retention: Generated videos are stored on the server for 2 days, after which they are removed… Extended videos are treated as newly generated videos." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Gemini API: "Videos per request: 1" for all Veo models. Text input is limited to 1,024 tokens. Output is "Video with audio". — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Vertex: `storageUri` is "Optional… the Cloud Storage bucket to store the output videos. If not provided, video bytes are returned in the response". Up to 4 videos per prompt (`sampleCount` 1–4). The MIME type is `video/mp4`. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image); [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- Omni Flash REST response: the `steps[]` entry with `"type": "model_output"` contains `{"type":"video","mime_type":"video/mp4","data":"<base64>"}`. "Use the `delivery="uri"` parameter in `response_format` to retrieve generated videos that are larger than 4MB. This returns a Google-hosted URI that you can poll until the video is `ACTIVE`". For faster synchronous generation, set `background=false, store=false, stream=false`. — [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Sora (historical): statuses were `queued`, `in_progress`, `completed` and `failed`, with `video.completed`/`video.failed` webhooks available. You downloaded via `GET /videos/{id}/content` (with variants `thumbnail`/`spritesheet`). "Download URLs are valid for a maximum of 1 hour after generation." Batch outputs were available for 24 h. — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- With 2-day retention, the pipeline must download immediately into its own storage; this fits the project's WORKDIR + cleanup pattern.
- A 1080p 9:16 Omni clip will exceed 4 MB, so plan for `delivery: "uri"` from the start.

### Gaps
- I found no documented Gemini API webhook or callback for Veo operations; polling appears to be the only path.

---

## 9. Content restrictions: realistic historical people, person generation, and watermarking

### Takeaway
For a **US developer**, Veo allows people. Text-to-video uses `personGeneration: "allow_all"`, and image-to-video, interpolation and reference images require `"allow_adult"`, so children cannot be animated from an input image. The extra EU/UK/CH/MENA restriction does **not** apply in the US. Anonymous 1890s Central Asian (Kyrgyz) people in traditional dress are not "prominent persons", so the celebrity filter should not trigger. Generic safety filters still apply. All Veo and Omni output carries an invisible **SynthID** watermark. Vertex additionally supports **C2PA Content Credentials**. No visible watermark is documented. Sora rejected any input image with a human face, which would have ruled it out for this use case.

### Cited Findings
- Gemini API `personGeneration` for Veo 3.1/Fast: "Text-to-video & Extension: `"allow_all"` only. Image-to-video, Interpolation, & Reference images: `"allow_adult"` only." Lite follows the same split. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- "Regional limitations: In EU, UK, CH, MENA locations, `allow_adult` is the only allowed value for `personGeneration`." The US is not in this list. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Vertex `personGeneration` values: `"allow_adult"` (default), "Only allow generation of adult people and faces", and `"disallow"`, "Doesn't generate people or faces". — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image)
- Vertex safety codes:
  - **Child** (`58061214`, `17301594`): "Rejects requests to generate content depicting children if `personGeneration` isn't set to `"allow_all"` or if the project isn't on the allowlist for this feature."
  - **Celebrity** (`29310472`, `15236754`): "Rejects requests to generate a photorealistic representation of a prominent person or if the project isn't on the allowlist."
  - Other categories: Violence, Sexual, Hate, Dangerous, Toxic, Vulgar, Prohibited content, and "Third-party content".
  - "If fewer videos than requested are returned, then some generated output is being blocked."
  - (page last updated 2026-10-09) — [Vertex: Responsible AI for Veo](https://cloud.google.com/vertex-ai/generative-ai/docs/video/responsible-ai-and-usage-guidelines)
- Gemini API: "Generated videos are passed through safety filters and memorization checking processes that help mitigate privacy, copyright and bias risks." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Watermarking, Gemini API: "Videos created by Veo are watermarked using SynthID… Videos can be verified using the SynthID verification platform." — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Watermarking, Vertex: Veo 3.1, Fast and Lite list "Content Credentials (C2PA) Supported". — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- Omni Flash:
  - "All generated videos include SynthID watermarking, which is invisible to viewers."
  - "Uploading and editing images containing certain recognizable people is not supported."
  - "Uploading and editing images containing minors is not supported in European Economic Area, Switzerland, and the United Kingdom."
  - "Omni applies content safety filters… (which vary by region)."
  - Omni touts "Gemini's knowledge of history, science, and cultural context".
  - [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
- Sora (historical): "Real people—including public figures—cannot be generated." "Input images with faces of humans are currently rejected." The API also enforced "Only content suitable for audiences under 18". — [OpenAI: Video generation guide](https://platform.openai.com/docs/guides/video-generation)

### Inferences
- Photorealistic first frames of anonymous adult 1890s Kyrgyz herders, elders or women in traditional dress should pass Veo image-to-video with `allow_adult` from the US. If the first frame contains children, the request will be rejected on image-to-video.
- Generated, non-identifiable faces should not trigger the "recognizable people" filter in Omni or the "prominent person" filter in Veo. Archival photos of real, identifiable historical individuals could trigger it, especially in Omni.
- SynthID is invisible, so "no text in frame" is not threatened by a visible watermark. Text-free frames still have to be enforced through the prompt, and through `negativePrompt` on Vertex.

### Gaps
- I found no official per-country list beyond "EU, UK, CH, MENA" for personGeneration. The US is assumed unrestricted beyond the default image-to-video `allow_adult` rule.
- Whether Gemini API Veo output also carries C2PA metadata is not stated on the Gemini API pages.

---

## 10. Availability for an individual developer in the USA

### Takeaway
A US individual can use the Gemini API with a Google account (18+). Creating a key in AI Studio and linking a Cloud billing account gives Tier 1, and Veo and Omni are paid-tier only. No organization or KYC verification step is documented for Veo on the Gemini API. Vertex requires a GCP project with billing and OAuth credentials, and Veo is served only from `us-central1`. OpenAI's video API is no longer available to anyone.

### Cited Findings
- The **United States** is on the list of countries where the Gemini API and Google AI Studio are available (page last updated 2026-04-28). The page also lists the age requirement: "You do not meet the minimum age requirement (18+)", together with Google Account age verification. — [Gemini API available regions](https://ai.google.dev/gemini-api/docs/available-regions)
- Tier 1 requires you to "Set up and link an active billing account". Veo and Omni have a free tier of "Not available", so billing is mandatory. The pricing page describes the model as "prepaid then pay-as-you-go pricing". — [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits); [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Upgrades are not automatic in every case: "in rare cases an upgrade request may be denied based on other factors identified during the review process." — [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- On the paid tier, content is "not used to improve our products". On the free tier it is. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Vertex Veo 3.1 model availability is "United States: `us-central1`". Security controls include data residency, CMEK and VPC-SC. — [Vertex: Veo 3.1 model page](https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate)
- OpenAI: the Sora 2 models and Videos API were shut down on 2026-09-24. — [OpenAI Deprecations](https://platform.openai.com/docs/deprecations)

### Inferences
- The shortest path for this project is a Gemini API key with linked billing and `x-goog-api-key`. This mirrors the existing `scripts/grok_video.py` pattern of a single key and a single host. Vertex adds OAuth/service-account setup in exchange for `negativePrompt`, video-only pricing and `gs://` output.
- "Prepaid then pay-as-you-go" suggests new accounts may need to load credit before the first Veo call.

### Gaps
- I found no official statement on whether new US Gemini API accounts must prepay, or on the minimum prepay amount.
- OpenAI organization verification requirements for Sora are now moot and were not researched.
- Whether Vertex Veo 3.1 is truly unavailable on pay-as-you-go for a new self-serve GCP project (as the model page says) could not be confirmed without a test.

---

## 11. Fit for this use case: about 10 clips per episode, each a 6 s 9:16 image-to-video clip at ≥1080×1920 with a negative prompt and no on-screen text

### Takeaway
No current first-party option meets every requirement natively. Veo 3.1 gives native 1080p 9:16 image-to-video, but only at 8 s, so you trim to 6 s. A negative prompt is documented only on Vertex. Omni Flash gives 6 s 9:16 at "1080p", but that resolution is upscaled and it has no negative-prompt parameter. Sora is gone.

### Cited Findings
- Veo 3.1 constraints: 1080p requires 8 s; 9:16 is supported; image-to-video requires `allow_adult`; output is 24 fps MP4. — [Gemini API: Veo 3.1](https://ai.google.dev/gemini-api/docs/veo)
- Vertex Veo: `negativePrompt`, `seed`, `sampleCount` up to 4, `resizeMode` crop/pad, `storageUri`, and video-only pricing ($0.20/s Standard, $0.10/s Fast, $0.05/s Lite at 1080p). — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image); [Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Omni Flash: 3–10 s duration (on Vertex); 1080p is "upscaled"; there is no negative-prompt parameter; it renders text readily when prompted. — [Vertex: Generate videos from an image](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos-from-an-image); [Gemini API: Omni Flash](https://ai.google.dev/gemini-api/docs/omni)

### Inferences
- **Recommended trial order:**
  - (a) **Veo 3.1 Fast** at 1080p, 9:16, 8 s, with a first frame, trimmed to 6 s with FFmpeg. It costs about $0.96 per clip on the Gemini API (about $9.60 per episode), and $0.80 per clip video-only on Vertex.
  - (b) **Veo 3.1 Lite** (about $0.64, or $0.40 on Vertex) as the cheap draft tier.
  - (c) **Veo 3.1 Standard** (about $3.20 per clip) only for hero shots.
- Omni Flash at 6 s is cost-comparable (about $0.91 per clip at 1080p), but it upscales and tends toward multi-shot cuts unless prompted "single continuous shot, no scene cuts".
- To keep frames text-free on the Gemini API, put "no text, no captions, no subtitles, no signage, no watermark" into the main prompt, because `negativePrompt` is not documented there. On Vertex, also pass it as `negativePrompt`.
- Throughput: on Gemini API Tier 1, the $10 per 10 minutes spend limit allows about 10 Veo 3.1 Fast 1080p clips per 10 minutes, so one episode per window at first-take rates.

### Gaps
- No official confirmation that Veo 3.1 9:16 1080p output is exactly 1080×1920.
- No official evidence on how well Veo 3.1 avoids rendering incidental text such as signage when there is no negative-prompt parameter.
