"""Ingest transcripts from the vetted YouTube channels in ``site/watch.html``.

The dry-run path contacts YouTube but does not touch Supabase:

    python build-video-kb.py --limit 2 --dry-run

Real ingestion requires the same three credentials as ``build-kb.py`` and must
run off-peak because embedding competes with the live site for two VPS CPUs:

    SUPABASE_DB_URL=postgresql://...
    SUPABASE_EMBED_URL=https://api.analyzingislam.com/functions/v1/embed
    SUPABASE_SERVICE_ROLE_KEY=...
"""
from __future__ import annotations

import argparse
import html as html_lib
import importlib.util
import json
import re
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).parent
SITE = ROOT / "site"
WORDS_PER_CHUNK = 250


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


client = _load("kb_client", ROOT / "kb_client.py")


def channels_from_watch_page(path: Path = SITE / "watch.html") -> dict[str, dict]:
    """Return the vetted channel slug, display name, and YouTube URL."""
    page = path.read_text(encoding="utf-8")
    match = re.search(
        r"\bchannels\s*:\s*\{(?P<body>.*?)\n\s*\},\s*\n\s*debates\s*:",
        page,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"{path}: WATCH_DATA.channels not found")

    channels: dict[str, dict] = {}
    pattern = re.compile(
        r"'(?P<slug>[a-z0-9-]+)'\s*:\s*\{\s*"
        r"name\s*:\s*'(?P<name>(?:\\.|[^'])*)'\s*,\s*"
        r"url\s*:\s*'(?P<url>(?:\\.|[^'])*)'",
        re.DOTALL,
    )
    for item in pattern.finditer(match.group("body")):
        channels[item.group("slug")] = {
            "name": item.group("name").replace("\\'", "'"),
            "url": item.group("url").replace("\\'", "'"),
        }
    if not channels:
        raise ValueError(f"{path}: WATCH_DATA.channels contains no channel records")
    return channels


def _timestamp_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"invalid VTT timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + int(float(seconds))


def _without_rolling_overlap(previous: str, current: str) -> str:
    """Remove a previous cue's suffix when it repeats as this cue's prefix."""
    before = previous.split()
    now = current.split()
    for size in range(min(len(before), len(now)), 1, -1):
        if before[-size:] == now[:size]:
            return " ".join(now[size:])
    return current


def parse_vtt(vtt_text: str) -> list[tuple[int, str]]:
    """Convert WebVTT cues to timestamped text.

    YouTube automatic captions often repeat the immediately preceding rolling
    cue. Only adjacent repeats are removed: the same sentence spoken later is
    legitimate transcript content and must remain searchable.
    """
    cues: list[tuple[int, str]] = []
    previous_text: str | None = None
    previous_start: int | None = None
    blocks = re.split(r"\r?\n\s*\r?\n", vtt_text.strip())
    timing = re.compile(
        r"(?P<start>(?:\d{2}:)?\d{2}:\d{2}\.\d+)\s+-->"
    )

    for block in blocks:
        lines = block.splitlines()
        timing_ix = next((ix for ix, line in enumerate(lines) if timing.search(line)), None)
        if timing_ix is None:
            continue
        start_match = timing.search(lines[timing_ix])
        raw_text = " ".join(lines[timing_ix + 1 :])
        raw_text = html_lib.unescape(re.sub(r"<[^>]+>", "", raw_text))
        raw_text = re.sub(r"\s+", " ", raw_text).strip()
        start = _timestamp_seconds(start_match.group("start"))
        if not raw_text:
            continue

        text = raw_text
        if previous_text is not None and previous_start is not None:
            if start - previous_start <= 10:
                text = _without_rolling_overlap(previous_text, raw_text)
        previous_text = raw_text
        previous_start = start
        if text:
            cues.append((start, text))
    return cues


def chunk_cues(
    cues: list[tuple[int, str]],
    words_per_chunk: int = WORDS_PER_CHUNK,
) -> list[tuple[int, str]]:
    """Group cues into passages tagged with the first cue's timestamp."""
    if words_per_chunk <= 0:
        raise ValueError("words_per_chunk must be positive")

    chunks: list[tuple[int, str]] = []
    start: int | None = None
    words: list[str] = []
    for timestamp, text in cues:
        if start is None:
            start = timestamp
        words.extend(text.split())
        if len(words) >= words_per_chunk:
            chunks.append((start, " ".join(words)))
            start = None
            words = []
    if words and start is not None:
        chunks.append((start, " ".join(words)))
    return chunks


def video_docs(
    channel_slug: str,
    channel_name: str,
    video: dict,
    cues: list[tuple[int, str]],
    words_per_chunk: int = WORDS_PER_CHUNK,
) -> list[dict]:
    """Build stable, timestamp-addressable KB documents for one video."""
    docs: list[dict] = []
    for passage_ix, (start, body) in enumerate(chunk_cues(cues, words_per_chunk)):
        citation_start = int(start)
        minutes, seconds = divmod(citation_start, 60)
        ref = f"{channel_name} · {minutes}:{seconds:02d}"
        docs.append(
            {
                "kind": "video",
                "slug": f"{video['id']}-p{passage_ix:04d}",
                "title": video["title"],
                "ref": ref,
                "source": channel_slug,
                "categories": [],
                "strength": None,
                "url": (
                    f"https://www.youtube.com/watch?v={video['id']}"
                    f"&t={citation_start}s"
                ),
                "body": body,
                "embed_text": f"{video['title']} · {ref}\n{body}"[:1800],
            }
        )
    return docs


def list_channel_videos(channel_url: str) -> list[dict]:
    """List a channel without downloading media."""
    import yt_dlp

    options = {
        "quiet": True,
        "noprogress": True,
        "extract_flat": True,
        "skip_download": True,
        "js_runtimes": {"node": {}},
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"{channel_url.rstrip('/')}/videos", download=False)
    return [
        {"id": entry["id"], "title": entry.get("title") or entry["id"]}
        for entry in (info.get("entries") or [])
        if entry.get("id")
    ]


def _english_track_keys(tracks: dict) -> list[str]:
    keys = [key for key in tracks if key == "en" or key.startswith("en-")]
    priority = {"en": 0, "en-US": 1, "en-GB": 2}
    return sorted(keys, key=lambda key: (priority.get(key, 10), key))


def english_track_candidates(info: dict) -> list[tuple[str, str]]:
    """Rank manual English captions ahead of automatic English variants."""
    candidates: list[tuple[str, str]] = []
    for source, field in (
        ("manual", "subtitles"),
        ("automatic", "automatic_captions"),
    ):
        candidates.extend(
            (source, language)
            for language in _english_track_keys(info.get(field) or {})
        )
    return candidates


def choose_english_track(info: dict) -> tuple[str, str] | None:
    candidates = english_track_candidates(info)
    return candidates[0] if candidates else None


def fetch_caption_cues(
    video_id: str,
    directory: Path,
    *,
    ydl_factory=None,
) -> list[tuple[int, str]]:
    """Fetch the best usable English VTT track for one video and parse it."""
    if ydl_factory is None:
        import yt_dlp

        ydl_factory = yt_dlp.YoutubeDL

    common = {
        "quiet": True,
        "noprogress": True,
        "skip_download": True,
        "js_runtimes": {"node": {}},
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    with ydl_factory(common) as ydl:
        info = ydl.extract_info(url, download=False)

    last_error: Exception | None = None
    for source, language in english_track_candidates(info):
        try:
            for old_file in directory.glob(f"{video_id}*.vtt"):
                old_file.unlink()
            options = common | {
                "writesubtitles": source == "manual",
                "writeautomaticsub": source == "automatic",
                "subtitleslangs": [language],
                "subtitlesformat": "vtt",
                "outtmpl": str(directory / "%(id)s.%(ext)s"),
            }
            with ydl_factory(options) as ydl:
                ydl.download([url])
            for caption_file in sorted(directory.glob(f"{video_id}*.vtt")):
                cues = parse_vtt(caption_file.read_text(encoding="utf-8"))
                if cues:
                    return cues
        except Exception as exc:
            last_error = exc
            continue
    if last_error:
        raise RuntimeError("captions unavailable") from last_error
    raise RuntimeError("captions unavailable")


def collect_video_docs(
    channels: dict[str, dict],
    *,
    limit: int | None,
    words_per_chunk: int = WORDS_PER_CHUNK,
    list_videos: Callable[[str], list[dict]] = list_channel_videos,
    fetch_cues: Callable[[str], list[tuple[int, str]]],
    report: Callable[[str], None] = print,
) -> tuple[list[dict], list[dict]]:
    """Collect every available transcript while logging failures and continuing."""
    docs: list[dict] = []
    skipped: list[dict] = []
    for slug, channel in channels.items():
        try:
            videos = list_videos(channel["url"])
        except Exception as exc:
            skipped.append({"channel": slug, "video_id": None, "reason": str(exc)})
            report(f"  ! {slug}: channel listing failed ({exc})")
            continue

        if not videos:
            reason = "channel returned no videos"
            skipped.append({"channel": slug, "video_id": None, "reason": reason})
            report(f"  ! {slug}: {reason}")
            continue

        if limit is not None:
            videos = videos[:limit]
        report(f"  {slug}: {len(videos)} videos")
        for video in videos:
            try:
                cues = fetch_cues(video["id"])
                if not cues:
                    raise RuntimeError("captions unavailable")
                docs.extend(
                    video_docs(
                        slug,
                        channel["name"],
                        video,
                        cues,
                        words_per_chunk,
                    )
                )
            except Exception as exc:
                skipped.append(
                    {"channel": slug, "video_id": video["id"], "reason": str(exc)}
                )
                report(f"    ! {video['id']}: {exc}")
    return docs, skipped


def validate_collection(docs: list[dict], skipped: list[dict]) -> None:
    """Reject a systemic extraction failure instead of reporting false success."""
    if not docs:
        detail = f"; {len(skipped)} channel/video failures" if skipped else ""
        raise SystemExit(f"no video transcript documents were collected{detail}")


def prune_stale_video_docs(
    expected_slugs: list[str],
    db_url: str,
    *,
    connect=None,
) -> int:
    """Delete video passages superseded by a complete successful collection."""
    if not expected_slugs:
        raise ValueError("refusing to prune video docs without an expected corpus")
    if connect is None:
        import psycopg2

        connect = psycopg2.connect

    connection = connect(db_url)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                delete from kb_docs
                where kind = 'video'
                  and not (slug = any(%s))
                """,
                (expected_slugs,),
            )
            deleted = cursor.rowcount
        connection.commit()
        return deleted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ingest_video_docs(
    docs: list[dict],
    *,
    db_url: str,
    embed_url: str,
    service_key: str,
    allow_prune: bool,
    upsert=client.upsert_docs,
    prune=prune_stale_video_docs,
) -> tuple[int, int, int]:
    """Commit one channel at a time, then reconcile stale rows when complete."""
    written = unchanged = 0
    by_source: dict[str, list[dict]] = {}
    for doc in docs:
        by_source.setdefault(doc["source"], []).append(doc)

    for source in sorted(by_source):
        source_written, source_unchanged = upsert(
            by_source[source],
            db_url,
            embed_url,
            service_key,
        )
        written += source_written
        unchanged += source_unchanged

    deleted = 0
    if allow_prune:
        deleted = prune(sorted(doc["slug"] for doc in docs), db_url)
    return written, unchanged, deleted


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=_positive_int, help="maximum videos per channel")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skipped-report",
        type=Path,
        help="optional JSON path for skipped channel/video diagnostics",
    )
    args = parser.parse_args()

    credentials = None
    if not args.dry_run:
        credentials = (
            client.env("SUPABASE_DB_URL"),
            client.env("SUPABASE_EMBED_URL"),
            client.env("SUPABASE_SERVICE_ROLE_KEY"),
        )

    channels = channels_from_watch_page()
    print(f"channels: {', '.join(channels)}")
    with tempfile.TemporaryDirectory() as temp_dir:
        directory = Path(temp_dir)
        docs, skipped = collect_video_docs(
            channels,
            limit=args.limit,
            fetch_cues=lambda video_id: fetch_caption_cues(video_id, directory),
        )

    print(f"\ndocuments {len(docs)}, skipped {len(skipped)}")
    if args.skipped_report:
        args.skipped_report.write_text(
            json.dumps(skipped, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"skipped report: {args.skipped_report}")

    validate_collection(docs, skipped)
    if args.dry_run:
        return

    written, unchanged, deleted = ingest_video_docs(
        docs,
        db_url=credentials[0],
        embed_url=credentials[1],
        service_key=credentials[2],
        allow_prune=args.limit is None and not skipped,
    )
    print(f"written {written}, unchanged {unchanged}, stale deleted {deleted}")
    if skipped:
        print("stale video rows were not pruned because collection had skips")


if __name__ == "__main__":
    main()
