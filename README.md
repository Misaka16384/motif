# Research Talk

A lightweight Agent Skill for researchers creating academic talks with explanatory Manim animations.

面向熟悉自己研究的作者：与模型对齐报告的种子，沿一条主线组织内容，用动画展示机制，并在本地持续维护项目状态。

## Install

Standard Agent Skills distribution, with Node/npm available:

```bash
npx skills add Misaka16384/research-talk --skill research-talk
```

Select your agent and project/user installation scope. To target Codex and Claude Code at user scope:

```bash
npx skills add Misaka16384/research-talk --skill research-talk -a codex -a claude-code -g -y
```

Skill installation and rendering-environment installation have separate scopes. First use detects dependencies and asks whether to prepare a project-local or user-level shared environment. It can reuse an existing compatible environment. No account, MCP server or external generation service is needed; a local agent with file and shell access is required for rendering.

Updates: `npx skills update research-talk`. `python tools/package.py` produces a standalone skill ZIP and an optional plugin ZIP. The skill ZIP contains `research-talk/SKILL.md` at the installable root; extract that folder into the host's skill directory. The plugin ZIP preserves the repository/plugin structure. Both use the same source resources.

## Collaboration

The default route is alignment → meaningful pilot → approved autonomous draft and review → human preview/revision → final format selection. The user/model adapt this route rather than filling out a fixed questionnaire. The skill records the main question, decisions and next step in `PROJECT.md`; it discovers existing marked projects and offers to continue them.

The central principles are motivation before notation, formula–figure correspondence, continuity between parts, the simplest case explained thoroughly, and detail proportional to new insight. On-screen text stays academic and economical. Language, theme, pacing and resolution are project settings.

## Local project

```text
my-talk/
├── PROJECT.md        # Human-readable state and handoff
├── talk.toml         # One scene list, environment and profiles
├── anim/             # Model-written scenes and helpers
├── reviews/          # Feedback, diagnostic frames and review reports
├── .build/           # Per-profile records, logs, isolated caches/media
└── deck/             # Versioned validated exports
```

All runtime resources live inside `skills/research-talk`, so the installed skill is self-contained. Read [operations](skills/research-talk/references/operations.md) for commands, and [rendering lessons](skills/research-talk/references/rendering.md) for cache, memory, interruption and playback pitfalls.

The generic starter has two demonstration scenes. It is not a predefined research talk. The supplied rendering stack is a tested baseline; other versions can be probed and smoke-tested. Python management supports 3.10+ through a bundled pure-Python TOML reader. The starter's mathematical typesetting requires LaTeX/dvisvgm; these can be reused or prepared within an approved scope.

## Outputs and verification

- HTML: offline interactive presentation, with a sibling assets folder or one-file export.
- PPTX: embedded H.264/yuv420p animation videos, automatic-start timing, one slide per beat. Formulas are not native editable objects.

Media/package checks and actual player tests are separate. The workflow calls for checking slide-entry autoplay in PowerPoint and WPS before claiming compatibility. A valid ZIP/XML package or a poster screenshot does not prove autoplay. If a player is unavailable, its result remains unverified.

## Development and release

```bash
python tools/validate_package.py
python -m unittest discover -s tests
python tools/package.py
```

CI checks package integrity and deterministic logic. Local integration checks must separately render/decode scenes and exercise exporters; see `PROJECT.md` for the current development state. Publishing a tag matching `plugin.json`, such as `v0.1.0`, triggers the ZIP release workflow after checks pass.

The root `plugin.json` is an optional portable-plugin wrapper around the same skill. Standard skill installation requires no platform-specific plugin setup. Future platform marketplace entries can reference this same source.

## License

MIT. The bundled Tomli 2.4.1 parser retains its own MIT license under `scripts/talklib/vendor/tomli/LICENSE`. Only generic examples and process guidance are distributed; private research and project material belong in local projects.
