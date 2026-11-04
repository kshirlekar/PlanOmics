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


@dataclass
class Evaluation:
    findings: list[Finding]
    missing: list[str]

    @property
    def blocked(self) -> bool:
        return any(f.severity == "block" for f in self.findings)

    def by_id(self) -> dict[str, Finding]:
        return {f.rule_id: f for f in self.findings}

    def recommended(self) -> dict[str, Any]:
        """Merged recommendations; higher severity wins on conflict."""
        out: dict[str, tuple[int, Any]] = {}
        for f in self.findings:
            for k, v in f.recommend.items():
                s = SEVERITY_ORDER[f.severity]
                if k not in out or s >= out[k][0]:
                    out[k] = (s, v)
        return {k: v for k, (_, v) in out.items()}


def get_path(data: dict, dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return _MISSING if cur is None else cur


def match(value: Any, cond: Any) -> bool:
    if isinstance(cond, dict):
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
            )
            findings.append(f)
            missing += [p for p in f.ask_if_missing if get_path(data, p) is _MISSING and p not in missing]
    return Evaluation(findings=findings, missing=missing)
