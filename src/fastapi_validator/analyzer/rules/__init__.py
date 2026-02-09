"""Regras de validação para APIs RESTful."""

from .documentation import DocumentationRules
from .error_handling import ErrorHandlingRules
from .http_methods import HTTPMethodRules
from .naming import NamingRules
from .pagination import PaginationRules
from .response import ResponseRules
from .security import SecurityRules
from .status_codes import StatusCodeRules
from .versioning import VersioningRules

__all__ = [
    "NamingRules",
    "HTTPMethodRules",
    "DocumentationRules",
    "StatusCodeRules",
    "ResponseRules",
    "VersioningRules",
    "SecurityRules",
    "PaginationRules",
    "ErrorHandlingRules",
]