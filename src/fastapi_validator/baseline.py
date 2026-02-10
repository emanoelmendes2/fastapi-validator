"""Baseline: salvar, carregar e comparar resultados de análise."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .analyzer.base import AnalysisReport, Issue, Severity
from .analyzer.scoring import APIScore


@dataclass
class BaselineComparison:
    """Resultado da comparação entre análise atual e baseline."""

    new_issues: list[Issue] = field(default_factory=list)
    fixed_issues: list[Issue] = field(default_factory=list)
    remaining_issues: list[Issue] = field(default_factory=list)
    score_before: float | None = None
    score_after: float | None = None
    categories_before: dict[str, float] = field(default_factory=dict)
    categories_after: dict[str, float] = field(default_factory=dict)

    @property
    def score_delta(self) -> float | None:
        """Retorna a diferença de score."""
        if self.score_before is not None and self.score_after is not None:
            return self.score_after - self.score_before
        return None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result: dict[str, Any] = {
            "new_issues": len(self.new_issues),
            "fixed_issues": len(self.fixed_issues),
            "remaining_issues": len(self.remaining_issues),
            "score_before": self.score_before,
            "score_after": self.score_after,
            "score_delta": self.score_delta,
        }
        if self.categories_before or self.categories_after:
            result["categories"] = {}
            all_cats = set(self.categories_before) | set(self.categories_after)
            for cat in sorted(all_cats):
                before = self.categories_before.get(cat)
                after = self.categories_after.get(cat)
                delta = None
                if before is not None and after is not None:
                    delta = after - before
                result["categories"][cat] = {
                    "before": before,
                    "after": after,
                    "delta": delta,
                }
        return result


def _issue_key(issue_dict: dict) -> tuple:
    """Cria chave única para um issue baseada em (rule_id, path, method)."""
    return (
        issue_dict.get("rule_id", ""),
        issue_dict.get("path", ""),
        issue_dict.get("method", ""),
    )


def save_baseline(
    report: AnalysisReport,
    score: APIScore | None,
    path: str,
) -> None:
    """Salva resultado como baseline JSON."""
    from . import __version__

    data: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "issues": [issue.to_dict() for issue in report.issues],
        "summary": {
            "analyzed_routes": report.analyzed_routes,
            "total_issues": len(report.issues),
            "errors": report.error_count,
            "warnings": report.warning_count,
            "infos": report.info_count,
        },
    }

    if score is not None:
        data["score"] = score.to_dict()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_baseline(path: str) -> dict:
    """Carrega baseline JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compare_with_baseline(
    current_report: AnalysisReport,
    current_score: APIScore | None,
    baseline_data: dict,
) -> BaselineComparison:
    """Compara análise atual com baseline e retorna diferenças."""
    # Indexar issues do baseline por chave
    baseline_issues = baseline_data.get("issues", [])
    baseline_keys = {_issue_key(i) for i in baseline_issues}

    # Indexar issues atuais por chave
    current_issues_dicts = [i.to_dict() for i in current_report.issues]
    current_keys = {_issue_key(i) for i in current_issues_dicts}

    # Classificar issues
    new_issues = []
    remaining_issues = []
    for issue in current_report.issues:
        key = (issue.rule_id, issue.path or "", issue.method or "")
        if key in baseline_keys:
            remaining_issues.append(issue)
        else:
            new_issues.append(issue)

    fixed_issues = []
    for issue_dict in baseline_issues:
        key = _issue_key(issue_dict)
        if key not in current_keys:
            fixed_issues.append(Issue(
                rule_id=issue_dict.get("rule_id", ""),
                message=issue_dict.get("message", ""),
                severity=Severity(issue_dict.get("severity", "info")),
                path=issue_dict.get("path"),
                method=issue_dict.get("method"),
            ))

    # Scores
    score_before = None
    categories_before: dict[str, float] = {}
    baseline_score = baseline_data.get("score")
    if baseline_score:
        score_before = baseline_score.get("score")
        for cat_name, cat_data in baseline_score.get("categories", {}).items():
            categories_before[cat_name] = cat_data.get("score", 0)

    score_after = current_score.total_score if current_score else None
    categories_after: dict[str, float] = {}
    if current_score:
        for cat_name, cat_score in current_score.categories.items():
            categories_after[cat_name] = cat_score.percentage

    return BaselineComparison(
        new_issues=new_issues,
        fixed_issues=fixed_issues,
        remaining_issues=remaining_issues,
        score_before=score_before,
        score_after=score_after,
        categories_before=categories_before,
        categories_after=categories_after,
    )


CATEGORY_NAMES = {
    "naming": "Nomenclatura",
    "http": "HTTP Methods",
    "docs": "Documentação",
    "status": "Status Codes",
    "response": "Response Format",
    "versioning": "Versionamento",
    "security": "Segurança",
    "pagination": "Paginação",
    "error_handling": "Error Handling",
}


def format_comparison(comparison: BaselineComparison) -> str:
    """Formata comparação para exibição no terminal com cores."""
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    lines = [
        f"\n{BOLD}Comparação com Baseline{RESET}",
        f"{BOLD}{'═' * 40}{RESET}",
    ]

    # Score delta
    if comparison.score_before is not None and comparison.score_after is not None:
        delta = comparison.score_delta
        if delta is not None:
            if delta > 0:
                delta_str = f"{GREEN}+{delta:.1f}{RESET}"
            elif delta < 0:
                delta_str = f"{RED}{delta:.1f}{RESET}"
            else:
                delta_str = f"{YELLOW}+0.0{RESET}"
            lines.append(
                f"  Score: {comparison.score_before:.1f} -> "
                f"{comparison.score_after:.1f} ({delta_str})"
            )
    elif comparison.score_after is not None:
        lines.append(f"  Score: {comparison.score_after:.1f}")

    lines.append("")

    # Issues summary
    new_count = len(comparison.new_issues)
    fixed_count = len(comparison.fixed_issues)
    remaining_count = len(comparison.remaining_issues)

    if new_count > 0:
        lines.append(f"  {RED}+{new_count} novos issues{RESET}")
    else:
        lines.append(f"  {GREEN}+0 novos issues{RESET}")

    if fixed_count > 0:
        lines.append(f"  {GREEN}-{fixed_count} issues corrigidos{RESET}")
    else:
        lines.append(f"  {YELLOW}-0 issues corrigidos{RESET}")

    lines.append(f"  {remaining_count} issues remanescentes")

    # Category evolution
    all_cats = set(comparison.categories_before) | set(comparison.categories_after)
    if all_cats:
        cat_deltas = []
        for cat in sorted(all_cats):
            before = comparison.categories_before.get(cat)
            after = comparison.categories_after.get(cat)
            if before is not None and after is not None:
                delta = after - before
                if abs(delta) >= 0.1:
                    cat_deltas.append((cat, before, after, delta))

        if cat_deltas:
            # Sort by absolute delta descending
            cat_deltas.sort(key=lambda x: abs(x[3]), reverse=True)
            lines.append("")
            lines.append(f"  {BOLD}Evolução por categoria:{RESET}")
            for cat, before, after, delta in cat_deltas:
                cat_name = CATEGORY_NAMES.get(cat, cat)
                if delta > 0:
                    delta_str = f"{GREEN}+{delta:.0f}{RESET}"
                else:
                    delta_str = f"{RED}{delta:.0f}{RESET}"
                lines.append(
                    f"    {cat_name:15} {before:.0f}/100 -> {after:.0f}/100 ({delta_str})"
                )

    lines.append(f"{BOLD}{'═' * 40}{RESET}")

    return "\n".join(lines)
