"""Offline contracts for the vetted YouTube transcript ingest."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "build-video-kb.py"


def load_script():
    spec = importlib.util.spec_from_file_location("build_video_kb", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def video_kb():
    return load_script()


def test_watch_page_yields_the_six_vetted_channels(video_kb):
    channels = video_kb.channels_from_watch_page(ROOT / "site" / "watch.html")

    assert list(channels) == [
        "apologetics-roadshow",
        "apostate-prophet",
        "godlogic-apologetics",
        "inspiring-philosophy",
        "islam-critiqued",
        "testify",
    ]
    assert channels["apostate-prophet"] == {
        "name": "Apostate Prophet",
        "url": "https://www.youtube.com/@ApostateProphet",
    }


def test_parse_vtt_removes_markup_and_adjacent_rolling_duplicates(video_kb):
    vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
<c>Allah</c> is not a father

00:00:02.500 --> 00:00:04.000
Allah is not a father

00:01:05.000 --> 00:01:07.000
The same words may be spoken again

00:02:05.000 --> 00:02:07.000
The same words may be spoken again
"""

    assert video_kb.parse_vtt(vtt) == [
        (1, "Allah is not a father"),
        (65, "The same words may be spoken again"),
        (125, "The same words may be spoken again"),
    ]


def test_parse_vtt_accepts_hourless_timestamps_and_decodes_entities(video_kb):
    vtt = """WEBVTT

01:02.500 --> 01:04.000
Qur&#39;an &amp; Bible
"""

    assert video_kb.parse_vtt(vtt) == [(62, "Qur'an & Bible")]


def test_parse_vtt_removes_partial_overlap_from_rolling_captions(video_kb):
    vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Allah is not

00:00:02.500 --> 00:00:04.000
is not a father

00:00:03.500 --> 00:00:05.000
a father in Islam
"""

    assert video_kb.parse_vtt(vtt) == [
        (1, "Allah is not"),
        (2, "a father"),
        (3, "in Islam"),
    ]


def test_chunk_cues_keeps_the_first_timestamp_and_flushes_tail(video_kb):
    cues = [
        (5, "one two"),
        (9, "three four"),
        (20, "five"),
    ]

    assert video_kb.chunk_cues(cues, words_per_chunk=4) == [
        (5, "one two three four"),
        (20, "five"),
    ]


def test_video_docs_have_stable_timestamped_identity_and_citation(video_kb):
    docs = video_kb.video_docs(
        channel_slug="testify",
        channel_name="Testify",
        video={"id": "abc123", "title": "Who Is Jesus?"},
        cues=[(65, "first passage"), (130, "second passage")],
        words_per_chunk=2,
    )

    assert docs == [
        {
            "kind": "video",
            "slug": "abc123-p0000",
            "title": "Who Is Jesus?",
            "ref": "Testify · 1:05",
            "source": "testify",
            "categories": [],
            "strength": None,
            "url": "https://www.youtube.com/watch?v=abc123&t=65s",
            "body": "first passage",
            "embed_text": "Who Is Jesus? · Testify · 1:05\nfirst passage",
        },
        {
            "kind": "video",
            "slug": "abc123-p0001",
            "title": "Who Is Jesus?",
            "ref": "Testify · 2:10",
            "source": "testify",
            "categories": [],
            "strength": None,
            "url": "https://www.youtube.com/watch?v=abc123&t=130s",
            "body": "second passage",
            "embed_text": "Who Is Jesus? · Testify · 2:10\nsecond passage",
        },
    ]


def test_collect_video_docs_fails_soft_for_listing_and_caption_errors(video_kb):
    channels = {
        "broken-channel": {"name": "Broken", "url": "https://example.invalid/broken"},
        "testify": {"name": "Testify", "url": "https://example.invalid/testify"},
    }

    def list_videos(url):
        if url.endswith("broken"):
            raise RuntimeError("listing unavailable")
        return [
            {"id": "missing", "title": "No captions"},
            {"id": "works", "title": "Works"},
        ]

    def fetch(video_id):
        if video_id == "missing":
            raise RuntimeError("captions unavailable")
        return [(10, "one two three")]

    docs, skipped = video_kb.collect_video_docs(
        channels,
        limit=None,
        words_per_chunk=3,
        list_videos=list_videos,
        fetch_cues=fetch,
        report=lambda _message: None,
    )

    assert [doc["slug"] for doc in docs] == ["works-p0000"]
    assert skipped == [
        {"channel": "broken-channel", "video_id": None, "reason": "listing unavailable"},
        {"channel": "testify", "video_id": "missing", "reason": "captions unavailable"},
    ]


def test_video_docs_use_sequence_identity_when_timestamps_share_a_second(video_kb):
    docs = video_kb.video_docs(
        channel_slug="testify",
        channel_name="Testify",
        video={"id": "same-second", "title": "Short cues"},
        cues=[(0.1, "one"), (0.9, "two")],
        words_per_chunk=1,
    )

    assert [doc["slug"] for doc in docs] == [
        "same-second-p0000",
        "same-second-p0001",
    ]


def test_choose_english_track_prefers_manual_then_exact_english(video_kb):
    info = {
        "subtitles": {
            "en-GB": [{"ext": "vtt"}],
            "en": [{"ext": "vtt"}],
        },
        "automatic_captions": {
            "en": [{"ext": "vtt"}],
        },
    }

    assert video_kb.choose_english_track(info) == ("manual", "en")


def test_choose_english_track_falls_back_to_automatic_variant(video_kb):
    info = {
        "subtitles": {},
        "automatic_captions": {
            "fr": [{"ext": "vtt"}],
            "en-US": [{"ext": "vtt"}],
        },
    }

    assert video_kb.choose_english_track(info) == ("automatic", "en-US")
    assert video_kb.choose_english_track({"subtitles": {}, "automatic_captions": {}}) is None


def test_fetch_caption_cues_falls_back_when_manual_download_fails(
    video_kb, tmp_path
):
    calls = []

    class FakeYoutubeDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def extract_info(self, _url, download):
            assert download is False
            return {
                "subtitles": {"en": [{"ext": "vtt"}]},
                "automatic_captions": {"en": [{"ext": "vtt"}]},
            }

        def download(self, _urls):
            if self.options.get("writesubtitles"):
                calls.append("manual")
                raise RuntimeError("manual track unavailable")
            calls.append("automatic")
            (tmp_path / "abc.en.vtt").write_text(
                "WEBVTT\n\n00:00:05.000 --> 00:00:06.000\nusable fallback\n",
                encoding="utf-8",
            )

    cues = video_kb.fetch_caption_cues(
        "abc",
        tmp_path,
        ydl_factory=FakeYoutubeDL,
    )

    assert calls == ["manual", "automatic"]
    assert cues == [(5, "usable fallback")]


def test_validate_collection_rejects_a_systemic_caption_failure(video_kb):
    with pytest.raises(SystemExit, match="no video transcript documents"):
        video_kb.validate_collection(
            [],
            [{"channel": "testify", "video_id": "abc", "reason": "blocked"}],
        )


def test_empty_channel_listing_is_a_skip_that_disables_pruning(video_kb):
    channels = {
        "empty": {"name": "Empty", "url": "https://example.invalid/empty"},
        "testify": {"name": "Testify", "url": "https://example.invalid/testify"},
    }

    docs, skipped = video_kb.collect_video_docs(
        channels,
        limit=None,
        words_per_chunk=1,
        list_videos=lambda url: (
            [] if url.endswith("empty") else [{"id": "works", "title": "Works"}]
        ),
        fetch_cues=lambda _video_id: [(1, "text")],
        report=lambda _message: None,
    )

    assert [doc["slug"] for doc in docs] == ["works-p0000"]
    assert skipped == [
        {"channel": "empty", "video_id": None, "reason": "channel returned no videos"}
    ]


def test_ingest_commits_each_channel_separately_before_pruning(video_kb):
    docs = [
        {"kind": "video", "source": "alpha", "slug": "a-p0000"},
        {"kind": "video", "source": "beta", "slug": "b-p0000"},
        {"kind": "video", "source": "alpha", "slug": "a-p0001"},
    ]
    batches = []
    pruned = []

    def upsert(batch, db_url, embed_url, service_key):
        batches.append(
            ([doc["slug"] for doc in batch], db_url, embed_url, service_key)
        )
        return len(batch), 0

    def prune(expected_slugs, db_url):
        pruned.append((expected_slugs, db_url))
        return 2

    assert video_kb.ingest_video_docs(
        docs,
        db_url="db",
        embed_url="embed",
        service_key="service",
        allow_prune=True,
        upsert=upsert,
        prune=prune,
    ) == (3, 0, 2)
    assert batches == [
        (["a-p0000", "a-p0001"], "db", "embed", "service"),
        (["b-p0000"], "db", "embed", "service"),
    ]
    assert pruned == [(["a-p0000", "a-p0001", "b-p0000"], "db")]


def test_prune_deletes_only_video_slugs_outside_complete_corpus(video_kb):
    class Cursor:
        rowcount = 2

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params):
            assert "where kind = 'video'" in sql
            assert "not (slug = any(%s))" in sql
            assert params == (["a-p0000", "b-p0000"],)

    class Connection:
        committed = False
        rolled_back = False
        closed = False

        def cursor(self):
            return Cursor()

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    connection = Connection()
    deleted = video_kb.prune_stale_video_docs(
        ["a-p0000", "b-p0000"],
        "db",
        connect=lambda _db_url: connection,
    )

    assert deleted == 2
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True


@pytest.mark.parametrize("value", ["0", "-1"])
def test_limit_must_be_positive(video_kb, value):
    with pytest.raises(Exception, match="positive"):
        video_kb._positive_int(value)
