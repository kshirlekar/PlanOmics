"""docs/WORKFLOW.md must match the rulebook. If this fails: python tools/build_workflow.py"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_workflow_doc_up_to_date():
    spec = importlib.util.spec_from_file_location("build_workflow", REPO / "tools/build_workflow.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = mod.build_md(*mod.load())
    current = (REPO / "docs/WORKFLOW.md").read_text()
    assert current == expected, "docs/WORKFLOW.md is stale; run: python tools/build_workflow.py"
