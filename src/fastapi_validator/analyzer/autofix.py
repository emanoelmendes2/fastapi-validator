"""Auto-fix e geração de sugestões de código."""

import re
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from .base import Issue, Severity


@dataclass
class CodeSuggestion:
    """Sugestão de código para corrigir um issue."""

    issue: Issue
    original_code: str | None = None
    suggested_code: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    explanation: str = ""
    can_auto_fix: bool = False

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "rule_id": self.issue.rule_id,
            "path": self.issue.path,
            "method": self.issue.method,
            "explanation": self.explanation,
            "can_auto_fix": self.can_auto_fix,
            "original_code": self.original_code,
            "suggested_code": self.suggested_code,
        }


@dataclass
class AutoFixReport:
    """Relatório de sugestões de auto-fix."""

    suggestions: list[CodeSuggestion] = field(default_factory=list)

    @property
    def fixable_count(self) -> int:
        """Retorna quantidade de issues que podem ser corrigidos automaticamente."""
        return sum(1 for s in self.suggestions if s.can_auto_fix)

    @property
    def manual_count(self) -> int:
        """Retorna quantidade de issues que precisam correção manual."""
        return sum(1 for s in self.suggestions if not s.can_auto_fix)

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "summary": {
                "total_suggestions": len(self.suggestions),
                "auto_fixable": self.fixable_count,
                "manual_required": self.manual_count,
            },
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


class AutoFixer:
    """
    Gerador de sugestões de código para corrigir issues.

    Para cada issue encontrado, gera uma sugestão de código
    que pode ser aplicada para corrigir o problema.

    Example:
        from fastapi_validator import APIAnalyzer, AutoFixer

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        fixer = AutoFixer()
        suggestions = fixer.generate_suggestions(app, report.issues)

        for suggestion in suggestions.suggestions:
            print(f"Issue: {suggestion.issue.rule_id}")
            print(f"Fix: {suggestion.suggested_code}")
    """

    def __init__(self) -> None:
        """Inicializa o auto-fixer."""
        self._suggestion_generators = {
            "naming-kebab-case": self._suggest_kebab_case,
            "naming-plural-resources": self._suggest_plural,
            "naming-no-verbs": self._suggest_no_verbs,
            "naming-lowercase": self._suggest_lowercase,
            "naming-no-trailing-slash": self._suggest_no_trailing_slash,
            "http-post-status": self._suggest_post_status,
            "http-delete-status": self._suggest_delete_status,
            "docs-summary-required": self._suggest_summary,
            "docs-tags-required": self._suggest_tags,
            "docs-response-model": self._suggest_response_model,
            "pagination-list-endpoints": self._suggest_pagination,
        }

    def generate_suggestions(
        self,
        app: FastAPI,
        issues: list[Issue],
    ) -> AutoFixReport:
        """
        Gera sugestões de código para os issues.

        Args:
            app: Instância da aplicação FastAPI
            issues: Lista de issues encontrados

        Returns:
            Relatório com sugestões de código
        """
        suggestions = []

        routes_by_path = self._index_routes(app)

        for issue in issues:
            generator = self._suggestion_generators.get(issue.rule_id)
            if generator:
                route = routes_by_path.get(issue.path)
                suggestion = generator(issue, route)
                if suggestion:
                    suggestions.append(suggestion)
            else:
                suggestion = self._generate_generic_suggestion(issue)
                suggestions.append(suggestion)

        return AutoFixReport(suggestions=suggestions)

    def _index_routes(self, app: FastAPI) -> dict[str, APIRoute]:
        """Indexa rotas por path."""
        routes = {}
        for route in app.routes:
            if isinstance(route, APIRoute):
                routes[route.path] = route
        return routes

    def _suggest_kebab_case(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere correção para kebab-case."""
        path = issue.path or ""
        fixed_path = re.sub(r"_", "-", path)
        fixed_path = re.sub(r"([a-z])([A-Z])", r"\1-\2", fixed_path).lower()

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.get("{path}")',
            suggested_code=f'@app.get("{fixed_path}")',
            explanation="URLs devem usar kebab-case (hífens) em vez de underscores ou camelCase",
            can_auto_fix=True,
        )

    def _suggest_plural(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere correção para plural."""
        path = issue.path or ""
        segments = path.split("/")

        for i, segment in enumerate(segments):
            if segment and not segment.startswith("{"):
                if not segment.endswith("s") and segment.isalpha():
                    segments[i] = segment + "s"

        fixed_path = "/".join(segments)

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.get("{path}")',
            suggested_code=f'@app.get("{fixed_path}")',
            explanation="Recursos devem usar nomes no plural para representar coleções",
            can_auto_fix=True,
        )

    def _suggest_no_verbs(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere correção para remover verbos."""
        path = issue.path or ""

        verbs_to_remove = [
            "get-", "create-", "update-", "delete-", "remove-",
            "add-", "fetch-", "list-", "find-", "search-",
        ]

        fixed_path = path
        for verb in verbs_to_remove:
            fixed_path = fixed_path.replace(verb, "")

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.get("{path}")',
            suggested_code=f'@app.get("{fixed_path}")  # Use HTTP method for action',
            explanation="O método HTTP (GET, POST, PUT, DELETE) deve indicar a ação, não a URL",
            can_auto_fix=False,
        )

    def _suggest_lowercase(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere correção para lowercase."""
        path = issue.path or ""
        fixed_path = path.lower()

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.get("{path}")',
            suggested_code=f'@app.get("{fixed_path}")',
            explanation="URLs devem ser totalmente em minúsculas",
            can_auto_fix=True,
        )

    def _suggest_no_trailing_slash(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere correção para trailing slash."""
        path = issue.path or ""
        fixed_path = path.rstrip("/")

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.get("{path}")',
            suggested_code=f'@app.get("{fixed_path}")',
            explanation="URLs não devem terminar com barra",
            can_auto_fix=True,
        )

    def _suggest_post_status(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere status 201 para POST."""
        path = issue.path or ""

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.post("{path}")\nasync def create_resource(...):',
            suggested_code=f'@app.post("{path}", status_code=201)\nasync def create_resource(...):',
            explanation="POST para criação deve retornar 201 Created",
            can_auto_fix=True,
        )

    def _suggest_delete_status(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere status 204 para DELETE."""
        path = issue.path or ""

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.delete("{path}")\nasync def delete_resource(...):',
            suggested_code=f'@app.delete("{path}", status_code=204)\nasync def delete_resource(...):\n    # Return None for 204 No Content',
            explanation="DELETE deve retornar 204 No Content quando não há body de resposta",
            can_auto_fix=True,
        )

    def _suggest_summary(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere adicionar summary."""
        path = issue.path or ""
        method = (issue.method or "GET").lower()

        resource = path.split("/")[-1].replace("{", "").replace("}", "").replace("-", " ")
        if "{" in path.split("/")[-1]:
            action = "Get" if method == "get" else method.capitalize()
        else:
            action = "List" if method == "get" else method.capitalize()

        suggested_summary = f"{action} {resource}"

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.{method}("{path}")',
            suggested_code=f'@app.{method}("{path}", summary="{suggested_summary}")',
            explanation="Endpoints devem ter um summary para documentação",
            can_auto_fix=True,
        )

    def _suggest_tags(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere adicionar tags."""
        path = issue.path or ""
        method = (issue.method or "GET").split(",")[0].strip().lower()

        segments = [s for s in path.split("/") if s and not s.startswith("{")]
        tag = segments[0] if segments else "default"

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.{method}("{path}")',
            suggested_code=f'@app.{method}("{path}", tags=["{tag}"])',
            explanation="Tags organizam endpoints na documentação",
            can_auto_fix=True,
        )

    def _suggest_response_model(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere adicionar response_model."""
        path = issue.path or ""
        method = (issue.method or "GET").split(",")[0].strip().lower()

        segments = [s for s in path.split("/") if s and not s.startswith("{")]
        resource = segments[-1] if segments else "Item"
        resource = resource.replace("-", "_").title().replace("_", "")

        if method == "get" and not any(s.startswith("{") for s in path.split("/")):
            model_name = f"list[{resource}Response]"
        else:
            model_name = f"{resource}Response"

        return CodeSuggestion(
            issue=issue,
            original_code=f'@app.{method}("{path}")\nasync def endpoint(...):',
            suggested_code=f'''# Define response model:
class {resource.rstrip("s")}Response(BaseModel):
    id: int
    # ... other fields

@app.{method}("{path}", response_model={model_name})
async def endpoint(...):''',
            explanation="Response models documentam e validam a resposta da API",
            can_auto_fix=False,
        )

    def _suggest_pagination(
        self,
        issue: Issue,
        route: APIRoute | None,
    ) -> CodeSuggestion:
        """Sugere adicionar paginação."""
        path = issue.path or ""

        return CodeSuggestion(
            issue=issue,
            original_code=f'''@app.get("{path}")
async def list_items():
    return items''',
            suggested_code=f'''@app.get("{path}")
async def list_items(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
):
    offset = (page - 1) * limit
    return {{
        "items": items[offset:offset + limit],
        "total": len(items),
        "page": page,
        "limit": limit,
    }}''',
            explanation="Endpoints que retornam listas devem suportar paginação",
            can_auto_fix=False,
        )

    def _generate_generic_suggestion(self, issue: Issue) -> CodeSuggestion:
        """Gera sugestão genérica para issues sem handler específico."""
        return CodeSuggestion(
            issue=issue,
            explanation=issue.suggestion or issue.message,
            can_auto_fix=False,
        )


def format_suggestions_report(
    report: AutoFixReport,
    use_colors: bool = True,
    show_code: bool = True,
) -> str:
    """Formata o relatório de sugestões para exibição."""
    if use_colors:
        BOLD = "\033[1m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
    else:
        BOLD = GREEN = YELLOW = RED = BLUE = CYAN = RESET = ""

    lines = [
        f"\n{BOLD}{'═' * 60}{RESET}",
        f"{BOLD}   CODE SUGGESTIONS{RESET}",
        f"{BOLD}{'═' * 60}{RESET}",
        "",
        f"  Total suggestions: {len(report.suggestions)}",
        f"  {GREEN}Auto-fixable:{RESET}    {report.fixable_count}",
        f"  {YELLOW}Manual required:{RESET} {report.manual_count}",
        "",
    ]

    for i, suggestion in enumerate(report.suggestions, 1):
        fix_tag = f"{GREEN}[AUTO-FIX]{RESET}" if suggestion.can_auto_fix else f"{YELLOW}[MANUAL]{RESET}"

        lines.extend([
            f"{BOLD}{'─' * 60}{RESET}",
            f"  {BOLD}#{i}{RESET} {fix_tag} {suggestion.issue.rule_id}",
        ])

        if suggestion.issue.path:
            path_info = suggestion.issue.path
            if suggestion.issue.method:
                path_info = f"{suggestion.issue.method} {path_info}"
            lines.append(f"  {BLUE}Path:{RESET} {path_info}")

        lines.append(f"  {CYAN}Explanation:{RESET} {suggestion.explanation}")

        if show_code and suggestion.original_code and suggestion.suggested_code:
            lines.extend([
                "",
                f"  {RED}Before:{RESET}",
            ])
            for line in suggestion.original_code.split("\n"):
                lines.append(f"    {RED}- {line}{RESET}")

            lines.append(f"  {GREEN}After:{RESET}")
            for line in suggestion.suggested_code.split("\n"):
                lines.append(f"    {GREEN}+ {line}{RESET}")

        lines.append("")

    lines.append(f"{BOLD}{'═' * 60}{RESET}")

    return "\n".join(lines)