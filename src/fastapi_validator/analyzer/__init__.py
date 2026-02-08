"""Analisador de APIs FastAPI para conformidade RESTful."""

from .base import AnalysisReport, Issue, Rule, Severity
from .runner import APIAnalyzer
from .scoring import APIScorer, APIScore, Grade, format_score_report
from .breaking_changes import (
    BreakingChangesDetector,
    BreakingChangesReport,
    Change,
    ChangeType,
    format_breaking_changes_report,
)
from .dependencies import (
    DependencyAnalyzer,
    DependencyAnalysisReport,
    format_dependency_report,
)
from .autofix import (
    AutoFixer,
    AutoFixReport,
    CodeSuggestion,
    format_suggestions_report,
)

__all__ = [
    # Core
    "APIAnalyzer",
    "AnalysisReport",
    "Issue",
    "Rule",
    "Severity",
    # Scoring
    "APIScorer",
    "APIScore",
    "Grade",
    "format_score_report",
    # Breaking Changes
    "BreakingChangesDetector",
    "BreakingChangesReport",
    "Change",
    "ChangeType",
    "format_breaking_changes_report",
    # Dependencies
    "DependencyAnalyzer",
    "DependencyAnalysisReport",
    "format_dependency_report",
    # Auto-fix
    "AutoFixer",
    "AutoFixReport",
    "CodeSuggestion",
    "format_suggestions_report",
]