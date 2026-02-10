"""FastAPI Validator - Uma biblioteca de validação para APIs FastAPI."""

from .analyzer import (
    AnalysisMetrics,
    AnalysisReport,
    APIAnalyzer,
    APIScore,
    # Scoring
    APIScorer,
    # Auto-fix
    AutoFixer,
    AutoFixReport,
    # Breaking Changes
    BreakingChangesDetector,
    BreakingChangesReport,
    CodeSuggestion,
    DependencyAnalysisReport,
    # Dependencies
    DependencyAnalyzer,
    Grade,
    Issue,
    Rule,
    Severity,
)
from .baseline import BaselineComparison
from .config import ValidatorConfig, load_config
from .decorators import validate_request, validate_response
from .exceptions import ValidationError, ValidatorException
from .middleware import ValidationMiddleware
from .openapi_analyzer import OpenAPIAnalyzer
from .validators import (
    CNPJValidator,
    CPFValidator,
    EmailValidator,
    NumberValidator,
    StringValidator,
    Validator,
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
    "AnalysisMetrics",
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
    # OpenAPI Analyzer
    "OpenAPIAnalyzer",
    # Baseline
    "BaselineComparison",
]
