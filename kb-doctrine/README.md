# Doctrine reference layer

Authored Christian-doctrine documents for the chatbot. The site carries Christian
*scripture* but no Christian *doctrine*, so without these a Muslim asking "is the
Trinity three gods?" hits the not-covered path — the wrong answer to a good-faith
question.

These are indexed as `kind='doctrine'` and cited like any other source, which keeps
the grounding rule intact and keeps the theology the site author's rather than a
model's.

**Baseline: ecumenical creedal — Nicene and Chalcedonian.** That is the core all
three major traditions share, and exactly what Islamic objections target. Where a
question touches something Christians genuinely dispute among themselves (Marian
veneration, icons, the deuterocanon, predestination), describe the range rather than
picking a side.

**The narrow-claim rule applies.** Never attribute a position to a named scholar
without a source for it. See spec §7.

## Format

    ---
    slug: kebab-case-unique
    title: Sentence-case title
    cluster: A
    ---

    Markdown body.

`cluster` maps to the §7 taxonomy: A God's nature · B Christology · C Scripture ·
D Muhammad in the Bible · E Salvation · F Comparative · G Asymmetric standards.

## Backlog

Clusters A–G in spec §7 list roughly 30 more documents worth writing. Priority
order comes from the admin panel's gap-rate metric once the chatbot is live.
