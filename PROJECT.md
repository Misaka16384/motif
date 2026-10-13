---
created_by: research-talk-development
schema: 1
title: Research Talk skill development
---

# Research Talk — development handoff

## Agreed intent

Build a lightweight, distributable skill for researchers who know their work. The model collaborates on one central question, creates a meaningful pilot when useful, completes approved work autonomously including review, and supports human preview/revision before resolving final output format. These are judgment-guiding defaults, not a scripted interview or fixed state machine.

## Required behavior

- Actively discover marked local talk projects and ask which to resume when not already specified.
- Maintain PROJECT.md for handoff between agents; preserve decisions and distinguish plans, implementations, renders and verification.
- Detect dependencies; offer project-level or user-level shared setup before installation.
- Use the standard Agent Skills layout and a single-command installer from a Git repository.
- Retain practical rendering, cache, memory, interruption and playback lessons in the skill.
- PPTX must autoplay on slide entry; verify Office and WPS behavior before claiming compatibility.
- Keep scripts limited to deterministic local operations; narrative and workflow decisions remain with the model/user.
- Public READMEs must not disclose the user's name, paper identifiers or source-paper links; demonstration descriptions stay generic.

## Current state

- Version: 0.1.0 released; native-autoplay correction 0.1.1 implemented and under verification.
- Implemented: core skill, references, generic starter, local project discovery/setup/build/check/export/preview, logic tests, release packaging.
- Passed: package/skill validation, 26 logic tests (one Windows-only symlink skip), actual formula compilation and smoke render, final 2560×1440/60 fps render, frame-cadence checks, HTML/PPTX export, and cache reuse.
- Independent review: completed; findings about early setup, environment replacement discovery, ZIP layout, scene selection and video timing/target validation were corrected and rechecked.
- Generic example: `examples/demo/`; final export pointer: `examples/demo/deck/latest-final.json`. Generated files are excluded from Git/distribution.
- Player verification: package, H.264/yuv420p and automatic-start timing checks passed; actual browser/Office/WPS playback has not been tested. WPS executable was not found on this host during detection.
- Publishing: user explicitly approved the public repository, now available at `https://github.com/Misaka16384/research-talk`.
- Cross-platform CI: Ubuntu and Windows jobs passed for commit `9795716` (run `38360587231`).
- Release archives: standalone skill and optional plugin ZIPs built locally for 0.1.0.
- Installer integration: `skills` 1.7.2 installed from the public repository into an isolated project; copied CLI, starter resources, project creation and discovery passed. Host execution was needed for this machine's Git credentials; no global skills/settings were changed.
- Documentation: complete English/Chinese READMEs; independently reviewed against the implementation and corrected. User authorized three public-paper animation excerpts for demonstration.
- Demonstrations: three inspected GIFs (2.15 MB total) and 1440p60 MP4s prepared. Local links and both release ZIPs verified; source talk remains untouched.
- Release: `https://github.com/Misaka16384/research-talk/releases/tag/v0.1.0`; standalone skill/plugin ZIPs and all three MP4 excerpts uploaded and verified against expected filenames/sizes.
- Release CI: validation and publishing passed for commit `e16bf00`; release run `38363506680`, validation runs `38363502752` and `38363506762`.
- No private scientific source material is included.

## Autoplay follow-up

- User confirms the corrected reference presentation plays automatically in Office and WPS; no application versions were supplied. This is reference-specific human evidence, not a fresh export test.
- Static comparison found identical embedded videos; the corrected export adds a native media-play command triggered with the slide. Zero-delay-only media timing was insufficient.
- Shared export now normalizes the native command/main-sequence timing and validates its activation path. A separate click-to-pause branch is retained. The normalizer preserves other XML/media and rejects unrelated animations.
- Passed: raw/click-trigger exports rejected, corrected reference and normalized copy accepted across 104 slides. All 104 timing trees match the corrected reference; all 104 videos, 118 relationships and other package members remain unchanged. Original input hashes preserved.
- Passed: actual cached-media HTML/PPTX export, no render-cache changes, new exports still marked `player_tested=false`. Evidence: local `.runtime/autoplay/` reports (excluded from publication).
- Review found and corrected three validation/guard gaps; corresponding regression cases and the independent focused recheck pass. Pending: release 0.1.1.
- Public README anonymity is enforced for this project; the previous plugin ZIP was replaced with anonymized documentation.

## Next step

Publish correction 0.1.1 and verify the release workflow/assets. Keep the reference deck intact. Distinguish the user's real-player evidence for the reference artifact from fresh exports' package checks.
