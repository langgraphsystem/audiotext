# Прямые API видеогенерации: Kling, MiniMax Hailuo, Vidu (состояние на октябрь 2026)

> Method note (read first): the official doc sites (platform.minimax.io, platform.vidu.com, kling.ai / app.klingai.com) could not be fetched directly from this environment: WebFetch got DNS failures and curl got proxy 403. Every "official" fact below comes from search-engine extracts of official pages. The extracts are paraphrases and sometimes truncated, so treat exact numbers as "seen on the official page per search extract" and re-check them live before committing money. Third-party sources are marked **[3P]**. Where the search engine gave a page's age, the date is noted.
>
> Use case for the calculations: 6 s, 9:16, image-to-video (I2V), ≥1080×1920, negative prompt, no text in frame, ~10 clips per episode.

## 1. Kuaishou Kling: endpoints, auth, models, I2V parameters, price, async, access

### Takeaway
Kling's official developer API changed in mid-2026. From 06/17/2026 the "new API" authenticates only with an **API Key sent as Bearer**. Legacy AccessKey/SecretKey→JWT credentials still work but "will not support new models". The current I2V endpoint for Kling 3.0 / 3.0 Omni takes `first_frame` / `last_frame` and a `settings` object (`resolution` 720p/1080p/4k, `audio` native/off, duration default 5). Billing is per second from prepaid unit packages that are valid 180 days. The standard pack is reported at $700 minimum, so for a solo developer Kling is the most capital-heavy of the three to enter directly.

### Cited Findings
**Hosts and auth**
- The official docs now live at `kling.ai/document-api/...` (global) and `klingai.com/document-api/...` (China, Chinese-language), plus the legacy `app.klingai.com/global/dev/document-api`. — [Kling Authentication](https://kling.ai/document-api/api/get-started/authentication); [Kling CN video models](https://klingai.com/document-api/apiReference/model/videoModels)
- There are two auth methods:
  - **API Key as `Authorization: Bearer <key>`** (new).
  - **Access Key/Secret Key → JWT** (RFC 7519, HS256, ~30 min expiry) sent as Bearer. The docs call this "only applicable to legacy version design standards".
  - The docs also say: "New API Key format is now available — simpler integration, full model coverage. Legacy Access Key / Secret Key credentials remain valid but will not support new models."
  - Source: [Kling Authentication](https://kling.ai/document-api/api/get-started/authentication)
- The 06/17/2026 API update says the new API supports authentication **via API Key only**. The 08/07/2026 update added **webhook signature** support. — [Kling API Updates](https://kling.ai/document-api/updates/api)
- The legacy request shape is `POST https://api.klingai.com/v1/videos/image2video` with `model_name: "kling-v3"` and a Bearer token. **[3P]**, so verify the host: older docs used `api-singapore.klingai.com` for the international region, but this was not confirmed in this research. — [aicontentdrop guide [3P]](https://aicontentdrop.com/blog/kling-3-0-motion-json-prompt-guide)

**Models**
- The model list includes **Kling 3.0 = `kling-v3`** and **Kling 2.6 = `kling-v2-6`**. Motion Control docs say `model_name` defaults to `kling-v2-6`. — [Kling video models](https://kling.ai/document-api/apiReference/model/videoModels)
- A note dated 11/17/2025 says "V2.5-Turbo PRO supports First/Last Frame" through the legacy `image_tail` parameter. That parameter does not appear in the current 3.0 docs. — [Kling API Updates](https://kling.ai/document-api/updates/api)
- Kling O1 / O3 and "Kling 4.0": third-party blogs mention O3 and Kling 4.0, but this research found no official model-ID confirmation for either. — [evolink [3P]](https://evolink.ai/blog/kling-3-o3-api-official-discount-pricing-developers); [aitoolanalysis [3P]](https://aitoolanalysis.com/kling-ai-complete-guide/)

**I2V parameters (current 3.0 / 3.0 Omni endpoint)**
- The endpoint is `POST /image-to-video/kling-3.0` and covers Kling 3.0 and 3.0 Omni. — [Kling 3.0 Omni I2V](https://kling.ai/document-api/api/video/3-0-omni/image-to-video)
- Image input:
  - It uses `first_frame` and `last_frame` entries.
  - First-frame-only and first+last are supported; last-frame-only is not.
  - Images must be **≥300 px** on each side, with an aspect ratio **between 1:2.5 and 2.5:1**.
  - Source: [Kling 3.0 Omni I2V](https://kling.ai/document-api/api/video/3-0-omni/image-to-video)
- The `settings` object holds:
  - `resolution`: enum `720p`, `1080p`, `4k`; default `720p`.
  - `audio`: `native` or `off`; **default off**.
  - duration: default 5.
  - The docs extract showed **no output aspect-ratio parameter**, so output aspect presumably follows the input image.
  - Source: [Kling 3.0 Omni I2V](https://kling.ai/document-api/api/video/3-0-omni/image-to-video)
- The legacy `v1/videos/image2video` schema has `negative_prompt`, `cfg_scale` (0–1, default 0.5), `mode` (`std`/`pro`), `duration` and `aspect_ratio` (16:9, 9:16, 1:1). **[3P]**
  - Duration is reported as 5/10 s in one source and 3–15 s in another (magnific, Kling 3 wrapper).
  - Sources: [magnific Kling 3 [3P]](https://docs.magnific.com/api-reference/video/kling-v3/overview); [fal Kling V3 Pro [3P]](https://fal.ai/docs/model-api-reference/video-generation-api/kling-video-v3-pro); [aicontentdrop [3P]](https://aicontentdrop.com/blog/kling-3-0-motion-json-prompt-guide)
- The search extract of the **new** 3.0 endpoint did **not show `negative_prompt`**. — [Kling 3.0 Omni I2V](https://kling.ai/document-api/api/video/3-0-omni/image-to-video)

**Price, packs, concurrency**
- Official pricing page (about 69 days old as of the search, roughly Aug 2026):
  - Packages are valid **180 days**, with no rollover or extension.
  - Standard packages cost **$0.14/unit**, with volume discounts.
  - "Flagship models" are listed at **$0.0035/unit**, a different unit scale.
  - Concurrency is **20** for the general package tier and **9** for the flagship tier.
  - Packs are bought and consumption is viewed in the developer console.
  - Source: [Kling API Pricing](https://kling.ai/dev/pricing)
- The 06/17/2026 update (new API, model not named in the extract) bills by generated duration: **0.8 units/s at 720p** and **1.0 unit/s at 1080p**. — [Kling API Updates](https://kling.ai/document-api/updates/api)
- Third-party figures **[3P]**:
  - Standard Package 1 is **$700 / 5,000 units** and Package 5 is **$7,560 / 60,000 units** ($0.126/unit), both valid 180 days.
  - Another source mentions a **$9.80 trial** pack.
  - API units can't be used in the web app.
  - Failed generations are not charged.
  - Sources: [costbench [3P]](https://costbench.com/software/ai-media-apis/kling-api/); [atlascloud [3P]](https://www.atlascloud.ai/blog/tips/kling-ai-api-pricing); [renderful [3P]](https://renderful.ai/blog/kling-api-pricing)
- Another per-second schedule for kling-v3 **[3P]** gives 0.6 units/s at 720p and 0.8 units/s at 1080p, or 0.9 and 1.2 with native audio. This conflicts with the official 0.8/1.0 above. — [renderful/costgoat [3P]](https://costgoat.com/pricing/kling)

**Async, retention**
- The pattern is: create task → poll the task by id, or receive a webhook (signed since 08/07/2026) → download.
- Generated videos are **cleared after 30 days**.
- `task_id` can be queried for only **24 h** (Alibaba-hosted Kling doc); after that the status is UNKNOWN.
- Sources: [Kling API Updates](https://kling.ai/document-api/apiReference/updateNotice); [Alibaba Model Studio Kling doc](https://help.aliyun.com/en/model-studio/kling-video-generation-api-reference/)

**Moderation and watermark**
- Moderation is reportedly three-layer, with no API bypass. **[3P]** — [atlascloud NSFW policy [3P]](https://www.atlascloud.ai/blog/guides/kling-ai-nsfw-policy)
- Moderation follows PRC rules on political or sensitive topics. — [Wikipedia: Kling AI](https://en.wikipedia.org/wiki/Kling_AI)
- Consumer-app watermark: free-tier output is watermarked. This research found no statement for the API. — [crepal [3P]](https://crepal.ai/blog/aivideo/kling-ai-watermark/)

### Inferences
- For 10 × 6 s at 1080p:
  - Official 1.0 unit/s × $0.14 gives **6 units ≈ $0.84 per clip, ≈ $8.40 per episode**.
  - The 3P kling-v3 schedule (0.8 units/s) gives ≈ $0.67 per clip.
  - The real constraint is the **$700 minimum pack expiring in 180 days** (if the 3P figure is right). That is ~830 clips at the official rate, far more than ~10 clips per episode needs unless output is high.
- New integrations should use the **API Key (Bearer)** path, not JWT. JWT is legacy and won't get new models.
- On the new 3.0 endpoint, 9:16 should come from a **9:16 input image** (1080×1920 sits within the allowed 1:2.5 range), with `resolution: "1080p"`. Set `audio: "off"`, which is already the default.
- Negative prompt is confirmed only on the legacy schema (3P). Check whether the new endpoint keeps it before relying on it.

### Gaps
- No exact live official price per model (kling-v3 vs v2-6 vs 2.5 Turbo vs O1/O3) in USD per second.
- No confirmed minimum pack and no confirmation of the $9.80 trial pack.
- Not confirmed whether 6 s is allowed on 3.0. Legacy is 5/10; one 3P source says 3–15. fps unknown.
- International vs China API host names on the new API, and whether the China host requires a mainland entity, are unknown.
- Individual signup, KYC, payment methods (card/PayPal) and country restrictions for Kyrgyzstan: nothing official found. 3P sources conflict on whether a phone number is needed.
- No official text on realistic-human or historical-figure moderation, or on API watermarking.

## 2. MiniMax Hailuo: endpoints, auth, models, I2V parameters, price, async, access

### Takeaway
MiniMax has a clear international platform (`platform.minimax.io`, API `api.minimax.io`) and a separate mainland one (`platform.minimaxi.com`). Auth is a Bearer API key, with pay-as-you-go from account balance. Hailuo-2.3 I2V is officially **$0.49 per 1080P 6 s** clip, and Hailuo-2.3-Fast is **$0.33**. **1080P is allowed only at 6 s**, which matches the use case exactly. The default rate limit is **RPM 20**. A newer **MiniMax-H3** family with its own v2 create endpoint appeared by Sept 2026, but its parameters were not retrievable.

### Cited Findings
**Hosts, auth, models**
- The I2V endpoint is `POST https://api.minimax.io/v1/video_generation`.
  - Example body: `model: "MiniMax-Hailuo-2.3"`, `duration: 6`, `resolution: "1080P"`, `first_frame_image` (public URL or Base64 data URL).
  - Source: [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- Supported I2V models: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-2.3-Fast`, `MiniMax-Hailuo-02`, `I2V-01-Director`, `I2V-01-live`, `I2V-01`. — [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- The mainland platform is `platform.minimaxi.com`, with the same API family. — [MiniMax CN T2V](https://platform.minimaxi.com/docs/api-reference/video-generation-t2v)
- Pay-as-you-go uses standard Open Platform API Keys and deducts from balance; top-up is via "Recharge Now". — [MiniMax Pay as You Go](https://platform.minimax.io/docs/guides/pricing-paygo)
- Other endpoints:
  - First+last frame endpoint: here output resolution **follows the first frame image**. — [MiniMax FL2V](https://platform.minimax.io/docs/api-reference/video-generation-fl2v)
  - Subject-reference endpoint. — [MiniMax S2V](https://platform.minimax.io/docs/api-reference/video-generation-s2v)
- **MiniMax-H3**: a newer "Create Video Generation Task" (v2) endpoint exists. In its flow, polling returns the video URL directly in `content.url`. — [MiniMax v2 create](https://platform.minimax.io/docs/api-reference/video-generation-v2-create); [MiniMax video guide](https://platform.minimax.io/docs/guides/video-generation)

**I2V parameters**
- `prompt_optimizer` is a boolean, **default true**; set it false for precise control. `fast_pretreatment` shortens optimization time and applies to 2.3 / 2.3-Fast / 02. — [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- Resolution and duration for Hailuo-2.3 / 02 / 2.3-Fast: **1080P only with 6 s**; 768P with 6 or 10 s; 512P is listed. — [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v); [MiniMax T2V](https://platform.minimax.io/docs/api-reference/video-generation-t2v)
- The extracts showed **no `negative_prompt`, no `seed`, no `aspect_ratio`, and no audio parameter** for Hailuo I2V. — [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v)

**Price, packs, limits**
- Pay-as-you-go:

  | Model | Clip | Price |
  |---|---|---|
  | Hailuo-2.3 | 1080P 6 s | **$0.49** |
  | Hailuo-02 | 1080P 6 s | **$0.49** |
  | Hailuo-2.3-Fast | 1080P 6 s | **$0.33** |
  | Hailuo-02 | 512P 6 s | $0.10 |

  Source: [MiniMax Pay as You Go](https://platform.minimax.io/docs/guides/pricing-paygo)
- An older snapshot of the pricing overview (~June 2026) lists Hailuo-2.3 at $0.28 (768P 6 s), $0.56 (768P 10 s) and $0.49 (1080P 6 s), and 2.3-Fast at $0.19 (768P 6 s). — [MiniMax Pricing Overview](https://platform.minimax.io/docs/pricing/overview)
- MiniMax-H3 pricing **[3P citing the official pay-go page, Sept 2026]**:
  - H3: $0.08/s at 768p, $0.13/s at 2K.
  - H3-Max: $0.05/s at 480p, $0.08/s at 768p.
  - Extra reference images: $0.04 each.
  - Sources: [framesurfer [3P]](https://framesurfer.com/blogs/hailuo-ai-video); [OpenRouter H3 [3P]](https://openrouter.ai/minimax/hailuo-3)
- Video packages: **$1,000–$6,000, valid 1 month**. The $1,000 tier = 3,760 video points; 1080P 6 s costs 2 points (2.3/02) or 1.3 points (2.3-Fast). — [MiniMax Video Packages](https://platform.minimax.io/docs/guides/pricing-video)
- Rate limits: Hailuo series **RPM 20**. Packages raise this: Standard 20, Business 50, custom unlimited. — [MiniMax Rate Limits](https://platform.minimax.io/docs/guides/rate-limits); [MiniMax Video Packages](https://platform.minimax.io/docs/guides/pricing-video)

**Async**
- Classic flow: create → `task_id` → query → `file_id` → file retrieve → `download_url`.
- An older official announcement says the download URL is **valid for 9 hours**. Current expiry is not confirmed. — [MiniMax Video-01 API news (old)](https://www.minimax.io/news/video-generation-api)

### Inferences
- **Cost per episode** (10 × 1080P 6 s): **$4.90** with Hailuo-2.3 or **$3.30** with 2.3-Fast, paid as you go with no minimum pack. That is the lowest entry barrier of the three.
- 9:16: Hailuo I2V has no aspect parameter, so output almost certainly follows the input frame, as FL2V states explicitly. Feed a 1080×1920 first frame.
  - Unverified: whether "1080P" yields 1080×1920 for portrait input.
- No negative prompt. To avoid text in frame, set `prompt_optimizer: false` and rely on positive phrasing.
- At ~10 clips per episode, RPM 20 is not a constraint.

### Gaps
- H3 video parameters (resolution, 9:16, durations, negative prompt, audio) were not retrievable.
- fps unknown. Exact output pixel dimensions for portrait input unknown.
- Moderation policy for realistic or historical people unknown.
- API watermark status unknown. Only the consumer app is known to watermark free output ([nemovideo [3P]](https://www.nemovideo.com/blog/free-chinese-ai-video-generator)).
- Individual signup, KYC, accepted cards, country restrictions: nothing official found.

## 3. ShengShu Vidu: endpoints, auth, models, I2V parameters, price, async, access

### Takeaway
The Vidu API (`platform.vidu.com`, docs also at `docs.platform.vidu.com`) bills in **credits at $0.005 each**.
- **Q3-pro I2V**: 1080p = 24 credits/s (**$0.12/s**), 720p = 20 credits/s.
- **Q3-turbo I2V**: 1080p = 13 credits/s (**$0.065/s**).
- Durations run 1–16 s, so **6 s is valid**. Q2 models allow 1–10 s.
- Audio is generated **by default on Q3** (`audio: true`) and can be turned off with `audio: false`.
- There is an `off_peak` mode at roughly half price, delivered within 48 h.
- Negative prompt and watermark parameters were not found.

### Cited Findings
**Endpoint, auth, models**
- I2V takes required `model` and `images`. `images` is one start frame, as a public URL or Base64 (png/jpeg/jpg/webp, ≤50 MB). Input aspect must be between **1:4 and 4:1**. — [Vidu I2V](https://platform.vidu.com/docs/image-to-video)
- Example body: `model: "viduq3-pro"`, `audio: true`, `duration: 5`, `seed: 0`, `resolution: "1080p"`, `movement_amplitude: "auto"`. — [Vidu I2V](https://platform.vidu.com/docs/image-to-video)
- Other model IDs:
  - `q2-pro` and `q2-turbo` are accepted on I2V: duration 1–10 s (default 5), resolution 540p/720p/1080p (default 720p).
  - Vidu 2.0 allows only 4 or 8 s.
  - Source: [Vidu I2V](https://platform.vidu.com/docs/image-to-video)
- Auth header: `Authorization: Token <key>` per the brief. Not re-confirmed in these extracts (see Gaps).

**Parameters**
- `seed`: optional; a manual value overrides random.
- `movement_amplitude`: auto/small/medium/large; **no effect on q2/q3**.
- `audio`: boolean, default false, **except q3 where the default is true**; false gives silent output.
- `off_peak`: boolean, default false, lower price, delivered **within 48 h**. Of the direct audio-video modes, only q3 supports off-peak.
- The recommended-prompt option adds 10 credits per task.
- Source: [Vidu I2V](https://platform.vidu.com/docs/image-to-video)
- `aspect_ratio` (16:9 default, 9:16, 1:1) exists on **reference-to-video**. It was not found on I2V, so output there presumably follows the image. — [Vidu Reference-to-Video](https://platform.vidu.com/docs/reference-to-video)
- No `negative_prompt` and no `watermark` parameter appeared in any retrieved extract. — [Vidu I2V](https://platform.vidu.com/docs/image-to-video)

**Price** (official page, but from a truncated search extract)
- Credit = **$0.005** plus applicable sales tax.
- Image-to-video rates:

  | Model | 1080p | 720p | 540p |
  |---|---|---|---|
  | Q3-pro | 24 cr/s ($0.12) | 20 cr/s ($0.10) | 9 cr/s ($0.045) |
  | Q3-turbo | 13 cr/s ($0.065) | 11 cr/s ($0.055) | 7 cr/s ($0.035) |
  | Q3-pro-fast (I2V only) | 25 cr/s ($0.125) | 20 cr/s ($0.10) | — |

- Off-peak rates are listed separately at roughly half. Q3 durations are 1–16 s.
- Source: [Vidu Pricing](https://platform.vidu.com/docs/pricing)
- Third-party resale prices differ: Atlas Cloud Q3 I2V is $0.07/$0.15/$0.16 per s at 540/720/1080p. — [atlascloud Vidu Q3 [3P]](https://www.atlascloud.ai/models/vidu/q3/image-to-video)

**Async**
- Set `callback_url` at task creation. Vidu POSTs status (processing/success/failed) and retries failed callbacks 3 times. A `credits` field appears in responses. — [Vidu I2V](https://platform.vidu.com/docs/image-to-video)
- Other endpoints: Start-End-to-Video ([Vidu docs](https://docs.platform.vidu.com/334381323e0)), Reference-to-Video, and an MCP endpoint ([Vidu MCP](https://platform.vidu.com/docs/mcp-streamable-https)).

### Inferences
- **Cost per episode** (10 × 6 s at 1080p):
  - Q3-pro: 6 × $0.12 = **$0.72/clip → $7.20/episode**.
  - Q3-turbo: **$0.39/clip → $3.90/episode**.
  - Off-peak could roughly halve both if a 48 h turnaround is acceptable.
  - Not confirmed whether `audio: false` lowers the Q3 price.
- Always send `audio: false` explicitly, because Q3 defaults to sound.
- For 9:16, feed a 1080×1920 first frame; 9:16 = 1:1.78, which is within the 1:4–4:1 range.

### Gaps
- `Authorization: Token` header, base host (`api.vidu.com/ent/v2/...`), polling endpoint and result-URL expiry: not confirmed in this research.
- Minimum top-up, payment methods, individual vs enterprise signup, KYC, country restrictions: not found.
- Rate limits and concurrency: not found.
- Negative prompt and watermark: not found. Moderation policy for realistic or historical people: not found.
- Q2 per-second prices: not captured (truncated extract).
- fps unknown.

## 4. Cross-provider fit for the use case (6 s, 9:16, ≥1080×1920, I2V, negative prompt, no text, ~10 clips/episode)

### Takeaway
- **All three** do I2V at 1080p where 6 s is allowed. For all three, portrait output is driven by a portrait input image, not by an aspect parameter (on the current docs).
- **Only Kling** has a documented `negative_prompt`, and only on the legacy schema (3P-confirmed); it is not confirmed on the new 3.0 endpoint.
- MiniMax is cheapest to start (pay-as-you-go, no minimum; ~$3.30–4.90 per episode).
- Vidu is comparable per clip (~$3.90–7.20 per episode) with explicit audio control.
- Kling likely costs ~$8.40 per episode but needs a large prepaid pack.

### Cited Findings
- Kling: 1080p at 1.0 unit/s, $0.14/unit, 180-day packs. — [Kling API Updates](https://kling.ai/document-api/updates/api); [Kling API Pricing](https://kling.ai/dev/pricing)
- MiniMax: 1080P only at 6 s; $0.49 (2.3) or $0.33 (2.3-Fast) per clip. — [MiniMax I2V](https://platform.minimax.io/docs/api-reference/video-generation-i2v); [MiniMax Pay as You Go](https://platform.minimax.io/docs/guides/pricing-paygo)
- Vidu: Q3 durations 1–16 s; Q3-pro 1080p $0.12/s; Q3-turbo $0.065/s. — [Vidu Pricing](https://platform.vidu.com/docs/pricing)
- Input aspect limits: Kling 1:2.5–2.5:1, Vidu 1:4–4:1, MiniMax FL2V follows the first frame. All three accept a 9:16 frame. — [Kling 3.0 Omni I2V](https://kling.ai/document-api/api/video/3-0-omni/image-to-video); [Vidu I2V](https://platform.vidu.com/docs/image-to-video); [MiniMax FL2V](https://platform.minimax.io/docs/api-reference/video-generation-fl2v)

### Inferences
- Without a reliable negative prompt on MiniMax and Vidu, "no text in frame" has to come from a clean input image plus positive prompting. With MiniMax, also set `prompt_optimizer: false` so the rewriter doesn't add elements.
- The cheapest direct path for a test run without commitment is **MiniMax pay-as-you-go**, then Vidu credits. Kling's direct API makes sense only at volume, or via resellers (fal, Atlas, PiAPI), which are out of scope here.

### Gaps
- No official source covered moderation of **realistic historical people** (1890s Central Asian or Kyrgyz people in traditional dress) for any provider. Expect generic PRC-aligned filtering (politics, sensitive topics), not ethnic or historical bans, but this is unverified. A test generation is the only reliable check.
- Availability from Kyrgyzstan (sanctions or geo-blocks, card acceptance, KYC) was not documented anywhere official in this research.
