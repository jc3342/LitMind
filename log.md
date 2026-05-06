# Activity log

Append-only. Each line: `YYYY-MM-DD HH:MM | command | summary`.
Never edit past entries.

2026-05-06 | bootstrap | repo initialized; CLAUDE.md, tools/lint.py, MEMORY.md created
2026-05-06 | schema-update | paper schema: Verbatim quotes -> Key points (free-form); added required `slug` field; filename = slug not id; ingest now renames source PDF to {slug}.pdf
2026-05-06 | ingest | paper/alpamayo-r1 (arxiv 2511.00088 v2); domains=[AV]; PDF renamed alpamayo-r1-v2.pdf
2026-05-06 | approve | paper/alpamayo-r1 -> wiki/papers/; files=[wiki/papers/alpamayo-r1.md]
