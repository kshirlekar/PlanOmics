from pathlib import Path

import pytest
import yaml

from expdesign import DesignState, evaluate
from expdesign.rules_engine import match

SCENARIOS = sorted((Path(__file__).parent / "scenarios").glob("*.yaml"))


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
def test_golden_scenario(path):
    spec = yaml.safe_load(path.read_text())
    result = evaluate(DesignState.model_validate(spec["state"]))
    fired = set(result.by_id())
    exp = spec["expect"]
    assert set(exp.get("fires", [])) <= fired, f"missing: {set(exp['fires']) - fired}"
    assert not (set(exp.get("not_fires", [])) & fired)
    rec = result.recommended()
    for k, v in exp.get("recommended", {}).items():
        assert rec.get(k) == v, f"{k}: expected {v}, got {rec.get(k)}"
    assert set(exp.get("missing_includes", [])) <= set(result.missing)
    if "blocked" in exp:
        assert result.blocked == exp["blocked"]
    conflicted = {c.field for c in result.conflicts()}
    assert conflicted == set(exp.get("conflicts", [])), f"conflicts: {conflicted}"
    assert not (conflicted & set(rec)), "conflicted fields must not be silently recommended"
    if "consult_required" in exp:
        assert result.consult_required == exp["consult_required"]


def test_all_rules_well_formed():
    for f in (Path(__file__).parents[1] / "knowledge").rglob("*rules*.yaml"):
        for r in yaml.safe_load(f.read_text())["rules"]:
            assert {"id", "when", "severity", "rationale", "source"} <= set(r), r.get("id")
            assert r["severity"] in {"info", "suggest", "strong", "block"}
            assert r["source"] in {"encode", "team", "literature", "facility"}
            assert isinstance(r.get("consult", False), bool), r["id"]


def test_unknown_operator_raises():
    # A typo such as `ge` must fail loudly, not silently match everything.
    with pytest.raises(ValueError):
        match(5, {"ge": 7})


@pytest.mark.parametrize("field,value", [("dv200", 101), ("rin", 11)])
def test_quality_metrics_range_checked(field, value):
    with pytest.raises(ValueError):
        DesignState.model_validate({"sample": {field: value}})
