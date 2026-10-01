# Project instructions

## Podcast manuscript work

- Before creating or revising a podcast manuscript, read `podcasts/节目档案.md`, the latest `podcasts/制作与文稿审核*.md`, and the target episode's outline, source notes, fact-check, quality report, and current script. User feedback takes precedence over all style samples.
- For the current EP06 revision, the user clarified that “上一次” means the previous episode about 徐阶 (EP05), not the previous EP06 draft. Read EP05's script to identify what made it engaging; do not treat a rejected EP06 draft or the previous agent's prose as the style target.
- Aim for an engaging, conversational two-host exchange. Let specific events and evidence move the story; give each host a real point of view. Be creative with structure and interpretation, but do not invent historical facts, dialogue, motives, private scenes, or audience reactions.
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
     - Brand badge: `笑 谈 历 史 · EPxx` (Gold `#F0CD6E`).
     - Pre-title & subtitle with multi-directional drop shadow and subtle top dark gradient for 100% readability.
     - Bottom-left: `主播：大开 × 小李` (White).
     - Bottom-right: 2×2 ancient seal with Vermilion Red background, Gold border, and traditional 4-character seal script text (reading right-column top-to-bottom, left-column top-to-bottom).
     - Save self-contained `make_cover.py` in the episode directory.

