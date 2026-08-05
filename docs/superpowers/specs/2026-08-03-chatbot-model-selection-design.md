# Chatbot model selection design

Date: 2026-08-03
Status: approved design; implementation plan not yet written

## 1. Decision summary

Use Claude Sonnet 5 as the selected launch model, subject to passing the citation,
quality and refusal gates in this specification. Validate that choice through a
blinded, three-model bake-off using real Analyzing Islam retrieval results. The
comparison set is:

- Claude Sonnet 5;
- GPT-5.6 Terra;
- Gemini 3.1 Pro.

Claude Sonnet 5 is preferred because its native document citations align closely
with the product's grounding and source-preview design. GPT-5.6 Terra and Gemini
3.1 Pro are evaluation baselines, not co-equal production integrations. Replace
Sonnet only if it fails a hard gate or another candidate demonstrates a material,
repeatable quality advantage.

Launch with Sonnet 5 as the single active model and no automatic routing. Keep the
server contract provider-neutral so a future model change does not require a
frontend rebuild, but implement only the Sonnet production adapter in this phase.
Reconsider other production adapters and routing only when evaluation or production
volume justifies the added complexity.

## 2. Priorities and constraints

The selection is quality-first within a controlled budget. Cost breaks close
quality ties; it never compensates for unreliable grounding.

Sonnet 5 must:

- make no fabricated scriptural or corpus references in the launch audit;
- ground claims about supplied texts in valid citations;
- synthesize several retrieved sources without blurring source claims and the
  model's own reasoning;
- follow the product's narrow-claim rule;
- refuse or use the corpus-gap path appropriately;
- handle legitimate religious criticism without materially excessive refusals;
- stream reliably with acceptable latency;
- remain viable under the approved cost controls.

No candidate may use live web search. All candidates receive context from the
existing `match_corpus()` retrieval pipeline. Query and document embeddings remain
on the deployed `gte-small` pipeline.

## 3. Bake-off protocol

### 3.1 Test set

Evaluate 40–60 representative questions. Include:

- exact Quran and Bible references;
- thematic synthesis across multiple sources;
- Christian doctrine;
- the Islamic Dilemma;
- method-consistency and asymmetric-standards arguments;
- weak retrieval and genuine corpus gaps;
- Al-Zutt and other topics the corpus should decline to resolve confidently;
- adversarial prompts likely to induce fabricated references or inappropriate
  refusals;
- multi-turn follow-ups that require conversation context.

Use existing Task 10 questions where appropriate, but do not describe Task 10 as
passed. Its live retrieval-quality gate remains deferred until the protected
fixture, SSH tunnel and `kb_reader` credential are available or the equivalent
owner-only production evaluation is completed.

### 3.2 Controlled inputs

Each model receives:

- the same user question and conversation history;
- the same retrieved document set in the same order;
- equivalent system rules and answer-length target;
- the same citation-validation requirements;
- comparable reasoning effort as far as provider controls permit;
- no provider-specific retrieval or web-grounding tool.

Record the exact model snapshot, provider settings, retrieved document IDs, token
usage, latency and estimated cost for every run. Use pinned snapshots for the final
comparison when providers expose them.

### 3.3 Blinded review

Remove provider and model identifiers before human scoring. Score each answer using
this rubric:

| Criterion | Weight |
|---|---:|
| Citation and grounding integrity | 35% |
| Factual and theological accuracy | 20% |
| Reasoning and synthesis | 15% |
| Narrow-claim compliance | 10% |
| Appropriate refusals and gap handling | 10% |
| Clarity and tone | 5% |
| Latency and cost | 5% |

Citation integrity is also a hard gate. Any fabricated reference, citation to a
document that was not supplied, or citation location that does not resolve is a
critical failure. A model with a critical failure cannot be selected from the
initial bake-off without remediation followed by a complete rerun of the affected
evaluation set.

Sonnet remains selected when the candidates have materially equivalent quality.
Cost alone does not displace it. Select another candidate only when Sonnet fails a
hard gate or the alternative shows a material, repeatable quality advantage large
enough to justify its different citation behavior and integration cost.

## 4. Provider-neutral model boundary

The `ask` Edge Function owns model access. Browser code never receives provider
credentials and does not make provider API calls.

Define a small provider adapter boundary. The production Sonnet adapter and the
evaluation-only candidate clients accept the same normalized request:

- system instructions;
- conversation messages;
- retrieved documents with stable IDs, titles, references, locations and bodies;
- reasoning and output limits;
- stream cancellation signal.

The production adapter emits this normalized stream:

- answer-text deltas;
- citation events containing a document ID and source location;
- cited-document metadata needed by the source preview;
- terminal completion, refusal or error status;
- provider token usage and calculated cost.

Claude's production adapter translates native citation objects into the normalized
citation format. The bake-off may use evaluation-only OpenAI and Gemini clients that
produce equivalent stored evaluation records; they do not need production retry,
streaming or deployment integration. Any candidate chosen to replace Sonnet must
first receive a production adapter and pass the same server-side validation and
integration tests. Provider-specific response objects must not leak into stored chat
messages or the browser protocol.

The adapter boundary exists to keep the Sonnet integration replaceable. It must not
grow into a general multi-provider orchestration system in this phase.

## 5. Citation validation

Validate every citation before persistence and rendering:

1. The cited document ID must be in the document set supplied to the model.
2. The cited location must resolve within that document's supplied content.
3. The cited text, when the provider returns it, must match the resolved source
   location after documented normalization.
4. The source URL and deep-link target must be generated from trusted corpus
   metadata, never copied from model-generated text.

Reject invalid citation events. If rejecting them leaves a textual claim presented
as sourced but unsupported, fail the answer rather than displaying a superficially
polished response. Record the validation failure for review without logging secrets
or unnecessary private conversation content.

## 6. Configuration

Store production model settings in the protected server-side chat configuration:

- active provider, initially Anthropic;
- pinned model identifier;
- reasoning level;
- maximum input and output tokens;
- timeout and bounded retry policy;
- input, cached-input and output prices;
- monthly application budget;
- daily user quota;
- emergency kill switch.

Changing the active Sonnet snapshot or reasoning level is an administrator
operation and does not require a frontend deployment. Activating another provider
requires its production adapter and tests to be deployed first. Configuration must
reject an unsupported provider/model pair instead of silently falling back.

## 7. Cost model and controls

For planning, use a representative turn of 8,000 input tokens and 1,200 output
tokens. These are assumptions to be replaced with measured owner-testing data.
Reasoning-token treatment differs by provider, so record billed usage rather than
inferring it from visible output.

At Claude Sonnet 5's post-introductory list price of $3 per million input tokens and
$15 per million output tokens, the representative turn is approximately $0.042.
This implies generation costs of approximately:

| Questions per month | Estimated generation cost |
|---:|---:|
| 500 | $21 |
| 1,000 | $42 |
| 2,500 | $105 |
| 5,000 | $210 |
| 10,000 | $420 |

These estimates exclude existing infrastructure cost and may move with conversation
length, reasoning usage, caching and provider price changes.

The owner-only launch uses:

- a $100 monthly application ceiling;
- a separate provider-console spending limit;
- a configurable daily message limit;
- an emergency kill switch;
- a pre-request budget reservation and post-response reconciliation using actual
  billed tokens.

The server blocks a request before provider invocation when its reservation would
exceed the ceiling. Reconcile successful, refused, interrupted and provider-error
responses according to actual reported usage so the budget ledger does not drift.

## 8. Rollout and growth policy

Start with owner-only access and Sonnet 5 as the single active model. Public access
remains disabled until the owner explicitly approves it.

After approximately 100–200 representative owner questions, review:

- grounding and citation failures;
- factual and theological corrections;
- inappropriate refusals;
- corpus-gap frequency;
- average and high-percentile latency;
- average input, output and reasoning-token usage;
- average and high-percentile cost per turn.

Use these volume checkpoints:

- Below 2,500 questions per month: retain the quality-first single model.
- Around 2,500–5,000: first optimize caching, retrieved-context size, conversation
  compaction and quotas.
- Above 5,000: evaluate a cheaper default or selective routing using production
  evidence and a new approved design.

These are review triggers, not automatic configuration changes. Any citation-
integrity regression can disable a model regardless of traffic or price.

## 9. Failures and fallback behavior

Provider failures receive at most one bounded retry when the error is retryable and
the response has not started streaming to the user. Do not silently switch providers
mid-answer or automatically send private conversation content to a second provider.

On failure:

- preserve a partial streamed answer only when it is clearly marked incomplete and
  its citations have passed validation;
- return a clear temporary-unavailability message;
- avoid charging the user's daily message quota where the server can determine that
  no useful answer was delivered;
- reconcile any provider cost already incurred;
- record operational diagnostics without secrets.

Refusals, empty content and provider stop reasons are terminal states that adapters
must normalize explicitly. Callers must inspect the terminal state before assuming
answer text exists.

## 10. Current pricing references

Pricing must be rechecked immediately before the bake-off and again before public
launch.

- Anthropic, "Introducing Claude Sonnet 5," 2026-06-30:
  https://www.anthropic.com/news/claude-sonnet-5
- Anthropic, "Citations":
  https://docs.anthropic.com/en/docs/build-with-claude/citations
- OpenAI, model comparison:
  https://developers.openai.com/api/docs/models/compare
- Google, Gemini Developer API pricing:
  https://ai.google.dev/gemini-api/docs/pricing

## 11. Superseded model decision

This specification confirms the earlier design's Sonnet 5 selection, adds a
comparative validation gate, and supersedes its $50 monthly ceiling. It does not
supersede the earlier product goals, citation UX, retrieval architecture, owner-only
authorization requirement or public-launch gate.
