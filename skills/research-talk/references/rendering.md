# Rendering and playback lessons

These are practical failure modes observed while producing a long animated research talk. Apply the relevant lesson to the actual environment; do not turn every past issue into a mandatory ceremony.

## Rendering concurrency and memory

- Real renders that share a TeX cache can collide on Windows file locks. Render sequentially by default. Parallel work is appropriate for discussion, source preparation and independent review. Parallel renders require isolated media/TeX paths and enough memory; the agent decides whether the gain warrants that complexity.
- The toolkit separates media by project/profile and serializes project operations. Avoid manually launching another render behind it. A layout checker with its own temporary media directory can be independent, but normal renders should not share mutable caches.
- A system supervisor once killed a background build under memory pressure while a child renderer continued running. A killed wrapper is not proof that its descendants stopped. Inspect known child PIDs and logs before resuming; preserve completed scenes. If the user/system explicitly says not to restart until asked, honor that instruction.
- The toolkit reports observed free memory. It does not invent a universal safe threshold. An author/agent may configure `min_free_memory_mb` in a profile when useful; that explicit threshold is enforced unless overridden intentionally. Check the actual scene, other workloads and whether a browser/player is retaining videos.
- Decode and inspect clips incrementally. Limit contact-sheet size. A browser can retain decoded inactive videos; assess the actual player and release/reload inactive media when a long deck demonstrates memory growth. Do not inject a speculative unload handler that breaks navigation.
- Estimate high-resolution build time from representative scenes and actual cache behavior. Pixel count alone is a poor predictor. Keep elapsed times and preserve a usable preview while final rendering runs.

## Frames, pacing, text and caches

- An animation may not write its exact alpha=1 state into the final frame. The starter records an unscaled 0.1 s hold before a slide pause. Check resulting frames, especially moving equation labels.
- `Scene.wait` calls `play(Wait(...))`. Scaling both methods can scale pauses twice. The starter scales `play` once and restores animation durations afterward. Do not deepcopy animations for pacing: that also copies their mobjects and can detach later transformations from the displayed objects.
- MathTex parent opacity can be zero while descendants are visible. A checker should inspect the family members. Bounding boxes are useful for clipping/text collisions; pixel layers better distinguish line/glyph overlap. Both produce intentional-overlap findings and miss semantic problems.
- End-frame sampling at a guessed time offset can capture motion or fail on a short clip. Decode to the actual final frame. Inspect mid-animation states separately.
- Shell/Python string escaping once turned LaTeX `\f`, `\b` and `\t` into control characters. Prefer raw Python strings and safe file edits; run syntax/control-character checks. Do not interpolate JSON-escaped strings as shell code.
- Two independent scene lists drifted: newly added scenes rendered but were omitted from the whole-deck check. Use one project manifest for build, QA and export.
- Cache reuse needs evidence. Check source/profile dependencies and actual media. After tool/font changes or unusual data dependencies, force affected renders deliberately. Never mix preview clips into a final export because their scene names happen to match.
- Concatenated clips can have decode-timestamp spans that make `average_rate` differ from their nominal frame rate while every presentation timestamp is correct. The toolkit records both rates and validates decoded presentation cadence, rather than rejecting a good clip from its average-rate header alone.

## Failures, export and real playback

- A shell pipeline ending with `tail` once masked an exporter error. Use direct process exit codes, per-scene logs and verified outputs. Do not print or record success merely because a converter returned.
- Keep incomplete exports in staging directories; publish a new release directory only when the whole requested export passes. Preserve old assets with their HTML so an earlier release stays usable.
- PPTX is a video backup: edit view displays poster images, formulas are not native editable objects, and slide count follows beats. Require embedded H.264/yuv420p media and automatic-start timing for the intended Office/WPS path. Verify slide-entry playback in the actual applications; a valid ZIP/XML document or a rendered poster is insufficient.
- Browser automation once inspected a hidden tab where videos never loaded. Check visibility and real playback before diagnosing broken clips. Metadata/codec verification remains a separate result.
- Some Windows LibreOffice wrappers assume Unix sockets. Discover actual available applications rather than repeatedly invoking a broken wrapper. Opening a deck for inspection must preserve unrelated user documents.
- Custom pip mirrors may lack a package. Use an explicit official index for a scoped installation when needed; do not rewrite the user's global pip configuration.
- Cleanup should follow current asset references, preserve current releases and source, and offer a recoverable path. The toolkit intentionally provides no blanket recursive-delete command.
- Tool sandboxes and the host can have different access to credential stores or output directories. A host-authenticated GitHub CLI once still returned 401 inside a restricted process. Diagnose the execution context and token-variable presence without exposing credentials; do not repeatedly ask the user to log in when host authentication already works. Likewise, distinguish a verifier's filesystem restriction from an implementation failure.
