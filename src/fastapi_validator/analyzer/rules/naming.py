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
                            message=(
                                f"Segmento '{segment}' usa "
                                f"underscore. Use kebab-case."
                            ),
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

    # Verbos agrupados por categoria para sugestões específicas
    RETRIEVAL_VERBS = {
        "get", "fetch", "retrieve", "download",
        "find", "search", "list",
    }
    CREATION_VERBS = {"create", "add", "save"}
    MUTATION_VERBS = {
        "update", "edit", "modify",
        "set", "put", "post", "patch",
    }
    DELETION_VERBS = {"delete", "remove"}
    STATE_VERBS = {
        "activate", "deactivate", "enable", "disable",
        "start", "stop", "cancel", "approve", "reject",
    }
    PROCESSING_VERBS = {
        "process", "validate", "verify", "check",
        "submit", "run", "execute", "perform",
    }
    TRANSFER_VERBS = {"upload", "send", "receive"}

    VERB_CATEGORIES = {
        "retrieval": RETRIEVAL_VERBS,
        "creation": CREATION_VERBS,
        "mutation": MUTATION_VERBS,
        "deletion": DELETION_VERBS,
        "state": STATE_VERBS,
        "processing": PROCESSING_VERBS,
        "transfer": TRANSFER_VERBS,
    }

    CATEGORY_HINTS = {
        "retrieval": (
            "O método GET já indica busca/obtenção. "
            "Ex: GET /recursos/{id}/arquivo em vez de "
            "GET /recursos/download/{id}"
        ),
        "creation": (
            "O método POST já indica criação. "
            "Ex: POST /recursos em vez de "
            "POST /recursos/create"
        ),
        "mutation": (
            "Os métodos PUT/PATCH já indicam alteração. "
            "Ex: PUT /recursos/{id} em vez de "
            "PUT /recursos/update/{id}"
        ),
        "deletion": (
            "O método DELETE já indica remoção. "
            "Ex: DELETE /recursos/{id} em vez de "
            "POST /recursos/delete/{id}"
        ),
        "state": (
            "Considere usar PATCH com o estado no body. "
            "Ex: PATCH /recursos/{id} com "
            "{\"active\": true} em vez de "
            "POST /recursos/{id}/activate"
        ),
        "processing": (
            "Verbos de processamento às vezes são "
            "necessários. Se não houver alternativa, "
            "considere usar um substantivo: "
            "/validations em vez de /validate"
        ),
        "transfer": (
            "O método HTTP já indica a direção. "
            "Ex: POST /recursos/{id}/arquivos "
            "em vez de POST /recursos/upload"
        ),
    }

    # Severidade mais branda para verbos comuns/aceitáveis
    INFO_CATEGORIES = {"state", "processing"}

    def _get_category(self, word: str) -> str | None:
        """Retorna a categoria de um verbo."""
        for category, verbs in self.VERB_CATEGORIES.items():
            if word in verbs:
                return category
        return None

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
                    category = self._get_category(word)
                    if category is None:
                        continue

                    severity = (
                        Severity.INFO
                        if category in self.INFO_CATEGORIES
                        else Severity.WARNING
                    )

                    hint = self.CATEGORY_HINTS[category]

                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            message=(
                                f"URL contém o verbo '{word}'. "
                                f"Em REST, a ação deve ser "
                                f"indicada pelo método HTTP, "
                                f"não pela URL."
                            ),
                            severity=severity,
                            path=route.path,
                            suggestion=hint,
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
