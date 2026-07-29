# Chatbot Retrieval Quality Design

## Purpose

Task 10 is the Phase 1 gate for deciding whether the chatbot can retrieve the
right Analyzing Islam material before an answer model or chat UI is built. The
gate must measure ranking quality, source-kind caps, citation integrity and
reference ambiguity. Mere presence anywhere in a twenty-result list is not
enough.

The fixture and evaluator are credential-free to author. Running the live recall
cases requires a scoped database reader and access to the embed endpoint.

## Decisions

### Rank requirements

- A recognized exact reference must be rank 1.
- The primary expected document for a natural-language question must be in the
  top 3.
- Supporting kinds, categories and documents may occur elsewhere in the capped
  result set unless a case sets a tighter bound.
- Assertions encode product requirements. They are not weakened merely to make
  the current retriever pass.

### Reference handling

The eventual chatbot uses an exact-first, guided-clarification policy:

1. If a supplied reference exists and its accompanying description agrees with
   that passage, answer from the exact passage.
2. If the supplied reference exists but its description points to different
   material, do not silently choose either meaning. Show the supplied passage and
   likely corpus-backed candidates, explain that the edition or numbering may
   differ, and ask which passage the user means.
3. If the supplied reference is unknown, ask for the source collection and a
   phrase, quotation or topic. Do not substitute a semantic near-match as though
   it were the requested reference.
4. After the user supplies that context, use it to find the matching reference
   in the editions indexed by Analyzing Islam. The intended passage must then
   appear in the top 3.

All suggested candidates must exist in the corpus and carry a site URL that
resolves to the cited source.

Task 10 does not generate final prose or call an answer model. It proves that the
retrieval layer supplies enough trustworthy evidence for the later `ask` function
to make these decisions. The `ask` function remains responsible for detecting the
conversation state, asking the clarification question and withholding a
substantive answer until the ambiguity is resolved.

## Fixture model

`tests/fixtures/retrieval_questions.json` is a reviewed product fixture, not
generated test data. Every case has:

- `id`: stable diagnostic identifier.
- `mode`: `natural`, `exact_match`, `reference_conflict`,
  `unknown_reference`, or `clarifying_follow_up`.
- `q`: the original user wording.
- `semantic_q`: optional description-only wording used to test likely candidates
  without allowing the supplied wrong reference to dominate ranking.
- `primary`: one corpus identity expressed as `ref` or `slug`, plus `max_rank`;
  required for every mode except a genuine `gap`.
- `support`: optional expected kinds, categories, references or slugs.
- `forbid_top`: optional kinds, references or slugs that must not appear within
  a stated rank window.
- `expected_decision`: `answer`, `clarify`, or `gap`.
- `note`: why the case exists and what failure would mean.

For `reference_conflict`, the fixture identifies both the exact supplied passage
and the likely intended candidate. The evaluator must establish that they are
different and that both have valid citations. It does not pretend that retrieval
alone has learned the user's intent.

For `unknown_reference`, the test asserts that exact lookup finds nothing and the
decision is `clarify`; semantic results may be retained as candidates but cannot
be treated as the requested passage. A genuinely uncovered topic uses `gap`
instead and has no `primary` because no correct corpus identity exists.

## Coverage

The first fixture should be small enough to review manually and broad enough to
expose corpus-shape failures. It includes:

- exact Quran, hadith and Bible references;
- paraphrased thematic questions targeting entries and dossiers;
- the three doctrine documents already proven by the smoke test;
- questions for which a Bible verse is the correct primary result;
- questions for which Bible verses are plausible but wrong primary results,
  exercising the `verse: 4` cap against a corpus that is roughly 80% Bible;
- a long-dossier question whose answer occurs outside the opening chunk;
- reference-description conflicts;
- unknown references followed by context-bearing clarification turns;
- an out-of-corpus topic that must take the gap path;
- citation checks for every expected or suggested result.

Question wording should resemble ordinary users rather than catalog titles.
Fixture authors verify every expected reference, slug, category and URL directly
against the parsed source before committing it.

## Evaluator

`tests/test_kb_retrieval.py` remains an integration test over the loaded corpus.
It embeds each query, calls `match_corpus()` and records ordered rows. Exact lookup
cases also call `kb_find_ref()`.

The evaluator:

1. validates the fixture schema before any network or database work;
2. reports ordered rank, score, kind, reference, slug and URL on failure;
3. applies the per-case primary rank bound;
4. checks supporting and forbidden expectations;
5. enforces exact-reference rank 1 independently of semantic retrieval;
6. validates that expected and suggested citations resolve to their source
   locations;
7. distinguishes `clarify` from `gap` rather than treating both as an empty result;
8. skips only the live integration cases when required environment variables are
   absent; fixture-schema tests still run locally.

Scores are diagnostic, not a frozen product contract. A minimum-score threshold
may be tuned against the full corpus, but rank and decision expectations remain
the fixture's stable requirements.

## Failure handling and tuning

Failures are diagnosed before SQL changes:

- exact reference below rank 1 indicates that the exact lookup path is not being
  prepended correctly;
- a primary result below rank 3 indicates ranking failure;
- too many Bible verses ahead of an entry, dossier or doctrine result indicates
  cap or fusion failure;
- missing dossier tail material points first to chunk candidate over-fetch or
  chunk recall;
- a broken citation is a hard failure even when ranking is correct;
- a conflict case that becomes an automatic answer indicates an unsafe
  conversation-policy implementation;
- an unknown reference that becomes a gap despite useful context indicates that
  clarification and corpus absence have been conflated.

Tune retrieval against the diagnosed cause, never by broadening an expected rank
or replacing a difficult question with catalog wording.

## Acceptance

Task 10 is ready for the full-corpus run when:

- fixture-schema tests pass without credentials;
- every expected identity has been manually verified in local source material;
- live tests require exact references at rank 1 and natural-language primaries in
  the top 3;
- the fixture contains both correct-verse and wrong-verse-cap cases;
- conflict, unknown-reference, clarification-follow-up and genuine-gap behavior
  are distinct;
- every expected and suggested citation resolves;
- failure output is sufficient to tune SQL without inspecting test internals.

The full-corpus results determine whether Phase 1 exits, retrieval is tuned, or the
chatbot remains blocked. They do not get converted to green by weakening the
fixture.
