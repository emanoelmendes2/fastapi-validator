"""Classes base para o analisador de APIs RESTful."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


class Severity(Enum):
    """Níveis de severidade para issues encontrados."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        return self.value


@dataclass
class Issue:
    """Representa um problema encontrado durante a análise."""

    rule_id: str
    message: str
    severity: Severity
    path: str | None = None
    method: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict:
        """Converte o issue para dicionário."""
        result = {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": str(self.severity),
        }
        if self.path:
            result["path"] = self.path
        if self.method:
            result["method"] = self.method
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class Rule(ABC):
    """Classe base abstrata para regras de validação."""

    rule_id: str
    description: str
    severity: Severity

    @abstractmethod
    def check(self, app: "FastAPI") -> list[Issue]:
        """
        Executa a verificação da regra na aplicação FastAPI.

        Args:
            app: Instância da aplicação FastAPI a ser analisada.

        Returns:
            Lista de issues encontrados.
        """
        pass

    def create_issue(
        self,
        message: str,
        path: str | None = None,
        method: str | None = None,
        suggestion: str | None = None,
    ) -> Issue:
        """Cria um issue com os dados da regra."""
        return Issue(
            rule_id=self.rule_id,
            message=message,
            severity=self.severity,
            path=path,
            method=method,
            suggestion=suggestion,
        )


@dataclass
class AnalysisMetrics:
    """Métricas detalhadas da análise para pesquisa."""

    execution_time_ms: float = 0.0
    rules_executed: int = 0
    rules_passed: int = 0
    rules_with_issues: int = 0
    routes_analyzed: int = 0
    issues_by_severity: dict[str, int] = field(default_factory=dict)
    issues_by_category: dict[str, int] = field(default_factory=dict)
    coverage: float = 0.0

    def to_dict(self) -> dict:
        """Converte as métricas para dicionário."""
        return {
            "execution_time_ms": round(self.execution_time_ms, 2),
            "rules_executed": self.rules_executed,
            "rules_passed": self.rules_passed,
            "rules_with_issues": self.rules_with_issues,
            "routes_analyzed": self.routes_analyzed,
            "issues_by_severity": self.issues_by_severity,
            "issues_by_category": self.issues_by_category,
            "coverage": round(self.coverage, 2),
        }


@dataclass
class AnalysisReport:
    """Relatório de análise da API."""

    issues: list[Issue] = field(default_factory=list)
    analyzed_routes: int = 0
    metrics: AnalysisMetrics | None = None

    @property
    def error_count(self) -> int:
        """Retorna a quantidade de erros."""
        return sum(1 for issue in self.issues if issue.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Retorna a quantidade de warnings."""
        return sum(1 for issue in self.issues if issue.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Retorna a quantidade de infos."""
        return sum(1 for issue in self.issues if issue.severity == Severity.INFO)

    @property
    def errors(self) -> list[Issue]:
        """Retorna apenas os erros."""
        return [issue for issue in self.issues if issue.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        """Retorna apenas os warnings."""
        return [issue for issue in self.issues if issue.severity == Severity.WARNING]

    @property
    def infos(self) -> list[Issue]:
        """Retorna apenas os infos."""
        return [issue for issue in self.issues if issue.severity == Severity.INFO]

    @property
    def has_errors(self) -> bool:
        """Verifica se existem erros."""
        return self.error_count > 0

    def to_dict(self) -> dict:
        """Converte o relatório para dicionário."""
        result = {
            "summary": {
                "analyzed_routes": self.analyzed_routes,
                "total_issues": len(self.issues),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "infos": self.info_count,
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }
        if self.metrics:
            result["metrics"] = self.metrics.to_dict()
        return result