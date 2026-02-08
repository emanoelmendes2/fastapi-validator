"""Executor principal do analisador de APIs."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from .base import AnalysisReport, Rule, Severity


class APIAnalyzer:
    """
    Analisador de APIs FastAPI para conformidade RESTful.

    Example:
        from fastapi import FastAPI
        from fastapi_validator import APIAnalyzer

        app = FastAPI()

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        print(f"Erros: {report.error_count}")
        print(f"Warnings: {report.warning_count}")
    """

    def __init__(
        self,
        rules: list[Rule] | None = None,
        exclude_rules: list[str] | None = None,
        min_severity: Severity | None = None,
    ) -> None:
        """
        Inicializa o analisador.

        Args:
            rules: Lista de regras customizadas. Se None, usa todas as regras padrão.
            exclude_rules: Lista de rule_ids a serem excluídos.
            min_severity: Severidade mínima para incluir no relatório.
        """
        self._custom_rules = rules
        self._exclude_rules = set(exclude_rules or [])
        self._min_severity = min_severity
        self._rules: list[Rule] = []

    def _load_default_rules(self) -> list[Rule]:
        """Carrega todas as regras padrão."""
        from .rules import (
            DocumentationRules,
            HTTPMethodRules,
            NamingRules,
            PaginationRules,
            ResponseRules,
            SecurityRules,
            StatusCodeRules,
            VersioningRules,
        )

        rules: list[Rule] = []

        rules.extend(NamingRules.all())
        rules.extend(HTTPMethodRules.all())
        rules.extend(DocumentationRules.all())
        rules.extend(StatusCodeRules.all())
        rules.extend(ResponseRules.all())
        rules.extend(VersioningRules.all())
        rules.extend(SecurityRules.all())
        rules.extend(PaginationRules.all())

        return rules

    def _get_rules(self) -> list[Rule]:
        """Obtém a lista de regras a serem aplicadas."""
        if self._custom_rules is not None:
            rules = self._custom_rules
        else:
            rules = self._load_default_rules()

        if self._exclude_rules:
            rules = [r for r in rules if r.rule_id not in self._exclude_rules]

        return rules

    def _count_api_routes(self, app: FastAPI) -> int:
        """Conta o número de rotas API na aplicação."""
        count = 0
        for route in app.routes:
            if isinstance(route, APIRoute):
                count += 1
        return count

    def _filter_by_severity(self, report: AnalysisReport) -> AnalysisReport:
        """Filtra issues por severidade mínima."""
        if self._min_severity is None:
            return report

        severity_order = {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
        }

        min_order = severity_order[self._min_severity]
        filtered_issues = [
            issue
            for issue in report.issues
            if severity_order[issue.severity] <= min_order
        ]

        return AnalysisReport(
            issues=filtered_issues,
            analyzed_routes=report.analyzed_routes,
        )

    def analyze(self, app: FastAPI) -> AnalysisReport:
        """
        Analisa uma aplicação FastAPI.

        Args:
            app: Instância da aplicação FastAPI.

        Returns:
            Relatório com os issues encontrados.
        """
        rules = self._get_rules()
        all_issues = []

        for rule in rules:
            issues = rule.check(app)
            all_issues.extend(issues)

        report = AnalysisReport(
            issues=all_issues,
            analyzed_routes=self._count_api_routes(app),
        )

        return self._filter_by_severity(report)

    def get_available_rules(self) -> list[dict]:
        """Retorna informações sobre as regras disponíveis."""
        rules = self._load_default_rules()
        return [
            {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "severity": str(rule.severity),
            }
            for rule in rules
        ]