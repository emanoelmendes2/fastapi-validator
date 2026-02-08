"""FastAPI Validator - Uma biblioteca de validação para APIs FastAPI."""

from .validators import (
    Validator,
    StringValidator,
    NumberValidator,
    EmailValidator,
    CPFValidator,
    CNPJValidator,
)
from .decorators import validate_request, validate_response
from .exceptions import ValidationError, ValidatorException
from .middleware import ValidationMiddleware
from .config import ValidatorConfig, load_config
from .analyzer import (
    APIAnalyzer,
    AnalysisReport,
    Issue,
    Rule,
    Severity,
    # Scoring
    APIScorer,
    APIScore,
    Grade,
    # Breaking Changes
    BreakingChangesDetector,
    BreakingChangesReport,
    # Dependencies
    DependencyAnalyzer,
    DependencyAnalysisReport,
    # Auto-fix
    AutoFixer,
    AutoFixReport,
    CodeSuggestion,
)

__version__ = "0.1.0"
__all__ = [
    # Validators
    "Validator",
    "StringValidator",
    "NumberValidator",
    "EmailValidator",
    "CPFValidator",
    "CNPJValidator",
    # Decorators
    "validate_request",
    "validate_response",
    # Exceptions
    "ValidationError",
    "ValidatorException",
    # Middleware
    "ValidationMiddleware",
    # Config
    "ValidatorConfig",
    "load_config",
    # Analyzer - Core
    "APIAnalyzer",
    "AnalysisReport",
    "Issue",
    "Rule",
    "Severity",
    # Analyzer - Scoring
    "APIScorer",
    "APIScore",
    "Grade",
    # Analyzer - Breaking Changes
    "BreakingChangesDetector",
    "BreakingChangesReport",
    # Analyzer - Dependencies
    "DependencyAnalyzer",
    "DependencyAnalysisReport",
    # Analyzer - Auto-fix
    "AutoFixer",
    "AutoFixReport",
    "CodeSuggestion",
]
