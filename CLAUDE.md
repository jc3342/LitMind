# LitMind — Operations Manual

This repo is a personal research knowledge base for AI/ML, inspired by Karpathy's
LLM-Wiki gist (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
and OmegaWiki (https://github.com/skyllwt/OmegaWiki). It is also an Obsidian Vault.

You (Claude) are the wiki maintainer. The user curates sources and asks questions;
you do the bookkeeping — summarizing, linking, lint, conflict detection.

## Mission

Serve three purposes:
1. **High-level**: surface trends and emerging ideas (via `topics/` + `trends/`)
2. **Detail**: recall specific paper details (via `papers/` with fixed schema)
3. **Q&A from past experience**: search prior reads, ideas, tricks (via `/ask`)

---

## Three-layer architecture

```
sources/   # immutable raw materials owned by user
wiki/      # markdown knowledge base owned by you (the LLM)
graph/     # machine-readable relationships
drafts/    # YOUR proposed wiki changes, awaiting user /approve
```

### sources/
- `sources/papers/{DOMAIN}/{id}.pdf` — PDFs, organized by domain (AV, LLM,
  multimodal, ...). Same paper may appear in multiple domain folders (physical
  duplication is fine). The list of folders is the authoritative `domains` field.
- `sources/notes/` — user's own freeform notes
- `sources/web/` — archived blogs, talks, tweets

PDFs are gitignored. Domain folders are user-defined; do not invent new ones
without confirmation.

### wiki/ (six entity types)
| Dir | Entity | Purpose |
|---|---|---|
| `wiki/papers/` | paper | one per arxiv paper |
| `wiki/concepts/` | concept | named technique (MoE-routing, RoPE) |
| `wiki/topics/` | topic | research direction (long-context, agentic-rl) |
| `wiki/ideas/` | idea | user's hypotheses with lifecycle status |
| `wiki/people/` | person | researcher / lab profile |
| `wiki/tricks/` | trick | small empirical recipe / gotcha |
| `wiki/trends/` | trend | periodic synthesis (output of `/reflect`) |

### graph/
- `graph/edges.jsonl` — semantic relationships, one JSON object per line:
  `{"from": "paper/2501.xxxxx", "to": "paper/2401.yyyyy", "type": "builds_on", "evidence": "§3.2"}`
  Allowed types: `builds_on`, `improves_on`, `contradicts`, `same_problem_as`,
  `inspired_by`, `applies`, `surveys`, `reproduces`.
- `graph/citations.jsonl` — bibliographic citations (separate from semantic).

---

## File naming

- **Paper filename** = the `slug:` frontmatter field. Slug should be a short,
  human-readable identifier — usually the method/system name in kebab-case:
  `alpamayo-r1.md`, `mamba.md`, `dpo.md`, `mixture-of-experts-v2.md`.
  - If the paper has no canonical short name, fall back to
    `{first-author-lastname}-{topic}-{year}`, e.g. `kim-bdd-x-2018.md`.
  - To disambiguate same-name papers, append year or version:
    `mamba-2-2024.md`, `bert-large.md`.
  - The arxiv id (or other canonical id) lives in the `id:` field — not in the
    filename.
- Concept/topic/trick: lowercase-hyphenated, e.g. `mixture-of-experts.md`,
  `kv-cache-quantization.md`.
- People: `firstname-lastname.md`.
- Avoid `:` `?` `/` in filenames (Obsidian wikilink reserved chars).

---

## Wikilinks

Use **bare slug** `[[wikilink]]` for all cross-references — never path-prefixed.
Examples: `[[mixture-of-experts]]`, `[[alpamayo-r1]]`, `[[grpo]]`.

**Why bare:** Obsidian resolves `[[paper/foo]]` as a literal path
(`paper/foo.md`) which doesn't match the real file at `wiki/papers/foo.md` —
this creates phantom nodes in the graph view.

**Slugs must be globally unique** across all entity types (paper/concept/topic/
idea/person/trick/trend). Lint enforces this. If a slug would collide:
- Disambiguate by appending year/version/qualifier:
  `mamba` (paper) vs `mamba-architecture` (concept).
- Or qualify with a more specific name: `attention-mechanism` instead of
  `attention`.

If you want labeled link text, use Obsidian's pipe alias:
`[[grpo|GRPO algorithm]]`.

---

## Style guide (bilingual)

- **Terms in English, prose in Chinese.** Example: "MoE 的 **load-balanced top-k
  routing** 在 ..."
- Code, equations, table/figure references: keep verbatim.
- Verbatim quotes from papers: keep in original language (usually English).
- TL;DR and "My take" sections: Chinese unless quoting.

---

## Provenance — IRON RULE

Every factual claim in the wiki is one of:
1. **Sourced**: followed by `^[paper-id:loc]`, e.g. `^[2501.12345:§3.2]`,
   `^[2501.12345:Table 4]`, `^[2501.12345:Fig 2]`. The paper id must exist in
   `wiki/papers/`.
2. **User opinion / your synthesis**: in a "My take" or "Synthesis" section,
   labeled as such.
3. **Unsourced**: tagged inline as `(unsourced)`. Lint will flag these.

Never paraphrase a number/result without `^[...:loc]`. Never delete a previously
sourced claim without leaving a `~~strikethrough~~` + reason.

---

## Schemas (frontmatter is enforced by `tools/lint.py`)

### paper
```yaml
---
slug: alpamayo-r1                    # required, human-readable, == filename
id: 2511.00088                       # required, canonical arxiv id (or other)
title: "..."                         # required
authors: [Lastname Firstname, ...]   # required, ≥1
venue: arxiv | ICML 2025 | ...       # required
date: 2025-01-15                     # required, YYYY-MM-DD
domains: [LLM, AV]                   # auto-filled from sources/ folder presence
tags: [moe, routing, efficiency]     # required, ≥1, free-form lowercase
status: queued | skimmed | read      # required
arxiv_url: https://arxiv.org/abs/2511.00088  # optional
arxiv_version: v2                    # optional
---
```
Body (sections **required in this order**):
1. `## TL;DR` — 1–2 sentences (Chinese)
2. `## Problem` — what it solves
3. `## Method` — core approach, with `^[id:loc]` citations
4. `## Key points` — implementation details worth recalling (multi-modal fusion,
   data format, training tricks, ablations, anything specific). Free-form; can
   include verbatim `> blockquote` lines when useful.
5. `## Results` — key numbers, with `^[id:Table N]`
6. `## My take` — your judgment, can be brief but section must exist
7. `## Connections` — bulleted wikilinks: `builds_on:: [[...]]`, etc.
8. `## Open questions`

### concept
```yaml
---
name: Mixture of Experts             # required, human-readable
slug: mixture-of-experts             # required, matches filename
aliases: [MoE, Sparse MoE]           # optional
tags: [...]                          # required
status: stub | active | mature       # required
---
```
Body sections:
1. `## Definition` — what it is, in one paragraph
2. `## Variants` — bulleted list, each with `^[paper:loc]`
3. `## Key papers` — `[[paper/...]]` wikilinks
4. `## Open questions`

### topic
```yaml
---
slug: long-context                   # required
name: Long-context modeling          # required
parent: null | <topic-slug>          # optional, hierarchical
tags: [...]                          # required
status: emerging | active | mature   # required
last_reflected: null | YYYY-MM-DD    # set by /reflect
---
```
Body sections:
1. `## Scope` — what's in / out
2. `## Schools of thought` — competing approaches
3. `## SOTA tracker` — table or list
4. `## Open problems`
5. `## Recent work` — chronological, auto-updated by /ingest
6. `## Related concepts` — wikilinks

### idea
```yaml
---
slug: ...                            # required
title: ...                           # required
created: YYYY-MM-DD                  # required
status: alive | exploring | dead | done   # required
reason: null | "..."                 # required if status=dead
tags: [...]                          # required
---
```
Body sections:
1. `## The idea` — what you're proposing
2. `## Novelty argument` — why it's not already done
3. `## Related work` — wikilinks to relevant `[[paper/...]]`
4. `## Risks / unknowns`
5. `## Status log` — append-only `YYYY-MM-DD: ...` entries

**Never delete an idea.** Mark `status: dead` with `reason`. Anti-repetition memory.

### person
```yaml
---
slug: firstname-lastname             # required
name: Firstname Lastname             # required
affiliation: [...]                   # required
tags: [...]                          # required
last_seen: YYYY-MM-DD                # last paper of theirs you read
---
```
Body sections:
1. `## Research areas`
2. `## Notable work` — wikilinks
3. `## Notes` — your impressions

### trick
```yaml
---
slug: ...                            # required
title: ...                           # required
tags: [...]                          # required
triggered_by: [paper/..., concept/...]  # required, ≥1 wikilink
verified: true | false | unknown     # required
---
```
Body: free-form short, but must include:
1. `## What` — one paragraph
2. `## Why it matters / when to use`
3. `## Source` — link or anecdote

### trend
```yaml
---
slug: 2026-Q2-long-context           # required
period: 2026-Q2                      # required
topic: long-context                  # required, matches a topic slug
generated: YYYY-MM-DD                # required
---
```
Body: synthesis, free-form, with citations.

---

## Five operations

You implement these as workflows. The user invokes them in conversation.

### `/ingest <pdf-path>` or `/ingest <arxiv-url>`
Goal: convert a source into a paper page (and ripple updates).

1. Resolve canonical `id` (arxiv id, e.g. `2511.00088`).
2. Resolve `slug` — short, human-readable, kebab-case, usually the method/system
   name (e.g. `alpamayo-r1`, `mamba`, `dpo`). If no canonical short name, use
   `{first-author-lastname}-{topic}-{year}`. Disambiguate w/ year/version when
   needed.
3. Read the PDF / fetch arxiv abstract+content.
4. **Rename the source PDF** to match the slug:
   - `sources/papers/<DOMAIN>/<original-filename>.pdf`
     → `sources/papers/<DOMAIN>/{slug}.pdf` (or `{slug}-v{N}.pdf` if arxiv
     version is meaningful and you want it visible on disk).
   - If the same paper has copies in multiple domain folders, rename all of them.
5. Detect `domains` by `find sources/papers -name "{slug}*.pdf"`.
6. Write `drafts/papers/{slug}.md` per the paper schema (note: filename matches
   `slug`, not `id`).
7. Identify connections to existing wiki entities. If both endpoints already
   exist in wiki/, write `drafts/{slug}.edges.jsonl` with proposed graph edges.
   For dangling endpoints, just leave the wikilinks in the Connections section —
   they will resolve when the other end is later ingested.
8. Identify wiki pages that *would* be touched (topics' Recent work,
   concepts' Variants, etc.) and write them as `drafts/...md` too — DO NOT
   modify wiki/ directly.
9. Output a summary: "Created N drafts, M edges. Run `/approve {slug}` to merge."

### `/approve <slug>` or `/approve <draft-path>`
1. Move all `drafts/.../{slug}.*` to `wiki/.../{slug}.*` and append edges to
   `graph/edges.jsonl`.
2. Update `MEMORY.md` index entry.
3. Append to `log.md`: `{timestamp} approve slug={slug} files=[...]`.
4. Run `tools/lint.py` and report.

### `/ask <question>`
1. Search wiki by filename, frontmatter tags, and full-text grep.
2. Synthesize an answer. **Every claim cites `^[wiki-page:section]` or
   `^[paper-id:loc]`.**
3. If the answer is novel/valuable, ask: "Save as `wiki/ideas/...` or extend
   `wiki/concepts/...`?" If yes → write to `drafts/`.
4. If you cannot answer from wiki, say so explicitly. Do not hallucinate.

### `/reflect <topic-slug>`
1. Read all papers in `wiki/papers/` whose tags overlap the topic OR that link
   to `[[topic/{slug}]]`.
2. Read the topic page itself for prior context.
3. Produce `drafts/trends/{YYYY-Qn}-{slug}.md`: evolution timeline, schools
   of thought emerging, contradictions found, open problems.
4. Update topic page's `last_reflected` (via draft).

### `/lint`
1. Run `python tools/lint.py`.
2. For each LINT FAIL, propose a fix in `drafts/` (do not auto-apply except
   for trivial whitespace).
3. Additionally: read the report's "tag promotion candidates" — if ≥5 papers
   share a tag with no matching `wiki/topics/{tag}.md`, propose a topic page
   draft and ask the user.

---

## Iron rules (review before any action)

1. **Drafts gate.** Only write to `wiki/` after explicit `/approve`. Exceptions:
   `MEMORY.md` and `log.md` may be updated as part of `/approve`, never standalone.
2. **Provenance.** Every claim has `^[id:loc]` or is in a "My take" / "Synthesis"
   section.
3. **No idea deletion.** `status: dead` instead.
4. **log.md is append-only.** Never rewrite history.
5. **Bottom-up topics.** Don't invent topic pages preemptively. Only after
   `/lint` flags ≥5 papers sharing a tag, AND user confirms.
6. **Don't invent domains.** Only use the folders that exist under
   `sources/papers/`.
7. **English terms, Chinese prose.**
8. **Same paper, multiple domains.** A paper's `domains` is the multiset of
   folders containing its PDF — derive, don't guess.
9. **Confirm before destructive moves.** Renames, deletions, schema migrations
   require user OK.

---

## What to do when invoked

1. Read `MEMORY.md` for the index.
2. Read `log.md` tail for recent activity.
3. Identify which operation the user is asking for. If unclear, ask.
4. Before any wiki write: confirm you're going through `drafts/`.
5. After any draft creation: tell the user how to `/approve`.

---

## Bootstrap status

This is a freshly initialized vault. `wiki/`, `drafts/`, `sources/papers/{DOMAIN}/`
are all empty. The first ingest will set the rhythm; lint after each approval.
