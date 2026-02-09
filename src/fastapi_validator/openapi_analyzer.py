"""Analisador de APIs via OpenAPI spec (JSON/YAML)."""

import json
import re
import time
from pathlib import Path

from .analyzer.base import AnalysisMetrics, AnalysisReport, Issue, Severity
from .analyzer.scoring import APIScorer

__all__ = [
    "OpenAPIAnalyzer",
]


class OpenAPIAnalyzer:
    """
    Analisa uma API a partir de sua especificação OpenAPI sem precisar de app FastAPI.

    Suporta specs em JSON e YAML. O relatório gerado é compatível com
    todos os reporters (HTML, JUnit, CSV, etc) e com o APIScorer.

    Example:
        from fastapi_validator import OpenAPIAnalyzer

        spec = OpenAPIAnalyzer.load_spec("openapi.json")
        report = OpenAPIAnalyzer.analyze(spec)

        print(f"Issues: {len(report.issues)}")
    """

    @classmethod
    def load_spec(cls, path: str | Path) -> dict:
        """
        Carrega uma spec OpenAPI de arquivo JSON ou YAML.

        Args:
            path: Caminho para o arquivo de spec.

        Returns:
            Dict com a spec OpenAPI.
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")

        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml
            except ImportError as err:
                raise ImportError(
                    "PyYAML é necessário para carregar specs YAML. "
                    "Instale com: pip install fastapi-validator[yaml]"
                ) from err
            return yaml.safe_load(content)

        return json.loads(content)

    @classmethod
    def analyze(cls, spec: dict) -> AnalysisReport:
        """
        Analisa uma spec OpenAPI e retorna um relatório.

        Args:
            spec: Dict com a spec OpenAPI.

        Returns:
            AnalysisReport com os issues encontrados.
        """
        start_time = time.perf_counter()

        issues: list[Issue] = []
        paths = spec.get("paths", {})

        issues.extend(cls._check_naming(paths))
        issues.extend(cls._check_http_methods(paths))
        issues.extend(cls._check_documentation(paths))
        issues.extend(cls._check_status_codes(paths))
        issues.extend(cls._check_security(spec, paths))
        issues.extend(cls._check_error_responses(paths))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        routes_analyzed = cls._count_routes(paths)

        # Métricas
        checks_executed = 6
        rules_with_issues: set[str] = {
            issue.rule_id for issue in issues
        }

        issues_by_severity: dict[str, int] = {}
        for issue in issues:
            sev = str(issue.severity)
            issues_by_severity[sev] = (
                issues_by_severity.get(sev, 0) + 1
            )

        issues_by_category: dict[str, int] = {}
        for issue in issues:
            cat = (
                issue.rule_id.rsplit("-", 1)[0]
                if "-" in issue.rule_id
                else issue.rule_id
            )
            issues_by_category[cat] = (
                issues_by_category.get(cat, 0) + 1
            )

        all_categories = set(APIScorer.CATEGORY_MAPPING.keys())
        categories_with_issues: set[str] = set()
        for issue in issues:
            for cat, rule_ids in APIScorer.CATEGORY_MAPPING.items():
                if issue.rule_id in rule_ids:
                    categories_with_issues.add(cat)
                    break
        categories_clean = (
            len(all_categories) - len(categories_with_issues)
        )
        coverage = (
            (categories_clean / len(all_categories) * 100)
            if all_categories
            else 0.0
        )

        metrics = AnalysisMetrics(
            execution_time_ms=elapsed_ms,
            rules_executed=checks_executed,
            rules_passed=checks_executed - len(rules_with_issues),
            rules_with_issues=len(rules_with_issues),
            routes_analyzed=routes_analyzed,
            issues_by_severity=issues_by_severity,
            issues_by_category=issues_by_category,
            coverage=coverage,
        )

        return AnalysisReport(
            issues=issues,
            analyzed_routes=routes_analyzed,
            metrics=metrics,
        )

    @classmethod
    def _count_routes(cls, paths: dict) -> int:
        """Conta o número total de operações."""
        count = 0
        http_methods = {
            "get", "post", "put", "patch",
            "delete", "head", "options",
        }
        for path_ops in paths.values():
            for method in path_ops:
                if method.lower() in http_methods:
                    count += 1
        return count

    @classmethod
    def _check_naming(cls, paths: dict) -> list[Issue]:
        """Verifica convenções de nomenclatura em paths."""
        issues = []

        for path in paths:
            # Remover parâmetros de path para análise
            clean_path = re.sub(r"\{[^}]+\}", "", path)
            segments = [s for s in clean_path.split("/") if s]

            for segment in segments:
                # Verificar kebab-case (não deve ter underscore)
                if "_" in segment:
                    issues.append(Issue(
                        rule_id="naming-kebab-case",
                        message=(
                            f"Path '{path}' usa underscore "
                            f"em vez de kebab-case."
                        ),
                        severity=Severity.WARNING,
                        path=path,
                        suggestion="Usar kebab-case: trocar '_' por '-'",
                    ))
                    break

                # Verificar lowercase
                if segment != segment.lower():
                    issues.append(Issue(
                        rule_id="naming-lowercase",
                        message=(
                            f"Path '{path}' contém "
                            f"letras maiúsculas."
                        ),
                        severity=Severity.WARNING,
                        path=path,
                        suggestion="Usar apenas letras minúsculas",
                    ))
                    break

            # Verificar trailing slash
            if path != "/" and path.endswith("/"):
                issues.append(Issue(
                    rule_id="naming-no-trailing-slash",
                    message=f"Path '{path}' termina com barra.",
                    severity=Severity.INFO,
                    path=path,
                    suggestion="Remover a barra final do path",
                ))

        return issues

    @classmethod
    def _check_http_methods(cls, paths: dict) -> list[Issue]:
        """Verifica uso correto de métodos HTTP."""
        issues = []

        for path, operations in paths.items():
            # POST deve retornar 201
            if "post" in operations:
                op = operations["post"]
                responses = op.get("responses", {})
                has_200 = "200" in responses
                has_201 = "201" in responses
                if responses and not has_201 and has_200:
                    issues.append(Issue(
                        rule_id="http-post-status",
                        message=(
                            f"POST '{path}' retorna 200 "
                            f"em vez de 201."
                        ),
                        severity=Severity.INFO,
                        path=path,
                        method="POST",
                        suggestion=(
                            "POST para criação deve "
                            "retornar 201 Created"
                        ),
                    ))

            # DELETE deve retornar 204
            if "delete" in operations:
                op = operations["delete"]
                responses = op.get("responses", {})
                has_200 = "200" in responses
                has_204 = "204" in responses
                if responses and not has_204 and has_200:
                    issues.append(Issue(
                        rule_id="http-delete-status",
                        message=(
                            f"DELETE '{path}' retorna 200 "
                            f"em vez de 204."
                        ),
                        severity=Severity.INFO,
                        path=path,
                        method="DELETE",
                        suggestion="DELETE deve retornar 204 No Content",
                    ))

        return issues

    @classmethod
    def _check_documentation(cls, paths: dict) -> list[Issue]:
        """Verifica documentação dos endpoints."""
        issues = []
        http_methods = {
            "get", "post", "put", "patch",
            "delete", "head", "options",
        }

        for path, operations in paths.items():
            for method, op in operations.items():
                if method.lower() not in http_methods:
                    continue
                if not isinstance(op, dict):
                    continue

                # Verificar summary
                if not op.get("summary"):
                    issues.append(Issue(
                        rule_id="docs-summary-required",
                        message="Endpoint sem summary.",
                        severity=Severity.WARNING,
                        path=path,
                        method=method.upper(),
                        suggestion="Adicionar summary ao endpoint",
                    ))

                # Verificar description
                if not op.get("description"):
                    issues.append(Issue(
                        rule_id="docs-description-required",
                        message="Endpoint sem description.",
                        severity=Severity.INFO,
                        path=path,
                        method=method.upper(),
                        suggestion="Adicionar description ao endpoint",
                    ))

                # Verificar tags
                if not op.get("tags"):
                    issues.append(Issue(
                        rule_id="docs-tags-required",
                        message="Endpoint sem tags.",
                        severity=Severity.INFO,
                        path=path,
                        method=method.upper(),
                        suggestion="Adicionar tags ao endpoint",
                    ))

                # Verificar operationId
                if not op.get("operationId"):
                    issues.append(Issue(
                        rule_id="docs-operation-id",
                        message="Endpoint sem operationId.",
                        severity=Severity.INFO,
                        path=path,
                        method=method.upper(),
                        suggestion="Definir operationId para o endpoint",
                    ))

        return issues

    @classmethod
    def _check_status_codes(cls, paths: dict) -> list[Issue]:
        """Verifica status codes nas respostas."""
        issues = []
        http_methods = {
            "get", "post", "put", "patch",
            "delete", "head", "options",
        }

        for path, operations in paths.items():
            for method, op in operations.items():
                if method.lower() not in http_methods:
                    continue
                if not isinstance(op, dict):
                    continue

                responses = op.get("responses", {})
                if not responses:
                    issues.append(Issue(
                        rule_id="status-responses-defined",
                        message="Endpoint não define responses.",
                        severity=Severity.WARNING,
                        path=path,
                        method=method.upper(),
                        suggestion=(
                            "Definir responses com "
                            "os códigos HTTP esperados"
                        ),
                    ))

        return issues

    @classmethod
    def _check_security(cls, spec: dict, paths: dict) -> list[Issue]:
        """Verifica configurações de segurança."""
        issues = []

        # Verificar se há securitySchemes definidos
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        global_security = spec.get("security", [])

        modifying_methods = {"post", "put", "patch", "delete"}

        exempt_keywords = [
            "/login", "/auth", "/register",
            "/signup", "/token", "/health",
        ]

        for path, operations in paths.items():
            for method, op in operations.items():
                if method.lower() not in modifying_methods:
                    continue
                if not isinstance(op, dict):
                    continue

                # Pular rotas de auth
                if any(kw in path.lower() for kw in exempt_keywords):
                    continue

                op_security = op.get("security")
                no_security = (
                    op_security is None
                    and not global_security
                    and not security_schemes
                )
                if no_security:
                    issues.append(Issue(
                        rule_id="security-auth-required",
                        message=(
                            "Endpoint que modifica dados "
                            "não tem segurança definida."
                        ),
                        severity=Severity.WARNING,
                        path=path,
                        method=method.upper(),
                        suggestion=(
                            "Adicionar security ao endpoint "
                            "ou definir securitySchemes globais"
                        ),
                    ))

        return issues

    @classmethod
    def _check_error_responses(cls, paths: dict) -> list[Issue]:
        """Verifica documentação de respostas de erro."""
        issues = []
        http_methods = {
            "get", "post", "put", "patch",
            "delete", "head", "options",
        }

        for path, operations in paths.items():
            for method, op in operations.items():
                if method.lower() not in http_methods:
                    continue
                if not isinstance(op, dict):
                    continue

                responses = op.get("responses", {})
                has_error_response = any(
                    str(code).startswith(("4", "5"))
                    for code in responses
                )

                if responses and not has_error_response:
                    issues.append(Issue(
                        rule_id="error-response-documented",
                        message=(
                            "Endpoint não documenta "
                            "respostas de erro (4xx/5xx)."
                        ),
                        severity=Severity.WARNING,
                        path=path,
                        method=method.upper(),
                        suggestion=(
                            "Adicionar responses "
                            "com códigos 4xx/5xx"
                        ),
                    ))

        return issues
