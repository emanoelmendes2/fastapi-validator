"""Regras de nomenclatura de URLs para APIs RESTful."""

import re

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


class KebabCaseRule(Rule):
    """Verifica se URLs usam kebab-case."""

    rule_id = "naming-kebab-case"
    description = "URLs devem usar kebab-case para separar palavras"
    severity = Severity.WARNING

    KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            segments = [
                seg for seg in route.path.split("/")
                if seg and not seg.startswith("{")
            ]

            for segment in segments:
                if "_" in segment:
                    issues.append(
                        self.create_issue(
                            message=f"Segmento '{segment}' usa underscore. Use kebab-case.",
                            path=route.path,
                            suggestion=f"Renomear para '{segment.replace('_', '-')}'",
                        )
                    )
                elif segment != segment.lower() and not segment.startswith("{"):
                    issues.append(
                        self.create_issue(
                            message=f"Segmento '{segment}' contém letras maiúsculas.",
                            path=route.path,
                            suggestion=f"Renomear para '{segment.lower()}'",
                        )
                    )

        return issues


class PluralResourcesRule(Rule):
    """Verifica se recursos usam nomes no plural."""

    rule_id = "naming-plural-resources"
    description = "Recursos devem usar nomes no plural"
    severity = Severity.WARNING

    COMMON_SINGULAR = {
        "user", "item", "product", "order", "customer", "account",
        "post", "comment", "category", "tag", "file", "image",
        "message", "notification", "setting", "profile", "address",
        "payment", "invoice", "task", "project", "team", "member",
        "role", "permission", "session", "token", "log", "event",
        "report", "document", "article", "page", "menu", "option",
    }

    IRREGULAR_PLURALS = {
        "person": "people",
        "child": "children",
        "man": "men",
        "woman": "women",
        "foot": "feet",
        "tooth": "teeth",
        "goose": "geese",
        "mouse": "mice",
    }

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            segments = [
                seg for seg in route.path.split("/")
                if seg and not seg.startswith("{")
            ]

            if not segments:
                continue

            resource = segments[-1].lower().replace("-", "_")

            if resource in self.COMMON_SINGULAR:
                suggested = self.IRREGULAR_PLURALS.get(resource, resource + "s")
                issues.append(
                    self.create_issue(
                        message=f"Recurso '{resource}' parece estar no singular.",
                        path=route.path,
                        suggestion=f"Considere usar '{suggested}' (plural)",
                    )
                )

        return issues


class NoVerbsRule(Rule):
    """Verifica se URLs não contêm verbos."""

    rule_id = "naming-no-verbs"
    description = "URLs não devem conter verbos de ação"
    severity = Severity.WARNING

    COMMON_VERBS = {
        "get", "create", "update", "delete", "remove", "add",
        "fetch", "retrieve", "list", "find", "search", "save",
        "edit", "modify", "set", "put", "post", "patch",
        "upload", "download", "send", "receive", "process",
        "validate", "verify", "check", "submit", "cancel",
        "approve", "reject", "activate", "deactivate", "enable",
        "disable", "start", "stop", "run", "execute", "perform",
    }

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            segments = [
                seg.lower().replace("-", "_")
                for seg in route.path.split("/")
                if seg and not seg.startswith("{")
            ]

            for segment in segments:
                words = segment.split("_")
                for word in words:
                    if word in self.COMMON_VERBS:
                        issues.append(
                            self.create_issue(
                                message=f"URL contém verbo '{word}'. Use métodos HTTP para ações.",
                                path=route.path,
                                suggestion="O método HTTP (GET, POST, PUT, DELETE) deve indicar a ação",
                            )
                        )
                        break

        return issues


class LowercaseRule(Rule):
    """Verifica se URLs são lowercase."""

    rule_id = "naming-lowercase"
    description = "URLs devem ser totalmente em minúsculas"
    severity = Severity.ERROR

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            segments = [
                seg for seg in route.path.split("/")
                if seg and not seg.startswith("{")
            ]

            for segment in segments:
                if segment != segment.lower():
                    issues.append(
                        self.create_issue(
                            message=f"Segmento '{segment}' contém letras maiúsculas.",
                            path=route.path,
                            suggestion=f"Renomear para '{segment.lower()}'",
                        )
                    )

        return issues


class NoTrailingSlashRule(Rule):
    """Verifica se URLs não terminam com barra."""

    rule_id = "naming-no-trailing-slash"
    description = "URLs não devem terminar com barra"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if route.path != "/" and route.path.endswith("/"):
                issues.append(
                    self.create_issue(
                        message="URL termina com barra.",
                        path=route.path,
                        suggestion=f"Remover barra final: '{route.path.rstrip('/')}'",
                    )
                )

        return issues


class NamingRules:
    """Coleção de todas as regras de nomenclatura."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de nomenclatura."""
        return [
            KebabCaseRule(),
            PluralResourcesRule(),
            NoVerbsRule(),
            LowercaseRule(),
            NoTrailingSlashRule(),
        ]