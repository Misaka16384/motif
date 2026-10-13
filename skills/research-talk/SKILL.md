---
name: research-talk
description: Collaborate with a researcher to create or revise an academic talk using explanatory Manim animations and interactive slides. Use for shaping a research narrative, continuing a local talk project, producing a deck, or reviewing its scientific and visual clarity.
license: MIT
---

# Research Talk

Work with an author who knows their research. Help sharpen and express their ideas; leave room for their judgment and yours. Explicit user instructions take precedence over these defaults.

## Start or resume

1. Locate this skill's `scripts/talk.py`. Run `discover` in the current workspace; it also checks previously registered projects and configured search roots. Search is bounded. Do not scan entire drives or read unrelated research.
2. If the user has not already selected a project, briefly show discovered projects, their current stage, and next step; ask which to continue or whether to start a new one. Do not repeat this question inside an active project or after an explicit continuation request.
3. Read the selected project's `PROJECT.md`, then only the relevant linked files. Check that referenced outputs exist before reporting them as available. Use `init` for a new project; never overwrite an existing project to restart it.
4. On first use, proactively detect available environments with `doctor`. Check its selected Python and reuse candidates before proposing installation: missing packages in the management Python do not imply an existing rendering environment is missing. Probe an author-supplied environment explicitly when needed. Complete setup and smoke testing when animation production is authorized; discussion-only work can proceed without them. Show reuse candidates, missing dependencies and proposed locations, then ask once whether to use a project or user-level shared environment if the scope is unresolved. Execute within that agreed scope. Read [operations](references/operations.md) for commands and external dependencies.

The skill itself can be installed at project or user scope; the rendering environment has its own independent scope. Installing this skill does not authorize system-wide package installation, public publishing, or changes to unrelated settings.

## Align before producing

Read the supplied material and the author's intentions first. Summarize a candidate **seed**: the reason for the talk and the one root question it answers. Ask a pointed follow-up only where ambiguity changes the narrative. Offer a grounded interpretation or a choice between plausible emphases instead of an intake questionnaire.

Keep the agreed root question as one sentence near the top of `PROJECT.md`. Local questions should advance it. Let audience, scientific contribution, evidence, and time determine the structure; paper order and page counts are flexible.

When the user wants discussion only, discuss and record decisions without starting production. A useful default route is: **interview and align → preview an important fragment → user approves the approach → complete the draft and review autonomously → human preview and revision → choose final HTML or PPTX output**. This is a collaboration guide, not a mandatory state machine. Adapt stages, depth, and timing to the user's explicit choices and the project's actual needs.

When a pilot is useful, select a fragment that demonstrates the central mechanism, not merely a title card. Record what the user approved. Once the user authorizes autonomous production, complete all parts, perform checks and review, and fix findings without per-part approval questions. Keep progress visible and state current. Ask again only when an essential missing fact or authorization genuinely prevents work.

## Make the explanation visible

- Present a physical or mathematical reason to care before introducing technical notation.
- Show what a new symbol denotes at first appearance. Connect each important formula term to the corresponding object through position, color, highlighting, or transformation.
- Use animations to demonstrate mechanisms and reasoning. Preserve visual identity when an object reappears in another part of the story.
- Explain the simplest useful case thoroughly. Spend time on a more complex case when it adds a new insight; otherwise show the result concisely.
- Give each page or beat a clear purpose. Freeze key states for live explanation. Keep on-screen text academic and economical.
- Adapt the starter palette, language, and pacing to the project. They are defaults, not requirements for every talk.
- Verify scientific claims against the relevant primary source/version or an explicit calculation. Keep attribution, assumptions, and disclosure boundaries clear. Related mechanisms do not automatically imply inclusion or equivalence of concepts.

Read [review principles and examples](references/review.md) when designing animations or consolidating feedback. Use the shared starter components rather than copying topic-specific scientific content into unrelated projects.

## Produce and review

Use `talk.toml` as the single scene list for rendering, checking, previewing, and export. Keep calculations/data separate from visual choreography when it improves correctness. Declare extra source/data dependencies for cache invalidation.

Iterate at preview resolution. Review actual key frames and selected animation intervals; metadata checks and geometry checks cannot certify understanding or flawless layout. An independent review is particularly useful after a complete draft, and should be included when requested. Choose its depth and timing according to the work. Give the reviewer the author's accumulated decisions and actual rendered draft; inspect scientific accuracy, audience comprehension, narrative drift, and visual issues. Ask for concrete findings, integrate supported fixes, and recheck affected content. If subagents are unavailable, record a separate review pass without calling it independent.

Consolidate human-preview feedback into principles and apply it across the deck. Agree on story changes before bulk revision when the user requests that workflow. Once the draft is accepted, resolve the final output choice: HTML, PPTX, or both. Ask if it has not already been specified. Internal HTML previews do not select the final delivery format. Render the chosen final profile after content is stable.

HTML includes its sibling assets folder unless one-file mode is requested. PPTX embeds videos with one slide per beat, not editable formulas. Read the [native autoplay mechanism](references/pptx-autoplay.md) for PPTX export: a zero-delay media node alone failed in WPS, so preserve and validate the native slide-entry play effect. Verify actual slide-entry playback in **both Microsoft PowerPoint and WPS Presentation** where those applications can be run. Do not trigger Play manually to prove autoplay. Record tested application/version and behavior; XML checks alone do not establish player compatibility. If either application is unavailable, state the verification gap and obtain a real-player check rather than claiming compatibility.

Read [rendering pitfalls](references/rendering.md) before long/high-resolution rendering or investigating interruptions and playback.

## Keep the handoff current

Actively update `PROJECT.md` after substantive decisions, completed revisions, reviews, successful or interrupted builds, and before yielding or compaction. Record:

- the seed and agreed decisions, including audience and disclosure limits;
- what is planned, implemented, rendered, and actually verified;
- the latest usable output paths and relevant evidence/review files;
- unresolved discussion separately from authorized next actions;
- the exact next step, plus any active process or interruption.

Use the tool's compact `status` output and run logs for execution facts; request `status --verbose` when full records are needed. Recorded progress is not a fresh media check. Preserve the project marker. Keep this file short and link to detailed storyboards/reports. The primary agent maintains it; subagents return reports for integration rather than concurrently rewriting it. Store private research only inside its authorized project, never in the shared skill or a public release.
