"""Regras de segurança para APIs RESTful."""

import inspect

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.security import (
    APIKeyHeader,
    APIKeyQuery,
    HTTPBasic,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from ..base import Issue, Rule, Severity


class AuthenticationRequiredRule(Rule):
    """Verifica se endpoints sensíveis têm autenticação."""

    rule_id = "security-auth-required"
    description = "Endpoints que modificam dados devem ter autenticação"
    severity = Severity.WARNING

    SECURITY_CLASSES = (
        HTTPBearer,
        HTTPBasic,
        OAuth2PasswordBearer,
        APIKeyHeader,
        APIKeyQuery,
    )

    EXEMPT_PATHS = {
        "/login", "/auth", "/register", "/signup",
        "/token", "/refresh", "/health", "/healthcheck",
        "/docs", "/redoc", "/openapi.json",
    }

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or set()
            modifying_methods = {"POST", "PUT", "PATCH", "DELETE"}

            if not methods.intersection(modifying_methods):
                continue

            path_lower = route.path.lower()
            if any(exempt in path_lower for exempt in self.EXEMPT_PATHS):
                continue

            has_security = self._has_security_dependency(route)

            if not has_security:
                issues.append(
                    self.create_issue(
                        message="Endpoint que modifica dados não tem autenticação.",
                        path=route.path,
                        method=", ".join(sorted(methods.intersection(modifying_methods))),
                        suggestion="Adicionar dependência de autenticação (HTTPBearer, OAuth2, etc.)",
                    )
                )

        return issues

    def _has_security_dependency(self, route: APIRoute) -> bool:
        """Verifica se a rota tem dependência de segurança."""
        for dependency in route.dependencies:
            dep_callable = dependency.dependency
            if dep_callable is None:
                continue

            if isinstance(dep_callable, self.SECURITY_CLASSES):
                return True

            if hasattr(dep_callable, "__self__"):
                if isinstance(dep_callable.__self__, self.SECURITY_CLASSES):
                    return True

        sig = inspect.signature(route.endpoint)
        for param in sig.parameters.values():
            if param.default is not inspect.Parameter.empty:
                if isinstance(param.default, self.SECURITY_CLASSES):
                    return True

        return False


class SensitiveDataInUrlRule(Rule):
    """Verifica se dados sensíveis não estão na URL."""

    rule_id = "security-sensitive-url"
    description = "Dados sensíveis não devem estar em parâmetros de URL"
    severity = Severity.ERROR

    SENSITIVE_PARAMS = {
        "password", "senha", "secret", "token", "api_key",
        "apikey", "api-key", "authorization", "auth",
        "credit_card", "creditcard", "card_number", "cvv",
        "ssn", "cpf", "cnpj", "private_key", "privatekey",
    }

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            path_params = self._extract_path_params(route.path)
            for param in path_params:
                if param.lower() in self.SENSITIVE_PARAMS:
                    issues.append(
                        self.create_issue(
                            message=f"Parâmetro sensível '{param}' está na URL.",
                            path=route.path,
                            suggestion="Mover dados sensíveis para o body da requisição ou headers",
                        )
                    )

            sig = inspect.signature(route.endpoint)
            for param_name, param in sig.parameters.items():
                if param_name.lower() in self.SENSITIVE_PARAMS:
                    from fastapi import Query
                    if param.default is not inspect.Parameter.empty:
                        if isinstance(param.default, Query):
                            issues.append(
                                self.create_issue(
                                    message=f"Parâmetro sensível '{param_name}' está como query parameter.",
                                    path=route.path,
                                    suggestion="Mover dados sensíveis para o body ou headers",
                                )
                            )

        return issues

    def _extract_path_params(self, path: str) -> list[str]:
        """Extrai nomes de parâmetros de path."""
        import re
        return re.findall(r"\{(\w+)\}", path)


class HttpsOnlyRule(Rule):
    """Verifica se a API está configurada para HTTPS."""

    rule_id = "security-https"
    description = "API deve usar HTTPS em produção"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        if hasattr(app, "servers") and app.servers:
            for server in app.servers:
                url = server.get("url", "")
                if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
                    issues.append(
                        self.create_issue(
                            message=f"Servidor configurado com HTTP: {url}",
                            suggestion="Usar HTTPS para servidores de produção",
                        )
                    )

        return issues


class DeprecatedEndpointRule(Rule):
    """Verifica se endpoints deprecados estão documentados."""

    rule_id = "security-deprecated-docs"
    description = "Endpoints deprecados devem ter documentação de migração"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if route.deprecated:
                has_migration_docs = False
                description = route.description or ""
                docstring = route.endpoint.__doc__ or ""

                migration_keywords = ["migrat", "replac", "use instead", "deprecated", "substituí"]
                full_text = (description + docstring).lower()

                for keyword in migration_keywords:
                    if keyword in full_text:
                        has_migration_docs = True
                        break

                if not has_migration_docs:
                    issues.append(
                        self.create_issue(
                            message="Endpoint deprecado sem documentação de migração.",
                            path=route.path,
                            method=", ".join(sorted(route.methods or set())),
                            suggestion="Adicionar descrição indicando qual endpoint usar no lugar",
                        )
                    )

        return issues


class SecurityRules:
    """Coleção de todas as regras de segurança."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de segurança."""
        return [
            AuthenticationRequiredRule(),
            SensitiveDataInUrlRule(),
            HttpsOnlyRule(),
            DeprecatedEndpointRule(),
        ]