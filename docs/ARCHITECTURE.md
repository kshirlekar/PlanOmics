# Architecture

```
User ↔ Frontend (stepper · chat · live design card · review/export)
            │
            ▼
       FastAPI backend
            ├── LLM layer (NaviGator Toolkit, function calling)
            │     • extracts fields from free text → proposes updates
            │     • phrases the next question chosen by the backend
            │     • explains rules using their rationale text
            ├── Design state (Pydantic schema) ← single source of truth
            ├── Rules engine (YAML rulebook: common + assay module + facility)
            ├── Calculators (depth→lanes, cost, batch layout, power)
            └── Renderer (Jinja → Markdown → DOCX/PDF; CSV sample sheet)
```

## Design rules

1. **The document is rendered from the design state, never written by the LLM.**
2. **Every recommendation comes from a rule** that carries a `rationale` and a `source` (ENCODE, paper, or team consensus). Both appear in the exported document.
3. **Numbers come from calculators or tables**, never from the LLM.
4. **Rulebook is versioned**; exported documents state the rulebook version used.
5. **Assays are modules**: shared core schema + per-assay schema extension + per-assay rules + golden scenarios.

## Rule format

```yaml
- id: rnaseq.whole_blood.globin
  when: {sample.sample_type: whole_blood}
  recommend:
    library.globin_depletion: true
  severity: strong            # info | suggest | strong | block
  rationale: >
    Globin transcripts can consume a large fraction of reads in whole blood,
    reducing effective depth for other genes.
  ask_if_missing: [sample.collection_tube]
  source: team
```

`severity: block` means the design cannot be exported without resolving it or requesting a consult.

## Interview order (RNA-seq)

Project context → biological question → sample type and quality → library prep → conditions and replicates → controls and spike-ins → batches and randomization → sequencing → QC and submission → budget/timeline → analysis plan → review/export.
