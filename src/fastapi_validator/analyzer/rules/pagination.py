"""Regras de paginação para APIs RESTful."""

import inspect
from typing import get_args, get_origin

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


class ListEndpointPaginationRule(Rule):
    """Verifica se endpoints que retornam listas têm paginação."""

    rule_id = "pagination-list-endpoints"
    description = "Endpoints que retornam listas devem suportar paginação"
    severity = Severity.WARNING

    PAGINATION_PARAMS = {"page", "limit", "offset", "skip", "take", "per_page", "page_size", "size"}

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or set()
            if "GET" not in methods:
                continue

            if not self._returns_list(route):
                continue

            if "{" in route.path:
                continue

            has_pagination = self._has_pagination_params(route)

            if not has_pagination:
                issues.append(
                    self.create_issue(
                        message="Endpoint que retorna lista não tem parâmetros de paginação.",
                        path=route.path,
                        method="GET",
                        suggestion="Adicionar parâmetros: page, limit (ou offset, skip)",
                    )
                )

        return issues

    def _returns_list(self, route: APIRoute) -> bool:
        """Verifica se o endpoint retorna uma lista."""
        if route.response_model:
            origin = get_origin(route.response_model)
            if origin is list:
                return True

        sig = inspect.signature(route.endpoint)
        return_annotation = sig.return_annotation
        if return_annotation is not inspect.Parameter.empty:
            origin = get_origin(return_annotation)
            if origin is list:
                return True

        return False

    def _has_pagination_params(self, route: APIRoute) -> bool:
        """Verifica se o endpoint tem parâmetros de paginação."""
        sig = inspect.signature(route.endpoint)
        param_names = {p.lower() for p in sig.parameters.keys()}
        return bool(param_names.intersection(self.PAGINATION_PARAMS))


class PaginationConsistencyRule(Rule):
    """Verifica se a paginação é consistente em toda a API."""

    rule_id = "pagination-consistency"
    description = "Parâmetros de paginação devem ser consistentes em toda a API"
    severity = Severity.INFO

    PAGINATION_STYLES = {
        "page_limit": {"page", "limit"},
        "page_size": {"page", "size"},
        "page_per_page": {"page", "per_page"},
        "offset_limit": {"offset", "limit"},
        "skip_take": {"skip", "take"},
        "skip_limit": {"skip", "limit"},
    }

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []
        styles_found: dict[str, list[str]] = {}

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            sig = inspect.signature(route.endpoint)
            param_names = {p.lower() for p in sig.parameters.keys()}

            for style_name, style_params in self.PAGINATION_STYLES.items():
                if style_params.issubset(param_names):
                    if style_name not in styles_found:
                        styles_found[style_name] = []
                    styles_found[style_name].append(route.path)
                    break

        if len(styles_found) > 1:
            styles_list = ", ".join(styles_found.keys())
            issues.append(
                self.create_issue(
                    message=f"Múltiplos estilos de paginação encontrados: {styles_list}",
                    suggestion="Padronizar para um único estilo de paginação (ex: page + limit)",
                )
            )

        return issues


class PaginationDefaultsRule(Rule):
    """Verifica se parâmetros de paginação têm valores padrão."""

    rule_id = "pagination-defaults"
    description = "Parâmetros de paginação devem ter valores padrão"
    severity = Severity.INFO

    PAGINATION_PARAMS = {"page", "limit", "offset", "skip", "take", "per_page", "page_size", "size"}

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            sig = inspect.signature(route.endpoint)

            for param_name, param in sig.parameters.items():
                if param_name.lower() not in self.PAGINATION_PARAMS:
                    continue

                if param.default is inspect.Parameter.empty:
                    issues.append(
                        self.create_issue(
                            message=f"Parâmetro de paginação '{param_name}' não tem valor padrão.",
                            path=route.path,
                            suggestion=f"Adicionar valor padrão (ex: {param_name}: int = 1)",
                        )
                    )

        return issues


class PaginationMaxLimitRule(Rule):
    """Verifica se há limite máximo para paginação."""

    rule_id = "pagination-max-limit"
    description = "Paginação deve ter um limite máximo para evitar sobrecarga"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            sig = inspect.signature(route.endpoint)

            for param_name, param in sig.parameters.items():
                if param_name.lower() not in {"limit", "per_page", "page_size", "size", "take"}:
                    continue

                has_max = False

                if param.default is not inspect.Parameter.empty:
                    default = param.default
                    # Query() retorna FieldInfo, verificamos atributos diretamente
                    if hasattr(default, "le") and default.le is not None:
                        has_max = True
                    if hasattr(default, "lt") and default.lt is not None:
                        has_max = True

                if not has_max:
                    issues.append(
                        self.create_issue(
                            message=f"Parâmetro '{param_name}' não tem limite máximo.",
                            path=route.path,
                            suggestion=f"Adicionar limite máximo: {param_name}: int = Query(default=10, le=100)",
                        )
                    )

        return issues


class PaginationRules:
    """Coleção de todas as regras de paginação."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de paginação."""
        return [
            ListEndpointPaginationRule(),
            PaginationConsistencyRule(),
            PaginationDefaultsRule(),
            PaginationMaxLimitRule(),
        ]