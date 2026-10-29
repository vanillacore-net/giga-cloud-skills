#!/usr/bin/env python3
"""Build the hosting-plan results app.

The app has a start page, a case page rendered from the case files and two
EMPTY result pages (planning.html, platform.html). The agent fills the result
pages; this script never pre-fills a result.

    python3 build_app.py --cases ./cases --out ./out
    python3 build_app.py --cases ./cases --out ./out --config app.json
    python3 build_app.py --cases ./cases --out ./site --static

Case files are Markdown files named case-*.md:

    # Case A: Business permit applications
    Label: "citizen services in the cloud"      (optional)
    - one supplied fact per bullet
    Not supplied: what is still unknown         (optional)

The config file is optional JSON. Every key is optional:

    {
      "title": "Hosting plan by workload",
      "subtitle": "What each service needs, and one platform for all of them",
      "question": "One sentence that states the question for the audience.",
      "context_label": "Text shown next to the logo, e.g. an event or team",
      "footer": "Footer text",
      "accent": "#0b5fff",
      "logo": "path/to/logo.svg",
      "links": [{"label": "Read more", "href": "https://example.org"}]
    }
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS = HERE / "app.css"
MAX_CASES = 4
CASE_CLASSES = ["a", "b", "c", "d"]
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULTS = {
    "title": "Hosting plan by workload",
    "subtitle": "What each service needs from its hosting, and how one platform can run them",
    "question": (
        "These services may share a label, but not their needs. What does each one need "
        "from its hosting, and how can one platform serve all of them?"
    ),
    "context_label": "",
    "footer": "",
    "accent": "#0b5fff",
    "logo": "",
    "links": [],
}

PAGES = [
    ("index.html", "Start"),
    ("use-cases.html", "Cases"),
    ("planning.html", "1 · Planning"),
    ("platform.html", "2 · Platform"),
]

RESULT_PAGES = [
    ("planning.html", "Planning",
     "What each case needs from its hosting, and how one platform can run all of them."),
    ("platform.html", "Platform",
     "The platform planned on IaaS and Kubernetes, with an architecture diagram."),
]


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def load_config(path: Path | None) -> dict:
    cfg = dict(DEFAULTS)
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"{path}: config must be a JSON object")
        unknown = set(data) - set(DEFAULTS)
        if unknown:
            raise SystemExit(f"{path}: unknown config keys {sorted(unknown)}")
        cfg.update({k: v for k, v in data.items() if v is not None})
    if not HEX.match(cfg["accent"]):
        raise SystemExit("config accent must be a #rrggbb colour")
    for link in cfg["links"]:
        if not isinstance(link, dict) or not link.get("label") or not link.get("href"):
            raise SystemExit("every link needs label and href")
        if not str(link["href"]).startswith(("https://", "http://", "./", "../")):
            raise SystemExit(f"link href must be http(s) or relative: {link['href']}")
    return cfg


def parse_case(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, re.M)
    if not title:
        raise SystemExit(f"{path}: first heading '# Case X: Name' is missing")
    parts = title.group(1).split(":", 1)
    head, name = (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else ("", parts[0].strip())
    label = re.search(r"^Label: (.+)$", text, re.M)
    missing = re.search(r"^Not supplied: (.+)$", text, re.M)
    facts = re.findall(r"^- (.+)$", text, re.M)
    if not facts:
        raise SystemExit(f"{path}: a case needs at least one '- fact' bullet")
    return {
        "head": head,
        "name": name,
        "label": label.group(1).strip() if label else "",
        "facts": facts,
        "missing": missing.group(1).strip() if missing else "",
    }


def nav(active: str) -> str:
    items = []
    for href, label in PAGES:
        cls = ' class="active"' if href == active else ""
        items.append(f'<a href="{href}"{cls}>{esc(label)}</a>')
    return "\n    ".join(items)


def page(cfg: dict, active: str, title: str, body: str, refresh: bool) -> str:
    meta = '<meta http-equiv="refresh" content="5">' if refresh else ""
    logo = f'<img src="assets/logo{Path(cfg["logo"]).suffix}" alt="">' if cfg["logo"] else ""
    context = f'<span class="context">{esc(cfg["context_label"])}</span>' if cfg["context_label"] else ""
    brand = f'<span class="brand">{esc(cfg["title"])}</span>' if not logo else ""
    footer = esc(cfg["footer"]) if cfg["footer"] else esc(cfg["title"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{meta}
<title>{esc(title)} · {esc(cfg["title"])}</title>
<link rel="stylesheet" href="assets/app.css">
<style>:root {{ --accent: {cfg["accent"]}; }}</style>
</head>
<body>
<header class="topbar">
  {logo}{brand}
  {context}
  <nav class="tabs">
    {nav(active)}
  </nav>
</header>
{body}
<footer>
  <span>{footer}</span>
</footer>
</body>
</html>
"""


def build(cases_dir: Path, out: Path, cfg: dict, static: bool) -> None:
    case_files = sorted(cases_dir.glob("case-*.md"))
    if not case_files:
        raise SystemExit(f"{cases_dir}: no case-*.md files")
    if len(case_files) > MAX_CASES:
        raise SystemExit(f"{cases_dir}: at most {MAX_CASES} cases fit one page")
    cases = [parse_case(p) for p in case_files]

    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    shutil.copy2(CSS, out / "assets" / "app.css")
    if cfg["logo"]:
        logo = Path(cfg["logo"])
        if not logo.is_file():
            raise SystemExit(f"logo not found: {logo}")
        shutil.copy2(logo, out / "assets" / f"logo{logo.suffix}")

    links = "\n    ".join(
        f'<a class="btn{" ghost" if i else ""}" href="{esc(link["href"])}" '
        f'target="_blank" rel="noopener">{esc(link["label"])}</a>'
        for i, link in enumerate(cfg["links"])
    )
    more = f'<h2>Learn more</h2>\n  <div class="links">\n    {links}\n  </div>' if links else ""
    index = f"""<section class="hero">
  <h1>{esc(cfg["title"])}</h1>
  <p>{esc(cfg["subtitle"])}</p>
</section>
<main>
  <h2>The question</h2>
  <p class="lead">{esc(cfg["question"])}</p>
  <h2>The route</h2>
  <div class="cards">
    <section class="card"><div class="label">Step 1</div><h3>Planning</h3><p>What each workload needs, and what one platform for all of them looks like.</p><a href="planning.html">Open planning →</a></section>
    <section class="card"><div class="label">Step 2</div><h3>Platform</h3><p>The platform planned on IaaS and Kubernetes, with an architecture diagram.</p><a href="platform.html">Open platform →</a></section>
  </div>
  {more}
</main>"""
    (out / "index.html").write_text(page(cfg, "index.html", "Start", index, False), encoding="utf-8")

    cards = []
    for i, case in enumerate(cases):
        facts = "\n      ".join(f"<li>{esc(f)}</li>" for f in case["facts"])
        label = f'<span class="tag">Label: {esc(case["label"])}</span>' if case["label"] else ""
        missing = f'<p class="open">Not known: {esc(case["missing"])}</p>' if case["missing"] else ""
        cards.append(f"""<section class="card {CASE_CLASSES[i]}">
    <div class="label">{esc(case["head"])}</div>
    <h3>{esc(case["name"])}</h3>
    {label}
    <ul>
      {facts}
    </ul>
    {missing}
  </section>""")
    use_cases = f"""<main>
  <h1>Cases</h1>
  <p class="lead">The supplied facts per service. Everything on the result pages is worked out from these.</p>
  <div class="cards">
  {"".join(cards)}
  </div>
</main>"""
    (out / "use-cases.html").write_text(
        page(cfg, "use-cases.html", "Cases", use_cases, False), encoding="utf-8")

    for href, label, what in RESULT_PAGES:
        big = "Filled by the agent" if static else "Waiting for the agent"
        note = ("An agent fills this page with the hosting planning skills."
                if static else "This page is filled by the agent. It reloads every five seconds until then.")
        body = f"""<main>
  <h1>{label}</h1>
  <p class="lead">{what}</p>
  <div class="waiting" id="waiting">
    <div class="big">{big}</div>
    <p>{note}</p>
  </div>
</main>"""
        (out / href).write_text(page(cfg, href, label, body, refresh=not static), encoding="utf-8")

    print(f"built {out} with {len(cases)} case(s), {'static' if static else 'live'} mode")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", type=Path, required=True, help="directory with case-*.md files")
    ap.add_argument("--out", type=Path, required=True, help="output directory (replaced)")
    ap.add_argument("--config", type=Path, help="optional app.json")
    ap.add_argument("--static", action="store_true",
                    help="no auto-reload on the empty result pages, for publishing a start state")
    args = ap.parse_args()
    build(args.cases.resolve(), args.out.resolve(), load_config(args.config), args.static)


if __name__ == "__main__":
    main()
