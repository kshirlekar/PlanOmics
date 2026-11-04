"""Omics Design Assistant core package."""
from .rules_engine import evaluate
from .schema import DesignState

__all__ = ["DesignState", "evaluate"]
__version__ = "0.1.0"
