"""Utilitários compartilhados entre módulos."""

from .analyzer.scoring import APIScorer


def group_issues_by_category(issues):
    """
    Agrupa issues por categoria usando CATEGORY_MAPPING.

    Retorna lista de tuplas (cat_id, issues) na ordem
    definida pelo CATEGORY_MAPPING.
    """
    mapping = APIScorer.CATEGORY_MAPPING
    grouped: dict[str, list] = {}
    uncategorized = []

    for issue in issues:
        found = False
        for cat, rule_ids in mapping.items():
            if issue.rule_id in rule_ids:
                grouped.setdefault(cat, []).append(issue)
                found = True
                break
        if not found:
            uncategorized.append(issue)

    result = []
    for cat in mapping:
        if cat in grouped:
            result.append((cat, grouped[cat]))

    if uncategorized:
        result.append(("other", uncategorized))

    return result
