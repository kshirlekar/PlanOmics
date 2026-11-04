"""Generate the workflow overview from the live rulebook.

    python tools/build_workflow.py

Writes:
  docs/WORKFLOW.md    - renders on GitHub (Mermaid diagrams + rule tables)
  docs/workflow.html  - richer page for opening locally in a browser

Each rule is placed at the interview step where all of its trigger (`when`) fields
are known, i.e. the latest step among those fields. Re-run after every rulebook change.
"""
from __future__ import annotations

import html
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
RULE_FILES = [REPO / "knowledge/common/core_rules.yaml", REPO / "knowledge/rnaseq/rules.yaml"]

STEPS = ["Question", "Samples", "Library", "Design", "Batches", "Sequencing", "Budget", "Review"]
STEP_BLURB = {
    "Question": "What is the biological question? Gene-level DE, isoforms, lncRNA; is global transcription expected to shift?",
    "Samples": "Organism, sample source, preservation, RNA quality (RIN, DV200), input amount, sex.",
    "Library": "Library prep, strandedness, globin depletion, spike-ins, UMIs.",
    "Design": "Factors and groups, replicates per group, pairing, perturbation and controls.",
    "Batches": "How samples are split across processing batches; condition must never be confounded with batch.",
    "Sequencing": "Depth, read layout and length. Receives depth recommendations from earlier steps.",
    "Budget": "Cost and timeline from the facility table.",
    "Review": "Design document, exports, and the consult request to the Bioinformatics team.",
}
PLANNED = {
    "Batches": ["Seeded, balanced batch-layout generator"],
    "Sequencing": ["Reads → lanes / flow cells calculator"],
    "Budget": ["Cost calculator (facility table)", "Power / replicate estimate"],
    "Review": ["Renderer: design doc, sample sheet CSV, budget table, rigor paragraph"],
}
SEV_RANK = {"block": 0, "strong": 1, "suggest": 2, "info": 3}
SEV_TEXT = {
    "info": "Context for the researcher; nothing to change.",
    "suggest": "A recommended default; easy to override.",
    "strong": "Strongly recommended for this design; override only with a reason.",
    "block": "Export is blocked until resolved or a consult is requested.",
    "consult": "Routes the design to the Bioinformatics team without blocking.",
}


def step_of_field(path: str) -> int:
    sec, _, name = path.partition(".")
    if sec in ("question", "project"):
        return 0
    if sec == "sample":
        return 1
    if sec == "library":
        return 2
    if sec == "design":
        return 4 if name.startswith("batch") else 3
    if sec == "sequencing":
        return 5
    return 7


def load():
    rules = []
    for f in RULE_FILES:
        doc = yaml.safe_load(f.read_text())
        for r in doc["rules"]:
            r["_file"] = f.relative_to(REPO).as_posix()
            r["_version"] = doc.get("version")
            r["_step"] = max(step_of_field(k) for k in r["when"])
            rules.append(r)
    by_step = {i: [] for i in range(len(STEPS))}
    for r in rules:
        by_step[r["_step"]].append(r)
    for lst in by_step.values():
        lst.sort(key=lambda r: (SEV_RANK[r["severity"]], r["id"]))
    stats = {k: sum(1 for r in rules if r["severity"] == k) for k in SEV_RANK}
    stats["consult"] = sum(1 for r in rules if r.get("consult"))
    stats["rules"] = len(rules)
    stats["scenarios"] = len(list((REPO / "tests/scenarios").glob("*.yaml")))
    versions = sorted({f"{r['_file']} v{r['_version']}" for r in rules})
    return rules, by_step, stats, versions


def fmt_val(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int) and v >= 1_000_000:
        return f"{v // 1_000_000}M"
    return str(v)


def fmt_when(w):
    parts = []
    for k, c in w.items():
        if isinstance(c, dict):
            for op, a in c.items():
                sym = {"lt": "<", "gt": ">", "gte": "≥", "lte": "≤"}.get(op)
                if sym:
                    parts.append(f"{k} {sym} {a}")
                elif op == "in":
                    parts.append(f"{k} ∈ {{{', '.join(map(str, a))}}}")
                elif op == "exists":
                    parts.append(f"{k} {'given' if a else 'not given'}")
        else:
            parts.append(f"{k} = {fmt_val(c)}")
    return " · ".join(parts)


def rationale(r):
    return " ".join(r["rationale"].split())


# ---------------------------------------------------------------- Markdown (GitHub)

MERMAID_TURN = """```mermaid
flowchart LR
  R([Researcher]) -->|answer| X["LLM: extract<br/>free text → field values"]
  X -->|proposed values| S["Schema check<br/>rejects invalid values"]
  S -->|valid values| D[("Design state")]
  D -->|re-evaluate| E["Rules engine<br/>{n} YAML rules"]
  E -->|findings + missing fields| Q["Next question<br/>chosen by the backend"]
  Q -->|field id| P["LLM: phrase<br/>wording + rule rationale"]
  P -->|question| R
  classDef llm stroke-dasharray: 5 5
  class X,P llm
```"""

MERMAID_REVIEW = """```mermaid
flowchart LR
  D[("Design state<br/>+ rule findings")] -->|reads| C["Calculators (planned)<br/>lanes · cost · batches · power"]
  D -->|choices + rationale + source| N["Renderer (planned)<br/>Jinja → Markdown → DOCX/PDF"]
  C -->|numbers| N
  N --> O["Design package (planned)<br/>design doc · sample sheet CSV<br/>budget table · rigor paragraph"]
  D -->|block · conflict · consult| F["Consult flag"]
  F -->|request| T["Bioinformatics team<br/>reviews before export"]
  classDef planned stroke-dasharray: 2 3
  class C,N,O planned
```"""


def md_cell(s: str) -> str:
    return s.replace("|", "\\|")


def build_md(rules, by_step, stats, versions) -> str:
    out = [
        "# How a design moves through PlanOmics",
        "",
        "<!-- GENERATED by tools/build_workflow.py from knowledge/*.yaml. Do not edit by hand; re-run the script. -->",
        "",
        "A researcher answers questions one step at a time. Each answer updates the design state, the rulebook "
        "re-evaluates it, and the backend chooses what to ask next. The LLM only handles wording.",
        "",
        f"**{stats['rules']}** rules · **{stats['scenarios']}** golden scenarios · "
        f"**{stats['block']}** block · **{stats['strong']}** strong · **{stats['suggest']}** suggest · "
        f"**{stats['info']}** info · **{stats['consult']}** request a consult",
        "",
        "## One turn of the interview",
        "",
        MERMAID_TURN.replace("{n}", str(stats["rules"])),
        "",
        "Dashed boxes are the only places the LLM is involved: it turns free text into proposed field values and "
        "phrases a question the backend already picked. Every recommendation and number comes from the rules engine "
        "or a calculator. Power users can edit the design card directly, which skips the extract step.",
        "",
        "## What happens at Review",
        "",
        MERMAID_REVIEW,
        "",
        "The document is rendered from the design state and never written by the LLM. A design goes to the team if "
        "any rule blocks it, two equally strong rules disagree, or a rule asks for a consult. Blocking rules also "
        "stop export until the issue is resolved. Dotted boxes are not built yet.",
        "",
        "## Severity levels",
        "",
        "| Level | Meaning |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in SEV_TEXT.items()],
        "",
        "## Rules at each step",
        "",
        "Each rule is listed at the first step where all of its trigger fields are known. What it recommends may "
        "land in a later step: depth rules triggered by the question fill in Sequencing.",
        "",
        " → ".join(f"[{s}](#{i + 1}-{s.lower()}) ({len(by_step[i])})" for i, s in enumerate(STEPS)),
        "",
    ]
    for i, s in enumerate(STEPS):
        out += [f"### {i + 1}. {s}", "", f"_{STEP_BLURB[s]}_", ""]
        for p in PLANNED.get(s, []):
            out.append(f"- **Planned:** {p}")
        if PLANNED.get(s):
            out.append("")
        lst = by_step[i]
        if not lst:
            out += ["No rules trigger at this step yet.", ""]
            continue
        out += ["| Rule | Severity | Source | When | Recommends | Asks for |", "|---|---|---|---|---|---|"]
        for r in lst:
            sev = f"**{r['severity']}**" + (" + consult" if r.get("consult") else "")
            rec = "<br>".join(f"`{k}` → {fmt_val(v)}" for k, v in (r.get("recommend") or {}).items()) or "—"
            ask = "<br>".join(f"`{a}`" for a in r.get("ask_if_missing") or []) or "—"
            out.append(f"| `{r['id']}` | {sev} | {r['source']} | {md_cell(fmt_when(r['when']))} | {md_cell(rec)} | {ask} |")
        out += ["", "<details><summary>Why does this matter? (rationales)</summary>", ""]
        for r in lst:
            out.append(f"- **`{r['id']}`**: {rationale(r)}")
        out += ["", "</details>", ""]
    out += [
        "---",
        "",
        f"Generated from: {' · '.join(versions)}. Rules marked `encode` follow ENCODE4 QC floors; all other "
        "thresholds are team drafts pending review.",
        "",
    ]
    return "\n".join(out)


# ---------------------------------------------------------------- HTML (local)

def build_html(rules, by_step, stats, versions) -> str:
    e = html.escape

    def rule_row(r):
        rec = r.get("recommend") or {}
        rec_html = "".join(f"<li><code>{e(k)}</code> → <b>{e(fmt_val(v))}</b></li>" for k, v in rec.items())
        ask_html = "".join(f"<li><code>{e(a)}</code></li>" for a in r.get("ask_if_missing") or [])
        flags = f'<span class="pill sev-{r["severity"]}">{r["severity"]}</span>'
        if r.get("consult"):
            flags += '<span class="pill consult">consult</span>'
        flags += f'<span class="src src-{r["source"]}">{r["source"]}</span>'
        body = ""
        if rec_html:
            body += f'<div class="kv"><span class="k">Recommends</span><ul>{rec_html}</ul></div>'
        if ask_html:
            body += f'<div class="kv"><span class="k">Asks for</span><ul>{ask_html}</ul></div>'
        return f"""
      <li class="rule sev-edge-{r['severity']}">
        <div class="rule-head"><code class="rid">{e(r['id'])}</code><span class="flags">{flags}</span></div>
        <div class="when"><span class="k">When</span> <code>{e(fmt_when(r['when']))}</code></div>
        {body}
        <details><summary>Why does this matter?</summary><p>{e(rationale(r))}</p></details>
      </li>"""

    stepper, sections = [], []
    for i, s in enumerate(STEPS):
        n, planned = len(by_step[i]), PLANNED.get(s, [])
        badge = (f'<span class="count">{n} rule{"s" if n != 1 else ""}</span>' if n
                 else '<span class="count muted">no rules yet</span>')
        if planned:
            badge += f'<span class="count planned">{len(planned)} planned</span>'
        stepper.append(f'<li><a href="#step-{s.lower()}"><span class="num">{i + 1}</span>'
                       f'<span class="sname">{s}</span>{badge}</a></li>')
        rows = "".join(rule_row(r) for r in by_step[i])
        plan = "".join(f'<li class="planned-item">{e(p)}<span class="pill planned-pill">planned</span></li>'
                       for p in planned)
        sections.append(f"""
    <section class="step" id="step-{s.lower()}">
      <header class="step-head">
        <span class="num big">{i + 1}</span>
        <div><h3>{s}</h3><p class="blurb">{e(STEP_BLURB[s])}</p></div>
      </header>
      {f'<ul class="planned-list">{plan}</ul>' if plan else ''}
      {'' if rows else '<p class="empty">No rules trigger at this step yet.</p>'}
      <ul class="rules">{rows}</ul>
    </section>""")

    page = (Path(__file__).parent / "workflow_template.html").read_text()
    subs = {
        "STEPPER": "".join(stepper), "SECTIONS": "".join(sections),
        "N_RULES": stats["rules"], "N_SCEN": stats["scenarios"], "N_BLOCK": stats["block"],
        "N_STRONG": stats["strong"], "N_SUGGEST": stats["suggest"], "N_INFO": stats["info"],
        "N_CONSULT": stats["consult"], "VERSIONS": " · ".join(e(v) for v in versions),
    }
    for k, v in subs.items():
        page = page.replace("{{" + k + "}}", str(v))
    # Template = head material (title, fonts, style) followed by <main>; wrap into a full document.
    head, body = page.split("<main", 1)
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<!-- GENERATED by tools/build_workflow.py. Do not edit by hand. -->\n'
            '<style>body{margin:0}[hidden]{display:none!important}</style>\n'
            f'{head.strip()}\n</head>\n<body>\n<main{body.rstrip()}\n</body>\n</html>\n')


def main():
    data = load()
    (REPO / "docs/WORKFLOW.md").write_text(build_md(*data))
    (REPO / "docs/workflow.html").write_text(build_html(*data))
    print(f"{data[2]['rules']} rules, {data[2]['scenarios']} scenarios -> docs/WORKFLOW.md, docs/workflow.html")


if __name__ == "__main__":
    main()
