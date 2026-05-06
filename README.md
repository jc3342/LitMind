# LitMind

> A persistent, LLM-maintained wiki for compounding AI/ML paper notes.

**Languages:** English · [中文](README.zh-CN.md)

A personal research knowledge base for AI/ML papers — also an Obsidian vault.
Designed to compound knowledge across paper reads instead of re-deriving
context every time.

Built around three goals:

1. **Surface trends** — bottom-up topic emergence shows what's heating up across many papers
2. **Recall details** — every paper page follows a fixed schema, so you know where to look
3. **Borrow past experience** — search prior reads, ideas, and tricks when tackling new questions

The system treats an LLM (e.g. Claude Code) as a persistent wiki maintainer:
the human curates source PDFs and asks strategic questions; the LLM does the
bookkeeping — summarizing, cross-linking, lint, conflict detection.

---

## How it works

Three layers, deliberately separated:

```
sources/   immutable raw materials owned by user (PDFs, organized by domain)
drafts/    LLM-proposed wiki changes, awaiting human /approve
wiki/      approved knowledge base (markdown + Obsidian wikilinks)
```

Six entity types live in `wiki/`:

| Dir | Entity | Purpose |
|---|---|---|
| `wiki/papers/` | paper | one per arxiv paper, fixed schema |
| `wiki/concepts/` | concept | named technique (MoE, RoPE, GRPO) |
| `wiki/topics/` | topic | research direction, emerges bottom-up |
| `wiki/ideas/` | idea | your hypotheses with lifecycle status |
| `wiki/people/` | person | researcher / lab profile |
| `wiki/tricks/` | trick | small empirical recipe / gotcha |

Five operations (defined in [CLAUDE.md](CLAUDE.md), invoked in conversation):

- `/ingest <pdf-or-url>` — convert source into draft paper page + propose links
- `/approve <slug>` — promote draft to wiki/, update index and log
- `/ask <question>` — search wiki, answer with provenance citations
- `/reflect <topic>` — periodic synthesis of a research direction
- `/lint` — deterministic checks via `tools/lint.py`

---

## Design choices that turned out to matter

These were learned from the gist comments and from running the system:

- **Drafts gate.** LLM never writes directly to `wiki/`. Every change is
  proposed in `drafts/` and merged on explicit approval. Avoids LLM-induced
  drift you only notice three weeks later.
- **Provenance is mandatory.** Every factual claim cites `^[paper-id:section]`
  or lives in a "My take" section. Anti-lossy-compression.
- **Bottom-up topics.** Don't seed topic pages preemptively. Lint flags
  candidates when ≥5 papers share a tag, then human approves promotion.
- **Bare-slug wikilinks.** `[[alpamayo-r1]]` not `[[paper/alpamayo-r1]]` —
  Obsidian treats path-prefixed links as literal paths and creates phantom
  graph nodes. Slugs are kept globally unique, lint enforces.
- **Failed ideas aren't deleted.** Mark `status: dead` with reason. Anti-
  repetition memory — prevents re-thinking the same dead end six months later.
- **Deterministic lint over LLM lint.** `tools/lint.py` checks frontmatter,
  body sections, slug collisions, dangling wikilinks, tag-promotion candidates,
  domain-folder consistency. Fast, repeatable, fails CI cleanly.

---

## Current status

**Early / experimental** — bootstrapped 2026-05-06.

What works end-to-end (validated on real input):
- `/ingest` of a PDF → schema-conformant draft paper page (PyMuPDF for text)
- `/approve` → draft to `wiki/`, MEMORY/log updated
- `/lint` → deterministic checks pass (frontmatter, sections, slug uniqueness,
  bare-slug wikilinks, domain-folder consistency)
- Obsidian graph view shows the entity + dangling pending links

What's designed but not yet exercised:
- `/ask` — search wiki and answer with provenance citations
- `/reflect <topic>` — periodic synthesis into `trends/`
- Tag-promotion flow: lint flags candidates when ≥5 papers share a tag, but
  no topic page has been promoted yet (only one paper indexed so far)

What's missing:
- Tests / CI
- `.claude/commands/` slash commands (operations are invoked via natural
  language; works but lacks tab-completion)
- A second paper to start exercising the cross-link / tag-promotion behavior

The schema (CLAUDE.md) has been deliberately revised once already after the
first ingest — expect more such revisions as the wiki grows. Schema changes
are tracked in `log.md`.

---

## Quick start (forking this for your own notes)

```bash
git clone https://github.com/jc3342/LitMind.git my-research-wiki
cd my-research-wiki
python3 -m pip install -r requirements.txt

# Open the directory as an Obsidian vault: File -> Open vault
# (Optional plugins: Dataview for queryable frontmatter, Graph Analysis)

# Drop a PDF under sources/papers/<DOMAIN>/, then in your Claude Code session:
#   "ingest sources/papers/AV/foo.pdf"
# Claude will read CLAUDE.md, create a draft, await your /approve.
```

The included sample is one paper page — `wiki/papers/alpamayo-r1.md` — so you
can see what a populated entity looks like.

---

## Repository layout

```
LitMind/
├── CLAUDE.md                # operations manual for the LLM (start here)
├── MEMORY.md                # top-level index of all entities
├── log.md                   # append-only audit of approve events
├── README.md
├── LICENSE
├── requirements.txt
├── sources/                 # raw PDFs, gitignored, domain-organized
│   ├── papers/<DOMAIN>/
│   ├── notes/
│   └── web/
├── drafts/                  # LLM proposals awaiting /approve
├── wiki/                    # the knowledge base
│   ├── papers/
│   ├── concepts/
│   ├── topics/
│   ├── ideas/
│   ├── people/
│   ├── tricks/
│   └── trends/
├── graph/
│   ├── edges.jsonl          # semantic relationships
│   └── citations.jsonl      # bibliographic
└── tools/
    └── lint.py
```

---

## Acknowledgments

Direct intellectual debts:

- **[Andrej Karpathy's LLM-Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  — the original idea: treat the LLM as a wiki maintainer that compounds
  synthesis over time, rather than re-deriving context per query. The
  three-layer architecture (sources / wiki / schema) is from there.
- **[OmegaWiki](https://github.com/skyllwt/OmegaWiki)** by DAIR Lab @ PKU —
  a richer realization of the same idea. We borrowed: typed entity hierarchy,
  Obsidian wikilink format, separate `graph/edges.jsonl` for semantic relations,
  and the failed-idea-as-anti-repetition-memory pattern. We dropped its 24
  slash commands and full research-lifecycle scope to stay minimal.

Pitfalls flagged in the gist comments and addressed here:

- **a-a-k**: lossy compression risk → key-points section + provenance citations
- **superimpactful**: index reflects LLM categorization, not user mental model
  → bottom-up topic emergence
- **ethanj** (llmwiki): need claim-level provenance + approval gates → drafts/
  workflow + `^[id:loc]` mandatory
- **theafh**: lint is non-negotiable → `tools/lint.py` deterministic checks

---

## License

MIT — see [LICENSE](LICENSE).
