"""Deterministic rules engine: evaluates YAML rules against a DesignState."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schema import DesignState

KNOWLEDGE_DIR = Path(__file__).resolve().parents[3] / "knowledge"
ASSAY_DIRS = {"bulk_rnaseq": "rnaseq"}
SEVERITY_ORDER = {"info": 0, "suggest": 1, "strong": 2, "block": 3}
_MISSING = object()


@dataclass
class Finding:
    rule_id: str
    severity: str
    rationale: str
    source: str
    recommend: dict[str, Any]
    ask_if_missing: list[str] = field(default_factory=list)
    consult: bool = False  # rule itself requests a Bioinformatics team consult


@dataclass
class Conflict:
    """Rules of equal (top) severity recommend different values for one field."""
    field: str
    severity: str
    options: dict[str, Any]  # rule_id -> recommended value


@dataclass
class Evaluation:
    findings: list[Finding]
    missing: list[str]

    @property
    def blocked(self) -> bool:
        return any(f.severity == "block" for f in self.findings)

    @property
    def consult_required(self) -> bool:
        """Route to the Bioinformatics team: a blocking rule fired, a rule asks for a
        consult, or rules conflict."""
        return self.blocked or any(f.consult for f in self.findings) or bool(self.conflicts())

    def by_id(self) -> dict[str, Finding]:
        return {f.rule_id: f for f in self.findings}

    def _top_recommendations(self) -> dict[str, tuple[int, dict[str, Any]]]:
        """Per field: the highest severity seen and {rule_id: value} at that severity."""
        top: dict[str, tuple[int, dict[str, Any]]] = {}
        for f in self.findings:
            s = SEVERITY_ORDER[f.severity]
            for k, v in f.recommend.items():
                if k not in top or s > top[k][0]:
                    top[k] = (s, {f.rule_id: v})
                elif s == top[k][0]:
                    top[k][1][f.rule_id] = v
        return top

    def conflicts(self) -> list[Conflict]:
        names = {v: k for k, v in SEVERITY_ORDER.items()}
        return [
            Conflict(field=k, severity=names[s], options=opts)
            for k, (s, opts) in self._top_recommendations().items()
            if len({repr(v) for v in opts.values()}) > 1
        ]

    def recommended(self) -> dict[str, Any]:
        """Merged recommendations. Higher severity wins; equal-severity disagreements
        are never resolved silently: the field is omitted and reported in conflicts()."""
        return {
            k: next(iter(opts.values()))
            for k, (_, opts) in self._top_recommendations().items()
            if len({repr(v) for v in opts.values()}) == 1
        }


def get_path(data: dict, dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return _MISSING if cur is None else cur


OPERATORS = {"exists", "in", "gt", "gte", "lt", "lte"}


def match(value: Any, cond: Any) -> bool:
    if isinstance(cond, dict):
        unknown = set(cond) - OPERATORS
        if unknown:
            raise ValueError(f"Unknown rule operator(s): {sorted(unknown)}")
        for op, arg in cond.items():
            if op == "exists":
                if (value is not _MISSING) != bool(arg):
                    return False
                continue
            if value is _MISSING:
                return False
            if op == "in" and value not in arg:
                return False
            if op == "gt" and not value > arg:
                return False
            if op == "lt" and not value < arg:
                return False
            if op == "gte" and not value >= arg:
                return False
            if op == "lte" and not value <= arg:
                return False
        return True
    return value is not _MISSING and value == cond


def load_rules(assay: str) -> list[dict]:
    files = sorted((KNOWLEDGE_DIR / "common").glob("*rules*.yaml"))
    sub = ASSAY_DIRS.get(assay)
    if sub:
        files += sorted((KNOWLEDGE_DIR / sub).glob("*rules*.yaml"))
    rules: list[dict] = []
    for f in files:
        rules.extend(yaml.safe_load(f.read_text())["rules"])
    ids = [r["id"] for r in rules]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"Duplicate rule ids: {sorted(dupes)}")
    return rules


def evaluate(state: DesignState) -> Evaluation:
    data = state.model_dump()
    findings, missing = [], []
    for rule in load_rules(state.assay):
        if all(match(get_path(data, k), c) for k, c in rule["when"].items()):
            f = Finding(
                rule_id=rule["id"],
                severity=rule["severity"],
                rationale=" ".join(rule["rationale"].split()),
                source=rule["source"],
                recommend=rule.get("recommend") or {},
                ask_if_missing=rule.get("ask_if_missing", []),
                consult=bool(rule.get("consult", False)),
            )
            findings.append(f)
            missing += [p for p in f.ask_if_missing if get_path(data, p) is _MISSING and p not in missing]
    return Evaluation(findings=findings, missing=missing)
