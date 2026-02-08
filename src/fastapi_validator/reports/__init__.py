"""Módulo de relatórios avançados para fastapi-validator."""

from .html import HTMLReporter
from .badges import BadgeGenerator
from .github import GitHubAnnotationsReporter
from .junit import JUnitReporter

__all__ = [
    "HTMLReporter",
    "BadgeGenerator",
    "GitHubAnnotationsReporter",
    "JUnitReporter",
]