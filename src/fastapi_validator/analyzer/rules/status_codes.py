"""Regras de códigos de status HTTP para APIs RESTful."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..base import Issue, Rule, Severity


VALID_STATUS_CODES = {
    100, 101, 102, 103,
    200, 201, 202, 203, 204, 205, 206, 207, 208, 226,
    300, 301, 302, 303, 304, 305, 307, 308,
    400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
    410, 411, 412, 413, 414, 415, 416, 417, 418,
    421, 422, 423, 424, 425, 426, 428, 429, 431, 451,
    500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511,
}


class ValidStatusCodeRule(Rule):
    """Verifica se status codes são válidos."""

    rule_id = "status-valid-codes"
    description = "Status codes devem ser códigos HTTP válidos"
    severity = Severity.ERROR

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if route.status_code and route.status_code not in VALID_STATUS_CODES:
                issues.append(
                    self.create_issue(
                        message=f"Status code {route.status_code} não é válido.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Usar um código HTTP válido (200, 201, 204, 400, 404, etc.)",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class ResponsesDefinedRule(Rule):
    """Verifica se responses estão documentados."""

    rule_id = "status-responses-defined"
    description = "Endpoints devem ter responses documentados"
    severity = Severity.WARNING

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not route.responses:
                issues.append(
                    self.create_issue(
                        message="Endpoint não tem responses adicionais documentados.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Adicionar parâmetro responses={...} para erros comuns",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class ErrorCodesDocumentedRule(Rule):
    """Verifica se códigos de erro estão documentados."""

    rule_id = "status-error-codes"
    description = "Códigos de erro comuns devem estar documentados"
    severity = Severity.INFO

    COMMON_ERROR_CODES = {400, 401, 403, 404, 422, 500}

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            responses = route.responses or {}
            documented_codes = set(responses.keys())

            methods = route.methods or set()
            expected_errors = set()

            if any(m in methods for m in ["GET", "PUT", "PATCH", "DELETE"]):
                expected_errors.add(404)

            if any(m in methods for m in ["POST", "PUT", "PATCH"]):
                expected_errors.add(422)

            missing_errors = expected_errors - documented_codes

            if missing_errors:
                issues.append(
                    self.create_issue(
                        message=f"Códigos de erro não documentados: {sorted(missing_errors)}",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Documentar possíveis erros no parâmetro responses=",
                    )
                )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class StatusCodeRules:
    """Coleção de todas as regras de status codes."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de status codes."""
        return [
            ValidStatusCodeRule(),
            ResponsesDefinedRule(),
            ErrorCodesDocumentedRule(),
        ]