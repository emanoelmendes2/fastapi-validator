"""Regras de resposta para APIs RESTful."""

import re

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel

from ..base import Issue, Rule, Severity


class SnakeCaseFieldsRule(Rule):
    """Verifica se campos do response usam snake_case."""

    rule_id = "response-snake-case"
    description = "Campos de resposta devem usar snake_case"
    severity = Severity.WARNING

    SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if not route.response_model:
                continue

            if not isinstance(route.response_model, type):
                continue

            if not issubclass(route.response_model, BaseModel):
                continue

            model_fields = self._get_model_fields(route.response_model)

            for field_name in model_fields:
                if not self.SNAKE_CASE_PATTERN.match(field_name):
                    suggested = self._to_snake_case(field_name)
                    issues.append(
                        self.create_issue(
                            message=f"Campo '{field_name}' não usa snake_case.",
                            path=route.path,
                            method=self._get_methods_str(route),
                            suggestion=f"Renomear para '{suggested}'",
                        )
                    )

        return issues

    def _get_model_fields(self, model: type[BaseModel]) -> list[str]:
        """Obtém os nomes dos campos do modelo."""
        return list(model.model_fields.keys())

    def _to_snake_case(self, name: str) -> str:
        """Converte nome para snake_case."""
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class PydanticResponseModelRule(Rule):
    """Verifica se response models usam Pydantic."""

    rule_id = "response-pydantic-model"
    description = "Response models devem ser modelos Pydantic"
    severity = Severity.INFO

    def check(self, app: FastAPI) -> list[Issue]:
        issues = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or set()
            if "DELETE" in methods:
                continue

            if route.response_model is None:
                continue

            if not isinstance(route.response_model, type):
                issues.append(
                    self.create_issue(
                        message="Response model não é um tipo válido.",
                        path=route.path,
                        method=self._get_methods_str(route),
                        suggestion="Usar um modelo Pydantic como response_model",
                    )
                )
                continue

            if not issubclass(route.response_model, BaseModel):
                if route.response_model not in (dict, list, str, int, float, bool):
                    issues.append(
                        self.create_issue(
                            message=f"Response model '{route.response_model.__name__}' não é Pydantic.",
                            path=route.path,
                            method=self._get_methods_str(route),
                            suggestion="Criar modelo Pydantic para tipagem e documentação",
                        )
                    )

        return issues

    def _get_methods_str(self, route: APIRoute) -> str:
        methods = route.methods or set()
        return ", ".join(sorted(methods))


class ResponseRules:
    """Coleção de todas as regras de resposta."""

    @staticmethod
    def all() -> list[Rule]:
        """Retorna todas as regras de resposta."""
        return [
            SnakeCaseFieldsRule(),
            PydanticResponseModelRule(),
        ]