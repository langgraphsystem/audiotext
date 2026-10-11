# First-party video APIs: ByteDance Seedance (BytePlus / Volcengine Ark), Alibaba Wan / HappyHorse (Model Studio), and others — state as of Oct 2026

Context for the report writer: the target user is an **individual developer based in the USA** (corrected by coordinator; the original brief said Kyrgyzstan). Use case: about 10 clips per episode, each a 6-second 9:16 image-to-video clip at 1080x1920 or more, with a negative prompt and no text in frame. Subjects are realistic historical people (1890s Kyrgyz people in traditional clothing).

Method note: `docs.byteplus.com` renders client-side, so its pages came back as navigation only. The Seedance parameter facts below come from the **Volcengine Ark (China) "Create video generation task" API reference**, which renders server-side and was updated in 2026 with Seedance 2.5. BytePlus ModelArk uses the same `content_generation.tasks` API shape (confirmed by the DataCamp tutorial, which uses the international base URL). Some BytePlus-specific numbers (international model IDs, USD prices) come from third-party pages and are marked as such. Alibaba pages were read in full from alibabacloud.com.

---

## 1. Regional availability, signup/KYC and legal risk for a US-based individual developer

### Takeaway
**BytePlus (Seedance international) is officially not available in the United States**, so a US developer cannot use Seedance first-party. Volcengine (China) needs Chinese real-name identity. **Alibaba Cloud Model Studio international is usable from the US:** it has a US (Virginia) region, individual accounts are accepted, a card can be used to pay, and identity verification is only mandatory for resources in the Chinese mainland. No US law currently bans using Chinese-provider APIs. Political risk exists on both sides: the US has floated sanctions over distillation, and China is weighing limits on overseas access to its top models.

### Cited Findings
- BytePlus's own Seedance 2.0 and 2.5 launch posts both state "(Note: BytePlus is not available in the United States)." — [BytePlus blog, Seedance 2.5, Aug 6 2026](https://www.byteplus.com/en/blog/dreamina-seedance2-5); [BytePlus blog, Seedance 2.0, Apr 14 2026](https://www.byteplus.com/en/blog/dreamina-seedance2-0)
- BytePlus "International Availability for BytePlus Model Service" (last updated 21 April 2026) lists the countries where the service is available. The **United States is not on the list**, while Canada, Mexico, the UK, Kyrgyzstan, Kazakhstan, Uzbekistan and others are. It adds that "Restricted Models" are excluded and that "availability… shall be determined at the point of purchase." — [BytePlus docs: International Availability](https://docs.byteplus.com/en/docs/ModelArk/availability)
- The Volcengine (China) Ark activation precondition for Seedance 2.5 / 2.0 is an account balance above ¥200, a ¥200+ savings plan, or a Seedance resource pack. — [Volcengine Ark: Create video generation task](https://www.volcengine.com/docs/82379/1520757)
- BytePlus activation for Seedance 2.0 needs a balance above $30, a $30+ AI Savings Plan, or a resource pack (third-party summary of the BytePlus tutorial). — [FrameSurfer, Sep 2026](https://framesurfer.com/blogs/seedance-2-0-pricing)
- A BytePlus account "means a sign-up with phone verification (personal accounts are accepted) and at least USD 30 in credits…" (third-party). — [APIMODELS, Sep 30 2026](https://apimodels.app/access/seedance-api-pricing)
- Alibaba Cloud international: "You must complete identity verification before purchasing cloud services deployed in the Chinese mainland or signing business contracts." Individual verification uses a passport or driver's license issued by the account's registration country, with manual review of about 3 business days. Enterprise verification is required only to sign contracts, get a credit limit, join ACPN, or link a foreign phone number. — [Alibaba Cloud: Identity verification overview](https://www.alibabacloud.com/help/en/account/account-verification-overview); [Individual identity verification](https://www.alibabacloud.com/help/en/account/verify-your-identity-individual-account)
- On mainland China, the same doc says the "China (Hong Kong) region… Does not require identity verification" (example of non-mainland regions being exempt). — [Alibaba Cloud: Individual identity verification](https://www.alibabacloud.com/help/en/account/verify-your-identity-individual-account)
- Alibaba Cloud accepts Visa, Mastercard, American Express, UnionPay, JCB, Discover and Diners Club cards, plus digital wallets (search snippet of the official page). — [Alibaba Cloud: Payment methods](https://www.alibabacloud.com/help/en/user-center/instruction-of-payment-management/)
- The Model Studio FAQ says: "If a message prompts you to complete real-name verification, you must complete real-name verification before proceeding." — [Model Studio FAQ](https://help.aliyun.com/en/model-studio/faq-about-alibaba-cloud-model-studio)
- Model Studio has a **US (Virginia) region** (`{WorkspaceId}.us-east-1.maas.aliyuncs.com`) for the Wan 2.1–2.6 i2v API and for Wan 3.0. Model, endpoint and API key must be in the same region. — [Wan i2v API reference (2.1–2.6)](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference); [Wan3.0 API reference](https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference)
- The rate-limit page lists `wan2.6-i2v` with a "United States" deployment scope (5 RPS, 5 concurrent). — [Model Studio rate limiting](https://www.alibabacloud.com/help/en/model-studio/rate-limit)
- **Free quota is Singapore-only:** "The following models offer a free quota only in Singapore. No free quota is available in other regions." — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- US policy (as of Jul 22 2026): "No Chinese AI models have been sanctioned." Treasury Secretary Bessent said on Jul 21 that the US could sanction Chinese developers over distillation. The labs named include **Alibaba**, but not ByteDance. Axios-reported options were Entity List additions, procurement rules and advisories (secondary source). — [Vibranium Labs, Jul 22 2026](https://vibraniumlabs.ai/blog/chinese-ai-models-sanctioned-whats-actually-happening)
- China side: the Ministry of Commerce met Alibaba, ByteDance and Z.ai about "potentially restricting overseas access to China's most advanced AI models, including those yet to be released." Scope and timing were undecided. — [Reuters, Jul 7 2026](https://www.reuters.com/world/beijing-is-looking-curbing-overseas-access-chinas-top-ai-models-sources-say-2026-07-07/)

### Inferences
- For a US individual, the only practical **first-party** Chinese option among these is **Alibaba Model Studio (Wan / HappyHorse)**, ideally in the US (Virginia) region. The Singapore region gives the free trial seconds; whether a US-registered account can use Singapore without restriction was not confirmed.
- Getting Seedance from the US would mean going through third-party resellers (fal, EvoLink, APIMODELS, Runway, Higgsfield and so on), which is out of scope for "first-party". Using a non-US BytePlus account from the US would breach the stated availability terms.
- Alibaba is named in the US distillation allegations, so this is a supply-risk item to flag even though nothing has been enacted (as of the latest sources, Jul–Aug 2026).

### Gaps
- No official statement was found on whether a US-registered Alibaba international account needs individual ID verification just to use Model Studio in Singapore or Virginia. The docs say verification is mandatory only for mainland resources, but the Model Studio FAQ mentions prompts for real-name verification.
- No primary source was found for any US federal or state rule effective by October 2026 that bars individuals from calling Chinese AI APIs. The September 2026 US–China talks outcome was not researched.
- The BytePlus Seedance free trial token quota was not found.

---

## 2. ByteDance Seedance — API host, auth, model lineup

### Takeaway
Seedance runs on an Ark "content generation tasks" REST API. Authentication is `Authorization: Bearer <ARK_API_KEY>`. The pattern is async: POST to create a task, then GET to poll it. The international host is `ark.ap-southeast.bytepluses.com/api/v3`; the China host is `ark.cn-beijing.volces.com/api/v3`. Current models are Seedance 2.5, the 2.0 family (2.0 / 2.0 fast / 2.0 mini), 1.0 pro and 1.0 pro fast. Seedance 1.5 Pro still has BytePlus prices, while 1.0 Lite no longer appears in the current API reference or pricing.

### Cited Findings
- China endpoint: `POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`, with API-key auth (a long-lived key from the API Key page). — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- International base URL used with the Ark SDK: `base_url="https://ark.ap-southeast.bytepluses.com/api/v3"`, `client.content_generation.tasks.create(...)`, model `dreamina-seedance-2-0-260128` (third-party tutorial, Jun 2026). — [DataCamp Seedance 2.0 API guide](https://www.datacamp.com/tutorial/seedance-2-0-api-guide)
- The BytePlus API reference section lists "Create / Retrieve / List / Cancel or delete a video generation task" (page last updated Oct 8 2026). — [BytePlus ModelArk API reference](https://docs.byteplus.com/en/docs/ModelArk/1520757)
- Models in the current Volcengine create-task reference (example China IDs: `doubao-seedance-2-5-260628`, `doubao-seedance-1-0-pro-250528`):
  - Seedance 2.5: T2V, I2V first frame, first+last frame, and omni-reference (0–30 images, 0–10 videos, 0–10 audios), up to 30 s.
  - Seedance 2.0 series: same task types (0–9 images, 0–3 videos, 0–3 audios).
  - 1.0 pro: T2V, first frame, first+last frame.
  - 1.0 pro fast: T2V and first frame only.

  — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- BytePlus docs navigation now has "Dreamina Seedance 2.5 tutorial", "Dreamina Seedance 2.0 series tutorial" and "Create portrait videos with Dreamina Seedance models". — [BytePlus ModelArk docs nav](https://docs.byteplus.com/en/docs/ModelArk/1544106)
- "BytePlus's pricing page does not list Seedance 1.0 Lite" (third-party, Sep 2026). — [FrameSurfer](https://framesurfer.com/blogs/seedance-2-0-pricing)
- Callback support: `callback_url` receives POSTs with status `queued/running/succeeded/failed/expired`. `execution_expires_after` defaults to 172800 s (48 h), range [3600, 259200]. Task `id` is kept **7 days**. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `service_tier`: `default` (online) or `flex` (offline, **50% price**, higher TPD). Flex is supported only by 1.0 pro / 1.0 pro fast, not 2.x. `priority` is 0–9 (2.x only). — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)

### Inferences
- The international model IDs follow the `dreamina-seedance-…` pattern (2.0: `dreamina-seedance-2-0-260128`). The exact BytePlus IDs for 2.5, Fast, Mini and 1.x were not verified from primary docs.

### Gaps
- The download-URL expiry for Seedance output (commonly cited as 24 h) was not confirmed in the fetched text. Only the 7-day task-ID retention was confirmed.
- BytePlus per-model RPM and concurrency quotas were not retrieved (the Volcengine model-list page did not render). The doc says the `default` tier has "lower RPM and concurrency quotas" (see model list).

---

## 3. Seedance — image-to-video inputs, resolutions (9:16 1080x1920), durations, fps

### Takeaway
I2V uses `content[]` items `{"type":"image_url","image_url":{"url":...},"role":"first_frame"|"last_frame"|"reference_image"}`, given as a URL, a base64 data URI or `asset://ID`. Exact 1080x1920 9:16 is supported by **Seedance 2.5 and 2.0**; 1.0 pro gives 1088x1920. 2.0 fast and mini stop at 720p. Seedance 2.5 forces `ratio=adaptive` for first-frame I2V, so the output follows the input image's aspect ratio. Output is 24 fps. A 6-second clip is possible on 2.0 (4–15 s) and 1.0 pro (2–12 s); 2.5 is 4–30 s.

### Cited Findings
- Image input rules: aspect ratio (w/h) in [0.4, 2.5], sides 300–6000 px, under 30 MB, request body up to 64 MB. Formats are jpeg/png/webp/bmp/tiff/gif, plus heic/heif on 2.0+. Base64 form is `data:image/png;base64,...`. First frame = 1 image, first+last = 2 images (role required). First-frame, first+last and omni-reference are **mutually exclusive** modes. First+last frame is supported on 2.5, 2.0 series and 1.0 pro. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `resolution`:
  - 2.5: 480p/720p/1080p, default 720p.
  - 2.0: 480p/720p/1080p/4k.
  - 2.0 fast and 2.0 mini: 480p/720p only.
  - 1.0 pro and pro fast: 480p/720p/1080p, default 1080p.
  - 2.5 1080p and 2.0 4k output is 10-bit H.265/HEVC.

  — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `ratio` values are `16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive`. Pixel table for **9:16 1080p**: Seedance 2.5 = **1080×1920**, 2.0 series = **1080×1920**, 1.0 series = **1088×1920**. 720p 9:16 is 720×1280 (1.0: 704×1248). — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- For first-frame or first+last I2V, Seedance 2.5 "defaults to and only supports adaptive" (keeps the first-frame aspect ratio). 2.0 and 1.0 accept an explicit ratio. If the chosen ratio differs from the image, Ark **center-crops** the image. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `duration`: 2.5 accepts [4, 30] or -1 (default -1). 2.0 series accepts [4, 15] or -1. 1.0 pro and pro fast accept [2, 12]. `frames` (1.0 only) is [29, 289] in the form 25+4n. The frame rate is 24, and the returned duration is total frames / 24 rounded down. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `return_last_frame` (default false) returns a no-watermark JPEG of the last frame for chaining clips. `draft` mode (2.5 only) gives 480p previews. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- Prompts: Chinese and English for all models; 2.0 also takes es/id/pt/ja. Recommended length is ≤500 Chinese characters or ≤1000 English words. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)

### Inferences
- If you were allowed to use Seedance at all, 2.0 at 1080p, ratio 9:16, duration 6 would hit 1080×1920 exactly. With 2.5 you would need a 9:16 first-frame image of the right size, because adaptive is forced.

### Gaps
- None material for the parameter shape. International (BytePlus) parity with these Volcengine values is assumed, not verified.

---

## 4. Seedance — negative prompt, seed, prompt extension, audio, watermark

### Takeaway
**Seedance has no `negative_prompt` parameter.** `seed` and `camera_fixed` exist only on 1.0 pro and pro fast. There is no prompt-rewrite toggle. Audio is generated by default on 2.x (`generate_audio`, default true) and can be turned off with `false`. The visible watermark is off by default (`watermark` default false), but BytePlus adds C2PA content credentials.

### Cited Findings
- The full body-parameter list is `model, content, omni_reference_task_type, resolution, ratio, duration, frames, generate_audio, watermark, output_format, seed, camera_fixed, return_last_frame, draft, service_tier, callback_url, execution_expires_after, priority, safety_identifier, tools`. There is **no negative-prompt field**. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `seed`: default -1, range [-1, 2147483647], **1.0 pro / 1.0 pro fast only**. `camera_fixed` is also 1.0 only. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `generate_audio` (boolean, default **true**) on 2.5 and 2.0 series; `false` gives silent video. Generated audio is mono. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- `watermark` (boolean, default **false**); `true` adds an "AI生成" mark in the lower-right corner. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- BytePlus implemented "C2PA Content Credentials… on top of our existing visible watermark capability." — [BytePlus blog, Seedance 2.5](https://www.byteplus.com/en/blog/dreamina-seedance2-5)

### Inferences
- "No text in frame" has to be handled in the prompt wording only (for example "no captions, no on-screen text"), because there is no negative prompt.

### Gaps
- Whether `generate_audio=false` lowers the 2.x price was not confirmed. The third-party summary says 2.0 pricing has "no separate audio line"; 1.5 Pro had separate silent pricing.

---

## 5. Seedance — pricing (USD) and quotas

### Takeaway
BytePlus bills Seedance by token: tokens ≈ (input s + output s) × W × H × 24 / 1024. At list prices (Sep 2026, third-party summaries of the BytePlus page), Seedance 2.0 is about **$0.15/s at 720p** and **$0.37/s at 1080p**. Seedance 2.5 is about $0.231/s at 720p and $0.569/s at 1080p. 1.0 Pro is about $0.12/s at 1080p (5 s, 16:9), and Fast/Mini have no 1080p. Only successful videos are billed.

### Cited Findings
- BytePlus example prices for a 5 s 16:9 clip with no video input (list price, Sep 2026): **Seedance 2.0**: 480p $0.35 ($0.07/s), 720p $0.76 ($0.15/s), 1080p $1.87 ($0.37/s), 4K $3.89 ($0.78/s). **2.0 Fast**: 480p $0.28, 720p $0.60 ($0.12/s), no 1080p. **2.0 Mini**: 480p $0.18, 720p $0.38 ($0.08/s). **2.5**: 480p $0.514, 720p $1.156 ($0.231/s), 1080p $2.843 ($0.569/s). Token rates for 2.0 without video input: $7.00/M (480p/720p), $7.70/M (1080p). — [FrameSurfer (third-party, citing BytePlus pricing page), Sep 24 2026](https://framesurfer.com/blogs/seedance-2-0-pricing)
- Older models, 5 s 16:9 list price: 1.5 Pro with audio $0.12/$0.26/$0.58 (480/720/1080p); 1.5 Pro silent $0.06/$0.13/$0.29; **1.0 Pro $0.12/$0.26/$0.61**; 1.0 Pro Fast $0.05/$0.10/$0.24. — [FrameSurfer](https://framesurfer.com/blogs/seedance-2-0-pricing)
- Token formula and per-second token counts at 16:9: about 9,607/s (480p), 21,600/s (720p), 48,600/s (1080p). — [APIMODELS (third-party)](https://apimodels.app/access/seedance-api-pricing)
- Resource packs: Seedance 2.0 at $4.30 per 1M tokens, $43/10M, $430/100M; 2.0 fast at $3.30/1M. The DataCamp author bought a 7M-token pack for $30.10. Tokens are model-specific. — [Kingy.ai review, Apr 2026](https://kingy.ai/news/byteplus-review-seedance-2-0-turns-byteplus-into-a-serious-ai-video-platform/); [DataCamp](https://www.datacamp.com/tutorial/seedance-2-0-api-guide)
- Limited-time discounts (Aug 7–Oct 7 2026, enterprise users only) have **already expired** as of Oct 11 2026. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- Failed generations are not charged. — [FrameSurfer](https://framesurfer.com/blogs/seedance-2-0-pricing)

### Inferences
- For 10 clips × 6 s at 1080p 9:16 on Seedance 2.0: 60 s × about $0.37 ≈ **$22 per episode** at list price, before retries. The token count for 1080×1920 equals 1920×1080, so the cost is the same as 16:9. This is moot for a US user (see §1).

### Gaps
- The primary BytePlus pricing page could not be rendered, so all USD figures are third-party relays dated Sep 2026.
- BytePlus free trial quota and RPM/concurrency for Seedance are unknown.

---

## 6. Seedance — content moderation for realistic people; watermark

### Takeaway
This is the biggest blocker for the use case. **Seedance 2.x (and 2.5) rejects input images or videos that contain real human faces.** A third-party test found the rejection also applies to *AI-generated* photorealistic people. The workarounds are BytePlus real-person verification with likeness authorization, the 10,000+ virtual-human asset library, or re-using faces that Seedance itself generated within the last 30 days (Volcengine).

### Cited Findings
- "Seedance 2.5、Seedance 2.0 系列模型不支持直接上传含有真人人脸的参考图 / 视频" (2.5 and 2.0 do not support directly uploading reference images or videos containing real human faces). The listed solutions are using face-containing outputs of these models as input, preset virtual portraits (`asset://`), and authorized real-person material. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- Ark trusts face-containing videos generated by Seedance 2.5/2.0 under the same account in the last 30 days as input. — [Volcengine Ark API ref](https://www.volcengine.com/docs/82379/1520757)
- BytePlus is "Restricting the ability to make videos from images or videos that contain real faces". It offers real-person verification with likeness authorization in the ModelArk console and "a library of over 10,000 high-quality virtual human assets across diverse ages and cultural backgrounds." — [BytePlus blog, Seedance 2.0](https://www.byteplus.com/en/blog/dreamina-seedance2-0); [BytePlus blog, Seedance 2.5](https://www.byteplus.com/en/blog/dreamina-seedance2-5)
- Third-party test: "The request failed because the input image may contain a real person. I noticed this consistently as I tried to use Seedance 2 with a reference image containing a realistic human, even with AI-generated ones." — [DataCamp, Jun 2026](https://www.datacamp.com/tutorial/seedance-2-0-api-guide)
- "The official Ark and BytePlus lines reject a reference showing an identifiable real person unless it is first registered in the asset library" (third-party). — [APIMODELS](https://apimodels.app/access/seedance-api-pricing)

### Inferences
- Photorealistic first frames of 1890s Kyrgyz people (likely AI-generated stills) would probably be rejected by Seedance 2.x. Seedance 1.0 pro is not listed under this face restriction in the API ref, but no source confirms that it accepts them.

### Gaps
- No source states whether the face filter applies to `first_frame` exactly as it does to `reference_image`. The wording mentions "参考图 / 视频", and the DataCamp test used a reference image.
- No information was found on whether first frames for 1.0 pro face the same filter.

---

## 7. Alibaba Wan / HappyHorse (Model Studio) — hosts, auth, models

### Takeaway
DashScope-style async REST. You POST `/api/v1/services/aigc/video-generation/video-synthesis` with headers `Authorization: Bearer sk-…` and **`X-DashScope-Async: enable`** (required), then GET `/api/v1/tasks/{task_id}`. Region hosts are workspace-specific (`{WorkspaceId}.ap-southeast-1|us-east-1|eu-central-1|ap-northeast-1|cn-hongkong|cn-beijing.maas.aliyuncs.com`); the legacy `dashscope-intl.aliyuncs.com` still works. Current video model families are **Wan 2.6 i2v** (first frame), **Wan 2.7 i2v** (first frame, first+last frame, continuation), **Wan 3.0** (all-in-one, preview) and **HappyHorse 1.0/1.1** (t2v / i2v / r2v / edit). Alibaba's docs now steer first-frame users toward HappyHorse and Wan 3.0.

### Cited Findings
- Endpoints and headers: `POST https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis` (also us-east-1, cn-beijing, eu-central-1). "X-DashScope-Async… HTTP requests support only asynchronous calls… If this request header is missing, the error 'current user api does not support synchronous calls' is returned." `Authorization: Bearer sk-xxxx`. — [Wan i2v API reference 2.1–2.6](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)
- Workspace-specific domains are recommended over `https://dashscope-intl.aliyuncs.com` (Singapore) and `https://dashscope.aliyuncs.com` (Beijing); "The existing domain remains fully functional." — [Wan 2.7 i2v API ref](https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference)
- Wan 2.7 i2v (`wan2.7-i2v-2026-04-25`, `wan2.7-i2v`) uses a new protocol with a `media` array (`type`: `first_frame`, `last_frame`, `driving_audio`, video continuation). "The earlier image-to-video from first frame API (wan2.6 and earlier) supports only first-frame-to-video." The Wan 2.7 page shows Singapore and Beijing endpoints only. — [Wan 2.7 i2v API ref](https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference)
- Wan 3.0 is "All-in-One… Text-to-Video, Image-to-Video (first frame/first-last frame), and Reference-based… up to 30 seconds long at 30fps. Currently in preview." Endpoints exist in Singapore, Beijing, US (Virginia), Tokyo, Frankfurt and Hong Kong. Its first-frame/first-last mode accepts only `first_frame` and `last_frame` (no audio). — [Wan3.0 API reference](https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference)
- Wan 2.6 i2v model names in the docs are `wan2.6-i2v-flash` and `wan2.6-i2v`. The 2.6 i2v endpoint list includes **us-east-1**. — [Wan i2v API reference 2.1–2.6](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)
- Rate limits: every listed Wan/HappyHorse video model (`wan2.7-i2v`, `wan2.6-i2v(-flash)`, `wan3.0-video(-prime)`, `happyhorse-1.x-*`) has **5 RPS and 5 concurrent tasks**. — [Model Studio rate limiting](https://www.alibabacloud.com/help/en/model-studio/rate-limit)

### Inferences
- With 5 concurrent tasks, 10 clips per episode can run in two batches of 5.
- On SDKs: DashScope Python ≥1.25.8 is needed for 2.6 and ≥1.25.16 for 2.7, according to the docs.

### Gaps
- Whether `wan2.7-i2v` is offered in the US (Virginia) region: it does not appear in Virginia pricing, and its API page shows only Singapore and Beijing.
- The HappyHorse i2v API reference page (parameter names, negative prompt, durations) was not fetched.

---

## 8. Wan — image-to-video inputs, resolution / 9:16, duration, fps

### Takeaway
Wan has **no aspect-ratio parameter for I2V**. The output follows the first-frame image's aspect ratio at the chosen `resolution` tier (`480P` / `720P` / `1080P`), with width and height snapped to multiples of 16. A 1080×1920 input at "1080P" should give about 1080×1920 (computed, not documented). Images can be a URL, base64 data URI, or a local path (SDK only). Durations are integers from 2 to 15 s per the guide (Wan 2.5/2.6 family); Wan 3.0 goes up to 30 s at 30 fps.

### Cited Findings
- "Supports integer video durations from 2 to 15 seconds, configurable video resolution (480P, 720P, or 1080P), smart prompt rewriting, and optional watermarking." — [Wan image-to-video guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- "The current API does not support setting the video aspect ratio directly… The `resolution` parameter controls the total number of pixels—not a fixed aspect ratio… both the width and height must be multiples of 16." Example: a 750×1000 input at 720P (about 920,000 px) gives 816×1104. — [Wan image-to-video guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Input image: one image, given as "Image URL, local file path, or Base64-encoded string" in the form `data:{MIME_type};base64,{base64_data}`. JPEG/JPG/PNG/BMP/WEBP are accepted. Parameter name in 2.6 is `input.img_url`; 2.6 audio uses `input.audio_url`. — [Wan image-to-video guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Multi-shot (`shot_type: "multi"`, requires `prompt_extend: true`) is Wan 2.6 only. — [Wan image-to-video guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Third-party claims Wan 2.6 i2v takes 5 / 10 / 15 s, which conflicts with the official "integer 2 to 15". — [EvoLink (via search summary)](https://evolink.ai/blog/wan-2-6-api-guide); official: [Wan image-to-video guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Wan 3.0: up to 30 s at **30 fps**. — [Wan3.0 API reference](https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference)

### Inferences
- To get a 9:16 1080×1920 output, supply a 1080×1920 (9:16) first frame with `resolution: "1080P"`. A small drift of ±16 px is possible, so plan a crop or pad step (the bot's FFmpeg is already present).

### Gaps
- Wan 2.6/2.7 output fps was not stated in the fetched text (historically 24 fps for Wan 2.x; unverified).
- Wan 3.0 duration, resolution and ratio parameter names were not extractable (the parameter tables collapsed in the scrape).

---

## 9. Wan — negative prompt, seed, prompt_extend, audio, watermark

### Takeaway
Wan supports **`negative_prompt`**, **`seed`**, **`prompt_extend`** (smart rewrite), **`watermark`**, and on 2.6-flash an **`audio`** boolean that can force silent output. `wan2.6-i2v-flash` produces audio by default, and its silent output is billed at **half price**.

### Cited Findings
- The 2.6 i2v request parameters include `negative_prompt`: "Use the negative_prompt parameter to prevent 'flowers' from appearing in the generated video." The official samples show `negative_prompt="", seed=12345, prompt_extend=True, watermark=True, resolution="720P", duration=10, shot_type="multi"`. — [Wan i2v API reference](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference); [Wan i2v guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Silent video: "`wan2.6-i2v-flash`: Generates audio-enabled videos by default. To generate a silent video, explicitly set `audio=false`. Even if you pass an `audio_url`, the output remains silent when `audio=false`. You are billed for silent videos." Wan 2.2 and earlier are silent by default. — [Wan i2v guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Automatic dubbing and custom audio (`audio_url`) are supported only by Wan 2.5 and 2.6. — [Wan i2v API reference](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)
- The `parameters` object controls "resolution, duration, prompt rewriting, and watermarks" (Wan 2.7). — [Wan 2.7 i2v API ref](https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference)

### Inferences
- Wan fits "negative prompt + no text in frame" well: put `text, subtitles, captions, watermark, logo` in `negative_prompt` and set `watermark=false`.
- Consider `prompt_extend=false` to keep historical-costume prompts literal. The rewrite may modernize details; this is an inference, not documented.

### Gaps
- Defaults not verified: whether `prompt_extend` and `watermark` default to true or false, the `negative_prompt` maximum length, the `seed` range, and whether `wan2.6-i2v` (non-flash) supports `audio=false`.
- Whether Wan 2.7 and Wan 3.0 accept `negative_prompt` (tables collapsed).

---

## 10. Wan / HappyHorse — pricing, free quota, async and URL expiry

### Takeaway
Only output seconds are billed, and failures are free. In the **Singapore** list prices:

| Model | 720p | 1080p | Notes |
| --- | --- | --- | --- |
| `wan2.6-i2v-flash` | $0.05/s | $0.075/s | silent: $0.025 / $0.0375 |
| `wan2.6-i2v` | $0.10/s | $0.15/s | |
| `wan2.7-i2v` | $0.10/s | $0.15/s | |
| `happyhorse-1.1-i2v` | $0.14/s | $0.18/s | |
| `wan3.0-video` | $0.10/s | $0.20/s | list, 30% off promo |
| `wan3.0-video-prime` | $0.14/s | $0.28/s | |

Other regions, including **US (Virginia)**, are about 12–15% cheaper but have **no free quota**. The free quota in Singapore is 50 s for Wan 2.x, 10 s for HappyHorse and 30 s for Wan 3.0, valid 90 days. Video URLs and task IDs **expire after 24 h**.

### Cited Findings
- Wanx image-to-video first frame, Singapore:
  - `wan2.6-i2v-flash`: audio video 720P $0.05/s, 1080P $0.075/s; silent video 720P $0.025/s, 1080P $0.0375/s; free quota 50 s.
  - `wan2.6-i2v`: 720P $0.10/s, 1080P $0.15/s; 50 s.
  - `wan2.5-i2v-preview`: 480P $0.05, 720P $0.10, 1080P $0.15.

  Beijing: 2.6-flash audio $0.043006 (720P) / $0.071676 (1080P); 2.6 $0.086012 / $0.143353. — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- Wanx image-to-video (2.7): `wan2.7-i2v` Singapore 720P $0.10/s, 1080P $0.15/s, 50 s free; Beijing $0.086012 / $0.143353. — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- HappyHorse i2v (first frame): `happyhorse-1.1-i2v` Singapore 480P $0.07, 720P $0.14, 1080P $0.18 /s, 10 s free. US (Virginia), "Global" scope: $0.0618845 / $0.123769 / $0.165026. `happyhorse-1.0-i2v` 720P $0.14, 1080P $0.24 (Singapore). — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- Wan 3.0 (input+output video seconds billed): `wan3.0-video` Singapore list 480P $0.05, 720P $0.10, 1080P $0.20 /s ("Limited-time 30% off"). `wan3.0-video-prime` $0.068 / $0.14 / $0.28. US (Virginia): wan3.0-video 1080P $0.165025 list; prime 1080P $0.254399. Free quota is 30 s (Singapore only). — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- "Free quota… Valid for 90 days from the date of Model Studio activation… only in Singapore." "Failed requests incur no cost and do not consume your free quota." — [Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- Async flow: task states go PENDING → RUNNING → SUCCEEDED/FAILED. Poll about every 15 s; tasks typically take 1–5 min. "Video URLs are valid for only 24 hours and then automatically purged." `task_id` is valid for 24 h, after which the status is `UNKNOWN`. — [Wan i2v API reference](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)

### Inferences
- Episode cost for 10 × 6 s at 1080p (60 s):

| Model | Region | Cost per episode |
| --- | --- | --- |
| `wan2.6-i2v-flash`, silent | Singapore | about **$2.25** |
| `wan2.6-i2v-flash`, with audio | Singapore | about $4.50 |
| `wan2.6-i2v` / `wan2.7-i2v` | Singapore | about $9.00 |
| `happyhorse-1.1-i2v` | Singapore | about $10.80 |
| `happyhorse-1.1-i2v` | US | about $9.90 |
| `wan3.0-video` | Singapore, list price | about $12 |

  Retries cost extra.

### Gaps
- US (Virginia) prices for `wan2.6-i2v(-flash)` were not extracted; that table was cut off in the scrape.

---

## 11. Wan — content moderation and watermark

### Takeaway
All inputs and outputs are moderated. Violations return `DataInspectionFailed` or `IPInfringementSuspect`. Alibaba documents no real-face ban comparable to Seedance's, and its own demos animate photorealistic people. The watermark is controlled by the `watermark` boolean.

### Cited Findings
- "Content moderation: All inputs (prompts, images) and output videos are subject to content moderation. Violations result in an `IPInfringementSuspect` or `DataInspectionFailed` error." — [Wan i2v API reference](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)
- The official examples include a realistic person lip-syncing from a single photo ("Makes characters in photos speak or sing"). — [Wan i2v guide](https://www.alibabacloud.com/help/en/model-studio/image-to-video-guide)
- Known issue: wan2.6-i2v-flash may stall for about 1 s near the 3 s mark on rotating circular objects; Alibaba suggests Wan 2.7 instead. — [Wan i2v API reference](https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference)

### Inferences
- Historical ethnographic portraits are unlikely to trip a celebrity or IP filter, but there is no explicit policy statement on this.

### Gaps
- Whether output carries C2PA or invisible watermarks was not documented in the fetched pages.

---

## 12. Other first-party video APIs: which are usable?

### Takeaway
- **Usable first-party APIs found:**
  - Pruna P-Video: US/EU company, cheap, 9:16 and 1080p, but needs an input image.
  - Adobe Firefly Video API (`/v3/videos/generate`): 5 s only, enterprise Firefly Services access.
  - Tencent Hunyuan Video: China site only.
  - Zhipu CogVideoX-3 on bigmodel.cn: China.
- **Not usable or not fit:**
  - Amazon Nova Reel: 1280×720 only, no 9:16, and v1:0 reached EOL on 2026-09-30.
  - Midjourney: no official API.
- **Not verified:** Stability AI, Meta, Moonshot and StepFun (no first-party video API found in this pass).

### Cited Findings
**Pruna P-Video**
- API endpoint `https://api.pruna.ai/v1/predictions`, header `apikey: YOUR_API_KEY`, async status URL `https://api.pruna.ai/v1/predictions/status/<id>`.
- Pricing: 720p $0.02/s and 1080p $0.04/s, or $0.005 / $0.01 in draft mode.
- Aspect ratios 16:9, 9:16, 1:1, 4:3, 3:4. Examples run at 24 fps and 48 fps. Native audio (can be off: "no-audio" example) and custom audio input.
- "P-Video requires an input image to work properly."

  — [Pruna docs: P-Video](https://docs.pruna.ai/en/stable/docs_pruna_endpoints/performance_models/p-video.html)
- The Pruna homepage lists a newer `p-video-2` at "$0.025 per second 720p" and "$0.045 per second 720p" (search snippet; probably P-Video-2 vs P-Video-2-Pro). — [pruna.ai](https://www.pruna.ai/)
- A third-party site lists P-Video 2 Pro at 5–15 s, 480p/768p, 24 fps, first and last frames. — [Wiro.ai (third-party)](https://wiro.ai/models/pruna/p-video-2-pro)

**Amazon Nova Reel**
- 1280x720, 24 fps, 6 s increments up to 2 min, English prompts only. `amazon.nova-reel-v1:1` is only in us-east-1. Async (`StartAsyncInvoke`) with output written to S3. — [AWS Nova user guide](https://docs.aws.amazon.com/nova/latest/userguide/video-generation.html)
- The model card lists `amazon.nova-reel-v1:0` as "Legacy (EOL: 2026-09-30)" in us-east-1, eu-west-1 and ap-northeast-1. Nova Reel 1.1 adds Content Credentials. — [Bedrock model card: Nova Reel](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-reel.html); [AWS AI Service Card](https://docs.aws.amazon.com/ai/responsible-ai/nova-reel/overview.html)

**Midjourney**
- Video is in the web app only: 5 s clips extendable by 4 s up to 21 s, SD 480p or HD 720p, start and end frames. The docs mention no API. — [Midjourney docs: Video](https://docs.midjourney.com/hc/en-us/articles/37460773864589-Video)
- "Does Midjourney have an official API in 2026? No." (third-party, Jun 2026). — [Wireflow](https://www.wireflow.ai/blog/best-midjourney-api-tools-in-2026)

**Adobe Firefly**
- Firefly API reference covers "video generation" (REST). — [Firefly API Reference](https://developer.adobe.com/firefly-services/docs/firefly-api/api/)
- Adobe Community: "text-to-video generation is available via the Firefly API. The generateVideoV3 endpoint…" — [Adobe Community, Aug 2026](https://community.adobe.com/questions-404/does-adobe-firefly-ai-supports-text-to-video-api-calls-1639384)
- Third-party summary of Adobe docs: fixed 5-second clips at 24 fps in 540p, 720p or 1080p; 20, 50 or 100 credits per second of output at 540p, 720p and 1080p respectively; endpoint `/v3/videos/generate`. — [AI Tool Blog (third-party)](https://aitool-blog.com/firefly-video/)

**Tencent Hunyuan Video (China)**
- API domain `vclm.tencentcloudapi.com`, with `SubmitHunyuanToVideoJob` (30 req/s) and `DescribeHunyuanToVideoJob` (20 req/s). Image-to-video "general" jobs are also available, and Vidu and Kling are resold through the same product. — [Tencent Cloud API overview (cn), Jul 2026](https://cloud.tencent.com/document/api/1616/107795)
- Billing: Hunyuan text/image-to-video costs 1.5 credits per 5 s 720p clip and 3 credits per 5 s 1080p clip. New users get 50 free credits (1 year, concurrency 1). Failed jobs, including moderation failures, are free. The service is migrating to TokenHub, and the old platform has stopped new purchases. — [Tencent Cloud billing (cn), Jun 2026](https://cloud.tencent.com/document/product/1616/118994)
- "积分单价为1元/积分" (1 credit = ¥1), from a search snippet of the same page. — [Tencent Cloud billing](https://cloud.tencent.com/document/product/1616/118994)
- The only video doc found on the international tencentcloud.com site was the Digital Human "Video Generation Service", not Hunyuan Video. — [tencentcloud.com doc](https://www.tencentcloud.com/document/product/1211/62083)

**Zhipu CogVideoX-3 (bigmodel.cn)**
- 5 s or 10 s, multi-resolution up to 4K, image/text/first+last-frame input, **¥1 per call**, `zai-sdk`. — [BigModel docs: CogVideoX-3](https://docs.bigmodel.cn/cn/guide/models/video-generation/cogvideox-3)
- Batch pricing mentions "图生视频1080p / 720p 1.25 元" (snippet). — [BigModel pricing](https://docs.bigmodel.cn/cn/guide/start/pricing)

### Inferences
- **Hunyuan 1080p** works out to about ¥3 per 5 s, roughly $0.08/s. It requires a Tencent Cloud China account, which for cloud.tencent.com normally means mainland real-name verification. That last point is general knowledge, not verified here, so treat Hunyuan as effectively unusable for a US individual.
- **Pruna P-Video** is the only "other" option that is clearly accessible to a US individual and natively supports 9:16 1080p I2V at a low price ($0.24 per 6 s clip at 1080p). Its negative-prompt and seed support were not verified.
- **Firefly**'s fixed 5 s length cannot produce the 6 s clips. Its API access is part of Firefly Services, which is usually enterprise-contracted (unverified).
- **Nova Reel** fails the 9:16 and 1080p requirements.

### Gaps
- Stability AI, Meta (Movie Gen), Moonshot, StepFun: not researched to primary sources in this pass, and no first-party public video API was found for them. Stability's Stable Video Diffusion API status in 2026 is unverified.
- Nova Reel v1:1 lifecycle and EOL date, and any Nova successor video model.
- Pruna parameter names (negative prompt, seed, duration range, last frame) and signup terms.
- Firefly Video API entitlement for individual developers, 9:16 support, and negative-prompt support.
- CogVideoX-3 international availability via z.ai, and its negative-prompt and 9:16 parameters.
