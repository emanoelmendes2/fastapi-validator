"""Analisador de APIs FastAPI para conformidade RESTful."""

from .autofix import (
    AutoFixer,
    AutoFixReport,
    CodeSuggestion,
    format_suggestions_report,
)
from .base import AnalysisMetrics, AnalysisReport, Issue, Rule, Severity
from .breaking_changes import (
    BreakingChangesDetector,
    BreakingChangesReport,
    Change,
    ChangeType,
    format_breaking_changes_report,
)
from .dependencies import (
    DependencyAnalysisReport,
    DependencyAnalyzer,
    format_dependency_report,
)
from .runner import APIAnalyzer
from .scoring import APIScore, APIScorer, Grade, format_score_report

__all__ = [
    # Core
    "APIAnalyzer",
    "AnalysisMetrics",
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
