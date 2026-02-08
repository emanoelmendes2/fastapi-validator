"""Detector de breaking changes entre versões de API."""

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel


class ChangeType(Enum):
    """Tipos de mudanças detectadas."""

    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    DEPRECATED = "deprecated"


class ChangeCategory(Enum):
    """Categorias de mudanças."""

    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_ADDED = "endpoint_added"
    METHOD_REMOVED = "method_removed"
    METHOD_ADDED = "method_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_ADDED_REQUIRED = "parameter_added_required"
    PARAMETER_ADDED_OPTIONAL = "parameter_added_optional"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    RESPONSE_MODEL_CHANGED = "response_model_changed"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    RESPONSE_FIELD_ADDED = "response_field_added"
    STATUS_CODE_CHANGED = "status_code_changed"
    PATH_CHANGED = "path_changed"
    DEPRECATED_ADDED = "deprecated_added"


@dataclass
class Change:
    """Representa uma mudança detectada entre versões."""

    category: ChangeCategory
    change_type: ChangeType
    path: str
    method: str | None = None
    description: str = ""
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result = {
            "category": self.category.value,
            "type": self.change_type.value,
            "path": self.path,
            "description": self.description,
        }
        if self.method:
            result["method"] = self.method
        if self.old_value is not None:
            result["old_value"] = str(self.old_value)
        if self.new_value is not None:
            result["new_value"] = str(self.new_value)
        return result


@dataclass
class BreakingChangesReport:
    """Relatório de breaking changes."""

    changes: list[Change] = field(default_factory=list)
    old_version: str = ""
    new_version: str = ""

    @property
    def breaking_changes(self) -> list[Change]:
        """Retorna apenas breaking changes."""
        return [c for c in self.changes if c.change_type == ChangeType.BREAKING]

    @property
    def compatible_changes(self) -> list[Change]:
        """Retorna mudanças compatíveis."""
        return [c for c in self.changes if c.change_type == ChangeType.COMPATIBLE]

    @property
    def deprecations(self) -> list[Change]:
        """Retorna deprecações."""
        return [c for c in self.changes if c.change_type == ChangeType.DEPRECATED]

    @property
    def has_breaking_changes(self) -> bool:
        """Verifica se há breaking changes."""
        return len(self.breaking_changes) > 0

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "summary": {
                "total_changes": len(self.changes),
                "breaking": len(self.breaking_changes),
                "compatible": len(self.compatible_changes),
                "deprecations": len(self.deprecations),
            },
            "has_breaking_changes": self.has_breaking_changes,
            "breaking_changes": [c.to_dict() for c in self.breaking_changes],
            "compatible_changes": [c.to_dict() for c in self.compatible_changes],
            "deprecations": [c.to_dict() for c in self.deprecations],
        }


class BreakingChangesDetector:
    """
    Detecta breaking changes entre duas versões de uma API FastAPI.

    Breaking changes incluem:
    - Remoção de endpoints
    - Remoção de métodos HTTP
    - Remoção de parâmetros
    - Adição de parâmetros obrigatórios
    - Mudança de tipos de parâmetros
    - Remoção de campos de resposta
    - Mudança de status codes

    Example:
        from fastapi_validator import BreakingChangesDetector

        detector = BreakingChangesDetector()
        report = detector.compare(old_app, new_app)

        if report.has_breaking_changes:
            print("Breaking changes detected!")
            for change in report.breaking_changes:
                print(f"  - {change.description}")
    """

    def __init__(self) -> None:
        """Inicializa o detector."""
        pass

    def _extract_routes_info(self, app: FastAPI) -> dict[str, dict]:
        """Extrai informações das rotas da aplicação."""
        routes_info = {}

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = route.methods or {"GET"}
            for method in methods:
                key = f"{method}:{route.path}"
                routes_info[key] = {
                    "path": route.path,
                    "method": method,
                    "name": route.name,
                    "deprecated": route.deprecated,
                    "status_code": route.status_code,
                    "response_model": route.response_model,
                    "parameters": self._extract_parameters(route),
                    "response_fields": self._extract_response_fields(route),
                }

        return routes_info

    def _extract_parameters(self, route: APIRoute) -> dict[str, dict]:
        """Extrai informações dos parâmetros de um endpoint."""
        params = {}
        sig = inspect.signature(route.endpoint)

        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue

            is_required = param.default is inspect.Parameter.empty
            param_type = param.annotation

            if param_type is inspect.Parameter.empty:
                type_name = "Any"
            elif hasattr(param_type, "__name__"):
                type_name = param_type.__name__
            else:
                type_name = str(param_type)

            params[name] = {
                "required": is_required,
                "type": type_name,
            }

        return params

    def _extract_response_fields(self, route: APIRoute) -> set[str]:
        """Extrai campos do modelo de resposta."""
        if not route.response_model:
            return set()

        if not isinstance(route.response_model, type):
            return set()

        if issubclass(route.response_model, BaseModel):
            return set(route.response_model.model_fields.keys())

        return set()

    def compare(
        self,
        old_app: FastAPI,
        new_app: FastAPI,
        old_version: str = "old",
        new_version: str = "new",
    ) -> BreakingChangesReport:
        """
        Compara duas versões de uma API e detecta mudanças.

        Args:
            old_app: Versão antiga da aplicação
            new_app: Versão nova da aplicação
            old_version: Nome/versão da API antiga
            new_version: Nome/versão da API nova

        Returns:
            Relatório com todas as mudanças detectadas
        """
        old_routes = self._extract_routes_info(old_app)
        new_routes = self._extract_routes_info(new_app)

        changes: list[Change] = []

        for key, old_info in old_routes.items():
            if key not in new_routes:
                changes.append(Change(
                    category=ChangeCategory.ENDPOINT_REMOVED,
                    change_type=ChangeType.BREAKING,
                    path=old_info["path"],
                    method=old_info["method"],
                    description=f"Endpoint {old_info['method']} {old_info['path']} foi removido",
                ))
                continue

            new_info = new_routes[key]

            if old_info["status_code"] != new_info["status_code"]:
                if old_info["status_code"] is not None and new_info["status_code"] is not None:
                    changes.append(Change(
                        category=ChangeCategory.STATUS_CODE_CHANGED,
                        change_type=ChangeType.BREAKING,
                        path=old_info["path"],
                        method=old_info["method"],
                        description=f"Status code mudou de {old_info['status_code']} para {new_info['status_code']}",
                        old_value=old_info["status_code"],
                        new_value=new_info["status_code"],
                    ))

            changes.extend(self._compare_parameters(old_info, new_info))

            changes.extend(self._compare_response_fields(old_info, new_info))

            if not old_info["deprecated"] and new_info["deprecated"]:
                changes.append(Change(
                    category=ChangeCategory.DEPRECATED_ADDED,
                    change_type=ChangeType.DEPRECATED,
                    path=old_info["path"],
                    method=old_info["method"],
                    description=f"Endpoint marcado como deprecated",
                ))

        for key, new_info in new_routes.items():
            if key not in old_routes:
                changes.append(Change(
                    category=ChangeCategory.ENDPOINT_ADDED,
                    change_type=ChangeType.COMPATIBLE,
                    path=new_info["path"],
                    method=new_info["method"],
                    description=f"Novo endpoint {new_info['method']} {new_info['path']} adicionado",
                ))

        return BreakingChangesReport(
            changes=changes,
            old_version=old_version,
            new_version=new_version,
        )

    def _compare_parameters(
        self,
        old_info: dict,
        new_info: dict,
    ) -> list[Change]:
        """Compara parâmetros entre versões."""
        changes = []
        old_params = old_info["parameters"]
        new_params = new_info["parameters"]

        for name, old_param in old_params.items():
            if name not in new_params:
                changes.append(Change(
                    category=ChangeCategory.PARAMETER_REMOVED,
                    change_type=ChangeType.BREAKING,
                    path=old_info["path"],
                    method=old_info["method"],
                    description=f"Parâmetro '{name}' foi removido",
                    old_value=old_param["type"],
                ))
            else:
                new_param = new_params[name]
                if old_param["type"] != new_param["type"]:
                    changes.append(Change(
                        category=ChangeCategory.PARAMETER_TYPE_CHANGED,
                        change_type=ChangeType.BREAKING,
                        path=old_info["path"],
                        method=old_info["method"],
                        description=f"Tipo do parâmetro '{name}' mudou de {old_param['type']} para {new_param['type']}",
                        old_value=old_param["type"],
                        new_value=new_param["type"],
                    ))

        for name, new_param in new_params.items():
            if name not in old_params:
                if new_param["required"]:
                    changes.append(Change(
                        category=ChangeCategory.PARAMETER_ADDED_REQUIRED,
                        change_type=ChangeType.BREAKING,
                        path=old_info["path"],
                        method=old_info["method"],
                        description=f"Novo parâmetro obrigatório '{name}' adicionado",
                        new_value=new_param["type"],
                    ))
                else:
                    changes.append(Change(
                        category=ChangeCategory.PARAMETER_ADDED_OPTIONAL,
                        change_type=ChangeType.COMPATIBLE,
                        path=old_info["path"],
                        method=old_info["method"],
                        description=f"Novo parâmetro opcional '{name}' adicionado",
                        new_value=new_param["type"],
                    ))

        return changes

    def _compare_response_fields(
        self,
        old_info: dict,
        new_info: dict,
    ) -> list[Change]:
        """Compara campos de resposta entre versões."""
        changes = []
        old_fields = old_info["response_fields"]
        new_fields = new_info["response_fields"]

        removed_fields = old_fields - new_fields
        for field in removed_fields:
            changes.append(Change(
                category=ChangeCategory.RESPONSE_FIELD_REMOVED,
                change_type=ChangeType.BREAKING,
                path=old_info["path"],
                method=old_info["method"],
                description=f"Campo de resposta '{field}' foi removido",
                old_value=field,
            ))

        added_fields = new_fields - old_fields
        for field in added_fields:
            changes.append(Change(
                category=ChangeCategory.RESPONSE_FIELD_ADDED,
                change_type=ChangeType.COMPATIBLE,
                path=old_info["path"],
                method=old_info["method"],
                description=f"Novo campo de resposta '{field}' adicionado",
                new_value=field,
            ))

        return changes


def format_breaking_changes_report(
    report: BreakingChangesReport,
    use_colors: bool = True,
) -> str:
    """Formata o relatório de breaking changes para exibição."""
    if use_colors:
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        RESET = "\033[0m"
    else:
        BOLD = GREEN = YELLOW = RED = RESET = ""

    lines = [
        f"\n{BOLD}{'═' * 50}{RESET}",
        f"{BOLD}   BREAKING CHANGES REPORT{RESET}",
        f"{BOLD}{'═' * 50}{RESET}",
        "",
        f"  Total changes: {len(report.changes)}",
        f"  {RED}Breaking:{RESET}    {len(report.breaking_changes)}",
        f"  {GREEN}Compatible:{RESET}  {len(report.compatible_changes)}",
        f"  {YELLOW}Deprecated:{RESET}  {len(report.deprecations)}",
        "",
    ]

    if report.breaking_changes:
        lines.extend([
            f"{BOLD}{'─' * 50}{RESET}",
            f"{RED}{BOLD}  Breaking Changes (require client updates){RESET}",
            f"{BOLD}{'─' * 50}{RESET}",
        ])
        for change in report.breaking_changes:
            lines.append(f"  {RED}✗{RESET} [{change.category.value}]")
            lines.append(f"    {change.description}")
            if change.method:
                lines.append(f"    Path: {change.method} {change.path}")
            lines.append("")

    if report.deprecations:
        lines.extend([
            f"{BOLD}{'─' * 50}{RESET}",
            f"{YELLOW}{BOLD}  Deprecations{RESET}",
            f"{BOLD}{'─' * 50}{RESET}",
        ])
        for change in report.deprecations:
            lines.append(f"  {YELLOW}⚠{RESET} {change.description}")
            if change.method:
                lines.append(f"    Path: {change.method} {change.path}")
            lines.append("")

    if report.compatible_changes:
        lines.extend([
            f"{BOLD}{'─' * 50}{RESET}",
            f"{GREEN}{BOLD}  Compatible Changes{RESET}",
            f"{BOLD}{'─' * 50}{RESET}",
        ])
        for change in report.compatible_changes:
            lines.append(f"  {GREEN}✓{RESET} {change.description}")
            lines.append("")

    lines.append(f"{BOLD}{'═' * 50}{RESET}")

    if report.has_breaking_changes:
        lines.append(f"\n{RED}{BOLD}⚠ API has breaking changes!{RESET}")
        lines.append("  Clients using the old API may break.")
    else:
        lines.append(f"\n{GREEN}{BOLD}✓ No breaking changes detected{RESET}")
        lines.append("  API update is backward compatible.")

    return "\n".join(lines)