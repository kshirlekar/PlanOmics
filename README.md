# Omics Design Assistant

A guided experiment-design assistant for UF Health Cancer Institute members, built by the Biostatistics and Computational Biology Shared Resource (bioinformatics team).

Users describe their sequencing experiment in plain language. The assistant asks targeted follow-up questions, applies a versioned, team-reviewed rulebook (anchored to ENCODE data standards where they exist), and produces a design package:

- Experiment design document (rationale and assumptions stated explicitly)
- Facility-ready sample sheet (ICBR or other cores)
- Budget and timeline estimate
- Grant-ready "Rigor & Reproducibility" paragraph
- Flags that route the design to the bioinformatics team for consult

**Status:** Phase 0 (design + rulebook). Bulk RNA-seq first; ATAC-seq, CUT&RUN/CUT&Tag and scRNA-seq planned as modules.

## Core principle

The LLM handles conversation. It does **not** make recommendations or produce numbers.

| Component | Responsible for |
|---|---|
| Design state (`schema.py`) | Single source of truth for a design |
| Rulebook (`knowledge/`) | Every recommendation, with rationale and source |
| Calculators | Arithmetic: depth, lanes, cost, batch layout, power |
| LLM (NaviGator Toolkit) | Extract fields from free text, ask the next question, explain rules |
| Renderer | Builds every output document from the design state |

## Repository layout

```
docs/                      Plan, architecture, infrastructure, ENCODE references
knowledge/
  common/                  Shared rules + ENCODE standards (all assays)
  rnaseq/                  Bulk RNA-seq module rulebook
  facility/                Facility price/requirement tables (example values only)
backend/src/expdesign/     Python package: schema, rules engine (FastAPI app later)
frontend/                  Web UI (Phase 2)
tests/scenarios/           Golden test scenarios with expected recommendations
```

## Quick start (Phase 0)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # runs golden scenarios through the rules engine
```

## Key documents

- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Workflow and rule map](docs/WORKFLOW.md) (generated: `python tools/build_workflow.py`)
- [Infrastructure and credentials](docs/INFRASTRUCTURE.md)
- [ENCODE references and how we use them](docs/ENCODE_REFERENCES.md)

## Data policy

Do not enter PHI or identifiable patient data. The assistant collects experimental design metadata only.
