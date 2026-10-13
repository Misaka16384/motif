# Motif

**3Blue1Brown-inspired research presentations.**

Build your talk around one question, and make the reasoning visible through animation.

A lightweight [Agent Skill](https://agentskills.io/) for researchers preparing academic talks with explanatory Manim animations. It helps an author and an agent sharpen the talk's starting question, develop a coherent narrative, build a meaningful pilot, and finish a reviewed presentation.

[中文说明](README.zh-CN.md) · [Install](#install) · [Skill instructions](skills/motif/SKILL.md) · [Releases](https://github.com/Misaka16384/motif/releases)

## See the approach

These animation excerpts show three uses of animation: building a pattern from a local rule, connecting a formula to its physical objects, and exposing the constraint behind a mobility rule.

### A local rule becomes a global pattern

[![A cellular automaton generates a symmetry pattern](docs/demos/ca-pattern.gif)](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-ca-pattern.mp4)

The construction is shown before its notation becomes central. [Watch or download the 1440p60 excerpt](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-ca-pattern.mp4).

### A formula stays connected to the figure

[![Formula terms correspond to objects on a lattice](docs/demos/formula-to-figure.gif)](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-formula-to-figure.mp4)

Objects, colors and formula terms retain their correspondence as the calculation unfolds. [Watch or download the 1440p60 excerpt](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-formula-to-figure.mp4).

### A conservation law explains mobility

[![Subsystem charge conservation constrains anyon mobility](docs/demos/mobility-constraints.gif)](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-mobility-constraints.mp4)

The audience sees which charges change under a proposed motion and why a motion is allowed or forbidden. [Watch or download the 1440p60 excerpt](https://github.com/Misaka16384/motif/releases/download/v0.1.0/demo-mobility-constraints.mp4).

The GIFs are small previews. The MP4s preserve the excerpt resolution and frame rate. The skill's starter scenes use a separate generic example; each project's scientific content is developed with its author.

## Install

For guided installation, send your local AI assistant this request:

> Please read https://github.com/Misaka16384/motif and help me install Motif following its README.

### Installation guide for people and AI assistants

For an installation request, use the following checklist and honor choices the user has already specified:

1. **Identify the destination.** Check the current AI host, workspace and any existing Motif installation. Resolve only missing choices: which hosts to install for, and project or user scope. For project scope, use the selected workspace.
2. **Install in the chosen scope.** Resolve the selected host's identifier using [Choose your host](#choose-your-host), then use the standard installer below; add `-g` for user scope. Once the choices are settled, execute without asking for the same approval again. If Node/npm is unavailable, use the host's supported skill-installation method or the standalone ZIP, or agree on the scope of any prerequisite installation.
3. **Verify the installed copy.** Confirm that its `SKILL.md` names `motif`, referenced scripts/assets are present, and the host can discover the skill. If Python 3.10+ is already available, run the installed `scripts/talk.py --help`. Report the installed path and any host reload still needed; file presence alone does not prove that the host has loaded it.
4. **Separate rendering setup.** Preparing a rendering environment belongs to authorized animation production; follow [the environment guide](#environment-a-separate-scope-choice) and the installed skill then. A skill-installation request does not require a demo render or a new talk project.

If local execution is unavailable, explain which steps the user needs to run and leave unperformed verification clearly identified. Keep the remaining work moving when a prerequisite affects only one step.

### Choose your host

Motif's portable entry point is [SKILL.md](skills/motif/SKILL.md); its Python/Manim helpers run through the host's local shell. [agents/openai.yaml](skills/motif/agents/openai.yaml) supplies optional Codex UI metadata. Other hosts use the same skill and resources through their own discovery and invocation mechanisms.

Select the identifier for the host you are using, or the additional hosts the user selected:

| Host | Installer `--agent` identifier |
|---|---|
| Codex | `codex` |
| Claude Code | `claude-code` |
| Gemini CLI | `gemini-cli` |
| OpenCode | `opencode` |
| Qwen Code | `qwen-code` |
| GitHub Copilot | `github-copilot` |
| Cursor | `cursor` |

This is a selection from the installer's [supported agents](https://github.com/vercel-labs/skills#supported-agents); use that list for other hosts and current identifiers. If the installer does not list your host, consult the host's native Agent Skills installation instructions and use the standalone ZIP in its documented skill directory. If native loading is unavailable, the agent can read `SKILL.md` and its linked resources as context; report this as manual use rather than a verified native installation.

Installer support identifies installation targets. Our recorded integration checks cover Codex/Claude Code installation and copied management commands; a complete Motif report workflow has not been tested in every host.

### Installer commands

With Node/npm available, run this in your workspace:

```bash
npx skills add Misaka16384/motif --skill motif
```

The standard [`skills` installer](https://github.com/vercel-labs/skills) lets you choose agents interactively or specify them explicitly. In the templates below, replace `AGENT_ID` with an identifier from the table or supported-agent list. Repeat `-a` for additional selected hosts. Add `-y` after resolving the installation choices to run without installer prompts.

**Project installation** is the default:

```text
npx skills add Misaka16384/motif --skill motif -a AGENT_ID
```

**User-level installation**, available across projects, adds `-g`:

```text
npx skills add Misaka16384/motif --skill motif -a AGENT_ID -g -y
```

No account, MCP server or external generation service is required by this skill. Rendering needs an agent with local file/shell access. The host determines its skill directory and invocation method.

For manual installation, download the **standalone skill ZIP** from [Releases](https://github.com/Misaka16384/motif/releases), then extract `motif/` into your host's skill directory. It contains `SKILL.md` and all resources. The optional **plugin ZIP** preserves the repository/plugin layout; ordinary skill installation needs no additional plugin configuration.

Check for updates with `npx skills check`, then update with `npx skills update`.

For installations under the former `research-talk` name, install using the Motif command above and invoke `motif`; an old skill installation is not renamed automatically. Existing report projects remain readable, and an existing default registry is reused when the new Motif registry has not been created.

## Start a talk

Invoke `motif` using your agent's skill mechanism. For example:

> Use motif to prepare a 40-minute talk from these papers. The audience includes researchers outside my specialty. First discuss the central question and narrative with me. After we approve a mechanism animation as the pilot, complete the draft and review it autonomously.

To resume:

> Use motif to find my existing talk projects and show their current state. Continue the selected project from its recorded next step.

Supply research material, the reason for the talk, and disclosure limits you already know. The agent asks focused questions where the answer affects the story. It proposes a grounded interpretation rather than requiring a fixed questionnaire.

## How collaboration works

1. **Align on the seed.** Identify the reason for the talk and the one root question it answers. Read the research before deciding what belongs in the story.
2. **Preview an important fragment.** Demonstrate a central mechanism, its visual language and pacing. A title card alone cannot establish that an explanation works.
3. **Finish the approved draft.** Once authorized, produce all parts, check them, review the rendered material and fix findings. Preserve progress without repeated per-part approval requests.
4. **Review with the author.** Consolidate feedback into principles and apply them throughout the deck. Agree on substantial story changes before bulk revision when requested.
5. **Choose the delivery.** Resolve HTML, PPTX or both after content acceptance, then render and validate the final profile.

The author and model adapt this route. Page counts, paper order, theme and stage boundaries remain decisions for them. Scripts handle deterministic operations; narrative judgment stays with the author and model.

The skill retains the lessons that mattered in the original talk:

- Give the audience a reason to care before teaching notation.
- Show what each important symbol denotes when it first appears.
- Connect formulas to visible objects and preserve their identity between sections.
- Explain the simplest useful case fully; spend time on complexity when it adds a new insight.
- Hold key states for live explanation, with academic and economical on-screen text.
- Verify claims and attribution; distinguish related mechanisms from equivalence between concepts.

See [the core skill](skills/motif/SKILL.md) and [review examples](skills/motif/references/review.md).

## A project another agent can resume

```text
my-talk/
├── PROJECT.md        # Root question, decisions, state, evidence and next step
├── talk.toml         # One scene list, environment and render profiles
├── anim/             # Agent-written scenes and shared helpers
├── reviews/          # Human feedback, diagnostic frames and review reports
├── .build/           # Per-profile records, logs and isolated media/caches
└── deck/             # Versioned, validated exports
```

The agent actively maintains `PROJECT.md` after decisions, revisions, reviews and interrupted or successful builds. It distinguishes **planned**, **implemented**, **rendered** and **actually verified** work, and records the authorized next action. Detailed storyboards/reports can be linked from this short handoff.

On entry, the skill discovers marked projects in bounded workspace/configured roots and its local registry. It offers continuation when no project has been selected. It does not scan entire drives or repeatedly ask an active project to restart. All runtime resources travel with the installed skill.

The CLI's `status` command shows a compact handoff summary, progress and interruption details. Use `status --verbose` for complete media records and export history; use `check` for fresh validation.

## Environment: a separate scope choice

Installing the skill and preparing the rendering environment are separate decisions.

| Choice | Skill location | Rendering environment |
|---|---|---|
| Project | Current project's agent-skill directory | `<talk>/.venv` |
| User/shared | Host's user skill directory (`-g`) | A dedicated environment in the user's configuration directory |
| Reuse | Either installation scope | An explicitly selected compatible existing environment |

First use detects available tools. When animation production is authorized, the agent offers reuse or scoped setup, completes missing prerequisites within the agreed scope, and runs a small integration test. Discussion can begin beforehand. Reuse does not change an environment's packages; shared setup uses a dedicated virtual environment rather than system Python.

`doctor` labels the Python it checks and lists bounded reuse candidates, including active virtualenv/Conda environments. Missing dependencies in the management Python do not imply that your existing rendering environment is missing. Probe another interpreter with `doctor --python <path>`, then review the provided `setup --reuse` plan before binding it.

The management CLI supports Python 3.10+. The tested rendering baseline uses Manim 0.19.1 and Manim Slides 5.7.0. Starter formulas require LaTeX/dvisvgm. PyAV handles rendering and inspection; a separate FFmpeg executable is optional. Native prerequisites depend on the platform. The agent uses official instructions and records its selected tools.

Windows and Linux have package/logic CI coverage. macOS runtime compatibility has not been verified. The host CLI agent resolves local prerequisites within the agreed scope; the skill does not prescribe a universal system installer. Missing prerequisites only block work that depends on them.

See [local operations](skills/motif/references/operations.md) for detection, installation scope, external prerequisites and exact commands.

## Rendering and review

Defaults are a dark palette, semantic colors, 720p30 previews and **2560 × 1440 at 60 fps** for final output. Pacing, theme and profiles are editable.

The toolkit renders sequentially, isolates media/TeX paths by profile, records processes and run state, and reuses successful fresh scenes. Rendering, checks, previews and export read one scene list. An interruption retains completed work; the agent inspects logs and child processes before resuming.

Checks cover dimensions, decoded frame cadence, stale/missing media, clipping and text/figure collision diagnostics. `preview --sample all` samples actual first, middle and final frames; the default samples final frames. Scientific accuracy, transitions and audience comprehension still require review; zero diagnostics cannot certify a good explanation.

Independent review is useful after a full draft and is included when requested and supported by the host. Without subagents, a separate review pass is recorded honestly.

[Rendering lessons](skills/motif/references/rendering.md) preserve cache/file-lock collisions, memory pressure, surviving child processes, final-frame holds, double-scaled waits, LaTeX escaping, misleading frame-rate headers and playback checks.

## HTML and PPTX

| Format | Delivery and behavior |
|---|---|
| HTML | Offline interactive deck with a sibling assets directory; one-file export is available. |
| PPTX | Embedded H.264/yuv420p clips, one slide per beat, with a native media-play effect triggered on slide entry. Formulas and diagrams remain video content. |

Exports enter a new versioned directory after the selected formats pass validation. Earlier releases stay usable.

**Office/WPS autoplay requires a real-player check.** Verify slide-entry playback in both Microsoft PowerPoint and WPS Presentation where available, without clicking Play. Record versions and observations. ZIP/XML timing and codec checks alone do not prove compatibility. An unavailable player remains explicitly unverified.

The exporter preserves the timing mechanism from a presentation reported working in both players. A raw converter's zero-delay video flag was not sufficient in the observed WPS failure. See [the autoplay case and regression checks](skills/motif/references/pptx-autoplay.md). Fresh exports retain their own verification status.

## Verification and development

Version 0.1.0 passed Windows/Linux CI, package validation, deterministic tests, actual 1440p60 rendering and decoded-cadence checks, HTML/PPTX export, cache reuse, and installation from the public repository into an isolated project. The copied management CLI, project creation and discovery were also exercised.

Real Office/WPS playback has **not** been verified on the development host. WPS was unavailable. This remains a recorded gap.

```bash
python tools/validate_package.py
python -m unittest discover -s tests
python tools/package.py
```

CI checks package/tool logic on Ubuntu and Windows. Render/export integration and actual player tests remain separate. A version tag matching `plugin.json` triggers the workflow that creates both release ZIPs. The [development handoff on GitHub](https://github.com/Misaka16384/motif/blob/main/PROJECT.md) records evidence and pending work.

## License and research material

MIT for the skill and toolkit. Bundled Tomli 2.4.1 retains its MIT license. Demonstration media are shared by permission for project demonstrations and are excluded from the toolkit's MIT license. Private research belongs in its authorized local project and must not be copied into the skill or a public release.
