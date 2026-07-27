# Analyzing Islam — AI chatbot ("Ask") design

Date: 2026-07-27
Status: approved design, not yet implemented

## 1. Summary

A signed-in-only chatbot on analyzingislam.com that answers questions about Islam
from a philosophical and polemical standpoint, grounded in the site's own corpus:
1,524 catalog entries, 147 dossiers, the Quran, the vetted video library, and a new
authored Christian-doctrine reference layer.

It answers in prose first and links second. Every claim about what a text says
resolves to a source on the site, with the reference shown. Reasoning, historical
context and argument construction are the model's own. When the corpus does not
cover a question, it says so plainly, summarises the nearest material anyway, and
offers a route to suggest the topic as a new entry.

Each signed-in user gets private, resumable conversation history.

## 2. Goals and non-goals

### Goals

- Give direct, substantive answers — not a list of entries to go read.
- Never fabricate a scriptural reference. This is the one failure that would
  discredit the whole project, since the site's entire value proposition is
  verifiable sourcing from Muslim-approved editions.
- Answer thematic apologetics questions ("Was Jesus a Muslim?", "Is Allah a
  father?") that no single entry addresses, by synthesising across the corpus.
- Answer basic Christian theology accurately for Muslim visitors.
- Recommend entries, dossiers and videos that are provably the sources used.
- Stay inside a hard monthly cost ceiling.

### Non-goals

- Not a general-purpose assistant. Off-topic questions get a short redirect.
- No live web search. Ruled out deliberately — see §12.
- No guided learning path or reading-progress tracking in this build. Possible
  later feature; own spec.
- No anonymous access. Sign-in is required, which is also the rate-limit anchor.

## 3. Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Site-grounded, answer-first | User: give real answers, not link dumps. Gap case says so explicitly and still summarises nearest material. |
| D2 | Textual claims cited; reasoning free | Any claim about what a text says must resolve to a site source with the reference shown. Historical and philosophical reasoning is the model's own. Kills the catastrophic failure mode while allowing real answers. |
| D3 | Polemical in first person; attacks claims, never people | Criticises texts, doctrines and historical figures. Never Muslims as a people. Keeps the edge while removing the screenshot liability. |
| D4 | Sonnet 5, ~$50/mo hard cap | Budget chosen by owner. Three independent cost ceilings (§8). |
| D5 | Hybrid retrieval (FTS + pgvector, RRF-fused) | Users ask both exact-reference questions ("what does 9:5 say") and semantic ones ("is Islam misogynistic"). Either index alone fails one badly. |
| D6 | Private ChatGPT-style conversation history | Owner's reading of "unique to each user". Reading-memory and learning-path variants deferred. |
| D7 | Videos cited by transcript content, with timestamps | Title matching cannot judge stance or relevance. A video with no usable transcript never enters the index and can never be suggested. |
| D8 | Deep-index all 6 vetted channels (~2,700 videos) | Editorial control comes from channel selection, already made. Strictly better than live search at everything it was wanted for. |
| D9 | Authored Christian-doctrine reference layer | Site has Christian scripture but no doctrine. Keeps D2 intact and keeps the theology the owner's, not a model average. |
| D10 | Ecumenical creedal baseline (Nicene, Chalcedonian) | The shared core all three major traditions hold, and exactly what Islamic objections target. Intra-Christian disputes get described, not adjudicated. |

## 4. Architecture

The site stays static on GitHub Pages. One Supabase Edge Function is added.

```
Browser (chat.html)                Supabase Edge Fn `ask`        Anthropic
  │  fetch + Supabase JWT              │                             │
  ├───────────────────────────────────►│  1. verify JWT              │
  │                                    │  2. chat_begin_turn() RPC   │
  │                                    │     quota + budget + switch │
  │                                    │  3. embed question          │
  │                                    │     (gte-small, in-process) │
  │                                    │  4. match_corpus() RPC      │
  │                                    │  5. messages.stream() ─────►│
  │  ◄════════ SSE tokens ══════════════┤◄═══════════════════════════┤
  │                                    │     ↳ if stop_reason ==     │
  │                                    │       tool_use: run         │
  │                                    │       search_again, loop    │
  │                                    │  6. persist + chat_end_turn │
```

The `search_again` tool (§6) means step 5 is a **tool loop**, not a single call:
if the response stops with `stop_reason: "tool_use"`, the function runs the search,
appends the result, and streams a continuation. Capped at 2 tool iterations per
turn so a confused model cannot spin. Tools and Citations compose fine — the
incompatibility is with `output_config.format`, not with tool use.

Design points:

- **The Edge Function is the trust boundary.** The Anthropic key is a Supabase
  secret and never reaches the browser. The site is static, so anything shipped in
  JS is public and would be scraped and drained.
- **Quota and budget are checked before the API call**, not reconciled after.
- **Ranking lives in SQL.** `match_corpus()` can be tuned in the SQL editor against
  real questions without redeploying, and tested independently of the chat path.
- **Embeddings run in-process.** Supabase's built-in `gte-small` costs one extra
  ~150ms, no network hop, no second API key, no cost.
- **Streaming is required.** Free-tier Edge Functions allow 150s wall-clock and 2s
  CPU; CPU time excludes waiting on network, so a slow Claude call is CPU-free.

A second, smaller Edge Function `embed` exists only for the ingest pipeline to
batch-embed corpus text. It is not on the request path.

### Anthropic API specifics

- Model ID: `claude-sonnet-5` (exact string, no date suffix).
- `temperature` / `top_p` / `top_k` are rejected on Sonnet 5 — do not send them.
- Adaptive thinking is on by default when `thinking` is omitted. Leave it on.
- `output_config: {effort: "medium"}` as the configured default. Sonnet 5 at
  medium is comparable to Sonnet 4.6 at high. Effort is a `chat_config` value so
  it can be raised without a redeploy.
- Thinking tokens bill as **output** tokens. Per-turn cost estimates in §8 must be
  re-measured in Phase 2 rather than assumed.
- Streaming via `messages.stream()`; `max_tokens` generous since streaming avoids
  HTTP timeouts.
- System prompt carries `cache_control: {type: "ephemeral"}`. Sonnet 5's minimum
  cacheable prefix is 1024 tokens; the system prompt is ~3K, so it caches.
- **`stop_reason` must be checked before reading `content`.** A refusal returns
  HTTP 200 with an empty or partial content array; code that indexes `content[0]`
  unconditionally crashes.

## 5. Knowledge base and ingest

### What is indexed

| Tier | Count | Vector | FTS | Notes |
|---|---|---|---|---|
| Dossiers | 147 | yes | yes | Thesis-level; primary tier for thematic questions |
| Entries | 1,524 | yes | yes | Passage-level evidence |
| Quran verses | 6,236 | yes | yes | Needed for verses no entry wraps (e.g. Q112:3) |
| Doctrine refs | ~30–50 | yes | yes | Authored; see §7 |
| Video chunks | ~21,000 | yes | yes | ~250-word passages with start timestamps |

**Deliberately excluded from phase 1:** the full 34K-hadith corpus and the external
texts (Bible, Tanakh, Talmud, Mishnah, Ibn Kathir, Josephus, Enoch, apocryphal
gospels). Every entry already carries its hadith's text verbatim in its blockquote,
so any hadith the site argues from is already indexed as part of that entry.
The readers are split per-chapter HTML with `anchors.json` ID→page maps, so this is
a real parse job, not a JSON import.

**Trigger to revisit:** if the gap-rate log (§8) shows the bot repeatedly answering
"not covered" on questions whose answer *is* in an uncited hadith or Bible passage,
that earns the ingest. The NT is the most likely first addition, since Christian
doctrine questions lean on it.

### Schema

```sql
create extension if not exists vector;

create table public.kb_docs (
  id           bigserial primary key,
  kind         text not null check (kind in
                 ('entry','dossier','verse','video','doctrine')),
  slug         text not null,              -- anchor id / verse ref / videoId#t=372
  title        text not null,
  ref          text,                       -- 'Bukhari 5134', 'Quran 4:34', 'Testify · 6:12'
  source       text,                       -- 'bukhari' | 'quran' | channel slug
  categories   text[] default '{}',
  strength     text,
  url          text not null,              -- deep link into the site or timestamped YouTube
  body         text not null,              -- full prose handed to Claude
  embed_text   text,                       -- composed field that gets embedded
  embedding    vector(384),
  content_hash text not null,              -- skip re-embedding unchanged docs
  fts tsvector generated always as (
    to_tsvector('english', title ||' '|| coalesce(ref,'') ||' '|| body)
  ) stored,
  updated_at   timestamptz default now(),
  unique (kind, slug)
);
create index on kb_docs using gin  (fts);
create index on kb_docs using hnsw (embedding vector_cosine_ops);
create index on kb_docs using gin  (categories);
create index on kb_docs (kind);
```

RLS is **enabled with no policies**. The anon key cannot read it; the Edge Function
reads with `service_role`. The corpus is public on the site, but there is no reason
to hand out a bulk-queryable copy.

### Why a weak embedding model is acceptable

This is not chunk-level RAG where the retrieved chunk *is* the context. Retrieval
returns document IDs; the full `body` is then loaded from the row. The embedding
only has to be good enough to **rank**, never to carry the answer.

So one vector per document over a composed `embed_text` — title, ref, categories and
the first ~350 tokens of the argument — and `gte-small`'s 512-token truncation is
never reached. Non-video vectors total ~12MB (7,957 docs × 384 dims × 4 bytes);
video chunks add ~32MB of vectors on top.

### Ingest scripts

**`build-kb.py`** — parses `site/catalog/*.html`, `site/arguments/**/*.html` and the
Quran reader into `kb_docs`; composes `embed_text`; batches to the `embed` Edge
Function; upserts. `content_hash` makes re-runs idempotent — rebuild the catalog,
re-run, and only changed documents re-embed. Slots into the existing chain alongside
`apply-source-links.py`, which already must run after any catalog rebuild.

**`build-video-kb.py`** — reads channel URLs from `WATCH_DATA` in `watch.html`,
enumerates each channel's full catalogue with `yt-dlp --flat-playlist`, fetches
captions per video (`--skip-download --write-auto-subs --write-subs --sub-langs
"en.*" --sub-format vtt`), parses the VTT, de-duplicates rolling-caption repeats,
and splits into ~250-word passages tagged with start seconds.

- `slug` → `qa6RT6MFzzA#t=372`
- `url` → `https://www.youtube.com/watch?v=qa6RT6MFzzA&t=372s`
- `ref` → `Testify · 6:12`
- `body` → the passage text

Verified feasible: captions fetch cleanly and ASR quality is good — "Quran",
"Surah", "Allah", "Muhammad" all transcribe correctly, no "Koran" mangling.
Channel sizes sampled: Islam Critiqued 393, Testify 449, Apostate Prophet 485;
expect ~2,700 across six channels, ~21,000 chunks, ~120MB, 2–3 hours for a first
run and incremental after that.

**Fails soft.** A video whose captions cannot be fetched is skipped and logged;
ingest never aborts. Whisper fallback is deliberately not used — hours of local
compute for a handful of videos, and "then don't suggest it" is the desired
behaviour anyway.

### Video constraints

1. **Transcripts are an index, not a quotable corpus.** The bot summarises why a
   video is relevant and links the timestamp. It does not paste transcript back.
   Legally this avoids republishing third-party content; practically, ASR still
   fumbles proper nouns, so a quoted line can misattribute a claim to a creator who
   did not make it.
2. **A video can never back a textual claim** under D2. It supports "someone argues
   this at length here", never "here is what the text says". Videos render in a
   separate **Watch** block, capped at 3, one chunk per video, so they cannot crowd
   out entry citations.
3. **This is the piece that will rot.** yt-dlp breaks when YouTube changes; captions
   get disabled; videos get deleted. Re-running ingest for new uploads is a manual
   step the owner owns.

## 6. Retrieval and the answer contract

### Fusion

`match_corpus(q_text, q_embedding, kinds, cats, k)` runs keyword and vector search
as two CTEs and merges with Reciprocal Rank Fusion — each document scores
`1/(60+rank)` in whichever list it appears in, summed. RRF is chosen over score
weighting because cosine distance and `ts_rank_cd` are not on comparable scales;
RRF needs only the ordering from each.

**No classifier call.** Per-tier caps with exact-reference pinning: up to 4
dossiers, 8 entries, 4 verses, 4 doctrine refs, 3 video chunks. If the question
contains a scripture reference (`4:34`, `Bukhari 5134`, a surah name), that exact
document is pinned to position one. A passage question naturally surfaces entries
and verses; a thematic one naturally surfaces dossiers and doctrine refs. The shape
falls out of the scores rather than a guess, and costs nothing.

### Two-tier hand-off

- **Top 6 by fused score** → `document` content blocks with full `body` and
  `citations: {enabled: true}`.
- **Next ~10** → a compact list: title, ref, category, one line each. Claude can see
  they exist and call a `search_again` tool to pull one in full if needed.

Roughly 3.5K tokens instead of 9.5K for the wide thematic case, without blinding the
model to what else the corpus holds.

### Citations enforce the grounding rule

Claude returns the exact `cited_text` span drawn from each document, with its index.
Two things fall out for free: inline citation markers, and a "further reading" list
that is **provably the set of documents actually used** — not a list the model was
asked to produce and might fabricate.

**Constraint:** Citations cannot be combined with `output_config.format`; the API
returns 400. So no structured JSON output. Entry links are derived from citation
metadata, which is the better outcome anyway.

### The gap flow

Two independent signals, neither of which skips the Claude call:

1. **Retrieval signal** — top fused score below threshold. Best-effort matches are
   still sent, with a flag in the prompt telling Claude retrieval was weak.
2. **Model signal** — Claude concludes the corpus does not cover it.

Either way the reply opens by saying plainly that nothing on Analyzing Islam
directly addresses this yet, then summarises the closest material anyway. The UI
shows a **Suggest this as an entry** button that stashes the question in
`sessionStorage` and opens `/contact.html`, which reads it if present.

**Deliberately not a URL parameter.** Questions people ask a chatbot about leaving
Islam can be sensitive, and URLs end up in browser history, referrer headers and
server logs.

### Follow-up turns

Document blocks are kept **only for the current turn**. Prior turns keep just the
user message and the answer text; otherwise turn five carries thirty documents.

A follow-up like "what about the Muslim response to that?" is a useless retrieval
query alone, so the retrieval query is built from the last user message plus the
titles of the documents cited in the previous answer.

## 7. Christian doctrine reference layer

The site has Christian scripture but no Christian doctrine. Without this layer, a
Muslim asking "is the Trinity three gods?" would hit the gap flow — the wrong answer
to a good-faith question.

~30–50 short authored reference documents indexed as `kind='doctrine'`, cited like
any other source, so D2 stays intact and the theology stays the owner's.

**Baseline: Nicene and Chalcedonian.** The shared core of all three major
traditions, and exactly what Islamic objections target. Where a question touches
something Christians genuinely dispute among themselves — Marian veneration, icons,
the deuterocanon, predestination — the bot describes the range rather than picking a
side.

### Question taxonomy (from research, 2026-07-27)

Documents should cover these clusters, ordered by observed frequency in
Muslim–Christian apologetics:

**A. God's nature — tawhid vs Trinity**
- Is the Trinity three gods? What "one in being, three in persons" means
- Is Allah the same God Christians worship?
- Is Allah a father in any sense? (Q112:3, Q19:88–92, Q6:101, Q5:18)
- Q112:3 "begets not" — eternal generation vs procreation. **The single
  most-repeated argument**, and it usually rests on reading "begotten" as physical
  procreation rather than eternal generation
- Origin of the Trinity — Nicaea 325, Constantine
- Does the Quran attack the actual Trinity? Q5:116 describes a triad of God, Jesus
  and **Mary**

**B. Christology**
- Hypostatic union — is "fully God and fully man" a contradiction? (Note: Muslim
  polemics engage this far less than expected; the Quran never addresses it)
- Did Jesus ever say "I am God, worship me"?
- Limitation passages: Mk 13:32, Jn 14:28, the cry of dereliction, praying to the Father
- Was Jesus a Muslim?
- Was Jesus crucified? Q4:157 and the substitution theory

**C. Scripture**
- What is the Injeel — the four Gospels, or a lost book given to Jesus?
- Tahrif: has the Bible been corrupted, when, by whom, where is the original?
- The Islamic Dilemma (site already covers this well — Q5:47, Q10:94, Q3:3)
- Ehrman and manuscript variants as used in dawah
- Which Bible? Canon differences

**D. Muhammad in the Bible**
- Paraclete (Jn 14:16); Deut 18:18; Song of Songs 5:16 "Muhammadim"; Isaiah 29:12

**E. Salvation**
- Original sin — why bear Adam's guilt?
- Is substitutionary atonement just?
- Why can't God simply forgive?
- Paul as corrupter of Jesus' message

**F. Comparative**
- How the two faiths actually differ; why Christians do not keep the Mosaic law

### Al-Zutt — a worked example of correct behaviour

The al-Zutt controversy concerns Musnad Ahmad 3778 and 3688 — a night excursion
involving Ibn Mas'ud and men of al-Zutt, turning on the verb *yarkabūn*. Critics
read it sexually; Muslim scholars argue that reading is a modern construction
resting on decontextualising a single verb, with a philological rebuttal published
January 2026.

Correct bot behaviour: it is in **Musnad Ahmad, not the six canonical collections**,
so it is outside the site's corpus, and its meaning is **actively contested on
linguistic grounds** rather than settled. The bot should say the site does not cover
it, note the dispute is philological, and stop. A confident answer here would
embarrass the project.

This case should be in the test fixture set.

## 8. Data model, quotas and cost control

| Table | Holds | RLS |
|---|---|---|
| `chat_conversations` | id, user_id, title, timestamps, archived_at | `user_id = auth.uid()` |
| `chat_messages` | conversation_id, role, content, `citations jsonb` | via parent conversation |
| `chat_usage` | user_id, day, message and token counters | select own; writes only via RPC |
| `chat_config` | singleton: enabled, model, effort, daily limit, monthly budget, month-to-date spend, month_key | service_role + admins only |

These follow the RLS patterns already used by `bookmarks` and `highlights`.

### The budget cap

One `SECURITY DEFINER` RPC, `chat_begin_turn(est_cents)`, runs before any Claude call:

```
select * into cfg from chat_config where id = 1 for update;   -- serialises turns
if not cfg.enabled                                  then return 'disabled';
if cfg.month_key <> current month                   then reset spend, roll month;
if cfg.month_spend_cents + est > cfg.budget_cents   then return 'budget';
-- atomically bump today's counter for auth.uid(), then:
if used > cfg.daily_user_limit                      then return 'quota';
return ok;
```

Two details that matter:

- **`for update` on the config row** serialises concurrent turns, so a burst cannot
  all pass the budget check and collectively overshoot.
- **Estimate before, reconcile after.** `chat_end_turn(actual_cents, tok_in,
  tok_out)` writes the real token counts from Claude's `usage` field. Without the
  reconcile step the cap drifts and stops meaning anything.

### Three independent layers

1. Anthropic console spend limit — enforced by Anthropic, outside this codebase
2. `monthly_budget_cents` + kill-switch — enforced in Postgres before any request
3. `daily_user_limit` — stops one user burning the month in an afternoon

### Admin panel

`admin.html` is already gated by the `admins` table and `is_creator()`. It gains a
chat section: month-to-date spend, messages/day, model and effort toggles, and
**gap rate** — how often "not covered" fired and on which questions.

That list is a content roadmap. Questions people repeatedly ask that the corpus does
not answer are precisely the entries worth writing next, and this feature generates
that list for free.

### Cost

Per-turn estimates at Sonnet 5, to be **re-measured in Phase 2** (thinking tokens
bill as output and are not yet observed):

- Passage question ≈ $0.035/turn
- Thematic question ≈ $0.05/turn
- Five-turn conversation ≈ $0.21
- $50/month ≈ 240 conversations

A larger corpus does not increase per-turn cost — it means better matches, not more
context.

**Total cost of ownership: ~$50/mo Anthropic + ~$25/mo Supabase Pro ≈ $75/mo.**
Pro should be treated as required, not optional: the free tier pauses on inactivity,
which for a public chatbot means it is down until someone wakes it, and the video
corpus puts storage at ~170MB against a 500MB ceiling. **This decision is deferred
to the Phase 4 gate** (§11) — nothing before it commits to a monthly bill.

## 9. UI

New `/chat.html` plus an "Ask" nav tab. `sync-nav.py` propagates the tab across all
995 pages.

- Signed out: explainer and sign-in CTA, reusing `auth-ui.js`.
- Signed in: conversation sidebar plus message pane, dark theme consistent with the
  site, sidebar collapsing to a drawer on mobile — where the traffic is.
- Answers stream token-by-token.
- Citations render as inline markers backed by `cited_text` spans, with a **Sources**
  block beneath deep-linking each cited entry/dossier, and a separate **Watch** block
  for video chunks with timestamps.
- Gap state gets its own treatment plus the **Suggest this as an entry** button.

### Failure modes

| Condition | Behaviour |
|---|---|
| Not signed in | Explainer + sign-in CTA; function returns 401 |
| Daily quota hit | Message with reset time — no API call made |
| Budget hit or kill-switch off | "Temporarily unavailable" — no API call made |
| Supabase paused (free tier) | Explicit error surfaced, never a silent spinner |
| Anthropic 429/529 | One retry with backoff, then "busy, try again" |
| Stream drops mid-answer | Partial answer kept and saved; retry offered |
| `stop_reason: "refusal"` | Checked **before** reading content, else the code crashes on an empty array |
| Retrieval returns nothing | Gap flow — not an error |
| yt-dlp fails on a video | Skip, log, continue — never aborts ingest |

## 10. Testing

The highest-value tests need no API spend, because `match_corpus()` is a SQL
function. `tests/` already runs pytest.

1. **Retrieval recall.** A fixture of ~30 real questions with expected results.
   "Was Jesus a Muslim?" must surface the Islamic Dilemma dossier and
   Jesus-category entries; "Is Allah a father?" must surface Q112:3 and Q19:88–92;
   "Al-Zutt" must return nothing above threshold. This is the test that actually
   predicts answer quality.
2. **Ingest.** Parsing yields exactly 1,524 entries; every entry has a quote and a
   "why this is a problem" section; every `url` resolves to a real anchor on a real
   page.
3. **Quota RPC.** Direct SQL tests: concurrent calls do not overshoot the budget;
   month rollover resets spend; kill-switch blocks.
4. **Chat path.** Mocked-Claude tests for the streaming and persistence path, plus a
   handful of real calls inspected by hand.
5. **Grounding audit.** 20 real answers, every textual claim traced back to its
   cited document. Manual, and the single thing most worth doing before launch.

## 11. Build order

Sequenced so cost commitments come last.

**Phase 1 — ingest and retrieval. Zero API cost, free tier.**
`build-kb.py`, `kb_docs`, `match_corpus()`, the recall fixture. Front-loads the real
technical risk: does retrieval actually find the right material for "Is Allah a
father?" If not, nothing downstream matters. Entries, dossiers, Quran and the
doctrine layer first; the 2–3 hour video ingest once retrieval is proven.

**Phase 2 — Edge Function and chat path. ~$5 of API credit.**
Owner-only testing of answer quality, tone and the grounding rule against real
questions. Per-turn cost measured here and §8 updated.

**Phase 3 — UI.**
`chat.html`, nav tab, streaming, citation rendering, conversation sidebar.

**Phase 4 — decision gate.**
Quotas, budget caps, admin panel, Supabase Pro, public launch. Nothing before this
point commits to a monthly bill.

## 12. Deliberate exclusions

- **Live web search.** Considered and rejected for video recommendation. Judging a
  video's stance from its title fails in this space — titles are deliberately
  ambiguous and often state the opposing argument ("The Islamic Dilemma DEBUNKED" is
  a Muslim rebuttal). Open search also discards the editorial control the six vetted
  channels represent, and a model generating YouTube URLs from memory produces
  confident dead links. Deep-indexing vetted channels is better at every point.
  Web search may later be worth revisiting for a *different* job — checking whether
  a claim has recent scholarly support — but not for recommendations.
- **Full hadith and external-text ingest.** See §5 for the trigger to revisit.
- **Whisper transcription fallback.** See §5.
- **Reading memory and guided learning path.** Deferred; own spec if wanted.
- **Anonymous access.** Sign-in is the rate-limit anchor.

## 13. Open questions

1. Owner to confirm the ecumenical creedal baseline (D10) is the right theological
   standard before doctrine documents are written.
2. Per-turn cost with adaptive thinking enabled is estimated, not measured. Phase 2
   resolves this and §8 must be updated with real figures.
3. Supabase Pro is assumed necessary but the decision is deferred to Phase 4.
