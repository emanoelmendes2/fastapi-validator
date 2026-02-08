"""Regras de versionamento para APIs RESTful."""

import re

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


class VersionInPathRule(Rule):
    """Verifica se a API tem versionamento na URL."""

    rule_id = "versioning-path"
    description = "API deve ter versionamento na URL (ex: /v1/, /api/v1/)"
    severity = Severity.WARNING

    VERSION_PATTERN = re.compile(r"^/v\d+/|^/api/v\d+/")

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []
        routes_without_version = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not self.VERSION_PATTERN.match(route.path):
                routes_without_version.append(route.path)

        if routes_without_version and len(routes_without_version) > 0:
            all_without = all(
                not self.VERSION_PATTERN.match(r.path)
                for r in app.routes
                if isinstance(r, APIRoute)
            )

            if all_without:
                issues.append(
                    self.create_issue(
                        message="API não possui versionamento na URL.",
                        suggestion="Adicionar prefixo de versão (ex: /v1/users, /api/v2/products)",
                    )
                )

        return issues


class ConsistentVersioningRule(Rule):
    """Verifica se o versionamento é consistente em todas as rotas."""

    rule_id = "versioning-consistent"
    description = "Versionamento deve ser consistente em todas as rotas"
    severity = Severity.WARNING

    VERSION_PATTERN = re.compile(r"^/(v\d+|api/v\d+)/")

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []
        versions_found: set[str] = set()
        routes_with_version = 0
        routes_without_version = 0

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            match = self.VERSION_PATTERN.match(route.path)
            if match:
                versions_found.add(match.group(1))
                routes_with_version += 1
            else:
                routes_without_version += 1

        if routes_with_version > 0 and routes_without_version > 0:
            issues.append(
                self.create_issue(
                    message="Algumas rotas têm versionamento e outras não.",
                    suggestion="Manter consistência: todas as rotas devem ter o mesmo padrão de versão",
                )
            )

        if len(versions_found) > 1:
            issues.append(
                self.create_issue(
                    message=f"Múltiplas versões encontradas: {sorted(versions_found)}",
                    suggestion="Considere separar versões em aplicações/routers diferentes",
                )
            )

        return issues


class VersioningRules:
    """Coleção de todas as regras de versionamento."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de versionamento."""
        return [
            VersionInPathRule(),
            ConsistentVersioningRule(),
        ]