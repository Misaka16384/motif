# Slide-entry playback in PowerPoint and WPS

Read this when exporting an animated PPTX or investigating a video that plays only after a click. HTML playback and PPTX playback use different mechanisms; identify the actual artifact before diagnosing it.

## The observed regression

A presenter confirmed that a corrected presentation played automatically in Office and WPS, while the earlier export did not autoplay in WPS. Comparing the packages showed byte-identical video content. The corrected package added a native media-play effect triggered with the slide. The raw converter output only assigned `delay="0"` to its `p:video` time node.

That raw flag is insufficient evidence of cross-player autoplay. An earlier toolkit validator accepted it and rejected the corrected package because the corrected video node itself used an indefinite start condition. The actual playback trigger lived in a separate command branch.

## Preserve the working mechanism

For this toolkit's single-video animation beats:

- A `p:cmd type="call" cmd="playFrom(0.0)"` targets the embedded video's shape ID.
- The command belongs to a `withEffect` media-call effect in the main sequence.
- Its enclosing start condition is `onBegin`, delay zero, referencing that main sequence. Nested immediate conditions also have zero delay.
- The separate `p:video` describes the same media shape; its indefinite condition does not prevent the command from starting playback.
- An independent click-to-`togglePause` branch is valid. Do not confuse it with a click required to start the video.

The shipped timing template preserves this reference structure, including manual sequence navigation and the separate pause control. Export normalizes the disposable converter output before validation. It replaces only the timing block, preserves XML namespace declarations/other slide content, and copies media unchanged in bounded chunks. It refuses to discard unrelated slide animations or normalize a slide with multiple video shapes. This is intended for the toolkit's one-full-slide-video-per-beat output, not arbitrary presentations.

If an agent instead normalizes through PowerPoint with an authorized desktop method, the useful sequence is:

```text
media shape.AnimationSettings.PlaySettings.PlayOnEntry = true
for each native media-play effect in slide.TimeLine.MainSequence:
    effect.Timing.TriggerType = msoAnimTriggerWithPrevious  # 2
    effect.Timing.TriggerDelayTime = 0
```

`PlayOnEntry` created a native effect whose default trigger still required a click in the observed case. Explicitly changing the media-play effect's trigger was the decisive additional step. Preserve manual slide advance and other open user documents; setting movie autoplay should not make the entire deck advance automatically.

## What to verify

The package check must trace the **play command**, its ancestor conditions and its embedded-video target. Reject a zero-delay-only raw export, a `clickEffect` play command, a missing/wrong main-sequence trigger, and a command targeting another shape. Accept the working command branch even when the separate media node is indefinite and click-to-pause exists.

Regression checks cover both the failed raw structure and the corrected native structure. The original reference deck was reported working by its presenter; fresh toolkit exports still require their own real Office/WPS playback check. Do not change `player_tested` to true merely because normalized XML matches the reference. Record each artifact and the source of its evidence.

Primary documentation: Microsoft describes media commands such as PlayFrom in [PresentationML Command](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.command), and the separate media-node role in [CommonMediaNode](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.commonmedianode).
