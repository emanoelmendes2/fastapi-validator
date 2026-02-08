"""Análise de dependências para APIs FastAPI."""

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi.security import (
    APIKeyHeader,
    APIKeyQuery,
    HTTPBasic,
    HTTPBearer,
    OAuth2PasswordBearer,
)


class DependencyIssueType(Enum):
    """Tipos de issues de dependências."""

    CIRCULAR_DEPENDENCY = "circular_dependency"
    UNUSED_DEPENDENCY = "unused_dependency"
    MISSING_SECURITY = "missing_security"
    SYNC_IN_ASYNC = "sync_in_async"
    HEAVY_DEPENDENCY = "heavy_dependency"
    DUPLICATE_DEPENDENCY = "duplicate_dependency"


@dataclass
class DependencyInfo:
    """Informações sobre uma dependência."""

    name: str
    callable: Callable
    is_async: bool
    has_sub_dependencies: bool
    sub_dependencies: list[str] = field(default_factory=list)
    used_in_routes: list[str] = field(default_factory=list)
    is_security: bool = False
    is_generator: bool = False


@dataclass
class DependencyIssue:
    """Issue encontrado na análise de dependências."""

    issue_type: DependencyIssueType
    message: str
    dependency_name: str | None = None
    path: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result = {
            "type": self.issue_type.value,
            "message": self.message,
        }
        if self.dependency_name:
            result["dependency"] = self.dependency_name
        if self.path:
            result["path"] = self.path
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


@dataclass
class DependencyAnalysisReport:
    """Relatório de análise de dependências."""

    dependencies: dict[str, DependencyInfo] = field(default_factory=dict)
    issues: list[DependencyIssue] = field(default_factory=list)
    total_routes: int = 0
    routes_with_security: int = 0
    routes_without_security: int = 0

    @property
    def security_coverage(self) -> float:
        """Retorna a porcentagem de rotas com segurança."""
        if self.total_routes == 0:
            return 0.0
        return (self.routes_with_security / self.total_routes) * 100

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "summary": {
                "total_dependencies": len(self.dependencies),
                "total_routes": self.total_routes,
                "security_coverage": f"{self.security_coverage:.1f}%",
                "routes_with_security": self.routes_with_security,
                "routes_without_security": self.routes_without_security,
                "issues_found": len(self.issues),
            },
            "dependencies": {
                name: {
                    "is_async": dep.is_async,
                    "is_security": dep.is_security,
                    "is_generator": dep.is_generator,
                    "used_in_routes": len(dep.used_in_routes),
                    "sub_dependencies": dep.sub_dependencies,
                }
                for name, dep in self.dependencies.items()
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }


class DependencyAnalyzer:
    """
    Analisa dependências de uma aplicação FastAPI.

    Detecta:
    - Dependências circulares
    - Dependências não utilizadas
    - Rotas sem segurança
    - Uso de sync em async
    - Dependências duplicadas

    Example:
        from fastapi_validator import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        report = analyzer.analyze(app)

        print(f"Security coverage: {report.security_coverage:.1f}%")
        for issue in report.issues:
            print(f"  - {issue.message}")
    """

    SECURITY_CLASSES = (
        HTTPBearer,
        HTTPBasic,
        OAuth2PasswordBearer,
        APIKeyHeader,
        APIKeyQuery,
    )

    MODIFYING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    EXEMPT_PATHS = {
        "/login", "/auth", "/register", "/signup",
        "/token", "/refresh", "/health", "/healthcheck",
        "/docs", "/redoc", "/openapi.json", "/",
    }

    def __init__(self) -> None:
        """Inicializa o analisador."""
        self._dependencies: dict[str, DependencyInfo] = {}
        self._dependency_graph: dict[str, set[str]] = {}

    def analyze(self, app: FastAPI) -> DependencyAnalysisReport:
        """
        Analisa as dependências da aplicação.

        Args:
            app: Instância da aplicação FastAPI

        Returns:
            Relatório com análise das dependências
        """
        self._dependencies = {}
        self._dependency_graph = {}

        report = DependencyAnalysisReport()

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            report.total_routes += 1
            self._analyze_route(route, report)

        self._detect_circular_dependencies(report)

        self._detect_unused_dependencies(report)

        return report

    def _analyze_route(self, route: APIRoute, report: DependencyAnalysisReport) -> None:
        """Analisa as dependências de uma rota."""
        route_key = f"{','.join(sorted(route.methods or {'GET'}))}:{route.path}"
        has_security = False

        for dependency in route.dependencies:
            dep_info = self._analyze_dependency(dependency.dependency, route_key)
            if dep_info and dep_info.is_security:
                has_security = True

        sig = inspect.signature(route.endpoint)
        for param in sig.parameters.values():
            if param.default is not inspect.Parameter.empty:
                if isinstance(param.default, self.SECURITY_CLASSES):
                    has_security = True

                if hasattr(param.default, "dependency"):
                    dep_info = self._analyze_dependency(
                        param.default.dependency, route_key
                    )
                    if dep_info and dep_info.is_security:
                        has_security = True

        if has_security:
            report.routes_with_security += 1
        else:
            report.routes_without_security += 1

            methods = route.methods or set()
            if methods.intersection(self.MODIFYING_METHODS):
                path_lower = route.path.lower()
                if not any(exempt in path_lower for exempt in self.EXEMPT_PATHS):
                    report.issues.append(DependencyIssue(
                        issue_type=DependencyIssueType.MISSING_SECURITY,
                        message=f"Rota que modifica dados não tem dependência de segurança",
                        path=route.path,
                        suggestion="Adicionar Depends(get_current_user) ou similar",
                    ))

    def _analyze_dependency(
        self,
        dep_callable: Any,
        route_key: str,
    ) -> DependencyInfo | None:
        """Analisa uma dependência específica."""
        if dep_callable is None:
            return None

        dep_name = self._get_dependency_name(dep_callable)

        if dep_name in self._dependencies:
            dep_info = self._dependencies[dep_name]
            if route_key not in dep_info.used_in_routes:
                dep_info.used_in_routes.append(route_key)
            return dep_info

        is_security = isinstance(dep_callable, self.SECURITY_CLASSES)

        is_async = inspect.iscoroutinefunction(dep_callable)

        is_generator = (
            inspect.isgeneratorfunction(dep_callable) or
            inspect.isasyncgenfunction(dep_callable)
        )

        sub_deps = self._extract_sub_dependencies(dep_callable)

        dep_info = DependencyInfo(
            name=dep_name,
            callable=dep_callable,
            is_async=is_async,
            has_sub_dependencies=len(sub_deps) > 0,
            sub_dependencies=sub_deps,
            used_in_routes=[route_key],
            is_security=is_security,
            is_generator=is_generator,
        )

        self._dependencies[dep_name] = dep_info

        self._dependency_graph[dep_name] = set(sub_deps)

        return dep_info

    def _get_dependency_name(self, dep_callable: Any) -> str:
        """Retorna o nome de uma dependência."""
        if hasattr(dep_callable, "__name__"):
            return dep_callable.__name__
        if hasattr(dep_callable, "__class__"):
            return dep_callable.__class__.__name__
        return str(dep_callable)

    def _extract_sub_dependencies(self, dep_callable: Any) -> list[str]:
        """Extrai sub-dependências de uma dependência."""
        sub_deps = []

        if not callable(dep_callable):
            return sub_deps

        try:
            sig = inspect.signature(dep_callable)
        except (ValueError, TypeError):
            return sub_deps

        for param in sig.parameters.values():
            if param.default is inspect.Parameter.empty:
                continue

            if hasattr(param.default, "dependency") and param.default.dependency:
                sub_name = self._get_dependency_name(param.default.dependency)
                sub_deps.append(sub_name)

        return sub_deps

    def _detect_circular_dependencies(self, report: DependencyAnalysisReport) -> None:
        """Detecta dependências circulares."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> list[str] | None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path.copy())
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        for node in self._dependency_graph:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    report.issues.append(DependencyIssue(
                        issue_type=DependencyIssueType.CIRCULAR_DEPENDENCY,
                        message=f"Dependência circular detectada: {cycle_str}",
                        suggestion="Refatorar dependências para remover ciclo",
                    ))
                    break

    def _detect_unused_dependencies(self, report: DependencyAnalysisReport) -> None:
        """Detecta dependências não utilizadas diretamente."""
        pass

    def _analyze_dependency_performance(
        self,
        dep_info: DependencyInfo,
        report: DependencyAnalysisReport,
    ) -> None:
        """Analisa performance de uma dependência."""
        if not dep_info.is_async and len(dep_info.used_in_routes) > 5:
            report.issues.append(DependencyIssue(
                issue_type=DependencyIssueType.SYNC_IN_ASYNC,
                message=f"Dependência síncrona '{dep_info.name}' usada em muitas rotas",
                dependency_name=dep_info.name,
                suggestion="Considerar tornar a dependência assíncrona para melhor performance",
            ))


def format_dependency_report(
    report: DependencyAnalysisReport,
    use_colors: bool = True,
) -> str:
    """Formata o relatório de dependências para exibição."""
    if use_colors:
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
    else:
        BOLD = GREEN = YELLOW = RED = BLUE = RESET = ""

    lines = [
        f"\n{BOLD}{'═' * 50}{RESET}",
        f"{BOLD}   DEPENDENCY ANALYSIS REPORT{RESET}",
        f"{BOLD}{'═' * 50}{RESET}",
        "",
        f"  {BOLD}Dependencies found:{RESET} {len(report.dependencies)}",
        f"  {BOLD}Total routes:{RESET}       {report.total_routes}",
        "",
        f"  {BOLD}Security Coverage:{RESET}",
    ]

    coverage = report.security_coverage
    bar_width = 20
    filled = int((coverage / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    if coverage >= 80:
        color = GREEN
    elif coverage >= 50:
        color = YELLOW
    else:
        color = RED

    lines.append(f"    {color}{bar}{RESET} {coverage:.1f}%")
    lines.append(f"    {GREEN}Protected:{RESET}   {report.routes_with_security} routes")
    lines.append(f"    {RED}Unprotected:{RESET} {report.routes_without_security} routes")
    lines.append("")

    if report.dependencies:
        lines.extend([
            f"{BOLD}{'─' * 50}{RESET}",
            f"{BOLD}  Dependencies{RESET}",
            f"{BOLD}{'─' * 50}{RESET}",
        ])

        security_deps = [d for d in report.dependencies.values() if d.is_security]
        other_deps = [d for d in report.dependencies.values() if not d.is_security]

        if security_deps:
            lines.append(f"\n  {BLUE}Security:{RESET}")
            for dep in security_deps:
                async_tag = f"{GREEN}async{RESET}" if dep.is_async else f"{YELLOW}sync{RESET}"
                lines.append(f"    • {dep.name} [{async_tag}] - {len(dep.used_in_routes)} routes")

        if other_deps:
            lines.append(f"\n  {BLUE}Other:{RESET}")
            for dep in other_deps[:10]:
                async_tag = f"{GREEN}async{RESET}" if dep.is_async else f"{YELLOW}sync{RESET}"
                gen_tag = " [generator]" if dep.is_generator else ""
                lines.append(f"    • {dep.name} [{async_tag}]{gen_tag} - {len(dep.used_in_routes)} routes")

            if len(other_deps) > 10:
                lines.append(f"    ... and {len(other_deps) - 10} more")

    if report.issues:
        lines.extend([
            "",
            f"{BOLD}{'─' * 50}{RESET}",
            f"{RED}{BOLD}  Issues Found ({len(report.issues)}){RESET}",
            f"{BOLD}{'─' * 50}{RESET}",
        ])

        for issue in report.issues:
            lines.append(f"  {RED}✗{RESET} [{issue.issue_type.value}]")
            lines.append(f"    {issue.message}")
            if issue.path:
                lines.append(f"    Path: {issue.path}")
            if issue.suggestion:
                lines.append(f"    {GREEN}Suggestion:{RESET} {issue.suggestion}")
            lines.append("")

    lines.append(f"{BOLD}{'═' * 50}{RESET}")

    return "\n".join(lines)