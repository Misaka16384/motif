# Local operations

Resolve `scripts/talk.py` relative to the installed skill, not a fixed machine path. Run with Python >= 3.10. A pure-Python TOML reader is bundled for 3.10; management commands do not require Manim. If Python is absent, detect the OS and install/reuse Python within the user-approved scope before running the CLI.

Commands return JSON; nonzero exit codes mean failure or incomplete detection. Do not infer success from a final printed line or a shell pipeline. Paths containing spaces are valid; quote them normally and never assemble commands with `eval`.

## Discover and create

```text
python <skill>/scripts/talk.py discover --root <workspace>
python <skill>/scripts/talk.py init <new-directory> --name "Talk title"
python <skill>/scripts/talk.py status --project <project>
python <skill>/scripts/talk.py roots --add <existing-search-root>
```

Discovery checks registered projects and bounded roots, skips caches/venvs and does not follow directory symlinks. `init` refuses nonempty directories. The local registry is `settings.json` in the user's configuration directory; `RESEARCH_TALK_HOME` can select another location for tests or a portable setup. Project contents, source material and scientific claims are never placed in that registry.

## Environment

```text
python <skill>/scripts/talk.py doctor --project <project>
python <skill>/scripts/talk.py doctor --project <project> --python <candidate-python> --path <tex-bin>
python <skill>/scripts/talk.py setup --project <project> --scope project
python <skill>/scripts/talk.py setup --project <project> --scope project --yes
python <skill>/scripts/talk.py setup --project <project> --scope shared --yes
python <skill>/scripts/talk.py setup --project <project> --reuse <existing-python> --path <tex-bin> --yes
```

Without `--yes`, setup reports a plan and makes no environment changes. After the user chooses the scope, the agent executes the necessary scoped installation without repeated prompts. Project scope uses `<project>/.venv`; shared scope uses `<user-config>/environments/render-v0.1`. Shared means a dedicated user-level environment, not installing into system Python. Reuse binds a chosen interpreter without changing its packages. Detected versions outside the tested stack are reported rather than rejected; inspect APIs and smoke-test them before relying on them.

Python packages are installed from the packaged requirements, using PyPI for this command only; global pip settings are untouched. Requirements are a tested starting point and can be revised deliberately. External tools are detected, not silently installed system-wide. **The agent completes missing external prerequisites**, using official installation instructions, the chosen scope and the tools available on the host. Explain any proposed system-level change separately when a project-only choice cannot cover it; do not silently change scope.

Manim 0.19+ renders video with PyAV, which the toolkit also uses to inspect videos and decode final frames. A separate FFmpeg executable is useful but not required by this toolkit. The supplied `Tex`/`MathTex` examples require LaTeX and dvisvgm. Prefer reusing an existing TeX distribution. For a scoped installation, consider TinyTeX/TeX Live in an approved location, ensure Manim's necessary packages are available, and record the binary directory in `environment.path`. Linux Cairo/Pango build prerequisites may require OS packages; discover the actual failure and follow the approved scope rather than running a universal install recipe.

Primary references: [Manim installation](https://docs.manim.community/en/stable/installation.html), [Manim 0.19 video backend](https://docs.manim.community/en/stable/changelog/0.19.0-changelog.html), [TinyTeX](https://yihui.org/tinytex/), [Manim Slides CLI](https://manim-slides.eertmans.be/latest/reference/cli.html).

## Render, inspect, deliver

```text
python <skill>/scripts/talk.py smoke --project <project>
python <skill>/scripts/talk.py render --project <project> --profile preview
python <skill>/scripts/talk.py render --project <project> --profile preview --scene SceneName
python <skill>/scripts/talk.py check --project <project> --profile preview
python <skill>/scripts/talk.py preview --project <project> --profile preview --sample all
python <skill>/scripts/talk.py render --project <project> --profile final
python <skill>/scripts/talk.py export --project <project> --profile final --format html
python <skill>/scripts/talk.py export --project <project> --profile final --format pptx
```

The workflow itself is decided with the author. `smoke` exercises the generic demonstration and both exporters; it does not approve talk content or select final delivery format. Use it before replacing starter scenes, or run equivalent small tests on the approved pilot.

Rendering is sequential and uses a per-project operation lock. Preview, smoke and final media live in separate `.build/<profile>` directories. Successful fresh scenes are reused; `--force` rerenders a selection. The cache key covers the scene source, shared helper sources, declared `depends` files, visual/profile settings and chosen Python. If a scene imports another scene module or reads data/images, declare them in its `depends` list. Changes to external packages/fonts may require `--force` even if local source is unchanged.

`check` rejects missing/stale/failed media and verifies actual dimensions, frame rates and duration. End-beat diagnostics report clipping, text/text boxes and text/figure pixel intersections. These are review aids, including possible intentional overlaps. `--strict-layout` makes findings a nonzero exit. A deliberate figure label can be annotated with `qa_allow_overlap = True`; explain the intention rather than suppressing the whole scene.

`preview --sample all` decodes actual first, middle and final frames into bounded contact sheets. It does not keep all full-resolution frames in memory. Inspect intermediate videos when a mechanism or transition needs review.

Exports are committed into a new versioned directory only after all requested formats validate. Old releases remain intact. HTML is offline, but the first conversion may need network access for RevealJS assets. Share HTML with its sibling `talk_assets` directory, or select `--one-file`. PPTX embeds the same animation clips, with automatic-start timing and one page per beat. Package validation does not prove playback in PowerPoint or WPS; test both applications without manually starting the media, and record their versions/results before claiming compatibility.

After an interrupted operation, inspect `status`, logs and recorded child PIDs. A stale lock is intentionally visible. Only after verifying the processes have stopped, use `unlock --yes` and explicitly resume. Never delete a lock to start a competing render.

## Actual PowerPoint/WPS autoplay check

Choose a permitted observation method on the presentation machine. Open only the generated PPTX, preserve unrelated documents, enter slideshow mode normally, and observe the video starting without a Play click. Advance to subsequent beats and verify that they start on entry too. Record application/version, file hash or release path, tested beats and observations in `reviews/playback.md`, then update PROJECT.md. A paused poster in edit mode is not a slideshow failure.

On an interactive Windows desktop with authorized PowerPoint automation, the documented `SlideShowView.Player(shapeId)` exposes read-only `State` and observable `CurrentPosition`. Increasing position after ordinary slide entry can provide evidence without calling `Play`. See [Player](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowview.player) and [CurrentPosition](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.player.currentposition). Headless Office automation is not a portable verification method. WPS may require direct visual observation because its available interfaces differ. If an app cannot be run, obtain a human check or clearly leave that app unverified; do not manufacture a compatibility result.
