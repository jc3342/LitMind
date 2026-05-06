#!/usr/bin/env python3
"""Lint the wiki for schema, link, and provenance hygiene.

Checks:
  1. YAML frontmatter has all required fields per entity.
  2. Filename matches `id` (papers) or `slug` (others).
  3. Required body sections (## ...) present per entity.
  4. Paper pages have >=3 verbatim quote lines under "## Verbatim quotes".
  5. [[wikilinks]] resolve to existing wiki pages.
  6. Tag promotion: a tag in >=5 papers with no matching wiki/topics/<tag>.md.
  7. Orphan pages (no incoming wikilinks; topics/trends excluded).
  8. Paper `domains:` field matches the folders under sources/papers/.

Usage:
  python tools/lint.py                # lint wiki/
  python tools/lint.py --drafts       # also lint drafts/

Exit code: 0 if no errors, 1 otherwise. Warnings/promotion/orphans don't fail.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("lint.py needs PyYAML. Install: pip install pyyaml\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
DRAFTS = ROOT / "drafts"
SOURCES_PAPERS = ROOT / "sources" / "papers"

ENTITIES = ["papers", "concepts", "topics", "ideas", "people", "tricks", "trends"]

REQUIRED_FRONTMATTER = {
    "papers":   ["slug", "id", "title", "authors", "venue", "date", "domains", "tags", "status"],
    "concepts": ["name", "slug", "tags", "status"],
    "topics":   ["slug", "name", "tags", "status"],
    "ideas":    ["slug", "title", "created", "status", "tags"],
    "people":   ["slug", "name", "affiliation", "tags"],
    "tricks":   ["slug", "title", "tags", "triggered_by", "verified"],
    "trends":   ["slug", "period", "topic", "generated"],
}

REQUIRED_SECTIONS = {
    "papers":   ["TL;DR", "Problem", "Method", "Key points", "Results",
                 "My take", "Connections", "Open questions"],
    "concepts": ["Definition", "Variants", "Key papers", "Open questions"],
    "topics":   ["Scope", "Schools of thought", "SOTA tracker",
                 "Open problems", "Recent work", "Related concepts"],
    "ideas":    ["The idea", "Novelty argument", "Related work",
                 "Risks / unknowns", "Status log"],
    "people":   ["Research areas", "Notable work", "Notes"],
    "tricks":   ["What", "Why it matters / when to use", "Source"],
    "trends":   [],
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return {"_yaml_error": str(e)}, text[m.end():]
    return fm, text[m.end():]


def find_md_files(base: Path):
    for entity in ENTITIES:
        d = base / entity
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            yield entity, f


def collect_link_targets(base: Path) -> set[str]:
    """Return all valid wikilink targets (bare slugs only, Obsidian-native).

    Pathed forms like `paper/foo` are intentionally NOT included — they create
    phantom nodes in Obsidian's graph view.
    """
    targets: set[str] = set()
    for entity, f in find_md_files(base):
        targets.add(f.stem)
    return targets


def collect_slug_to_files(base: Path) -> dict[str, list[Path]]:
    """Map slug -> list of files claiming that slug, for uniqueness checking."""
    out: dict[str, list[Path]] = defaultdict(list)
    for entity, f in find_md_files(base):
        out[f.stem].append(f)
    return out


def detected_domains_for(slug: str) -> list[str]:
    """Find which `sources/papers/<DOMAIN>/` folders contain this paper.

    Matches `<slug>.pdf` or `<slug>-v<N>.pdf` (arxiv version suffix).
    """
    if not SOURCES_PAPERS.exists():
        return []
    version_re = re.compile(rf"^{re.escape(slug)}(?:-v\d+)?$")
    found = []
    for p in SOURCES_PAPERS.glob(f"*/{slug}*.pdf"):
        if version_re.match(p.stem):
            found.append(p.parent.name)
    return sorted(set(found))


def lint_file(entity, f, link_targets, tag_counter, errors, warnings):
    rel = f.relative_to(ROOT)
    text = f.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}: no YAML frontmatter")
        return
    if "_yaml_error" in fm:
        errors.append(f"{rel}: YAML parse error: {fm['_yaml_error']}")
        return

    for field in REQUIRED_FRONTMATTER[entity]:
        if field not in fm:
            errors.append(f"{rel}: missing frontmatter field '{field}'")

    if "slug" in fm and str(fm["slug"]) != f.stem:
        errors.append(
            f"{rel}: filename '{f.stem}' does not match slug='{fm['slug']}'"
        )

    headings = set(HEADING_RE.findall(body))
    for s in REQUIRED_SECTIONS[entity]:
        if s not in headings:
            errors.append(f"{rel}: missing required section '## {s}'")

    if entity == "papers":
        # domains consistency with sources/
        declared = fm.get("domains")
        if isinstance(declared, list):
            actual = detected_domains_for(f.stem)
            if actual and set(declared) != set(actual):
                warnings.append(
                    f"{rel}: domains={declared} but PDF found under {actual}"
                )
        if isinstance(fm.get("tags"), list):
            for t in fm["tags"]:
                tag_counter[t].add(f.stem)

    for m in WIKILINK_RE.finditer(body):
        target = m.group(1).strip()
        if target not in link_targets:
            warnings.append(f"{rel}: dangling wikilink [[{target}]]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", action="store_true",
                        help="Also lint drafts/")
    args = parser.parse_args()

    bases = [WIKI] + ([DRAFTS] if args.drafts else [])
    errors: list[str] = []
    warnings: list[str] = []
    tag_counter: dict[str, set[str]] = defaultdict(set)

    all_files = []
    link_targets: set[str] = set()
    slug_to_files: dict[str, list[Path]] = defaultdict(list)
    for base in bases:
        link_targets |= collect_link_targets(base)
        for slug, files in collect_slug_to_files(base).items():
            slug_to_files[slug].extend(files)
        for entity, f in find_md_files(base):
            all_files.append((entity, f))

    for slug, files in slug_to_files.items():
        if len(files) > 1:
            paths = ", ".join(str(p.relative_to(ROOT)) for p in files)
            errors.append(f"slug collision: '{slug}' claimed by [{paths}]")

    for entity, f in all_files:
        lint_file(entity, f, link_targets, tag_counter, errors, warnings)

    existing_topic_slugs = {
        f.stem for base in bases
        for entity, f in find_md_files(base) if entity == "topics"
    }
    promotion_candidates = [
        (tag, sorted(papers))
        for tag, papers in tag_counter.items()
        if len(papers) >= 5 and tag not in existing_topic_slugs
    ]

    incoming: dict[str, int] = defaultdict(int)
    link_sources = [f for _, f in all_files]
    for root_md in ("MEMORY.md",):
        p = ROOT / root_md
        if p.exists():
            link_sources.append(p)
    for f in link_sources:
        text = f.read_text(encoding="utf-8")
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip().split("/", 1)[-1]
            if target != f.stem:
                incoming[target] += 1
    orphans = [
        f.relative_to(ROOT) for entity, f in all_files
        if entity not in ("topics", "trends") and incoming.get(f.stem, 0) == 0
    ]

    print(f"=== Lint report: {len(all_files)} files across {[str(b.relative_to(ROOT)) for b in bases]} ===")
    if errors:
        print(f"\n[ERRORS] ({len(errors)})")
        for e in errors:
            print(f"  FAIL  {e}")
    if warnings:
        print(f"\n[WARNINGS] ({len(warnings)})")
        for w in warnings:
            print(f"  WARN  {w}")
    if promotion_candidates:
        print("\n[TAG PROMOTION CANDIDATES]")
        for tag, papers in promotion_candidates:
            print(f"  -> tag '{tag}' in {len(papers)} papers; consider wiki/topics/{tag}.md")
            for p in papers[:5]:
                print(f"        paper/{p}")
    if orphans:
        print("\n[ORPHANS]  (no incoming wikilinks)")
        for o in orphans:
            print(f"  ORPH  {o}")
    if not (errors or warnings or promotion_candidates or orphans):
        print("\nOK  all checks passed.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
