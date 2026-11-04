# Implementation Plan

Each phase ends with something usable and testable. Later phases reuse earlier ones; nothing is thrown away.

## Phase 0 — Foundations (no LLM)

Goal: encode the team's expertise and prove the logic works.

1. **Repository and conventions** — this repo; branch protection on `main`; PR review by one teammate for any rulebook change.
2. **Design-state schema** (`backend/src/expdesign/schema.py`) — shared core fields (project, organism, samples, conditions, replicates, batches, sequencing, budget) plus an RNA-seq module.
3. **Rulebook v0.1** (`knowledge/`) — YAML rules, each with `when`, `recommend`, `severity`, `rationale`, `source`.
   - ENCODE standards as the QC floor (see `docs/ENCODE_REFERENCES.md`).
   - Team rules on top where ENCODE is silent or targets reference-data production rather than differential testing (e.g. replicates for DE).
4. **Rules engine** — evaluates rules against a design state and returns recommendations, warnings, and missing required fields.
5. **Golden scenarios** (`tests/scenarios/`) — 6 to start, growing to 20–30:
   1. Cell-line drug treatment, 2 lines × 2 doses × 2 timepoints
   2. Whole-blood patient cohort, pre/post treatment (PAXgene vs EDTA)
   3. FFPE tumor archive
   4. Degron time course with expected global transcriptional change (spike-ins)
   5. Sorted PBMC subsets, low input
   6. PDX tumors (mouse read removal)
6. **CI** — GitHub Actions runs `pytest` and validates every YAML file on each PR.

Exit criterion: all golden scenarios pass and two teammates agree with the recommendations.

## Phase 1 — Calculators and outputs

7. **Calculators** — reads per sample → lanes/flow cells; cost from facility table; batch layout generator (balanced, randomized, seeded for reproducibility); replicate/power estimate (DESeq2-style approximation).
8. **Renderer** — Jinja templates → Markdown → DOCX/PDF (pandoc). Outputs: design doc, sample sheet CSV, budget table, rigor paragraph.
9. **Form-based wizard** — a minimal web form over the schema. Fallback path if the LLM is unavailable; also the fastest way for teammates to test rules.

## Phase 2 — Conversational layer

10. **FastAPI backend** — endpoints: `/session`, `/message` (streaming), `/design` (get/patch), `/export`.
11. **LLM integration (NaviGator Toolkit)** — OpenAI-compatible `chat/completions` with function calling:
    - `update_design(fields)` — LLM proposes field values; backend validates against schema
    - `get_next_question()` — backend decides what is missing, LLM phrases it
    - `explain_rule(rule_id)` — LLM explains using the rule's rationale text
    - The LLM never writes numbers into the document directly.
12. **Frontend** — single page: progress stepper, chat (left), live design card (right), review/export screen.
13. **Prompt + extraction tests** — scripted conversations for each golden scenario; assert the final design state matches expectations.

## Phase 3 — Internal alpha → closed beta

14. **Deploy on PubApps** (container, assigned port, UF-authenticated access).
15. **Internal alpha** — team runs golden scenarios + 10 past real projects; compare tool designs to what was actually recommended.
16. **Closed beta** — 5–10 Cancer Institute members plan a real upcoming experiment; feedback form; team reviews every design.
17. **Metrics** — completion rate, time to completed design, correction rate by team, satisfaction.

## Phase 4 — Expansion

18. **Assay modules** — ATAC-seq → CUT&RUN/CUT&Tag → scRNA-seq. Each = schema extension + rulebook + golden scenarios.
19. **RAG (optional)** — over ICBR submission docs, team SOPs, kit manuals, curated methods papers, for citations and ad hoc Q&A.
20. **Public launch on the bioinformatics website** + consult-request handoff.

## Later enhancements (post-v1)

- **`vendor` rule source.** Kit/instrument manufacturer guidance (Illumina, 10x Genomics, Takara, etc.)
  is neither facility policy nor peer-reviewed literature. Add `vendor` to the allowed `source` values,
  with kit name + document version in the rule, and re-tag rules that currently cite vendor-derived
  thresholds under `team`. Deferred: vendor specs are kit-specific and change often, so they need a
  versioning/refresh process first.

## Decisions to make early

- [ ] Facility scope: ICBR-specific vs facility-agnostic with an ICBR profile (recommended: agnostic + profile)
- [ ] Rulebook ownership and review process (who approves changes; version in every exported doc)
- [ ] Which NaviGator model(s) — must support function calling / structured output reliably
- [ ] Data classification approved for NaviGator use; confirm no PHI enters the tool
- [ ] Authentication on PubApps (UF Shibboleth/GatorLink vs open access)
