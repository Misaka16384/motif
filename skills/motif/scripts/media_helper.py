"""Run with the configured render Python; never requires system FFmpeg."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def inspect_video(path, decode=False):
    import av
    with av.open(str(path)) as container:
        video = container.streams.video[0]
        duration = float(video.duration * video.time_base) if video.duration is not None else float(container.duration or 0) / av.time_base
        fps = float(video.base_rate or video.guessed_rate or video.average_rate or 0)
        result = {"path": str(Path(path).resolve()), "width": video.width, "height": video.height,
                  "fps": fps, "average_fps": float(video.average_rate or 0), "duration": duration,
                  "codec": video.codec_context.name, "pixel_format": video.codec_context.format.name}
        if decode:
            count, errors, previous = 0, 0, None
            tolerance = max(float(video.time_base) * 1.5, 0.0001)
            for frame in container.decode(video):
                current = frame.time
                if current is None:
                    errors += 1
                elif previous is not None and (fps <= 0 or abs(current - previous - 1 / fps) > tolerance):
                    errors += 1
                previous = current
                count += 1
            result.update(decoded_frames=count, cadence_errors=errors)
            if not count:
                raise ValueError(f"No decodable frames: {path}")
        return result


def frames(path, destination, sample="last"):
    import av
    from PIL import Image
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    metadata = inspect_video(path)
    first = middle = last = None
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            if sample == "all" and first is None:
                first = frame
            if sample == "all" and middle is None and float(frame.time or 0) >= metadata["duration"] / 2:
                middle = frame
            last = frame
    if last is None:
        raise ValueError(f"No decodable frames: {path}")
    samples = {"last": last} if sample == "last" else {"first": first, "middle": middle or last, "last": last}
    outputs = {}
    for name, frame in samples.items():
        image = frame.to_image()
        image.thumbnail((640, 360), Image.Resampling.LANCZOS)
        output = destination / (name + ".png")
        image.save(output)
        outputs[name] = str(output)
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["probe", "frames", "sheet"])
    parser.add_argument("--input", required=True, help="JSON request path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if args.mode == "probe":
        result = [inspect_video(path, decode=request.get("decode", True)) for path in request["files"]]
    elif args.mode == "frames":
        result = [dict(item, frames=frames(item["file"], item["destination"], request.get("sample", "last")))
                  for item in request["items"]]
    else:
        from PIL import Image, ImageDraw
        items = request["items"]
        columns = 3
        rows = (len(items) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * 480, rows * 300), "#101010")
        drawing = ImageDraw.Draw(sheet)
        for index, item in enumerate(items):
            x, y = (index % columns) * 480, (index // columns) * 300
            frame = Image.open(item["image"]).convert("RGB")
            frame.thumbnail((464, 261))
            sheet.paste(frame, (x + 8, y + 8))
            drawing.text((x + 10, y + 275), item["label"], fill="white")
        sheet.save(request["destination"])
        result = {"sheet": request["destination"], "frames": len(items)}
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Media inspection failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
