"""Unit tests for the ingest client's pure logic.

Everything here runs without a database and without the edge runtime — the
chunking and retry behaviour is exactly the part that is expensive to debug
against a live box, so it is tested here instead.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location("kb_client", ROOT / "kb_client.py")
kc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kc)


def doc(body="", **kw):
    base = {
        "kind": "entry", "slug": "s", "title": "Title", "ref": "Quran 4:34",
        "source": "quran", "categories": ["morality"], "strength": "strong",
        "url": "catalog/quran.html#s", "body": body,
    }
    base.update(kw)
    return base


# ---------- content_hash ----------

def test_hash_is_stable_and_order_independent_for_categories():
    a = doc("text", categories=["a", "b"])
    b = doc("text", categories=["b", "a"])
    assert kc.content_hash(a) == kc.content_hash(b)


def test_hash_changes_when_body_changes():
    assert kc.content_hash(doc("one")) != kc.content_hash(doc("two"))


def test_hash_ignores_fields_that_do_not_affect_embedding():
    """strength is not in HASH_FIELDS: changing it must not force a re-embed."""
    assert kc.content_hash(doc("x", strength="basic")) == kc.content_hash(
        doc("x", strength="strong")
    )


# ---------- chunk_doc ----------

def test_short_document_is_one_chunk_carrying_the_heading():
    cs = kc.chunk_doc(doc("A short body."))
    assert len(cs) == 1
    assert cs[0].startswith("Title · Quran 4:34 · morality")
    assert "A short body." in cs[0]


def test_long_document_splits_into_several_chunks():
    body = " ".join(f"word{i}" for i in range(3000))
    cs = kc.chunk_doc(doc(body))
    assert len(cs) > 1


def test_no_chunk_exceeds_the_char_limit():
    """gte-small truncates at 512 tokens silently — the limit is a hard ceiling,
    and the heading counts against it."""
    body = " ".join(f"word{i}" for i in range(5000))
    for c in kc.chunk_doc(doc(body)):
        assert len(c) <= kc.CHUNK_CHAR_LIMIT


def test_every_chunk_carries_the_heading():
    body = " ".join(f"word{i}" for i in range(3000))
    for c in kc.chunk_doc(doc(body)):
        assert c.startswith("Title · Quran 4:34 · morality")


def test_chunks_do_not_cut_mid_word():
    body = " ".join(f"word{i:05d}" for i in range(2000))
    for c in kc.chunk_doc(doc(body)):
        tail = c.rsplit(" ", 1)[-1]
        assert tail.startswith("word") and len(tail) == 9, f"cut mid-word: {tail!r}"


def test_chunk_count_is_capped():
    body = " ".join(f"word{i}" for i in range(20000))
    assert len(kc.chunk_doc(doc(body))) == kc.MAX_CHUNKS


def test_cap_is_high_enough_for_a_full_length_dossier():
    """Regression guard. At the bake-off's cap of 4 (~7200 chars), 124 of 140
    dossiers lost roughly half their body. Real dossiers run to ~13,700 chars."""
    body = "x" * 13_800
    assert not kc.chunks_were_truncated(doc(body)), (
        "a full-length dossier is being truncated again — check MAX_CHUNKS"
    )


def test_cap_is_reported_rather_than_silent():
    long_body = " ".join(f"word{i}" for i in range(20000))
    assert kc.chunks_were_truncated(doc(long_body)) is True
    assert kc.chunks_were_truncated(doc("short")) is False


def test_document_with_no_body_still_yields_one_chunk():
    """Otherwise the document is unfindable by vector search entirely."""
    cs = kc.chunk_doc(doc(""))
    assert len(cs) == 1 and "Title" in cs[0]


def test_document_with_neither_body_nor_heading_yields_nothing():
    cs = kc.chunk_doc(doc("", title="", ref=None, categories=[]))
    assert cs == []


# ---------- embed_texts ----------

class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


def test_batches_are_capped_at_batch_size():
    seen = []

    def post(url, json=None, headers=None, timeout=None):
        seen.append(len(json["input"]))
        return FakeResponse(200, {"embeddings": [[0.0] * 384] * len(json["input"])})

    kc.embed_texts([f"t{i}" for i in range(25)], "u", "k", batch=10, post=post)
    assert seen == [10, 10, 5]


def test_default_batches_stay_within_the_live_edge_runtime_limit():
    """The production 2-vCPU Edge runtime cannot sustain ten-text batches."""
    seen = []

    def post(url, json=None, headers=None, timeout=None):
        seen.append(len(json["input"]))
        return FakeResponse(200, {"embeddings": [[0.0] * 384] * len(json["input"])})

    kc.embed_texts([f"t{i}" for i in range(12)], "u", "k", post=post)

    assert seen == [5, 5, 2]


def test_request_uses_the_input_key_the_function_actually_expects():
    captured = {}

    def post(url, json=None, headers=None, timeout=None):
        captured.update(json=json, headers=headers)
        return FakeResponse(200, {"embeddings": [[0.0] * 384]})

    kc.embed_texts(["one"], "u", "secret", post=post)
    assert "input" in captured["json"], "the deployed function reads `input`, not `texts`"
    assert captured["headers"]["Authorization"] == "Bearer secret"


def test_a_500_is_retried_and_can_succeed(monkeypatch):
    """The edge runtime's CPU soft limit surfaces as an opaque 500 on a used
    worker; the next request gets a fresh isolate."""
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)
    calls = []

    def post(url, json=None, headers=None, timeout=None):
        calls.append(1)
        if len(calls) == 1:
            return FakeResponse(500, text="CPU time soft limit reached")
        return FakeResponse(200, {"embeddings": [[0.1] * 384]})

    out = kc.embed_texts(["one"], "u", "k", post=post)
    assert len(calls) == 2
    assert out == [[0.1] * 384]


def test_repeated_500_splits_the_batch_and_preserves_vector_order(monkeypatch):
    """A CPU-heavy batch must recover on smaller fresh isolates, not abort a kind."""
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)
    seen = []

    def post(url, json=None, headers=None, timeout=None):
        texts = json["input"]
        seen.append(list(texts))
        if len(texts) > 5:
            return FakeResponse(
                500,
                text='{"msg":"WorkerRequestCancelled: request has been cancelled by supervisor"}',
            )
        return FakeResponse(200, {"embeddings": [[float(t[1:])] * 384 for t in texts]})

    out = kc.embed_texts([f"t{i}" for i in range(10)], "u", "k", batch=10, post=post)

    assert [len(group) for group in seen] == [10, 10, 10, 10, 5, 5]
    assert [vector[0] for vector in out] == list(map(float, range(10)))


def test_a_403_fails_immediately_instead_of_retrying(monkeypatch):
    """Wrong key is a config error. Retrying it four times just delays the report."""
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)
    calls = []

    def post(url, json=None, headers=None, timeout=None):
        calls.append(1)
        return FakeResponse(403, {"error": "forbidden"}, text='{"error":"forbidden"}')

    with pytest.raises(SystemExit) as e:
        kc.embed_texts(["one"], "u", "anon-key", post=post)
    assert len(calls) == 1
    assert "service_role" in str(e.value)


def test_persistent_500_eventually_raises(monkeypatch):
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)

    def post(url, json=None, headers=None, timeout=None):
        return FakeResponse(500, text="boom")

    with pytest.raises(RuntimeError, match="after 4 attempts"):
        kc.embed_texts(["one"], "u", "k", post=post)


def test_persistent_503_does_not_claim_a_one_text_500(monkeypatch):
    """Exhausted retries must report the failure that actually occurred."""
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)

    def post(url, json=None, headers=None, timeout=None):
        return FakeResponse(503, text="temporarily unavailable")

    with pytest.raises(RuntimeError) as error:
        kc.embed_texts(["a", "b", "c"], "u", "k", post=post)

    assert "HTTP 503" in str(error.value)
    assert "one-text batch" not in str(error.value)


def test_short_vector_count_is_caught(monkeypatch):
    """A batch that comes back short would silently misalign every chunk after
    it, pairing documents with other documents' vectors."""
    monkeypatch.setattr(kc.time, "sleep", lambda *_: None)

    def post(url, json=None, headers=None, timeout=None):
        return FakeResponse(200, {"embeddings": [[0.0] * 384]})   # asked for 3

    with pytest.raises(RuntimeError):
        kc.embed_texts(["a", "b", "c"], "u", "k", post=post)


def test_empty_input_makes_no_request():
    def post(*a, **k):
        raise AssertionError("should not have been called")

    assert kc.embed_texts([], "u", "k", post=post) == []
