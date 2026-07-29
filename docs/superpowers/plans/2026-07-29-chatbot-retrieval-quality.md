# Chatbot Retrieval Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Task 10's reviewed recall fixture and evaluator so exact references must rank first, natural-language primary results must rank in the top three, ambiguity remains distinct from corpus gaps, and every expected citation resolves.

**Architecture:** A JSON fixture stores product expectations and, after Hein's bounded pre-embedding step, non-secret 384-dimensional query vectors. A credential-free Python helper validates the fixture and evaluates ordered result rows; a pytest integration layer connects through the restricted `kb_reader` SSH tunnel and calls only `match_corpus()` and `kb_find_ref()`. Final answer generation and clarification prose remain outside Task 10.

**Tech Stack:** Python 3, pytest, psycopg2, PostgreSQL/pgvector, bare JSON, existing `preembed-kb-questions.py`, existing `kb_reader` role and SSH tunnel.

## Global Constraints

- A recognized exact reference must be rank 1.
- The primary expected document for a natural-language question must be in the top 3.
- Supporting expectations may occur elsewhere in the capped twenty-result set unless the fixture sets a tighter bound.
- `reference_conflict`, `unknown_reference`, `clarifying_follow_up`, and genuine `gap` are distinct outcomes.
- Never send Zander the Supabase service-role key or superuser database URL.
- Never reopen the embed Edge Function to `anon` or `kb_reader`; Hein pre-embeds the bounded fixture on the authorized machine.
- `kb_reader` may call only `public.match_corpus(...)` and `public.kb_find_ref(text)` and may read only `public.kb_docs` and `public.kb_chunks`.
- Every expected or suggested citation must exist in the corpus and resolve into `site/`.
- Do not weaken rank or decision assertions to make current retrieval pass.
- Do not implement the later `ask` function, final clarification prose, or chat UI in this plan.
- Preserve unrelated changes in `book-design/vol1-quran/` and any other dirty worktree files.

---

## File Structure

- `preembed-kb-questions.py` — preserves fixture metadata and embeds both `q` and optional `semantic_q`.
- `tests/test_preembed_kb_questions.py` — unit tests for fixture-shaped pre-embedding input.
- `kb_retrieval_eval.py` — credential-free fixture validation, ordered-rank assertions, decision checks, citation-path checks and failure formatting.
- `tests/test_kb_retrieval_eval.py` — unit tests for the evaluator with synthetic rows; always runnable.
- `tests/fixtures/retrieval_questions.json` — canonical reviewed product fixture without credentials or vectors.
- `tests/fixtures/retrieval_questions.embedded.json` — generated non-secret vectors from Hein; safe to transfer, but do not commit until the repository owner explicitly chooses to version the ~384-float vectors.
- `tests/test_kb_retrieval.py` — live integration tests using the SSH tunnel and embedded fixture.
- `docs/superpowers/specs/2026-07-27-ai-chatbot-design.md` — receives only measured retrieval constants after the live run.
- `docs/migration/RETRIEVAL-EVAL-2026-07-29.md` — records corpus counts, per-case results, failures, tuning and the Phase 1 decision.

---

### Task 1: Make Pre-Embedding Preserve the Retrieval Fixture

**Files:**
- Modify: `preembed-kb-questions.py`
- Modify: `tests/test_preembed_kb_questions.py`

**Interfaces:**
- Consumes: either the existing `{"questions": [{"question": "..."}]}` format or the approved fixture `{"questions": [{"id": "...", "q": "...", "semantic_q": "..."}]}`.
- Produces: `normalize_questions(payload: object) -> list[dict]`.
- Produces: `embedding_requests(records: list[dict]) -> list[tuple[int, str, str]]`, where each tuple is `(record_index, output_field, text)`.
- Produces: generated records carrying `embedding` for `q`/`question` and `semantic_embedding` for `semantic_q`, each exactly 384 dimensions.

- [ ] **Step 1: Add failing tests for fixture-shaped records**

Append tests that preserve expectation metadata and discard stale vectors:

```python
def test_normalize_questions_preserves_fixture_fields():
    payload = {
        "questions": [{
            "id": "reference-conflict",
            "mode": "reference_conflict",
            "q": "Does Quran 9:5 say there is no compulsion in religion?",
            "semantic_q": "There is no compulsion in religion",
            "primary": {"ref": "Quran 2:256", "max_rank": 3},
            "expected_decision": "clarify",
            "embedding": [0.0],
            "semantic_embedding": [0.0],
        }]
    }
    assert MODULE.normalize_questions(payload) == [{
        "id": "reference-conflict",
        "mode": "reference_conflict",
        "q": "Does Quran 9:5 say there is no compulsion in religion?",
        "semantic_q": "There is no compulsion in religion",
        "primary": {"ref": "Quran 2:256", "max_rank": 3},
        "expected_decision": "clarify",
    }]


def test_embedding_requests_include_description_only_query():
    records = [{
        "id": "reference-conflict",
        "q": "Does Quran 9:5 say there is no compulsion in religion?",
        "semantic_q": "There is no compulsion in religion",
    }]
    assert MODULE.embedding_requests(records) == [
        (0, "embedding", records[0]["q"]),
        (0, "semantic_embedding", records[0]["semantic_q"]),
    ]
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
python -m pytest tests/test_preembed_kb_questions.py -q
```

Expected: failures because fixture `q` is not accepted and `embedding_requests` does not exist.

- [ ] **Step 3: Implement the minimal format adapter**

Update normalization and add the request flattener:

```python
def normalize_questions(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("questions")
    if not isinstance(payload, list) or not payload:
        raise ValueError("input must contain a non-empty questions list")

    questions = []
    for index, item in enumerate(payload, start=1):
        if isinstance(item, str):
            record = {"id": f"q{index}", "question": item.strip()}
        elif isinstance(item, dict):
            record = dict(item)
        else:
            raise ValueError(f"question {index} must be a string or object")

        field = "q" if "q" in record else "question"
        text = record.get(field)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"question {index} has no non-empty 'q' or 'question'")
        record[field] = text.strip()

        semantic = record.get("semantic_q")
        if semantic is not None:
            if not isinstance(semantic, str) or not semantic.strip():
                raise ValueError(f"question {index} has an invalid 'semantic_q'")
            record["semantic_q"] = semantic.strip()

        record.setdefault("id", f"q{index}")
        record.pop("embedding", None)
        record.pop("semantic_embedding", None)
        questions.append(record)
    return questions


def embedding_requests(records: list[dict]) -> list[tuple[int, str, str]]:
    requests = []
    for index, record in enumerate(records):
        text = record.get("q", record.get("question"))
        requests.append((index, "embedding", text))
        if record.get("semantic_q"):
            requests.append((index, "semantic_embedding", record["semantic_q"]))
    return requests
```

In `main()`, flatten once, embed once, and assign by index/field:

```python
requests = embedding_requests(questions)
vectors = kb_client.embed_texts(
    [text for _, _, text in requests],
    embed_url,
    service_key,
)
for (index, field, _), vector in zip(requests, vectors, strict=True):
    if len(vector) != 384:
        raise RuntimeError(
            f"{questions[index]['id']}:{field}: expected 384 dimensions, "
            f"got {len(vector)}"
        )
    questions[index][field] = vector
```

- [ ] **Step 4: Run focused and related tests**

Run:

```bash
python -m pytest tests/test_preembed_kb_questions.py tests/test_kb_client.py -q
```

Expected: all tests in both files pass.

- [ ] **Step 5: Commit the adapter**

```bash
git add preembed-kb-questions.py tests/test_preembed_kb_questions.py
git commit -m "test(chatbot): preembed retrieval fixture queries"
```

---

### Task 2: Build the Credential-Free Fixture Evaluator

**Files:**
- Create: `kb_retrieval_eval.py`
- Create: `tests/test_kb_retrieval_eval.py`

**Interfaces:**
- Consumes: one fixture case and ordered retrieval rows shaped as `kind`, `slug`, `title`, `ref`, `categories`, `url`, `score`.
- Produces: `validate_fixture(payload: object, require_embeddings: bool = False) -> list[dict]`.
- Produces: `find_rank(rows: list[dict], identity: dict) -> int | None`, using one of `ref` or `slug`.
- Produces: `assert_case(case: dict, semantic_rows: list[dict], exact_rows: list[dict]) -> None`.
- Produces: `citation_path(url: str, site_root: Path) -> tuple[Path, str | None]`.
- Produces: `format_rows(rows: list[dict]) -> str`.

- [ ] **Step 1: Write failing schema tests**

Create tests covering accepted modes, one-of identity, rank bounds and required embeddings:

```python
def test_validate_fixture_accepts_approved_shape():
    payload = {"questions": [{
        "id": "trinity",
        "mode": "natural",
        "q": "Is the Trinity three gods?",
        "primary": {"slug": "trinity-not-three-gods", "max_rank": 3},
        "support": {"kinds": ["doctrine"]},
        "expected_decision": "answer",
        "note": "Doctrine smoke-test document.",
    }]}
    assert evaluate.validate_fixture(payload) == payload["questions"]


@pytest.mark.parametrize("mutator", [
    lambda c: c.pop("id"),
    lambda c: c.update(mode="other"),
    lambda c: c.update(primary={"max_rank": 3}),
    lambda c: c.update(primary={"ref": "Quran 9:5", "slug": "x", "max_rank": 1}),
    lambda c: c.update(expected_decision="guess"),
])
def test_validate_fixture_rejects_ambiguous_contract(mutator):
    case = {
        "id": "exact",
        "mode": "exact_match",
        "q": "Quran 9:5",
        "primary": {"ref": "Quran 9:5", "max_rank": 1},
        "expected_decision": "answer",
        "note": "Exact reference.",
    }
    mutator(case)
    with pytest.raises(ValueError):
        evaluate.validate_fixture({"questions": [case]})


def test_validate_fixture_requires_vectors_only_for_live_run():
    payload = {"questions": [{
        "id": "exact",
        "mode": "exact_match",
        "q": "Quran 9:5",
        "primary": {"ref": "Quran 9:5", "max_rank": 1},
        "expected_decision": "answer",
        "note": "Exact reference.",
    }]}
    with pytest.raises(ValueError, match="embedding"):
        evaluate.validate_fixture(payload, require_embeddings=True)
```

- [ ] **Step 2: Run the new test file and confirm RED**

Run:

```bash
python -m pytest tests/test_kb_retrieval_eval.py -q
```

Expected: collection fails because `kb_retrieval_eval.py` does not exist.

- [ ] **Step 3: Implement schema validation**

Use fixed allowed sets and explicit field checks:

```python
MODES = {
    "natural", "exact_match", "reference_conflict",
    "unknown_reference", "clarifying_follow_up", "gap",
}
DECISIONS = {"answer", "clarify", "gap"}


def validate_fixture(payload: object, require_embeddings: bool = False) -> list[dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get("questions"), list):
        raise ValueError("fixture must be {'questions': [...]}")
    cases = payload["questions"]
    if not cases:
        raise ValueError("fixture must contain at least one question")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("every question must be an object")
        for field in ("id", "mode", "q", "expected_decision", "note"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError(f"case missing non-empty {field!r}")
        if case["id"] in seen:
            raise ValueError(f"duplicate id: {case['id']}")
        seen.add(case["id"])
        if case["mode"] not in MODES:
            raise ValueError(f"{case['id']}: invalid mode")
        if case["expected_decision"] not in DECISIONS:
            raise ValueError(f"{case['id']}: invalid expected_decision")
        primary = case.get("primary")
        if case["mode"] == "gap":
            if primary is not None:
                raise ValueError(f"{case['id']}: gap cases cannot name a primary")
        else:
            if not isinstance(primary, dict):
                raise ValueError(f"{case['id']}: primary must be an object")
            identities = [name for name in ("ref", "slug") if primary.get(name)]
            if len(identities) != 1:
                raise ValueError(f"{case['id']}: primary needs exactly one ref or slug")
            if primary.get("max_rank") not in (1, 2, 3):
                raise ValueError(f"{case['id']}: primary max_rank must be 1, 2 or 3")
        if require_embeddings:
            _validate_vector(case, "embedding")
            if case.get("semantic_q"):
                _validate_vector(case, "semantic_embedding")
    return cases
```

`_validate_vector()` accepts only a list of 384 finite numbers.

- [ ] **Step 4: Add failing ordered-rank and decision tests**

```python
ROWS = [
    {"kind": "verse", "slug": "quran/9:5", "title": "Quran 9:5",
     "ref": "Quran 9:5", "categories": [], "url": "read/quran/9.html#s9v5", "score": 0.03},
    {"kind": "entry", "slug": "unrelated", "title": "An unrelated entry",
     "ref": "Quran 9:6", "categories": ["warfare"], "url": "catalog/quran.html#unrelated", "score": 0.02},
]


def test_exact_match_requires_rank_one():
    case = {
        "id": "exact", "mode": "exact_match", "q": "Quran 9:5",
        "primary": {"ref": "Quran 9:5", "max_rank": 1},
        "expected_decision": "answer", "note": "Exact reference.",
    }
    evaluate.assert_case(case, semantic_rows=[], exact_rows=ROWS)
    with pytest.raises(AssertionError, match="rank 1"):
        evaluate.assert_case(case, semantic_rows=[], exact_rows=list(reversed(ROWS)))


def test_reference_conflict_requires_distinct_exact_and_candidate():
    case = {
        "id": "conflict", "mode": "reference_conflict",
        "q": "Does Quran 9:5 say there is no compulsion?",
        "semantic_q": "There is no compulsion in religion",
        "supplied": {"ref": "Quran 9:5"},
        "primary": {"ref": "Quran 2:256", "max_rank": 3},
        "expected_decision": "clarify", "note": "Description conflicts with number.",
    }
    exact = [ROWS[0]]
    semantic = [{
        **ROWS[0], "slug": "quran/2:256", "title": "Quran 2:256",
        "ref": "Quran 2:256", "url": "read/quran/2.html#s2v256",
    }]
    evaluate.assert_case(case, semantic, exact)


def test_forbid_top_rejects_wrong_verse_primary():
    case = {
        "id": "wrong-verse", "mode": "natural", "q": "What is the Injeel?",
        "primary": {"slug": "what-is-the-injeel", "max_rank": 3},
        "forbid_top": [{"kind": "verse", "max_rank": 3}],
        "expected_decision": "answer", "note": "Doctrine must lead.",
    }
    with pytest.raises(AssertionError, match="forbidden"):
        evaluate.assert_case(case, semantic_rows=ROWS, exact_rows=[])
```

- [ ] **Step 5: Implement ordered assertions and diagnostic formatting**

`find_rank()` returns one-based rank. `assert_case()` selects exact rows for
`exact_match`, semantic rows for other modes, checks primary rank, then checks:

```python
def find_rank(rows: list[dict], identity: dict) -> int | None:
    field = "ref" if identity.get("ref") else "slug"
    expected = identity[field]
    for rank, row in enumerate(rows, start=1):
        if row.get(field) == expected:
            return rank
    return None


def format_rows(rows: list[dict]) -> str:
    return "\n".join(
        f"{rank:>2}. {row.get('kind')} | {row.get('ref') or '-'} | "
        f"{row.get('slug')} | {row.get('score', 0):.6f} | {row.get('url')}"
        for rank, row in enumerate(rows, start=1)
    )
```

For `reference_conflict`, require `supplied.ref`, require it in `exact_rows`, require
the primary candidate in `semantic_rows`, require the two refs to differ, and require
`expected_decision == "clarify"`. For `unknown_reference`, require empty
`exact_rows` and `expected_decision == "clarify"`. For `gap`, require
`expected_decision == "gap"`; the later live threshold task decides whether any
semantic row is strong enough to violate the gap.

- [ ] **Step 6: Add citation-path tests and implementation**

```python
def test_citation_path_resolves_page_and_anchor():
    page, anchor = evaluate.citation_path(
        "read/quran/9.html#s9v5", ROOT / "site"
    )
    assert page.exists()
    assert anchor == "s9v5"


def test_citation_path_rejects_escape():
    with pytest.raises(ValueError):
        evaluate.citation_path("../CLAUDE.md", ROOT / "site")
```

Implementation resolves the path under `site_root`, rejects absolute/external URLs
for expected internal corpus rows, rejects `..` escapes, verifies the file exists,
and verifies `id="<fragment>"` exists when a fragment is present. Doctrine URLs are
allowed to lack a built page during Phase 1 only when `kind == "doctrine"`; record
that exception explicitly in the assertion message.

- [ ] **Step 7: Run evaluator tests**

Run:

```bash
python -m pytest tests/test_kb_retrieval_eval.py -q
```

Expected: all tests pass without database or network access.

- [ ] **Step 8: Commit the evaluator**

```bash
git add kb_retrieval_eval.py tests/test_kb_retrieval_eval.py
git commit -m "test(chatbot): add retrieval quality evaluator"
```

---

### Task 3: Author and Verify the Product Fixture

**Files:**
- Create: `tests/fixtures/retrieval_questions.json`
- Modify: `tests/test_kb_retrieval_eval.py`

**Interfaces:**
- Consumes: local corpus produced by `build-kb.py --dry-run` collectors.
- Produces: at least fifteen reviewed cases accepted by `validate_fixture()`.
- Produces: coverage labels in each case's `tags` array for auditability.

- [ ] **Step 1: Add a failing test that loads the real fixture**

```python
FIXTURE = ROOT / "tests" / "fixtures" / "retrieval_questions.json"


def test_real_fixture_schema_and_coverage():
    cases = evaluate.validate_fixture(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )
    assert len(cases) >= 15
    modes = {case["mode"] for case in cases}
    assert {
        "natural", "exact_match", "reference_conflict",
        "unknown_reference", "clarifying_follow_up", "gap",
    } <= modes
    tags = {tag for case in cases for tag in case.get("tags", [])}
    assert {
        "quran", "hadith", "bible-correct", "bible-wrong",
        "doctrine", "entry", "dossier-tail", "citation",
    } <= tags
```

- [ ] **Step 2: Run the fixture test and confirm RED**

Run:

```bash
python -m pytest tests/test_kb_retrieval_eval.py::test_real_fixture_schema_and_coverage -q
```

Expected: fail because the fixture file does not exist.

- [ ] **Step 3: Build the initial question set**

Create `{"questions": [...]}` with these reviewed intents:

| ID | Mode | User wording | Primary requirement |
|---|---|---|---|
| `exact-quran-9-5` | exact_match | `what does Quran 9:5 say` | `Quran 9:5`, rank 1 |
| `exact-bukhari-5134` | exact_match | `Bukhari 5134` | `Bukhari 5134`, rank 1 |
| `exact-john-14-17` | exact_match | `John 14:17` | `John 14:17`, rank 1 |
| `trinity-three-gods` | natural | `Is the Trinity three gods?` | doctrine slug `trinity-not-three-gods`, top 3 |
| `injeel-meaning` | natural | `What is the Injeel?` | doctrine slug `what-is-the-injeel`, top 3 |
| `eternal-generation` | natural | `How can Christians say Jesus is begotten but not created?` | doctrine slug `begets-not-eternal-generation`, top 3 |
| `paraclete-bible` | natural | `Is Muhammad the Paraclete promised by Jesus?` | `John 14:17`, top 3; Bible-correct |
| `abrogation-dossier` | natural | `What do Muslims say about verses being abrogated?` | dossier slug `quran/q09-abrogation`, top 3 |
| `crucifixion-dossier` | natural | `Why does the Quran deny that Jesus was crucified?` | dossier slug `quran/q14-denial-of-crucifixion`, top 3 |
| `aisha-response-tail` | natural | `How do Muslims defend the reports that Aisha was nine?` | dossier slug `bukhari/b01-aisha-age`, top 3; dossier-tail |
| `wife-beating-not-bible` | natural | `Does Islam allow a husband to strike his wife?` | a verified Quran-entry slug for Q4:34, top 3; forbid Bible verses in top 3 |
| `conflict-no-compulsion` | reference_conflict | `Does Quran 9:5 say there is no compulsion in religion?` | supplied `Quran 9:5`; likely `Quran 2:256`, top 3; clarify |
| `unknown-reference-with-topic` | unknown_reference | `What does Bukhari 99999 say about Aisha's age?` | exact empty; likely `Bukhari 5134`, top 3; clarify |
| `follow-up-aisha-phrase` | clarifying_follow_up | `I mean the report saying she was six when married and nine at consummation` | `Bukhari 5134`, top 3 |
| `gap-al-zutt` | gap | `What does the al-Zutt report in Musnad Ahmad prove?` | no exact corpus reference; gap |

Use `semantic_q` for conflict and unknown-reference cases so a wrong number does
not dominate candidate retrieval. Set `primary.max_rank` to 1 only for exact cases
and 3 elsewhere. Add `support` and `forbid_top` only where they express a real
product requirement.

- [ ] **Step 4: Verify every identity against local parsed source**

Run a temporary read-only inspection from PowerShell; do not write generated HTML:

```powershell
python build-kb.py --dry-run
@'
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("build_kb", Path("build-kb.py"))
build_kb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_kb)

docs = []
for name in ("entries", "dossiers", "quran", "bible", "doctrine"):
    docs.extend(build_kb.COLLECTORS[name]())
for wanted in {
    "trinity-not-three-gods",
    "what-is-the-injeel",
    "begets-not-eternal-generation",
    "quran/q09-abrogation",
    "quran/q14-denial-of-crucifixion",
    "bukhari/b01-aisha-age",
}:
    matches = [d for d in docs if d["slug"] == wanted]
    assert len(matches) == 1, (wanted, len(matches))
    print(wanted, matches[0]["ref"], matches[0]["url"])
'@ | python -
```

Before committing, locate the actual Q4:34 entry slug from `collect_entries()` and
write that concrete slug into the fixture. Do not leave a label or guessed slug.
Confirm exact refs `Quran 9:5`, `Quran 2:256`, `Bukhari 5134`, and `John 14:17`
each exist in the collected corpus.

- [ ] **Step 5: Verify every internal citation**

Extend the real-fixture test to build a local identity index from the collectors.
For each `primary`, `supplied`, and expected support identity:

1. assert exactly one matching corpus row where uniqueness is required;
2. pass its URL through `citation_path()`;
3. verify the target page and fragment;
4. permit doctrine's not-yet-built page only with an explicit doctrine assertion.

Run:

```bash
python -m pytest tests/test_kb_retrieval_eval.py tests/test_kb_urls_resolve.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the reviewed fixture**

```bash
git add tests/fixtures/retrieval_questions.json tests/test_kb_retrieval_eval.py
git commit -m "test(chatbot): add reviewed retrieval questions"
```

---

### Task 4: Add the Live `kb_reader` Integration Harness

**Files:**
- Create: `tests/test_kb_retrieval.py`
- Reuse, do not commit by default: `tests/fixtures/retrieval_questions.embedded.json`

**Interfaces:**
- Consumes: `KB_READER_PASSWORD`; fixed tunnel defaults `127.0.0.1:15432`, database `postgres`, user `kb_reader`.
- Consumes: optional overrides `KB_READER_HOST`, `KB_READER_PORT`, `KB_READER_DB`, `KB_READER_USER`.
- Consumes: pre-embedded fixture containing `embedding` and optional `semantic_embedding`.
- Produces: `_retrieve(cur, q_text: str, embedding: list[float]) -> list[dict]`.
- Produces: `_find_ref(cur, q_text: str) -> list[dict]`.
- Produces: parametrized live recall results checked by `assert_case()`.

- [ ] **Step 1: Write the connection and skip-boundary tests first**

The module must load and fixture-schema tests must run without secrets. Only a
fixture requiring a database cursor may skip:

```python
ROOT = Path(__file__).resolve().parents[1]
EMBEDDED = ROOT / "tests" / "fixtures" / "retrieval_questions.embedded.json"
PASSWORD = os.environ.get("KB_READER_PASSWORD")


def _connection_kwargs() -> dict:
    return {
        "host": os.environ.get("KB_READER_HOST", "127.0.0.1"),
        "port": int(os.environ.get("KB_READER_PORT", "15432")),
        "dbname": os.environ.get("KB_READER_DB", "postgres"),
        "user": os.environ.get("KB_READER_USER", "kb_reader"),
        "password": PASSWORD,
        "connect_timeout": 5,
    }


def test_connection_defaults_are_the_restricted_tunnel():
    kwargs = _connection_kwargs()
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 15432
    assert kwargs["user"] == "kb_reader"
```

Do not accept `SUPABASE_DB_URL` or `SUPABASE_SERVICE_ROLE_KEY` as fallbacks.

- [ ] **Step 2: Run the focused file and confirm RED**

Run:

```bash
python -m pytest tests/test_kb_retrieval.py -q
```

Expected: fail because the file or required helpers do not yet exist; after the
local-only test is added, live cases may skip but the connection-default test must
pass.

- [ ] **Step 3: Implement the read-only database helpers**

```python
ROW_FIELDS = [
    "kind", "slug", "title", "ref", "categories", "url", "score",
]


def _retrieve(cur, q_text: str, embedding: list[float]) -> list[dict]:
    vector = "[" + ",".join(str(value) for value in embedding) + "]"
    cur.execute(
        """
        select kind, slug, title, ref, categories, url, score
        from public.match_corpus(%s, %s::vector, 20)
        """,
        (q_text, vector),
    )
    return [dict(zip(ROW_FIELDS, row)) for row in cur.fetchall()]


def _find_ref(cur, q_text: str) -> list[dict]:
    cur.execute(
        """
        select kind, slug, title, ref, categories, url, 1.0::double precision
        from public.kb_find_ref(%s)
        """,
        (q_text,),
    )
    return [dict(zip(ROW_FIELDS, row)) for row in cur.fetchall()]
```

The session fixture opens one connection, sets `default_transaction_read_only = on`,
and rolls back/closes in `finally`. Failure to connect must mention the SSH tunnel
command from `docs/migration/KB-READER.md`, never print the password or DSN.

- [ ] **Step 4: Add the parametrized live test**

Load the embedded fixture only when both the file and password exist:

```python
LIVE = EMBEDDED.exists() and bool(PASSWORD)
LIVE_REASON = (
    "start the restricted SSH tunnel, set KB_READER_PASSWORD, and obtain "
    "retrieval_questions.embedded.json from Hein"
)


@pytest.mark.skipif(not LIVE, reason=LIVE_REASON)
@pytest.mark.parametrize("case", _embedded_cases(), ids=lambda case: case["id"])
def test_live_retrieval(case, kb_cursor):
    semantic_text = case.get("semantic_q", case["q"])
    semantic_vector = case.get("semantic_embedding", case["embedding"])
    semantic_rows = _retrieve(kb_cursor, semantic_text, semantic_vector)
    exact_rows = (
        _find_ref(kb_cursor, case["q"])
        if case["mode"] in {"exact_match", "reference_conflict", "unknown_reference"}
        else []
    )
    evaluate.assert_case(case, semantic_rows, exact_rows)
```

For `gap`, calculate strong rows using a single module constant `MIN_SCORE`; begin
with `0.02` as a hypothesis from the old plan, label it explicitly provisional, and
record the measured distribution before changing it.

- [ ] **Step 5: Prove the evaluator cannot write**

Add one live permission test using a transaction that attempts:

```sql
insert into public.kb_docs
  (kind, slug, title, categories, url, body, content_hash)
values
  ('doctrine', 'forbidden-probe', 'forbidden', '{}', 'x', 'x', 'x')
```

Expected: `psycopg2.errors.ReadOnlySqlTransaction` or
`psycopg2.errors.InsufficientPrivilege`. Roll back immediately. Do not probe any
private application table from this routine test; Hein's credential verification
report already records the broader negative tests.

- [ ] **Step 6: Run credential-free verification**

Run:

```bash
python -m pytest \
  tests/test_preembed_kb_questions.py \
  tests/test_kb_retrieval_eval.py \
  tests/test_kb_retrieval.py -q
```

Expected without tunnel/password/embedded vectors: all local tests pass and only
live-marked cases skip.

- [ ] **Step 7: Commit the integration harness**

```bash
git add tests/test_kb_retrieval.py
git commit -m "test(chatbot): add kb_reader recall harness"
```

---

### Task 5: Pre-Embed, Run, Diagnose, and Record the Gate

**Files:**
- Generate outside the public commit by default: `tests/fixtures/retrieval_questions.embedded.json`
- Modify only if measured evidence requires it: `supabase/chatbot-kb.sql`
- Modify after measurement: `docs/superpowers/specs/2026-07-27-ai-chatbot-design.md`
- Create: `docs/migration/RETRIEVAL-EVAL-2026-07-29.md`

**Interfaces:**
- Consumes: canonical fixture from Task 3.
- Produces: Hein-generated embedded fixture with 384-dimensional vectors.
- Produces: per-case rank/citation results and a Phase 1 go/no-go decision.
- Produces: tuned SQL only when a diagnosed retrieval defect requires it.

- [ ] **Step 1: Hand the bounded fixture to Hein for pre-embedding**

On Hein's authorized machine, with `SUPABASE_EMBED_URL` and
`SUPABASE_SERVICE_ROLE_KEY` already set:

```bash
python preembed-kb-questions.py \
  tests/fixtures/retrieval_questions.json \
  tests/fixtures/retrieval_questions.embedded.json
```

Expected: output reports the number of embedded original and semantic queries.
The generated file contains no credential. Confirm every vector has 384 dimensions.

- [ ] **Step 2: Start the restricted tunnel and run the live suite**

Follow the exact restricted-tunnel command supplied by Hein with the credential
handoff; its `permitopen` target must match the current `supabase-db` container
address. Do not paste either secret into a command committed to shell history.

In a second terminal, set `KB_READER_PASSWORD` using a hidden prompt, then run:

```bash
python -m pytest tests/test_kb_retrieval.py -v
```

- [ ] **Step 3: Capture diagnostic evidence before tuning**

For every failure, record:

- case ID and mode;
- ordered top 20 with kind/ref/slug/score/URL;
- expected primary and maximum rank;
- actual primary rank or absence;
- exact-lookup rows for reference cases;
- whether the citation resolved;
- number and positions of Bible verses;
- likely failure class: exact lookup, FTS/vector fusion, kind cap, chunk
  over-fetch/collapse, threshold, missing corpus content, or fixture error.

Also ask Hein to record after full ingest:

```sql
select kind, count(*) from public.kb_docs group by kind order by kind;
select count(*) from public.kb_chunks;
select count(*) from public.kb_chunks where embedding is null;
analyze public.kb_docs;
analyze public.kb_chunks;
```

The expected document total is 39,106 and expected chunk total is 43,016. Stop and
diagnose if counts differ materially before tuning recall.

- [ ] **Step 4: Change one retrieval variable at a time**

Use the symptom boundary:

| Evidence | First change to test |
|---|---|
| Exact ref exists but is not first | prepend `kb_find_ref()` output in the future request orchestrator; do not distort RRF |
| Correct document absent from vector candidates | inspect chunk over-fetch collapse and HNSW plan at real scale |
| Correct document present but below top 3 | tune RRF inputs or cap ordering |
| Bible verses occupy wrong top positions | tune `caps.verse` or verse ordering, retaining correct-Bible cases |
| Dossier-tail case absent | inspect best-chunk retrieval and the 240-chunk/60-document collapse |
| Gap case has weak noise only | tune `MIN_SCORE` from the measured score distribution |
| Expected identity is absent from corpus | classify as corpus gap; do not tune SQL |

If SQL changes, write a failing integration assertion first, modify only
`supabase/chatbot-kb.sql`, apply that reviewed function deliberately on the VPS, and
rerun the full fixture plus the HNSW query-plan verification.

- [ ] **Step 5: Write the evaluation report**

Create `docs/migration/RETRIEVAL-EVAL-2026-07-29.md` with:

```markdown
# Retrieval evaluation — 2026-07-29

## Corpus and index state
## Fixture coverage
## Per-case results
## Exact-reference results
## Bible-cap results
## Clarification and gap results
## Citation resolution
## Tuning performed
## Remaining failures
## Phase 1 decision
```

Use actual counts, ranks, scores and commands. Do not write “all good” without the
per-case table.

- [ ] **Step 6: Record measured constants in the product spec**

Update the retrieval section of
`docs/superpowers/specs/2026-07-27-ai-chatbot-design.md` with:

- the landed `MIN_SCORE`;
- landed per-kind caps;
- whether exact rows must be prepended outside `match_corpus()`;
- real-corpus HNSW plan result;
- recall pass count and known failures;
- the guided-clarification evidence boundary.

- [ ] **Step 7: Run final verification**

Run:

```bash
python -m pytest \
  tests/test_preembed_kb_questions.py \
  tests/test_kb_retrieval_eval.py \
  tests/test_kb_retrieval.py \
  tests/test_kb_urls_resolve.py -q
node --test tests/*.mjs
node scripts/mirror-agents-md.mjs --check
git diff --check
```

Report skips separately from passes. Do not claim Task 10 or Phase 1 complete while
any required live case is skipped.

- [ ] **Step 8: Commit measured results**

Stage only files actually changed by evidence:

```bash
git add \
  docs/migration/RETRIEVAL-EVAL-2026-07-29.md \
  docs/superpowers/specs/2026-07-27-ai-chatbot-design.md
git add supabase/chatbot-kb.sql  # only when SQL was actually tuned
git commit -m "test(chatbot): record full-corpus retrieval gate"
```

Do not add the embedded-vector file unless the repository owner explicitly chooses
to version it after reviewing its size and reproducibility.

---

## Plan Self-Review Checklist

- Spec coverage: rank 1 exact refs, top 3 natural primaries, source caps,
  citation integrity, ambiguity, follow-up and gap paths are each implemented by
  a named task.
- Credential boundary: fixture authoring is local; embedding stays with Hein;
  retrieval uses only `kb_reader` through the restricted tunnel.
- Type consistency: fixture uses `q`, optional `semantic_q`, `embedding`,
  `semantic_embedding`, `primary`, `support`, `forbid_top`, and
  `expected_decision` consistently across pre-embedding, evaluator and live tests.
- Scope: final answer generation, chat UI and Task 9 video ingest are excluded.
- No fixture rank is broadened as a tuning shortcut.
- Unrelated dirty worktree files remain unstaged.
