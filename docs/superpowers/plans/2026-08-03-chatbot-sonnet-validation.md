# Chatbot Sonnet Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate Claude Sonnet 5 against two current baselines, then build the tested Sonnet-only model, citation, and cost-control boundary needed by the owner-only chatbot backend.

**Architecture:** A credential-free Python evaluation core owns fixtures, anonymization, scoring, and reports; thin provider clients perform paid calls only from an explicitly authorized machine. The production Deno Edge Function uses one Sonnet adapter behind normalized request/event types, validates every citation against retrieved documents, and reserves then reconciles budget in Postgres. The browser UI and video ingest are separate later plans.

**Tech Stack:** Python 3.12, pytest, Deno/TypeScript, Node's built-in test runner, PostgreSQL/Supabase SQL, Anthropic Messages API with citations, existing `gte-small` embeddings and `match_corpus()` retrieval.

## Global Constraints

- Start execution only after `feature/chatbot-retrieval-quality` is merged or after the owner explicitly designates that branch as the implementation base; do not duplicate or discard its 16 commits.
- Use Claude Sonnet 5 as the selected launch model; GPT-5.6 Terra and Gemini 3.1 Pro are evaluation baselines only.
- No live web search.
- Public access remains disabled until the owner explicitly approves it.
- The `ask` Edge Function is the trust boundary; never expose provider or Supabase service-role credentials to browser code.
- Enforce the single owner email server-side for the first deployment.
- Use the deployed `gte-small` pipeline for query embeddings and `match_corpus()` for ranking.
- Treat any fabricated or unresolvable corpus reference as a hard-gate failure.
- Launch with a $100 monthly application ceiling, a separate provider-console limit, daily quota, and emergency kill switch.
- Do not silently switch providers or forward a conversation to a second provider after a failure.
- Do not replay all `supabase/*.sql`; apply each reviewed schema deliberately.
- Preserve unrelated dirty files and untracked handoffs in the primary checkout.

---

## File map

| File | Responsibility |
|---|---|
| `chatbot_model_eval.py` | Pure fixture validation, anonymization, rubric aggregation, hard-gate selection decision |
| `chatbot_model_providers.py` | Evaluation-only HTTP clients and normalized recorded responses |
| `run-chatbot-model-eval.py` | Explicit paid-run CLI; reads secrets from environment and writes raw local results |
| `tests/fixtures/chatbot_model_questions.json` | Reviewed 40–60-question answer-quality fixture |
| `tests/test_chatbot_model_eval.py` | Credential-free evaluation-core tests |
| `tests/test_chatbot_model_providers.py` | Mocked provider-contract and secret-boundary tests |
| `docs/migration/CHATBOT-MODEL-EVAL-2026-08-03.md` | Measured blinded result and launch gate |
| `supabase/chatbot-chat.sql` | Chat tables, RLS, configuration, budget reservation/reconciliation RPCs |
| `supabase/functions/ask/types.ts` | Provider-neutral request, document, event, usage, and terminal-state types |
| `supabase/functions/ask/citations.ts` | Trusted citation resolution and rejection |
| `supabase/functions/ask/citations_test.ts` | Executable citation validator tests |
| `supabase/functions/ask/sonnet.ts` | Sonnet 5 Messages API streaming adapter |
| `supabase/functions/ask/sonnet_test.ts` | Mocked Sonnet stream and failure tests |
| `supabase/functions/ask/index.ts` | JWT/owner gate, retrieval orchestration, budget lifecycle, normalized SSE |
| `supabase/functions/ask/index_test.ts` | Owner authorization and orchestration tests |
| `tests/test_chatbot_chat_sql.py` | Static SQL security and contract tests; live SQL checks are explicitly gated |
| `tests/test_ask_function.mjs` | Deno module contract, auth boundary, citation, streaming, and error-path tests |

---

### Task 1: Build the credential-free evaluation contract

**Files:**
- Create: `chatbot_model_eval.py`
- Create: `tests/test_chatbot_model_eval.py`

**Interfaces:**
- Produces: `validate_questions(payload: object) -> list[dict]`
- Produces: `validate_result(result: dict, question_ids: set[str]) -> dict`
- Produces: `anonymize(results: list[dict], seed: str) -> tuple[list[dict], dict[str, str]]`
- Produces: `aggregate(scores: list[dict], identities: dict[str, str]) -> dict`
- Produces: `select_model(summary: dict, preferred: str = "claude-sonnet-5") -> dict`

- [ ] **Step 1: Write failing schema and hard-gate tests**

```python
def test_fabricated_reference_blocks_selection():
    summary = {
        "claude-sonnet-5": {"weighted": 91.0, "critical_failures": 1},
        "gpt-5.6-terra": {"weighted": 88.0, "critical_failures": 0},
    }
    assert evaluate.select_model(summary)["selected"] == "gpt-5.6-terra"


def test_preferred_model_wins_materially_equivalent_scores():
    summary = {
        "claude-sonnet-5": {"weighted": 91.0, "critical_failures": 0},
        "gpt-5.6-terra": {"weighted": 92.0, "critical_failures": 0},
    }
    assert evaluate.select_model(summary)["selected"] == "claude-sonnet-5"
```

Define a material advantage as at least 5.0 weighted points and require zero critical failures for any selectable model.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m pytest tests/test_chatbot_model_eval.py -q`

Expected: FAIL because `chatbot_model_eval` does not exist.

- [ ] **Step 3: Implement exact fixture and result contracts**

Each question requires `id`, `category`, `messages`, `expected_behavior`, `required_sources`, `forbidden_claims`, and `review_note`. Allow only these behaviors: `answer`, `clarify`, `gap`, `refuse`. Each recorded model result requires `question_id`, `provider`, `model`, `snapshot`, `answer`, `citations`, `terminal_state`, `usage`, `latency_ms`, and `cost_usd`.

Use these rubric weights exactly:

```python
WEIGHTS = {
    "citation_grounding": 0.35,
    "factual_theological_accuracy": 0.20,
    "reasoning_synthesis": 0.15,
    "narrow_claim_compliance": 0.10,
    "refusal_gap_handling": 0.10,
    "clarity_tone": 0.05,
    "latency_cost": 0.05,
}
MATERIAL_ADVANTAGE = 5.0
```

Anonymization must replace provider/model with stable labels such as `model-a` and return the private label map separately. It must not alter answer or citation content.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m pytest tests/test_chatbot_model_eval.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the evaluation core**

```powershell
git add chatbot_model_eval.py tests/test_chatbot_model_eval.py
git commit -m "test(chatbot): add blinded model evaluation core"
```

---

### Task 2: Author the reviewed answer-quality fixture

**Files:**
- Create: `tests/fixtures/chatbot_model_questions.json`
- Modify: `tests/test_chatbot_model_eval.py`

**Interfaces:**
- Consumes: stable document identities from `tests/fixtures/retrieval_questions.json` after the retrieval-quality branch lands.
- Produces: 40–60 valid questions spanning all required product behaviors.

- [ ] **Step 1: Add the failing coverage test**

```python
def test_real_fixture_has_required_coverage():
    cases = evaluate.validate_questions(json.loads(FIXTURE.read_text("utf-8")))
    assert 40 <= len(cases) <= 60
    categories = {case["category"] for case in cases}
    assert {
        "exact-reference", "thematic", "christian-doctrine",
        "islamic-dilemma", "method-consistency", "weak-retrieval",
        "corpus-gap", "adversarial", "multi-turn",
    } <= categories
    behaviors = {case["expected_behavior"] for case in cases}
    assert {"answer", "clarify", "gap", "refuse"} <= behaviors
```

- [ ] **Step 2: Run the coverage test and verify RED**

Run: `python -m pytest tests/test_chatbot_model_eval.py::test_real_fixture_has_required_coverage -q`

Expected: FAIL because the fixture does not exist.

- [ ] **Step 3: Create 45 reviewed cases**

Seed the fixture with the 15 retrieval questions, then add 30 answer-quality variants. Include Quran 9:5, Quran 2:256, John 14:17, the Trinity, the Injeel, eternal generation, crucifixion denial, Aisha's age, Quran 4:34, Paul-as-corrupter, manuscript variants, Uthmanic standardization, Gospel dating versus hadith dating, Muhammad-in-the-Bible claims, five multi-turn follow-ups, five prompt-injection/reference-invention attacks, and Al-Zutt as a gap.

For every case, list only source IDs verified in the local corpus. `forbidden_claims` must contain concrete assertions whose appearance is a failure, for example `"Musnad Ahmad is one of the six canonical hadith collections"` for Al-Zutt.

- [ ] **Step 4: Add source-identity verification**

Load the local corpus through the same collectors used by `build-kb.py`. Assert every `required_sources` ID resolves exactly once and every internal URL resolves using `citation_path()` from `kb_retrieval_eval.py`. Preserve its explicit unresolved-doctrine exception until doctrine pages exist.

- [ ] **Step 5: Run fixture tests and dry-run parsing**

Run:

```powershell
python build-kb.py --dry-run
python -m pytest tests/test_chatbot_model_eval.py tests/test_kb_retrieval_eval.py tests/test_kb_urls_resolve.py -q
```

Expected: dry run reports 39,106 documents and 43,016 chunks; tests PASS. If current verified counts differ, stop and diagnose rather than rewriting fixture expectations.

- [ ] **Step 6: Commit the reviewed fixture**

```powershell
git add tests/fixtures/chatbot_model_questions.json tests/test_chatbot_model_eval.py
git commit -m "test(chatbot): add answer quality fixture"
```

---

### Task 3: Add evaluation-only provider clients and paid runner

**Files:**
- Create: `chatbot_model_providers.py`
- Create: `run-chatbot-model-eval.py`
- Create: `tests/test_chatbot_model_providers.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `run_candidate(candidate: Candidate, case: dict, documents: list[dict], post: Callable) -> dict`
- Produces: immutable `Candidate(provider, model, snapshot, input_per_million, output_per_million)`.
- Reads only: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.
- Writes only: `.chatbot-model-eval/raw-results.jsonl` and `.chatbot-model-eval/label-map.json`.

- [ ] **Step 1: Write mocked HTTP contract tests**

```python
def test_cost_uses_reported_input_and_output_tokens():
    candidate = Candidate("anthropic", "claude-sonnet-5", "pinned", 3.0, 15.0)
    usage = {"input_tokens": 8000, "output_tokens": 1200}
    assert calculate_cost(candidate, usage) == pytest.approx(0.042)


def test_result_never_contains_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-sentinel")
    result = run_candidate(CLAUDE, CASE, DOCS, post=fake_anthropic_response)
    assert "secret-sentinel" not in json.dumps(result)
```

Also test refusal, empty content, timeout, 429/529 retry once, non-retryable 400, and citation normalization.

- [ ] **Step 2: Run provider tests and verify RED**

Run: `python -m pytest tests/test_chatbot_model_providers.py -q`

Expected: FAIL because the provider module does not exist.

- [ ] **Step 3: Implement thin evaluation clients**

Send identical retrieved documents and system rules to all candidates. Use provider-native citations for Sonnet. Require OpenAI and Gemini to return source IDs in a minimal JSON citation envelope, then validate those IDs locally; do not claim equivalence with Anthropic native citations.

The runner must require `--ack-paid-run`, accept `--candidate` one or more times, refuse to start when any requested key is missing, and print the candidate name plus completed-case count without printing prompts, answers, headers, or secrets.

- [ ] **Step 4: Ignore raw evaluation artifacts**

Add exactly this line to `.gitignore`:

```gitignore
.chatbot-model-eval/
```

- [ ] **Step 5: Run all credential-free model tests**

Run: `python -m pytest tests/test_chatbot_model_eval.py tests/test_chatbot_model_providers.py -q`

Expected: PASS without network or API keys.

- [ ] **Step 6: Commit the clients and runner**

```powershell
git add .gitignore chatbot_model_providers.py run-chatbot-model-eval.py tests/test_chatbot_model_providers.py
git commit -m "feat(chatbot): add model comparison runner"
```

---

### Task 4: Run the blinded bake-off and record the gate

**Files:**
- Create: `docs/migration/CHATBOT-MODEL-EVAL-2026-08-03.md`
- Do not commit: `.chatbot-model-eval/*`

**Interfaces:**
- Consumes: retrieved document bundles produced against production corpus through the restricted `kb_reader` path.
- Produces: anonymized answer packet, completed human scores, aggregate decision, actual token/cost evidence.

- [ ] **Step 1: Recheck provider names and prices**

Use official provider documentation on the execution date. Update only the `Candidate` constants and design pricing references if names or prices changed. Record the access date in the report.

- [ ] **Step 2: Generate the frozen retrieval bundles**

On Hein's authorized machine, use the protected embedding endpoint and restricted tunnel. Save the exact top results used for each question under `.chatbot-model-eval/`. Do not include service-role credentials, database URLs, or `kb_reader` passwords.

- [ ] **Step 3: Run all three candidates**

```powershell
python run-chatbot-model-eval.py --ack-paid-run --candidate claude-sonnet-5 --candidate gpt-5.6-terra --candidate gemini-3.1-pro
```

Expected: one valid result per candidate per fixture case; failures are recorded as terminal states rather than silently omitted.

- [ ] **Step 4: Blind and score the packet**

Run the anonymizer with a fixed recorded seed. Score every answer from 0–5 on each rubric criterion. Record fabricated references separately as critical failures. Reveal the label map only after all scoring is complete.

- [ ] **Step 5: Write the measured report**

The report must contain candidate snapshots, settings, question count, per-category scores, critical failures, refusal counts, median and p95 latency, total and mean cost, scorer identity, exceptions, and the selection decision. Sonnet passes when it has zero critical failures and no alternative beats it by at least 5.0 weighted points without a critical failure.

- [ ] **Step 6: Commit only the report**

```powershell
git add docs/migration/CHATBOT-MODEL-EVAL-2026-08-03.md
git commit -m "test(chatbot): record Sonnet model gate"
```

Stop here if Sonnet fails. Revise the approved design before building another production adapter.

---

### Task 5: Add chat persistence and atomic cost controls

**Files:**
- Create: `supabase/chatbot-chat.sql`
- Create: `tests/test_chatbot_chat_sql.py`

**Interfaces:**
- Produces tables: `chat_conversations`, `chat_messages`, `chat_usage`, `chat_config`, `chat_turns`.
- Produces RPC: `chat_begin_turn(p_estimated_cents integer) -> table(turn_id uuid, status text)`.
- Produces RPC: `chat_end_turn(p_turn_id uuid, p_actual_cents integer, p_input_tokens bigint, p_output_tokens bigint, p_status text) -> void`.

- [ ] **Step 1: Write failing static security tests**

Assert the SQL contains RLS on conversation/message tables, owner-scoped policies, a singleton configuration row with `budget_cents = 10000`, `enabled = false`, `FOR UPDATE` inside `chat_begin_turn`, grants only to `authenticated`, and no corpus/demo seed data.

- [ ] **Step 2: Run static tests and verify RED**

Run: `python -m pytest tests/test_chatbot_chat_sql.py -q`

Expected: FAIL because the schema file does not exist.

- [ ] **Step 3: Implement schema and RPCs**

`chat_begin_turn` must authenticate with `auth.uid()`, roll the month when `month_key` changes, lock the singleton config row, reject disabled/budget/quota states before creating a reserved turn, and atomically reserve estimated cents. `chat_end_turn` must lock the turn, be idempotent, replace the reservation with actual cost, store provider usage, and never permit a caller to reconcile another user's turn.

Do not put the owner email in public SQL. The Edge Function reads `CHAT_OWNER_EMAIL` from its server environment.

- [ ] **Step 4: Add gated live SQL tests**

Use a test transaction against a deliberately selected non-production database. Verify concurrent reservations cannot cross the cap, month rollover, daily quota, double reconciliation, foreign-user rejection, and kill switch. Skip unless `CHATBOT_TEST_DB_URL` is present; never accept `SUPABASE_DB_URL` as a fallback.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_chatbot_chat_sql.py -q`

Expected without the explicit test database: static tests PASS and live tests SKIP with a clear reason.

- [ ] **Step 6: Commit the schema**

```powershell
git add supabase/chatbot-chat.sql tests/test_chatbot_chat_sql.py
git commit -m "feat(chatbot): add atomic chat budget controls"
```

---

### Task 6: Implement normalized types and citation validation

**Files:**
- Create: `supabase/functions/ask/types.ts`
- Create: `supabase/functions/ask/citations.ts`
- Create: `supabase/functions/ask/citations_test.ts`
- Create: `tests/test_ask_function.mjs`

**Interfaces:**
- Produces: `RetrievedDocument`, `ModelRequest`, `CitationEvent`, `Usage`, `TerminalState`, `ModelEvent`.
- Produces: `validateCitation(citation: CitationEvent, docs: RetrievedDocument[]): CitationEvent`.
- Produces: `trustedSource(doc: RetrievedDocument): {title: string; ref: string | null; url: string}`.

- [ ] **Step 1: Write failing Deno citation tests**

Test valid document/block citation, unknown document ID, negative/out-of-range block, mismatched cited text, and model-supplied URL replacement. The expected validator error code is `invalid_citation`; never render an invalid citation after dropping only its marker.

- [ ] **Step 2: Run and verify RED**

Run: `deno test supabase/functions/ask/citations_test.ts`

Expected: FAIL because modules do not exist. If Deno is unavailable, use the repository's Edge Runtime container only after obtaining approval; do not replace this with a text-presence test.

- [ ] **Step 3: Implement focused types and validator**

Represent locations as `{type: "content_block"; start: number; end: number}`. Resolve IDs only from the supplied document array. Normalize CRLF to LF for cited-text comparison, but do not lowercase or collapse meaningful whitespace. Build title/ref/URL only from the matched trusted document.

- [ ] **Step 4: Run Deno tests and Node repository tests**

```powershell
deno test supabase/functions/ask/citations_test.ts
node --test tests/*.mjs
```

Expected: PASS.

- [ ] **Step 5: Commit citation primitives**

```powershell
git add supabase/functions/ask/types.ts supabase/functions/ask/citations.ts supabase/functions/ask/citations_test.ts tests/test_ask_function.mjs
git commit -m "feat(chatbot): add trusted citation validation"
```

---

### Task 7: Implement the Sonnet 5 streaming adapter

**Files:**
- Create: `supabase/functions/ask/sonnet.ts`
- Create: `supabase/functions/ask/sonnet_test.ts`

**Interfaces:**
- Consumes: `ModelRequest` from `types.ts`.
- Produces: `streamSonnet(request: ModelRequest, options: SonnetOptions): AsyncGenerator<ModelEvent>`.
- Reads: `ANTHROPIC_API_KEY`; receives pinned model, effort, timeout and injectable `fetch` through `SonnetOptions`.

- [ ] **Step 1: Write failing stream-contract tests**

Use mocked Anthropic SSE frames to test text deltas, `citations_delta`, usage, normal completion, refusal before content access, empty content, malformed event, abort, 429/529 retry before streaming, and no retry after the first emitted answer event.

- [ ] **Step 2: Run and verify RED**

Run: `deno test supabase/functions/ask/sonnet_test.ts`

Expected: FAIL because `sonnet.ts` does not exist.

- [ ] **Step 3: Implement the Messages API request**

Send each retrieved source as a custom-content document with citations enabled. Include stable document IDs in document context, use the configured pinned Sonnet 5 identifier, request streaming, and translate provider events into `ModelEvent`. Never combine native citations with structured-output response formatting.

- [ ] **Step 4: Validate citations before yielding them**

Pass every translated citation through `validateCitation()`. On failure yield terminal state `{kind: "error", code: "invalid_citation"}` and stop without presenting the unsupported answer as complete.

- [ ] **Step 5: Run adapter tests**

Run: `deno test supabase/functions/ask/sonnet_test.ts supabase/functions/ask/citations_test.ts`

Expected: PASS without network or an API key.

- [ ] **Step 6: Commit the adapter**

```powershell
git add supabase/functions/ask/sonnet.ts supabase/functions/ask/sonnet_test.ts
git commit -m "feat(chatbot): add Sonnet streaming adapter"
```

---

### Task 8: Build the owner-only `ask` orchestration boundary

**Files:**
- Create: `supabase/functions/ask/index.ts`
- Create: `supabase/functions/ask/index_test.ts`
- Modify: `tests/test_ask_function.mjs`

**Interfaces:**
- Consumes: authenticated request body `{conversation_id: string | null, message: string}`.
- Calls: embed session, `kb_find_ref()`, `match_corpus()`, `chat_begin_turn()`, `streamSonnet()`, `chat_end_turn()`.
- Produces SSE events: `status`, `sources`, `text`, `citation`, `usage`, `done`, `error`.

- [ ] **Step 1: Write failing auth and orchestration tests**

Test POST-only, missing/invalid JWT, authenticated non-owner email, missing owner configuration, disabled chat, quota, budget, retrieval gap, successful stream, invalid citation, provider refusal, dropped stream, and reconciliation after provider cost is incurred. Assert authorization happens before embedding, retrieval, budget reservation, or provider invocation.

- [ ] **Step 2: Run and verify RED**

Run: `deno test supabase/functions/ask/index_test.ts`

Expected: FAIL because `index.ts` does not exist.

- [ ] **Step 3: Implement server-side owner authorization**

Verify the Supabase JWT using the established self-hosted pattern, load the authenticated user, compare its normalized email to `CHAT_OWNER_EMAIL`, and return 403 for every other account. Do not trust a browser-supplied email claim or UI state.

- [ ] **Step 4: Implement retrieval and budget order**

The order is: validate request, authorize owner, reserve budget, embed query, retrieve exact and hybrid results, detect gap/clarification, emit trusted source metadata, call Sonnet, validate streamed citations, persist messages, reconcile actual cost. If work stops after reservation, reconcile the turn with the actual known cost and terminal status.

- [ ] **Step 5: Implement normalized SSE**

Set `Content-Type: text/event-stream`, `Cache-Control: no-cache`, and `X-Content-Type-Options: nosniff`. Encode every event as one JSON object. Never include API keys, service-role credentials, raw provider errors, or provider-specific objects.

- [ ] **Step 6: Run Edge Function tests**

```powershell
deno test supabase/functions/ask/index_test.ts supabase/functions/ask/sonnet_test.ts supabase/functions/ask/citations_test.ts
node --test tests/*.mjs
```

Expected: PASS.

- [ ] **Step 7: Commit the orchestration boundary**

```powershell
git add supabase/functions/ask/index.ts supabase/functions/ask/index_test.ts tests/test_ask_function.mjs
git commit -m "feat(chatbot): add owner-only ask function"
```

---

### Task 9: Verify and hand off the owner-only backend

**Files:**
- Create: `docs/migration/CHATBOT-OWNER-TESTING.md`
- Modify only if behavior changed: `docs/superpowers/specs/2026-08-03-chatbot-model-selection-design.md`

**Interfaces:**
- Produces: deployment checklist, required secret names, rollback steps, owner-test rubric, and measured cost review procedure.

- [ ] **Step 1: Run focused verification**

```powershell
python -m pytest tests/test_chatbot_model_eval.py tests/test_chatbot_model_providers.py tests/test_chatbot_chat_sql.py -q
deno test supabase/functions/ask/
node --test tests/*.mjs
node scripts/mirror-agents-md.mjs --check
git diff --check
```

Expected: all credential-free tests PASS; explicitly gated live tests may SKIP and must be reported separately.

- [ ] **Step 2: Perform targeted secret scan**

Search only changed files for `sk-ant-`, `service_role`, PostgreSQL credential URLs, bearer-token literals, and the actual owner email. Expected: no secret values; identifier names and security documentation are allowed.

- [ ] **Step 3: Write the owner-testing runbook**

Document deliberate application of `supabase/chatbot-chat.sql`, required server secret names, initial `enabled = false`, owner-email verification, provider-console limit, enabling order, a one-question smoke test, cost reconciliation query, kill-switch test, rollback, and the 100–200-question review metrics. Do not include secret values or a production DSN.

- [ ] **Step 4: Deploy only with explicit owner authorization**

Schema application, Edge Function deployment, secret writes, and production enablement are external state changes and require explicit authorization at execution time. Re-query every database write. Keep public access disabled.

- [ ] **Step 5: Commit the runbook**

```powershell
git add docs/migration/CHATBOT-OWNER-TESTING.md
git commit -m "docs(chatbot): add owner testing runbook"
```

---

## Plan self-review

- Spec coverage: candidate evaluation, Sonnet preference, citation hard gate, provider-neutral contract, production Sonnet adapter, configuration, $100 cap, reconciliation, rollout thresholds, refusal/error handling, and no silent failover each map to a task.
- Scope boundary: chat UI, source-preview presentation, admin UI, public launch, and video ingest are explicitly excluded and require later approved plans.
- Credential boundary: all unit tests are offline; paid evaluation and production deployment are explicit gated actions.
- Type consistency: `ModelRequest`, `ModelEvent`, `CitationEvent`, `Usage`, and `TerminalState` originate in Task 6 and are consumed unchanged by Tasks 7–8.
- Retrieval dependency: execution waits for the 16-commit retrieval-quality branch to land or be designated as the base.
- No generated raw answer packet, embedded fixture, secret, DSN, or private conversation is committed.
