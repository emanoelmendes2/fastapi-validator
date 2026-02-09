"""Sistema de scoring para avaliação de qualidade de APIs."""

from dataclasses import dataclass, field
from enum import Enum

from .base import AnalysisReport, Severity


class Grade(Enum):
    """Grades de qualidade da API."""

    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

    @classmethod
    def from_score(cls, score: float) -> "Grade":
        """Retorna a grade baseada na pontuação."""
        if score >= 95:
            return cls.A_PLUS
        elif score >= 85:
            return cls.A
        elif score >= 70:
            return cls.B
        elif score >= 55:
            return cls.C
        elif score >= 40:
            return cls.D
        else:
            return cls.F


@dataclass
class CategoryScore:
    """Pontuação de uma categoria específica."""

    name: str
    score: float
    max_score: float
    issues_count: int
    weight: float

    @property
    def percentage(self) -> float:
        """Retorna a porcentagem da pontuação."""
        if self.max_score == 0:
            return 100.0
        return (self.score / self.max_score) * 100

    @property
    def weighted_score(self) -> float:
        """Retorna a pontuação ponderada."""
        return self.percentage * self.weight


@dataclass
class APIScore:
    """Resultado completo do scoring da API."""

    total_score: float
    grade: Grade
    categories: dict[str, CategoryScore] = field(default_factory=dict)
    total_routes: int = 0
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "score": round(self.total_score, 1),
            "grade": self.grade.value,
            "total_routes": self.total_routes,
            "summary": {
                "total_issues": self.total_issues,
                "errors": self.errors,
                "warnings": self.warnings,
                "infos": self.infos,
            },
            "categories": {
                name: {
                    "score": round(cat.percentage, 1),
                    "issues": cat.issues_count,
                    "weight": f"{cat.weight * 100:.0f}%",
                }
                for name, cat in self.categories.items()
            },
        }


class APIScorer:
    """
    Calculador de score para APIs FastAPI.

    O score é calculado baseado em:
    - Quantidade de issues por severidade
    - Categorias de regras
    - Pesos configuráveis

    Example:
        from fastapi_validator import APIAnalyzer, APIScorer

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        scorer = APIScorer()
        score = scorer.calculate(report)

        print(f"Score: {score.total_score}/100 ({score.grade.value})")
    """

    CATEGORY_WEIGHTS = {
        "naming": 0.10,
        "http": 0.15,
        "docs": 0.10,
        "status": 0.10,
        "response": 0.10,
        "versioning": 0.10,
        "security": 0.15,
        "pagination": 0.10,
        "error_handling": 0.10,
    }

    SEVERITY_PENALTIES = {
        Severity.ERROR: 10.0,
        Severity.WARNING: 3.0,
        Severity.INFO: 1.0,
    }

    CATEGORY_MAPPING = {
        "naming": ["naming-kebab-case", "naming-plural-resources", "naming-no-verbs",
                   "naming-lowercase", "naming-no-trailing-slash"],
        "http": ["http-get-no-body", "http-post-status", "http-delete-status",
                 "http-put-patch-body"],
        "docs": ["docs-summary-required", "docs-description-required", "docs-tags-required",
                 "docs-operation-id", "docs-response-model"],
        "status": ["status-valid-codes", "status-responses-defined", "status-error-codes"],
        "response": ["response-snake-case", "response-pydantic-model"],
        "versioning": ["versioning-path", "versioning-consistent"],
        "security": ["security-auth-required", "security-sensitive-url", "security-https",
                     "security-deprecated-docs"],
        "pagination": ["pagination-list-endpoints", "pagination-consistency",
                       "pagination-defaults", "pagination-max-limit"],
        "error_handling": ["error-response-documented", "error-consistent-format",
                          "error-exception-handlers", "error-http-exception-usage"],
    }

    def __init__(
        self,
        category_weights: dict[str, float] | None = None,
        severity_penalties: dict[Severity, float] | None = None,
    ) -> None:
        """
        Inicializa o scorer.

        Args:
            category_weights: Pesos customizados para categorias (soma deve ser 1.0)
            severity_penalties: Penalidades customizadas por severidade
        """
        self.category_weights = category_weights or self.CATEGORY_WEIGHTS.copy()
        self.severity_penalties = severity_penalties or self.SEVERITY_PENALTIES.copy()

    def _get_category(self, rule_id: str) -> str:
        """Retorna a categoria de uma regra."""
        for category, rules in self.CATEGORY_MAPPING.items():
            if rule_id in rules:
                return category
        return "other"

    def _calculate_category_scores(
        self,
        report: AnalysisReport,
    ) -> dict[str, CategoryScore]:
        """Calcula scores por categoria."""
        category_issues: dict[str, list] = {cat: [] for cat in self.category_weights}
        category_issues["other"] = []

        for issue in report.issues:
            category = self._get_category(issue.rule_id)
            if category in category_issues:
                category_issues[category].append(issue)
            else:
                category_issues["other"].append(issue)

        scores = {}
        for category, weight in self.category_weights.items():
            issues = category_issues.get(category, [])

            penalty = sum(
                self.severity_penalties[issue.severity]
                for issue in issues
            )

            max_score = 100.0
            score = max(0, max_score - penalty)

            scores[category] = CategoryScore(
                name=category,
                score=score,
                max_score=max_score,
                issues_count=len(issues),
                weight=weight,
            )

        return scores

    def calculate(self, report: AnalysisReport) -> APIScore:
        """
        Calcula o score da API.

        Args:
            report: Relatório de análise do APIAnalyzer

        Returns:
            APIScore com a pontuação detalhada
        """
        category_scores = self._calculate_category_scores(report)

        total_weighted = sum(
            cat.weighted_score
            for cat in category_scores.values()
        )

        total_weight = sum(self.category_weights.values())
        final_score = total_weighted / total_weight if total_weight > 0 else 0

        final_score = max(0, min(100, final_score))

        return APIScore(
            total_score=final_score,
            grade=Grade.from_score(final_score),
            categories=category_scores,
            total_routes=report.analyzed_routes,
            total_issues=len(report.issues),
            errors=report.error_count,
            warnings=report.warning_count,
            infos=report.info_count,
        )


def format_score_report(score: APIScore, use_colors: bool = True) -> str:
    """
    Formata o relatório de score para exibição.

    Args:
        score: Resultado do scoring
        use_colors: Se deve usar cores ANSI

    Returns:
        String formatada para exibição
    """
    if use_colors:
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
    else:
        BOLD = GREEN = YELLOW = RED = BLUE = RESET = ""

    grade_colors = {
        Grade.A_PLUS: GREEN,
        Grade.A: GREEN,
        Grade.B: BLUE,
        Grade.C: YELLOW,
        Grade.D: YELLOW,
        Grade.F: RED,
    }

    grade_color = grade_colors.get(score.grade, "")

    lines = [
        f"\n{BOLD}{'═' * 50}{RESET}",
        f"{BOLD}       API QUALITY SCORE{RESET}",
        f"{BOLD}{'═' * 50}{RESET}",
        "",
        f"  {BOLD}Score:{RESET}  {grade_color}{score.total_score:.1f}/100{RESET}",
        f"  {BOLD}Grade:{RESET}  {grade_color}{score.grade.value}{RESET}",
        "",
        f"  {BOLD}Routes analyzed:{RESET} {score.total_routes}",
        f"  {BOLD}Issues found:{RESET}   {score.total_issues}",
        f"    {RED}Errors:{RESET}   {score.errors}",
        f"    {YELLOW}Warnings:{RESET} {score.warnings}",
        f"    {BLUE}Info:{RESET}     {score.infos}",
        "",
        f"{BOLD}{'─' * 50}{RESET}",
        f"{BOLD}  Category Breakdown{RESET}",
        f"{BOLD}{'─' * 50}{RESET}",
    ]

    for name, cat in sorted(score.categories.items(), key=lambda x: -x[1].percentage):
        bar_width = 20
        filled = int((cat.percentage / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        if cat.percentage >= 85:
            color = GREEN
        elif cat.percentage >= 70:
            color = BLUE
        elif cat.percentage >= 50:
            color = YELLOW
        else:
            color = RED

        lines.append(
            f"  {name:12} {color}{bar}{RESET} {cat.percentage:5.1f}% "
            f"({cat.issues_count} issues)"
        )

    lines.extend([
        "",
        f"{BOLD}{'═' * 50}{RESET}",
    ])

    return "\n".join(lines)