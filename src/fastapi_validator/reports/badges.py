"""Gerador de badges SVG."""

from pathlib import Path

from ..analyzer.scoring import APIScore, Grade


class BadgeGenerator:
    """
    Gera badges SVG para exibir qualidade da API.

    Os badges seguem o padrão shields.io e podem ser usados
    em READMEs, documentação e dashboards.

    Example:
        from fastapi_validator import APIAnalyzer, APIScorer
        from fastapi_validator.reports import BadgeGenerator

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        scorer = APIScorer()
        score = scorer.calculate(report)

        badge = BadgeGenerator()
        svg = badge.generate_score_badge(score)

        with open("api-score.svg", "w") as f:
            f.write(svg)
    """

    GRADE_COLORS = {
        Grade.A_PLUS: "#4c1",
        Grade.A: "#4c1",
        Grade.B: "#97ca00",
        Grade.C: "#dfb317",
        Grade.D: "#fe7d37",
        Grade.F: "#e05d44",
    }

    SCORE_COLORS = {
        90: "#4c1",
        80: "#97ca00",
        70: "#a4a61d",
        60: "#dfb317",
        50: "#fe7d37",
        0: "#e05d44",
    }

    def generate_score_badge(
        self,
        score: APIScore,
        label: str = "API Score",
    ) -> str:
        """
        Gera badge com o score da API.

        Args:
            score: Score da API
            label: Label do badge

        Returns:
            String SVG do badge
        """
        value = f"{score.total_score}/100"
        color = self._get_score_color(score.total_score)
        return self._generate_badge(label, value, color)

    def generate_grade_badge(
        self,
        score: APIScore,
        label: str = "API Grade",
    ) -> str:
        """
        Gera badge com o grade da API.

        Args:
            score: Score da API
            label: Label do badge

        Returns:
            String SVG do badge
        """
        value = score.grade.value
        color = self.GRADE_COLORS.get(score.grade, "#9f9f9f")
        return self._generate_badge(label, value, color)

    def generate_issues_badge(
        self,
        error_count: int,
        warning_count: int,
        label: str = "API Issues",
    ) -> str:
        """
        Gera badge com contagem de issues.

        Args:
            error_count: Número de erros
            warning_count: Número de warnings
            label: Label do badge

        Returns:
            String SVG do badge
        """
        if error_count == 0 and warning_count == 0:
            value = "0"
            color = "#4c1"
        elif error_count == 0:
            value = f"{warning_count} warnings"
            color = "#dfb317"
        else:
            value = f"{error_count} errors"
            color = "#e05d44"

        return self._generate_badge(label, value, color)

    def generate_coverage_badge(
        self,
        coverage_percent: float,
        label: str = "Security Coverage",
    ) -> str:
        """
        Gera badge de cobertura de segurança.

        Args:
            coverage_percent: Porcentagem de cobertura
            label: Label do badge

        Returns:
            String SVG do badge
        """
        value = f"{coverage_percent:.0f}%"
        color = self._get_score_color(int(coverage_percent))
        return self._generate_badge(label, value, color)

    def _get_score_color(self, score: int) -> str:
        """Retorna cor baseada no score."""
        for threshold, color in sorted(self.SCORE_COLORS.items(), reverse=True):
            if score >= threshold:
                return color
        return "#9f9f9f"

    def _generate_badge(self, label: str, value: str, color: str) -> str:
        """Gera SVG do badge seguindo padrão shields.io."""
        label_width = len(label) * 6.5 + 10
        value_width = len(value) * 6.5 + 10
        total_width = label_width + value_width

        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img">
  <title>{label}: {value}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14" fill="#fff">{label}</text>
    <text x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14" fill="#fff">{value}</text>
  </g>
</svg>'''

    def save_all_badges(
        self,
        score: APIScore,
        output_dir: str | Path,
        error_count: int = 0,
        warning_count: int = 0,
        security_coverage: float | None = None,
    ) -> list[Path]:
        """
        Salva todos os badges em um diretório.

        Args:
            score: Score da API
            output_dir: Diretório de saída
            error_count: Número de erros
            warning_count: Número de warnings
            security_coverage: Cobertura de segurança

        Returns:
            Lista de paths dos arquivos salvos
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = []

        score_path = output_dir / "api-score.svg"
        score_path.write_text(self.generate_score_badge(score), encoding="utf-8")
        saved.append(score_path)

        grade_path = output_dir / "api-grade.svg"
        grade_path.write_text(self.generate_grade_badge(score), encoding="utf-8")
        saved.append(grade_path)

        issues_path = output_dir / "api-issues.svg"
        issues_path.write_text(
            self.generate_issues_badge(error_count, warning_count),
            encoding="utf-8",
        )
        saved.append(issues_path)

        if security_coverage is not None:
            security_path = output_dir / "security-coverage.svg"
            security_path.write_text(
                self.generate_coverage_badge(security_coverage),
                encoding="utf-8",
            )
            saved.append(security_path)

        return saved