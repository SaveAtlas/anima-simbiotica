#!/usr/bin/env python3
"""Render docs/*.md → site/docs/*.html with shared style + nav."""
from __future__ import annotations

import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "site" / "docs"

CSS = """:root { --bg:#0c1210; --fg:#e6ebe7; --muted:#9aab9f; --line:#243028; --accent:#7d9e86; }
body { margin:0; font-family: Georgia, serif; background:var(--bg); color:var(--fg); line-height:1.65; font-size:1.1rem; }
.wrap { max-width:44rem; margin:0 auto; padding:2.5rem 1.5rem 4rem; }
a { color:var(--accent); }
nav { font-family: system-ui, sans-serif; font-size:0.85rem; margin-bottom:2rem; color:var(--muted); }
nav a { white-space: nowrap; }
h1,h2,h3 { font-weight:500; letter-spacing:-0.02em; }
h1 { font-size:1.75rem; }
h2 { font-size:1.25rem; border-top:1px solid var(--line); padding-top:1.25rem; margin-top:2rem; }
h3 { font-size:1.05rem; color:var(--muted); }
p,li { color:var(--fg); }
code, pre { font-family: ui-monospace, monospace; font-size:0.9em; }
pre { background:#121a16; border:1px solid var(--line); padding:1rem; overflow:auto; }
table { border-collapse:collapse; width:100%; font-size:0.95rem; margin:1rem 0; }
th,td { border:1px solid var(--line); padding:0.45rem 0.6rem; text-align:left; vertical-align:top; }
th { color:var(--muted); font-family:system-ui,sans-serif; font-weight:600; }
hr { border:none; border-top:1px solid var(--line); margin:2rem 0; }
.muted { color:var(--muted); }
ul { padding-left: 1.25rem; }
ol { padding-left: 1.25rem; }
"""

# (stem, nav label) — order for shared nav
NAV_ITEMS = [
    ("CONSTITUTION", "Constitution"),
    ("PROTOCOL", "Protocol"),
    ("REUSE-VS-INVENT", "Reuse vs invent"),
    ("EVENT-AND-CONSENT", "Event & Consent"),
    ("FEDERATION", "Federation"),
    ("GUARDIANSHIP", "Guardianship"),
    ("NODE-BINDING", "NodeBinding"),
    ("REVOKE-NODE", "Revoke node"),
    ("SIGNED-EVENTS", "Signed events"),
    ("A2A-MCP-MAPPING", "A2A/MCP"),
    ("EXPORT-AND-EXIT", "Export & exit"),
    ("COMPUTE-MESH", "Compute mesh"),
    ("THREAT-MODEL", "Threat model"),
    ("ACTION-CLASSES", "Action classes"),
    ("GLOSSARY", "Glossary"),
    ("ARCHITECTURE-OVERVIEW", "Architecture"),
    ("STEWARDSHIP", "Stewardship"),
    ("HABITAT-VERTICAL", "Habitat"),
    ("ANIMAL-VERTICAL", "Animal"),
    ("INTEROP-TESTS", "Interop tests"),
    ("SITE-HOSTING", "Site hosting"),
    ("AGENT-CARD", "Agent card"),
    ("VERSIONING", "Versioning"),
    ("CHANGELOG", "Changelog"),
    ("ROADMAP", "Roadmap"),
    ("MEMORY-CUSTODY", "Memory custody"),
    ("FIRST-SLICE-STATUS", "First slice"),
    ("SECOND-SLICE", "Second slice"),
    ("SECOND-SLICE-STATUS", "Second slice status"),
    ("DUAL-PROCESS-BOND", "Dual-process bond"),
    ("THIRD-SLICE", "Third slice"),
    ("THIRD-SLICE-STATUS", "Third slice status"),
    ("CHALLENGE-AND-FRESH", "Challenge & fresh"),
    ("THREE-PARTY-FEDERATION", "Three-party fed"),
    ("FOURTH-SLICE", "Fourth slice"),
    ("FOURTH-SLICE-STATUS", "Fourth slice status"),
    ("FIFTH-SLICE", "Fifth slice"),
    ("FIFTH-SLICE-STATUS", "Fifth slice status"),
    ("SIXTH-SLICE", "Sixth slice"),
    ("GUARDIAN-CHALLENGE", "Guardian challenge"),
    ("INTRODUCE", "Introduce"),
    ("PEERS-DIRECTORY", "Peers directory"),
    ("OPERATOR-GUIDE", "Operator guide"),
]

# Docs to render from markdown (flat under docs/)
RENDER = [
    "CONSTITUTION",
    "PROTOCOL",
    "REUSE-VS-INVENT",
    "EVENT-AND-CONSENT",
    "FEDERATION",
    "GUARDIANSHIP",
    "NODE-BINDING",
    "REVOKE-NODE",
    "SIGNED-EVENTS",
    "A2A-MCP-MAPPING",
    "EXPORT-AND-EXIT",
    "COMPUTE-MESH",
    "THREAT-MODEL",
    "ACTION-CLASSES",
    "GLOSSARY",
    "AGENT-CARD",
    "ARCHITECTURE-OVERVIEW",
    "STEWARDSHIP",
    "HABITAT-VERTICAL",
    "ANIMAL-VERTICAL",
    "INTEROP-TESTS",
    "SITE-HOSTING",
    "FIRST-SLICE-STATUS",
    "VERSIONING",
    "CHANGELOG",
    "ROADMAP",
    "MEMORY-CUSTODY",
    "SECOND-SLICE",
    "SECOND-SLICE-STATUS",
    "DUAL-PROCESS-BOND",
    "THIRD-SLICE",
    "THIRD-SLICE-STATUS",
    "CHALLENGE-AND-FRESH",
    "THREE-PARTY-FEDERATION",
    "FOURTH-SLICE",
    "FOURTH-SLICE-STATUS",
    "FIFTH-SLICE",
    "FIFTH-SLICE-STATUS",
    "SIXTH-SLICE",
    "GUARDIAN-CHALLENGE",
    "INTRODUCE",
    "PEERS-DIRECTORY",
    "OPERATOR-GUIDE",
    "README",
]


def rewrite_md_links(body: str, *, adr: bool = False) -> str:
    """Point .md hrefs at sibling .html where we have rendered pages."""
    def repl(m: re.Match[str]) -> str:
        href = m.group(1)
        text = m.group(2)
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
            return m.group(0)
        # schemas/ and fixtures stay as dirs / md for now
        if href.endswith(".md"):
            stem = Path(href).name[:-3]
            parent = Path(href).parent.as_posix()
            if parent in (".", ""):
                new = f"{stem}.html"
            elif parent == "adr":
                new = f"adr/{stem}.html" if not adr else f"{stem}.html"
            else:
                new = href  # leave schemas etc.
            if adr and parent in (".", ""):
                new = f"../{stem}.html"
            return f'<a href="{html.escape(new)}">{text}</a>'
        return m.group(0)

    return re.sub(r'<a href="([^"]+)">([^<]*)</a>', repl, body)


def nav_html(*, adr: bool = False) -> str:
    home = "../../index.html" if adr else "../index.html"
    parts = [f'<a href="{home}">← ANIMA home</a>']
    for stem, label in NAV_ITEMS:
        if adr:
            href = f"../{stem}.html"
        else:
            href = f"{stem}.html"
        parts.append(f'<a href="{href}">{html.escape(label)}</a>')
    adr1 = "ADR-001-being-vs-node-keys.html" if adr else "adr/ADR-001-being-vs-node-keys.html"
    adr2 = "ADR-002-deny-unknown-action-class.html" if adr else "adr/ADR-002-deny-unknown-action-class.html"
    adr3 = "ADR-003-license-defaults.html" if adr else "adr/ADR-003-license-defaults.html"
    adr4 = "ADR-004-dual-process-data-dirs.html" if adr else "adr/ADR-004-dual-process-data-dirs.html"
    parts.append(f'<a href="{adr1}">ADR-001</a>')
    parts.append(f'<a href="{adr2}">ADR-002</a>')
    parts.append(f'<a href="{adr3}">ADR-003</a>')
    parts.append(f'<a href="{adr4}">ADR-004</a>')
    return "<nav>" + " · ".join(parts) + "</nav>"


def title_from_md(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def page(title: str, body: str, *, adr: bool = False) -> str:
    short = title.split("—")[0].split("–")[0].strip()
    if len(short) > 40:
        short = fallback_short(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(short)} — ANIMA</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
{nav_html(adr=adr)}
{body}
</div>
</body>
</html>
"""


def fallback_short(title: str) -> str:
    return title[:36] + "…"


def md_to_body(md_text: str, *, adr: bool = False) -> str:
    # Convert markdown.md links in source to .html for known docs before render
    def md_link_repl(m: re.Match[str]) -> str:
        text, href = m.group(1), m.group(2)
        if href.startswith("http") or href.startswith("#"):
            return m.group(0)
        if href.endswith(".md"):
            p = Path(href)
            stem = p.name[:-3]
            parent = p.parent.as_posix()
            if parent in (".", ""):
                nh = f"../{stem}.html" if adr else f"{stem}.html"
            elif parent == "adr":
                nh = f"{stem}.html" if adr else f"adr/{stem}.html"
            else:
                return m.group(0)
            return f"[{text}]({nh})"
        return m.group(0)

    md_text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", md_link_repl, md_text)
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return body


def render_one(stem: str) -> Path:
    src = DOCS / f"{stem}.md"
    text = src.read_text(encoding="utf-8")
    title = title_from_md(text, stem)
    body = md_to_body(text)
    out = OUT / f"{stem}.html"
    out.write_text(page(title if stem != "README" else "Docs", body), encoding="utf-8")
    return out


def render_adr() -> list[Path]:
    out_dir = OUT / "adr"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    adr_dir = DOCS / "adr"
    if not adr_dir.is_dir():
        return written
    for src in sorted(adr_dir.glob("ADR-*.md")):
        text = src.read_text(encoding="utf-8")
        title = title_from_md(text, src.stem)
        body = md_to_body(text, adr=True)
        out = out_dir / f"{src.stem}.html"
        out.write_text(page(title, body, adr=True), encoding="utf-8")
        written.append(out)
    return written


def update_index() -> None:
    index = ROOT / "site" / "index.html"
    text = index.read_text(encoding="utf-8")
    # Replace the links div contents
    new_links = """            <div class="links">
        <a href="docs/CONSTITUTION.html">Constitution (v0.1)</a>
        <a href="docs/PROTOCOL.html">Protocol principles (v0)</a>
        <a href="docs/ARCHITECTURE-OVERVIEW.html">Architecture overview</a>
        <a href="docs/REUSE-VS-INVENT.html">Reuse vs invent</a>
        <a href="docs/EVENT-AND-CONSENT.html">Event &amp; Consent</a>
        <a href="docs/FEDERATION.html">Federation</a>
        <a href="docs/GUARDIANSHIP.html">Guardianship</a>
        <a href="docs/NODE-BINDING.html">NodeBinding</a>
        <a href="docs/REVOKE-NODE.html">Revoke stolen node</a>
        <a href="docs/SIGNED-EVENTS.html">Signed events</a>
        <a href="docs/A2A-MCP-MAPPING.html">A2A / MCP</a>
        <a href="docs/EXPORT-AND-EXIT.html">Export &amp; exit</a>
        <a href="docs/ACTION-CLASSES.html">Action classes</a>
        <a href="docs/COMPUTE-MESH.html">Compute mesh</a>
        <a href="docs/THREAT-MODEL.html">Threat model</a>
        <a href="docs/GLOSSARY.html">Glossary</a>
        <a href="docs/AGENT-CARD.html">Agent card</a>
        <a href="docs/STEWARDSHIP.html">Stewardship</a>
        <a href="docs/HABITAT-VERTICAL.html">Habitat vertical</a>
        <a href="docs/ANIMAL-VERTICAL.html">Animal vertical</a>
        <a href="docs/INTEROP-TESTS.html">Interop tests</a>
        <a href="docs/SITE-HOSTING.html">Site hosting</a>
        <a href="docs/VERSIONING.html">Versioning</a>
        <a href="docs/CHANGELOG.html">Changelog</a>
        <a href="docs/ROADMAP.html">Roadmap</a>
        <a href="docs/MEMORY-CUSTODY.html">Memory custody</a>
        <a href="docs/FIRST-SLICE-STATUS.html">First-slice status</a>
        <a href="docs/SECOND-SLICE.html">Second slice</a>
        <a href="docs/DUAL-PROCESS-BOND.html">Dual-process bond</a>
        <a href="docs/THIRD-SLICE.html">Third slice</a>
        <a href="docs/THIRD-SLICE-STATUS.html">Third-slice status</a>
        <a href="docs/CHALLENGE-AND-FRESH.html">Challenge &amp; fresh</a>
        <a href="docs/THREE-PARTY-FEDERATION.html">Three-party federation</a>
        <a href="docs/FOURTH-SLICE.html">Fourth slice</a>
        <a href="docs/INTRODUCE.html">bond.introduce</a>
        <a href="docs/OPERATOR-GUIDE.html">Operator guide</a>
        <a href="docs/adr/ADR-001-being-vs-node-keys.html">ADR-001</a>
        <a href="docs/adr/ADR-002-deny-unknown-action-class.html">ADR-002</a>
        <a href="docs/adr/ADR-003-license-defaults.html">ADR-003</a>
        <a href="docs/adr/ADR-004-dual-process-data-dirs.html">ADR-004</a>
        <a href="docs/README.html">All docs</a>
      </div>"""
    text2, n = re.subn(
        r'<div class="links">.*?</div>',
        new_links,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit(f"index.html links replace failed (n={n})")
    index.write_text(text2, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for stem in RENDER:
        written.append(render_one(stem))
    written.extend(render_adr())
    update_index()
    for p in written:
        print(f"wrote {p.relative_to(ROOT)}")
    print("updated site/index.html links")


if __name__ == "__main__":
    main()
