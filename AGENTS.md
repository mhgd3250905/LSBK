# Project instructions

## Topic-planning collaboration

- For topic-selection (选题) work, start from `podcasts/节目档案.md` ("已挖的坑" topic pool plus per-episode archive) and pitch via the 选题三要素 (a fleshed-out protagonist with an extreme contradiction / a verifiable dark-humor set piece from official history / a human-nature question that travels to the present). Follow any episode's `选题卡.md` format, including the "九型公式" headline candidates. Do not start production on a new episode without user approval of the topic.

## Podcast manuscript work

- Before creating or revising a podcast manuscript, read `podcasts/节目档案.md`, `podcasts/AI书写规范.md` (the single consolidated writing/de-AI rules doc; rule revisions go there first, not into the review retrospectives), the latest `podcasts/制作与文稿审核*.md` (kept as background/evidence), and the target episode's outline, source notes, fact-check, quality report, and current script. User feedback takes precedence over all style samples.
- For the current EP06 revision, the user clarified that “上一次” means the previous episode about 徐阶 (EP05), not the previous EP06 draft. Read EP05's script to identify what made it engaging; do not treat a rejected EP06 draft or the previous agent's prose as the style target.
- Aim for an engaging, conversational two-host exchange. Let specific events and evidence move the story; give each host a real point of view. Be creative with structure and interpretation, but do not invent historical facts, dialogue, motives, private scenes, or audience reactions.
- **坚决消灭流水账，确立影视化听感（2026-10-14 用户最高指示）**：严禁写成跨年份罗列史料、比对文献数字的“论文式对账流水账”。每期文稿必须二选一：① **大主角命运叙事（首选）**：必须有一个故事主角，通过其具体血肉丰满的生命经历与命运起伏，见微知著折射时代变局，让听众有极强代入感与共鸣；② **绝对话题中心推演（备选）**：若无连续主角，必须围绕一个绝对核心命题/体制死结层层递进推演。冷开场必须影视级高潮抓人，考据留在幕后，人性与戏在台前。
- Avoid formulaic transitions, repeated summaries or rhetorical questions, abstract wrap-ups, forced metaphors, and over-explaining. Do not copy another show's catchphrases or mannerisms from `06-style-samples.md`.
- Keep factual accuracy, evidence boundaries, two-speaker voice, and Markdown as the source of truth as hard requirements. Episode duration and per-act word counts are estimates, not quotas; never add filler to hit them.
- For manuscript-only requests, edit Markdown and regenerate the matching TXT with `md_to_timeline.py`; do not create or modify audio unless the user explicitly asks. Preserve unrelated existing files and changes.
- Do not claim a script was read aloud, blind-read, or audio-tested unless that review actually happened. State estimated duration and distinguish the current manuscript from audio made from an earlier version.

## Podcast cover production

- All podcast episode covers must follow the hybrid workflow established in EP09/EP10:
  1. **AI Scene Background**: Use `generate_image` to generate a 1:1 thematic cinematic or ink-wash visual background. **Crucial composition rule**: explicitly specify that the main subjects (characters, architecture, action) are placed in the lower 50% of the canvas, while the upper 40-50% must be clean, expansive dark atmospheric negative space (storm clouds, night sky, misty eaves, etc.) with strictly zero text/letters/calligraphy. Save as local `cover_bg.jpg` in the episode folder.
  2. **Automated Python Assembly**: Assemble the final 3000x3000px cover via Python PIL with automated adaptive typography:
     - Main title width must be dynamically clamped to ≤2150px (ensuring ≥425px safe margins on both left and right, well within the 85px frame line).
     - Standard dual-line border (gold outer, thin white inner).
     - Brand badge: `笑 谈 历 史 · EPxx` (第一季明朝篇) / `笑 谈 历 史 · S2Exx` (第二季宋朝篇) (Gold `#F0CD6E`).
     - Pre-title & subtitle with multi-directional drop shadow and subtle top dark gradient for 100% readability.
     - Bottom-left: `主播：大开 × 小李` (White).
     - Bottom-right: 2×2 ancient seal with Vermilion Red background, Gold border, and traditional 4-character seal script text (reading right-column top-to-bottom, left-column top-to-bottom).
     - Save self-contained `make_cover.py` in the episode directory.

