"""Regras de métodos HTTP para APIs RESTful."""

import inspect

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel

from ..base import Issue, Rule, Severity


class GetNoBodyRule(Rule):
    """Verifica se requisições GET não têm body."""

    rule_id = "http-get-no-body"
    description = "Requisições GET não devem ter request body"
    severity = Severity.ERROR

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if "GET" not in (route.methods or set()):
                continue

            sig = inspect.signature(route.endpoint)
            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue

                annotation = param.annotation
                if annotation is inspect.Parameter.empty:
                    continue

                if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    issues.append(
                        self.create_issue(
                            message=f"GET endpoint tem body parameter '{param_name}'.",
                            path=route.path,
                            method="GET",
                            suggestion="Mover dados para query parameters ou path parameters",
                        )
                    )

        return issues


class PostStatusRule(Rule):
    """Verifica se POST retorna status 201 para criação."""

    rule_id = "http-post-status"
    description = "POST para criação deve retornar status 201"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if "POST" not in (route.methods or set()):
                continue

            if route.status_code == 200 or route.status_code is None:
                path_lower = route.path.lower()
                if not any(
                    word in path_lower
                    for word in ["login", "auth", "search", "query", "filter"]
                ):
                    issues.append(
                        self.create_issue(
                            message="POST endpoint retorna 200. Para criação, use 201.",
                            path=route.path,
                            method="POST",
                            suggestion="Adicionar status_code=201 ao decorator",
                        )
                    )

        return issues


class DeleteStatusRule(Rule):
    """Verifica se DELETE retorna status 204."""

    rule_id = "http-delete-status"
    description = "DELETE deve retornar status 204 (No Content)"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if "DELETE" not in (route.methods or set()):
                continue

            if route.status_code not in (204, None):
                if route.status_code == 200:
                    issues.append(
                        self.create_issue(
                            message="DELETE retorna 200. Considere usar 204 (No Content).",
                            path=route.path,
                            method="DELETE",
                            suggestion="Usar status_code=204 se não houver body na resposta",
                        )
                    )

        return issues


class PutPatchBodyRule(Rule):
    """Verifica se PUT/PATCH têm request body."""

    rule_id = "http-put-patch-body"
    description = "PUT e PATCH devem ter request body"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or set()
            if "PUT" not in methods and "PATCH" not in methods:
                continue

            has_body = False
            sig = inspect.signature(route.endpoint)
            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue

                annotation = param.annotation
                if annotation is inspect.Parameter.empty:
                    continue

                if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    has_body = True
                    break

            if not has_body:
                method = "PUT" if "PUT" in methods else "PATCH"
                issues.append(
                    self.create_issue(
                        message=f"{method} endpoint não tem request body.",
                        path=route.path,
                        method=method,
                        suggestion=f"Adicionar um modelo Pydantic como parâmetro para o body",
                    )
                )

        return issues


class HTTPMethodRules:
    """Coleção de todas as regras de métodos HTTP."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de métodos HTTP."""
        return [
            GetNoBodyRule(),
            PostStatusRule(),
            DeleteStatusRule(),
            PutPatchBodyRule(),
        ]