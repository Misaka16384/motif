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

- Version: 0.1.0 released; implementation, documentation and demonstration media complete.
- Implemented: core skill, references, generic starter, local project discovery/setup/build/check/export/preview, logic tests, release packaging.
- Passed: package/skill validation, 16 logic tests (one Windows-only symlink skip), actual formula compilation and smoke render, final 2560×1440/60 fps render, frame-cadence checks, HTML/PPTX export, and cache reuse.
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

## Next step

The requested implementation and publication are complete. Continue from the next user-selected talk or requested toolkit revision. Actual browser/Office/WPS playback remains a separate verification task on a suitable presentation machine; do not claim WPS/Office autoplay was observed from XML checks alone.
