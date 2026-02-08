"""Gerador de relatórios HTML."""

from datetime import datetime
from pathlib import Path

from ..analyzer.base import AnalysisReport, Severity
from ..analyzer.scoring import APIScore, Grade


class HTMLReporter:
    """
    Gera relatórios HTML visuais para análise de API.

    Segue boas práticas separando HTML template e CSS em arquivos distintos.

    Example:
        from fastapi_validator import APIAnalyzer, APIScorer
        from fastapi_validator.reports import HTMLReporter

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        scorer = APIScorer()
        score = scorer.calculate(report)

        reporter = HTMLReporter()
        html = reporter.generate(report, score)

        with open("report.html", "w") as f:
            f.write(html)
    """

    TEMPLATES_DIR = Path(__file__).parent / "templates"

    GRADE_CLASSES = {
        Grade.A_PLUS: "a-plus",
        Grade.A: "a",
        Grade.B: "b",
        Grade.C: "c",
        Grade.D: "d",
        Grade.F: "f",
    }

    def __init__(self) -> None:
        """Inicializa o reporter carregando templates."""
        self._template = self._load_template()
        self._styles = self._load_styles()

    def _load_template(self) -> str:
        """Carrega o template HTML."""
        template_path = self.TEMPLATES_DIR / "report.html"
        return template_path.read_text(encoding="utf-8")

    def _load_styles(self) -> str:
        """Carrega os estilos CSS."""
        styles_path = self.TEMPLATES_DIR / "style.css"
        return styles_path.read_text(encoding="utf-8")

    def generate(
        self,
        report: AnalysisReport,
        score: APIScore | None = None,
        app_title: str = "API Analysis",
    ) -> str:
        """
        Gera o relatório HTML.

        Args:
            report: Relatório de análise
            score: Score da API (opcional)
            app_title: Título da aplicação

        Returns:
            String HTML do relatório
        """
        context = self._build_context(report, score, app_title)
        return self._render(context)

    def _build_context(
        self,
        report: AnalysisReport,
        score: APIScore | None,
        app_title: str,
    ) -> dict:
        """Constrói o contexto para renderização."""
        context = {
            "app_title": app_title,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "version": "0.1.0",
            "routes_count": report.analyzed_routes,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "info_count": report.info_count,
            "total_issues": len(report.issues),
            "has_issues": len(report.issues) > 0,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "rule_id": issue.rule_id,
                    "message": issue.message,
                    "path": issue.path,
                    "method": issue.method,
                    "suggestion": issue.suggestion,
                }
                for issue in report.issues
            ],
        }

        if score:
            context.update({
                "score": score.total_score,
                "grade": score.grade.value,
                "grade_class": self.GRADE_CLASSES.get(score.grade, "c"),
                "score_color": self._get_score_color(score.total_score),
                "categories": [
                    {
                        "name": self._format_category_name(name),
                        "score": cat_score,
                        "color": self._get_score_color(cat_score),
                    }
                    for name, cat_score in score.category_scores.items()
                ],
            })

        return context

    def _render(self, context: dict) -> str:
        """Renderiza o template com o contexto."""
        html = self._template.replace("{{styles}}", self._styles)

        for key, value in context.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (list, dict)):
                continue
            placeholder = "{{" + key + "}}"
            html = html.replace(placeholder, str(value))

        html = self._render_conditionals(html, context)
        html = self._render_loops(html, context)

        return html

    def _render_conditionals(self, html: str, context: dict) -> str:
        """Renderiza blocos condicionais {{#if}}...{{/if}}."""
        import re

        pattern = r"\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}"

        def replace_conditional(match: re.Match) -> str:
            key = match.group(1)
            content = match.group(2)
            value = context.get(key)

            if value:
                return content
            return ""

        return re.sub(pattern, replace_conditional, html, flags=re.DOTALL)

    def _render_loops(self, html: str, context: dict) -> str:
        """Renderiza loops {{#each}}...{{/each}}."""
        import re

        pattern = r"\{\{#each (\w+)\}\}(.*?)\{\{/each\}\}"

        def replace_loop(match: re.Match) -> str:
            key = match.group(1)
            template = match.group(2)
            items = context.get(key, [])

            if not items:
                return ""

            rendered_items = []
            for item in items:
                item_html = template
                for item_key, item_value in item.items():
                    if item_value is None:
                        continue
                    placeholder = "{{" + item_key + "}}"
                    item_html = item_html.replace(placeholder, str(item_value))

                item_html = self._render_item_conditionals(item_html, item)
                rendered_items.append(item_html)

            return "".join(rendered_items)

        return re.sub(pattern, replace_loop, html, flags=re.DOTALL)

    def _render_item_conditionals(self, html: str, item: dict) -> str:
        """Renderiza condicionais dentro de itens de loop."""
        import re

        pattern = r"\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}"

        def replace_conditional(match: re.Match) -> str:
            key = match.group(1)
            content = match.group(2)
            value = item.get(key)

            if value:
                return content
            return ""

        return re.sub(pattern, replace_conditional, html, flags=re.DOTALL)

    def _get_score_color(self, score: int) -> str:
        """Retorna cor baseada no score."""
        if score >= 90:
            return "#4caf50"
        if score >= 80:
            return "#8bc34a"
        if score >= 70:
            return "#ff9800"
        if score >= 60:
            return "#ff5722"
        return "#f44336"

    def _format_category_name(self, name: str) -> str:
        """Formata nome da categoria para exibição."""
        names = {
            "naming": "Nomenclatura",
            "http": "HTTP Methods",
            "documentation": "Documentacao",
            "status_codes": "Status Codes",
            "response": "Response Format",
            "versioning": "Versionamento",
            "security": "Seguranca",
            "pagination": "Paginacao",
        }
        return names.get(name, name.replace("_", " ").title())

    def save(
        self,
        report: AnalysisReport,
        output_path: str | Path,
        score: APIScore | None = None,
        app_title: str = "API Analysis",
    ) -> Path:
        """
        Salva o relatório em arquivo HTML.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída
            score: Score da API (opcional)
            app_title: Título da aplicação

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)
        html = self.generate(report, score, app_title)
        output_path.write_text(html, encoding="utf-8")
        return output_path