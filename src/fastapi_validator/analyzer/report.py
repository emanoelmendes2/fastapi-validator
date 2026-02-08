"""Formatadores de relatório para o analisador."""

import json
from typing import TextIO

from .base import AnalysisReport, Severity


class ReportFormatter:
    """Classe base para formatadores de relatório."""

    def format(self, report: AnalysisReport) -> str:
        """Formata o relatório como string."""
        raise NotImplementedError

    def write(self, report: AnalysisReport, output: TextIO) -> None:
        """Escreve o relatório formatado em um arquivo."""
        output.write(self.format(report))


class JSONFormatter(ReportFormatter):
    """Formatador JSON."""

    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def format(self, report: AnalysisReport) -> str:
        """Formata o relatório como JSON."""
        return json.dumps(
            report.to_dict(),
            indent=self.indent,
            ensure_ascii=False,
        )


class TextFormatter(ReportFormatter):
    """Formatador de texto simples."""

    def format(self, report: AnalysisReport) -> str:
        """Formata o relatório como texto."""
        lines = [
            "Relatório de Análise de API RESTful",
            "=" * 50,
            f"Rotas analisadas: {report.analyzed_routes}",
            f"Total de issues: {len(report.issues)}",
            f"  Erros: {report.error_count}",
            f"  Warnings: {report.warning_count}",
            f"  Info: {report.info_count}",
            "=" * 50,
            "",
        ]

        if report.issues:
            lines.append("Issues encontrados:")
            lines.append("")

            for issue in report.issues:
                severity_str = str(issue.severity).upper()
                lines.append(f"[{severity_str}] {issue.rule_id}")

                if issue.path:
                    method_str = f" ({issue.method})" if issue.method else ""
                    lines.append(f"  Path: {issue.path}{method_str}")

                lines.append(f"  {issue.message}")

                if issue.suggestion:
                    lines.append(f"  Sugestão: {issue.suggestion}")

                lines.append("")

        if report.has_errors:
            lines.append(f"API tem {report.error_count} erro(s)!")
        elif report.warning_count > 0:
            lines.append(f"API tem {report.warning_count} warning(s).")
        else:
            lines.append("API está em conformidade!")

        return "\n".join(lines)


class MarkdownFormatter(ReportFormatter):
    """Formatador Markdown."""

    def format(self, report: AnalysisReport) -> str:
        """Formata o relatório como Markdown."""
        lines = [
            "# Relatório de Análise de API RESTful",
            "",
            "## Resumo",
            "",
            f"- **Rotas analisadas:** {report.analyzed_routes}",
            f"- **Total de issues:** {len(report.issues)}",
            f"  - Erros: {report.error_count}",
            f"  - Warnings: {report.warning_count}",
            f"  - Info: {report.info_count}",
            "",
        ]

        if report.issues:
            lines.append("## Issues")
            lines.append("")

            severity_emojis = {
                Severity.ERROR: "🔴",
                Severity.WARNING: "🟡",
                Severity.INFO: "🔵",
            }

            for issue in report.issues:
                emoji = severity_emojis.get(issue.severity, "")
                lines.append(f"### {emoji} {issue.rule_id}")
                lines.append("")

                if issue.path:
                    method_str = f" `{issue.method}`" if issue.method else ""
                    lines.append(f"**Path:** `{issue.path}`{method_str}")
                    lines.append("")

                lines.append(f"**Mensagem:** {issue.message}")
                lines.append("")

                if issue.suggestion:
                    lines.append(f"> **Sugestão:** {issue.suggestion}")
                    lines.append("")

        lines.append("---")
        lines.append("")

        if report.has_errors:
            lines.append(f"**Status:** 🔴 API tem {report.error_count} erro(s)!")
        elif report.warning_count > 0:
            lines.append(f"**Status:** 🟡 API tem {report.warning_count} warning(s).")
        else:
            lines.append("**Status:** 🟢 API está em conformidade!")

        return "\n".join(lines)