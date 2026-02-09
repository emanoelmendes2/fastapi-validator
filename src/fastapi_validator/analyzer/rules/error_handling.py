"""Regras de error handling para APIs RESTful."""

import inspect

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


class ErrorResponseDocumentedRule(Rule):
    """Verifica se endpoints documentam respostas de erro."""

    rule_id = "error-response-documented"
    description = "Endpoints devem documentar respostas de erro (4xx/5xx)"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            responses = route.responses or {}
            has_error_response = any(
                isinstance(code, int) and code >= 400
                for code in responses
            )

            if not has_error_response:
                issues.append(
                    self.create_issue(
                        message="Endpoint não documenta respostas de erro (4xx/5xx).",
                        path=route.path,
                        method=", ".join(sorted(route.methods or set())),
                        suggestion="Adicionar responses com códigos 4xx/5xx na definição do endpoint",
                    )
                )

        return issues


class ErrorConsistentFormatRule(Rule):
    """Verifica se respostas de erro seguem formato consistente."""

    rule_id = "error-consistent-format"
    description = "Respostas de erro devem seguir formato consistente"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []
        error_model_fields: set[tuple[str, ...]] | None = None

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            responses = route.responses or {}
            for code, response_info in responses.items():
                if not isinstance(code, int) or code < 400:
                    continue

                model = None
                if isinstance(response_info, dict):
                    model = response_info.get("model")

                if model is None:
                    continue

                if hasattr(model, "model_fields"):
                    fields = tuple(sorted(model.model_fields.keys()))
                elif hasattr(model, "__fields__"):
                    fields = tuple(sorted(model.__fields__.keys()))
                else:
                    continue

                if error_model_fields is None:
                    error_model_fields = {fields}
                else:
                    if fields not in error_model_fields:
                        error_model_fields.add(fields)
                        issues.append(
                            self.create_issue(
                                message=(
                                    f"Modelo de erro com campos {list(fields)} difere "
                                    f"dos modelos anteriores."
                                ),
                                path=route.path,
                                method=", ".join(sorted(route.methods or set())),
                                suggestion="Usar um modelo de erro padronizado para todas as respostas de erro",
                            )
                        )

        return issues


class ErrorExceptionHandlersRule(Rule):
    """Verifica se a aplicação tem exception handlers registrados."""

    rule_id = "error-exception-handlers"
    description = "Aplicação deve ter exception handlers registrados"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        exception_handlers = getattr(app, "exception_handlers", {})
        if not exception_handlers:
            issues.append(
                self.create_issue(
                    message="Aplicação não tem exception handlers registrados.",
                    suggestion="Registrar handlers para exceções comuns (HTTPException, ValidationError, Exception)",
                )
            )

        return issues


class ErrorHTTPExceptionUsageRule(Rule):
    """Verifica se endpoints usam HTTPException para erros."""

    rule_id = "error-http-exception-usage"
    description = "Endpoints devem usar HTTPException para retornar erros"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            try:
                source = inspect.getsource(route.endpoint)
            except (OSError, TypeError):
                continue

            has_raise = "raise" in source
            has_http_exception = "HTTPException" in source

            if not has_raise and not has_http_exception:
                methods = route.methods or set()
                modifying_methods = {"POST", "PUT", "PATCH", "DELETE"}
                if methods.intersection(modifying_methods):
                    issues.append(
                        self.create_issue(
                            message="Endpoint não usa HTTPException para tratamento de erros.",
                            path=route.path,
                            method=", ".join(sorted(methods)),
                            suggestion="Usar raise HTTPException(status_code=4xx, detail='...') para erros",
                        )
                    )

        return issues


class ErrorHandlingRules:
    """Coleção de todas as regras de error handling."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de error handling."""
        return [
            ErrorResponseDocumentedRule(),
            ErrorConsistentFormatRule(),
            ErrorExceptionHandlersRule(),
            ErrorHTTPExceptionUsageRule(),
        ]
