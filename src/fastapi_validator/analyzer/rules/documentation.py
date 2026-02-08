"""Regras de documentação para APIs RESTful."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


class SummaryRequiredRule(Rule):
    """Verifica se endpoints têm summary."""

    rule_id = "docs-summary-required"
    description = "Endpoints devem ter summary definido"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not route.summary:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem summary.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar parâmetro summary= ao decorator",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class DescriptionRequiredRule(Rule):
    """Verifica se endpoints têm description."""

    rule_id = "docs-description-required"
    description = "Endpoints devem ter description definida"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            has_description = route.description or (
                route.endpoint.__doc__ and route.endpoint.__doc__.strip()
            )

            if not has_description:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem description.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar docstring à função ou parâmetro description=",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class TagsRequiredRule(Rule):
    """Verifica se endpoints têm tags."""

    rule_id = "docs-tags-required"
    description = "Endpoints devem ter tags para organização"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not route.tags:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem tags.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar parâmetro tags=[...] ao decorator",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class OperationIdRule(Rule):
    """Verifica se endpoints têm operation_id."""

    rule_id = "docs-operation-id"
    description = "Endpoints devem ter operation_id definido"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not route.operation_id:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem operation_id explícito.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar parâmetro operation_id= ao decorator",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class ResponseModelRule(Rule):
    """Verifica se endpoints têm response_model definido."""

    rule_id = "docs-response-model"
    description = "Endpoints devem ter response_model definido"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or set()
            if "DELETE" in methods:
                continue

            if not route.response_model:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem response_model.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar parâmetro response_model= com modelo Pydantic",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class DocumentationRules:
    """Coleção de todas as regras de documentação."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de documentação."""
        return [
            SummaryRequiredRule(),
            DescriptionRequiredRule(),
            TagsRequiredRule(),
            OperationIdRule(),
            ResponseModelRule(),
        ]