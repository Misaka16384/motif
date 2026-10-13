---
created_by: motif-development
schema: 1
title: Motif skill development
---

# Motif — development handoff

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

- Brand: Motif — 3Blue1Brown-inspired research presentations. User authorized renaming the public repository, skill entry point, docs and package identifiers consistently.
- Version: 0.2.0 released as Motif; rename, legacy-project compatibility, packaging, CI and isolated public installation verified. Earlier tags/releases remain preserved.
- README follow-up: English/Chinese installation entry points now share a human/AI-readable checklist; the copyable prompt only needs the repository link and installation intent. Package validation, source/ZIP parity and 24 links/anchors checked. No toolkit or skill behavior change; existing release archives remain unchanged.
- Implemented: core skill, references, generic starter, local project discovery/setup/build/check/export/preview, logic tests, release packaging.
- Passed: package/skill validation, 35 logic tests (one Windows-only symlink skip), actual formula compilation and smoke render, final 2560×1440/60 fps render, frame-cadence checks, HTML/PPTX export, and cache reuse. Rendering/player evidence is from earlier releases; this rename does not claim a new render or player test.
- Independent review: completed; findings about early setup, environment replacement discovery, ZIP layout, scene selection and video timing/target validation were corrected and rechecked.
- Generic example: `examples/demo/`; final export pointer: `examples/demo/deck/latest-final.json`. Generated files are excluded from Git/distribution.
- Player verification: package, H.264/yuv420p and automatic-start timing checks passed; actual browser/Office/WPS playback has not been tested. WPS executable was not found on this host during detection.
- Publishing: user explicitly approved the public repository; canonical URL is `https://github.com/Misaka16384/motif` with the approved subtitle in its description.
- Cross-platform CI: Ubuntu and Windows jobs passed for commit `9795716` (run `38360587231`).
- Release archives: standalone skill and optional plugin ZIPs built locally for 0.1.0.
- Installer integration: `skills` 1.7.2 installed from the public repository into an isolated project; copied CLI, starter resources, project creation and discovery passed. Host execution was needed for this machine's Git credentials; no global skills/settings were changed.
- Documentation: complete English/Chinese READMEs; independently reviewed against the implementation and corrected. User authorized three public-paper animation excerpts for demonstration.
- Demonstrations: three inspected GIFs (2.15 MB total) and 1440p60 MP4s prepared. Local links and both release ZIPs verified; source talk remains untouched.
- Release: `https://github.com/Misaka16384/motif/releases/tag/v0.1.0`; standalone skill/plugin ZIPs and all three MP4 excerpts uploaded and verified against expected filenames/sizes.
- Release CI: validation and publishing passed for commit `e16bf00`; release run `38363506680`, validation runs `38363502752` and `38363506762`.
- No private scientific source material is included.

## Autoplay follow-up

- User confirms the corrected reference presentation plays automatically in Office and WPS; no application versions were supplied. This is reference-specific human evidence, not a fresh export test.
- Static comparison found identical embedded videos; the corrected export adds a native media-play command triggered with the slide. Zero-delay-only media timing was insufficient.
- Shared export now normalizes the native command/main-sequence timing and validates its activation path. A separate click-to-pause branch is retained. The normalizer preserves other XML/media and rejects unrelated animations.
- Passed: raw/click-trigger exports rejected, corrected reference and normalized copy accepted across 104 slides. All 104 timing trees match the corrected reference; all 104 videos, 118 relationships and other package members remain unchanged. Original input hashes preserved.
- Passed: actual cached-media HTML/PPTX export, no render-cache changes, new exports still marked `player_tested=false`. Evidence: local `.runtime/autoplay/` reports (excluded from publication).
- Review found and corrected three validation/guard gaps; corresponding regression cases and the independent focused recheck pass.
- Release 0.1.1 published: `https://github.com/Misaka16384/motif/releases/tag/v0.1.1`. Cross-platform validation and release jobs passed for commit `1117ca5` (runs `38367353829`, `38367358760`, `38367358741`). Both release ZIPs present.
- Public README anonymity is enforced for this project; the previous plugin ZIP was replaced with anonymized documentation.

## Next step

No authorized implementation remains after pushing the README-only follow-up. Minimal installation prompt: read the Motif repository and install following its README. Verification: package validator and packaging exited 0; 24 source/ZIP links and heading anchors passed; no personal names, paper identifiers or private artifacts added. Local regenerated ZIPs: `.runtime/readme-guided/dist/`; no new release requested. Existing Motif v0.2.0 release remains preserved at `https://github.com/Misaka16384/motif/releases/tag/v0.2.0`. Tagged source commit `ea680d9`; Windows/Linux validation and release jobs passed (runs `38387798899`, `38387879961`, `38387879900`). Both assets verified: `motif-skill-0.2.0.zip` (56,153 bytes), `motif-plugin-0.2.0.zip` (2,134,822 bytes). Original demo videos remain under the renamed repository's v0.1.0 release.

Local evidence: `.runtime/verify-motif/` (35 tests; existing demo/trial status, doctor and discovery passed; 88 config/record/settings paths unchanged). Final ZIP audit passed after correcting packaged README development-state links. Installer `skills` 1.7.2 installed Motif into an isolated project for Codex/Claude Code; all 28 skill files match the pushed source, and the copied CLI's help/init/discover/status passed. No global skill/config installation, new render or native player check was performed. Reports: `report-final.md`, `installer-report.md`. Initial network timeouts recovered with bounded retries; no global Git transport setting changed.

Source checkout path remains unchanged to preserve generated local media/cache references; no private talk or ignored trial artifacts are renamed. Legacy project markers, registry override/default location and copied-scene rendering variables remain supported; new public names and markers use motif/Motif/MOTIF_HOME.

Previous release v0.1.2 remains preserved at `https://github.com/Misaka16384/motif/releases/tag/v0.1.2`; both standalone skill and plugin ZIPs verified present (56,156 and 2,134,434 bytes). Tagged commit `ea0059d`; Windows/Linux validation and release workflows passed (runs `38374724555`, `38374730440`, `38374730351`).

Local validation: `.runtime/verify-012/verification.json` and command logs; 30 tests passed (one Windows symlink skip), package validation and both ZIPs passed. Actual trial status reduced from 1,096 lines to 90, preserving current scene states, latest exports and `player_tested=false`; full records remain in `--verbose`. Management/configured/explicit Python labels, known-environment probing and non-executing reuse plan passed; manifests, registry and media records stayed unchanged. Platform audit found no macOS-specific blocker, but macOS runtime remains untested. Host CLI agents resolve platform prerequisites; independent work continues when a dependency is unavailable.

Local trial report: `.runtime/user-trial-20261013/report.md`. Trial created three new scenes/ten beats at 720p30 and inspected 30 keyframes. Author replies/handoff were simulated by the same evaluator; browser/Office/WPS playback and fresh installation were not tested. Trial artifacts remain local and excluded from publication.
