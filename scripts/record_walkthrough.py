import argparse
import csv
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import wave

import imageio_ffmpeg
from PIL import Image
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1600, 900


def scroll_to(page: Page, locator) -> None:
    locator.scroll_into_view_if_needed()
    locator.evaluate(
        "(element) => { const main = document.querySelector('[data-testid=\"stMain\"]');"
        " if (main) main.scrollTop += element.getBoundingClientRect().top - 110; }"
    )
    page.wait_for_timeout(600)


def top(page: Page) -> None:
    page.locator('[data-testid="stMain"]').evaluate("(element) => element.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def run_comparison(page: Page) -> None:
    page.get_by_role("button", name="Run comparison", exact=True).click()
    expect(page.get_by_text("Settings changed.", exact=False)).to_have_count(0)
    expect(page.get_by_role("heading", name="PatientFlow", exact=True)).to_be_visible()
    page.wait_for_timeout(900)
    errors = page.locator('[data-testid="stException"], [data-testid="stAlertContainer"]')
    if errors.filter(has_text="Scenario cannot run:").count():
        raise RuntimeError("The recorded scenario failed to run.")


def perform_action(page: Page, action: str, work: Path) -> None:
    if action in ("intro", "recommendation", "settings"):
        top(page)
    elif action == "waiting":
        page.get_by_role("tab", name="Waiting times", exact=True).click()
        scroll_to(page, page.get_by_role("heading", name="Compare the two staffing plans"))
    elif action == "busy":
        page.get_by_role("button", name="Busy clinic", exact=True).click()
        expect(page.get_by_role("spinbutton", name="Arrivals per hour", exact=True)).to_have_value("18.00")
        page.wait_for_timeout(1200)
        run_comparison(page)
        top(page)
    elif action == "reset":
        page.get_by_role("button", name="Load demo", exact=True).click()
        expect(page.get_by_role("spinbutton", name="Arrivals per hour", exact=True)).to_have_value("12.00")
        page.wait_for_timeout(1200)
        run_comparison(page)
        expect(page.get_by_test_id("stMetricValue").nth(1)).to_have_text("80.80 min")
        top(page)
    elif action == "queue":
        page.get_by_role("tab", name="Queues & doctors", exact=True).click()
        scroll_to(page, page.get_by_role("heading", name="Where does the queue build up?"))
    elif action == "doctors":
        scroll_to(page, page.get_by_text("Doctor utilization period", exact=True))
        page.get_by_role("radiogroup", name="Doctor utilization period").get_by_text("Full session", exact=True).click()
        page.wait_for_timeout(800)
    elif action == "patients":
        page.get_by_role("tab", name="Patient records", exact=True).click()
        page.get_by_role("textbox", name="Patient ID", exact=True).fill("P0050")
        page.get_by_role("textbox", name="Patient ID", exact=True).press("Enter")
        expect(page.get_by_text("Showing 1 of 102 patients.", exact=False)).to_be_visible()
        page.get_by_role("radiogroup", name="Staffing plan").get_by_text("Recommended", exact=True).click()
        scroll_to(page, page.get_by_role("heading", name="Look up a patient"))
    elif action == "exports":
        page.get_by_role("textbox", name="Patient ID", exact=True).fill("")
        page.get_by_role("textbox", name="Patient ID", exact=True).press("Enter")
        expect(page.get_by_text("Showing 102 of 102 patients.", exact=False)).to_be_visible()
        scroll_to(page, page.get_by_role("button", name="Download paired comparison", exact=True))
        with page.expect_download() as download:
            page.get_by_role("button", name="Download paired comparison", exact=True).click()
        download.value.save_as(work / "paired_export.csv")
        with (work / "paired_export.csv").open(encoding="utf-8", newline="") as exported:
            rows = list(csv.DictReader(exported))
        if len(rows) != 102 or any(
            row.get("data_mode") != "Synthetic demo"
            or row.get("arrival_source") != "synthetic_exponential"
            or float(row["improved_wait_min"]) > float(row["baseline_wait_min"]) + 1e-9
            for row in rows
        ):
            raise ValueError("Recorded paired download does not match the demonstrated cohort.")
    elif action == "hybrid":
        page.get_by_role("radiogroup", name="Patient data").get_by_text("Hangu hybrid", exact=True).click()
        expect(page.get_by_role("spinbutton", name="Mean consultation (minutes)", exact=True)).to_have_count(0)
        page.wait_for_timeout(1200)
        run_comparison(page)
        expect(page.get_by_text("Hybrid data:", exact=False)).to_be_visible()
        top(page)
        page.get_by_text("Data sources and assumptions", exact=True).click()
    elif action == "models":
        page.get_by_role("tab", name="How it works", exact=True).click()
        scroll_to(page, page.get_by_role("heading", name="How the comparison is calculated"))
    elif action == "closing":
        page.get_by_role("tab", name="Waiting times", exact=True).click()
        panel = page.locator('[data-testid="stExpander"]').filter(
            has=page.get_by_text("Data sources and assumptions", exact=True)
        )
        if panel.locator("details").get_attribute("open") is not None:
            page.get_by_text("Data sources and assumptions", exact=True).click()
        top(page)
    else:
        raise ValueError(f"Unknown recording action: {action}")


def set_caption(page: Page, title: str, caption: str) -> None:
    page.evaluate(
        """({title, caption}) => {
            let panel = document.getElementById('walkthrough-caption');
            if (!panel) {
                panel = document.createElement('div');
                panel.id = 'walkthrough-caption';
                panel.style.cssText = 'position:fixed;bottom:18px;left:330px;right:24px;'
                    + 'padding:16px 24px;background:#102a43;color:white;border-radius:12px;'
                    + 'font-family:Arial,sans-serif;z-index:999999;pointer-events:none;'
                    + 'box-shadow:0 5px 20px #0003;';
                document.body.appendChild(panel);
            }
            panel.replaceChildren();
            const heading = document.createElement('div');
            heading.textContent = title;
            heading.style.cssText = 'font-size:23px;font-weight:bold;margin-bottom:7px;';
            const summary = document.createElement('div');
            summary.textContent = caption;
            summary.style.cssText = 'font-size:19px;line-height:1.4;color:#e0f2f1;';
            const credit = document.createElement('div');
            credit.textContent = 'Local application recording | Standard computer-generated narration';
            credit.style.cssText = 'font-size:11px;margin-top:8px;color:#b0c9d8;';
            panel.append(heading, summary, credit);
        }""",
        {"title": title, "caption": caption},
    )


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8517")
    parser.add_argument("--output", type=Path, default=ROOT / "deliverables")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    chapters = json.loads((ROOT / "scripts" / "video_narration.json").read_text(encoding="utf-8"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="patientflow-video-") as directory:
        work = Path(directory)
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(ROOT / "scripts" / "narrate_video.ps1"),
             "-NarrationFile", str(ROOT / "scripts" / "video_narration.json"),
             "-OutputDirectory", str(work)],
            check=True,
        )
        speech = []
        audio_format = None
        for index in range(len(chapters)):
            with wave.open(str(work / f"speech-{index:02}.wav"), "rb") as wav:
                current_format = (wav.getnchannels(), wav.getsampwidth(), wav.getframerate())
                if audio_format is not None and current_format != audio_format:
                    raise ValueError("Narration segments have inconsistent audio formats.")
                audio_format = current_format
                speech.append((wav.readframes(wav.getnframes()), wav.getnframes() / wav.getframerate()))
        narrated_seconds = sum(duration for _, duration in speech)
        if not 170 <= narrated_seconds <= 280:
            raise ValueError(f"Narration is {narrated_seconds:.1f}s; adjust the script/voice for a 3-5 minute video.")
        print(f"Narration ready: {narrated_seconds:.1f} seconds.", flush=True)

        timeline = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                viewport={"width": WIDTH, "height": HEIGHT},
                record_video_dir=str(work / "recording"),
                record_video_size={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
                reduced_motion="reduce",
                accept_downloads=True,
            )
            started = time.monotonic()
            page = context.new_page()
            page.set_default_timeout(30_000)
            page.goto(args.url)
            expect(page.get_by_test_id("stMetricValue").nth(1)).to_have_text("80.80 min", timeout=60_000)
            for index, chapter in enumerate(chapters):
                perform_action(page, chapter["action"], work)
                set_caption(page, chapter["title"], chapter["caption"])
                begin = time.monotonic() - started
                payload, duration = speech[index]
                timeline.append({"start": begin, "end": begin + duration, **chapter})
                print(f"Recording {index + 1}/{len(chapters)}: {chapter['title']}", flush=True)
                if chapter["action"] in ("recommendation", "queue", "hybrid"):
                    page.screenshot(path=str(output / f"{chapter['action']}.png"))
                page.wait_for_timeout(duration * 1000 + 400)
            if page.video is None:
                raise RuntimeError("Browser video capture was not created.")
            video = page.video
            elapsed = time.monotonic() - started
            context.close()
            raw_video = video.path()
            browser.close()

        if audio_format is None:
            raise ValueError("No narration audio was generated.")
        channels, sample_width, sample_rate = audio_format
        audio = bytearray()
        for chapter, (payload, _) in zip(timeline, speech):
            desired_start = round(chapter["start"] * sample_rate) * channels * sample_width
            if desired_start < len(audio):
                raise ValueError("Narration segments overlap.")
            audio.extend(b"\x00" * (desired_start - len(audio)))
            audio.extend(payload)
        desired_length = round(elapsed * sample_rate) * channels * sample_width
        audio.extend(b"\x00" * max(0, desired_length - len(audio)))
        with wave.open(str(work / "narration.wav"), "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(sample_width)
            wav.setframerate(sample_rate)
            wav.writeframes(audio)
        destination = output / "PatientFlow_walkthrough.mp4"
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(raw_video), "-i", str(work / "narration.wav"),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "fast",
             "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             "-shortest", "-movflags", "+faststart", str(destination)],
            check=True,
        )
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(destination), "-f", "null", "-"],
            check=True,
        )
        reader = imageio_ffmpeg.read_frames(str(destination), pix_fmt="rgb24")
        metadata = next(reader)
        reader.close()
        if not 180 <= metadata["duration"] <= 300:
            raise ValueError(f"Video duration {metadata['duration']}s is outside the requested 3-5 minutes.")
        audio_check = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", str(destination), "-vn",
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, check=True,
        )
        volume = re.search(r"mean_volume:\s*(-?[\d.]+) dB", audio_check.stderr)
        if volume is None or float(volume.group(1)) < -45:
            raise ValueError("Final narration is missing or too quiet.")
        if metadata["size"] != (WIDTH, HEIGHT):
            raise ValueError(f"Unexpected video dimensions: {metadata['size']}")
        report = {
            "duration_seconds": metadata["duration"],
            "dimensions": list(metadata["size"]),
            "video_codec": metadata["codec"],
            "mean_audio_volume_db": float(volume.group(1)),
            "voice": "Microsoft Zira Desktop, Windows System.Speech, rate 2",
            "capture": "Actual automated local Chromium app recording with chapter-summary captions",
            "paired_export_verified": "102 synthetic-demo rows, source labels, and paired wait ordering",
            "chapters": timeline,
        }
        (output / "video_details.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (output / "walkthrough_transcript.txt").write_text(
            "PatientFlow walkthrough\nStandard computer-generated narration; no voice cloning.\n\n"
            + "\n\n".join(f"{chapter['title']}\n{chapter['narration']}" for chapter in chapters)
            + "\n", encoding="utf-8",
        )
        (output / "walkthrough_captions.srt").write_text(
            "\n\n".join(
                f"{index + 1}\n{srt_time(chapter['start'])} --> {srt_time(chapter['end'])}\n"
                f"{chapter['title']}\n{chapter['caption']}"
                for index, chapter in enumerate(timeline)
            ) + "\n", encoding="utf-8",
        )
        for name in ("recommendation", "queue", "hybrid"):
            with Image.open(output / f"{name}.png") as screenshot:
                if screenshot.size != (WIDTH, HEIGHT):
                    raise ValueError(f"Unexpected screenshot size for {name}.")
        print(
            f"Verified {destination.name}: {metadata['duration']:.1f}s, {WIDTH}x{HEIGHT}, "
            f"audible narration ({volume.group(1)} dB), complete decode succeeded.",
            flush=True,
        )


if __name__ == "__main__":
    main()
