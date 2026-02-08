"""Gerador de anotações para GitHub Actions."""

import json
from dataclasses import dataclass
from pathlib import Path

from ..analyzer.base import AnalysisReport, Issue, Severity


@dataclass
class GitHubAnnotation:
    """
    Anotação do GitHub Actions.

    Representa uma mensagem que aparece diretamente no código
    durante Pull Requests e commits no GitHub.
    """

    level: str  # "error", "warning", "notice"
    message: str
    file: str | None = None
    line: int | None = None
    end_line: int | None = None
    title: str | None = None

    def to_workflow_command(self) -> str:
        """
        Converte para comando de workflow do GitHub.

        Formato: ::level file=X,line=Y::message
        """
        params = []

        if self.file:
            params.append(f"file={self.file}")
        if self.line:
            params.append(f"line={self.line}")
        if self.end_line:
            params.append(f"endLine={self.end_line}")
        if self.title:
            params.append(f"title={self.title}")

        params_str = ",".join(params)
        if params_str:
            return f"::{self.level} {params_str}::{self.message}"
        return f"::{self.level}::{self.message}"


class GitHubAnnotationsReporter:
    """
    Gera anotações para GitHub Actions.

    Permite visualizar issues diretamente no PR/commit do GitHub.
    As anotações aparecem inline no diff do código.

    Example:
        from fastapi_validator import APIAnalyzer
        from fastapi_validator.reports import GitHubAnnotationsReporter

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        github = GitHubAnnotationsReporter()

        # Output para console (GitHub Actions processa automaticamente)
        print(github.generate(report))

    No GitHub Actions workflow (.github/workflows/api-check.yml):

        - name: Validate API
          run: |
            python -c "
            from myapp import app
            from fastapi_validator import APIAnalyzer
            from fastapi_validator.reports import GitHubAnnotationsReporter

            report = APIAnalyzer().analyze(app)
            print(GitHubAnnotationsReporter().generate(report))
            exit(1 if report.error_count > 0 else 0)
            "
    """

    SEVERITY_MAP = {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "notice",
    }

    def __init__(self, source_file: str | None = None) -> None:
        """
        Inicializa o reporter.

        Args:
            source_file: Arquivo fonte da API (opcional, para anotações com arquivo)
        """
        self.source_file = source_file

    def generate(self, report: AnalysisReport) -> str:
        """
        Gera comandos de workflow do GitHub Actions.

        Args:
            report: Relatório de análise

        Returns:
            String com comandos de workflow que o GitHub interpreta
        """
        lines = []

        # Grupo com resumo
        lines.append("::group::FastAPI Validator Report")
        lines.append(f"Analyzed {report.analyzed_routes} routes")
        lines.append(f"Found {len(report.issues)} issues:")
        lines.append(f"  - Errors: {report.error_count}")
        lines.append(f"  - Warnings: {report.warning_count}")
        lines.append(f"  - Info: {report.info_count}")
        lines.append("::endgroup::")
        lines.append("")

        # Anotações para cada issue
        for issue in report.issues:
            annotation = self._issue_to_annotation(issue)
            lines.append(annotation.to_workflow_command())

        # Erro final se houver erros
        if report.error_count > 0:
            lines.append("")
            lines.append(
                f"::error::API validation failed with {report.error_count} error(s)"
            )

        return "\n".join(lines)

    def generate_summary(self, report: AnalysisReport) -> str:
        """
        Gera markdown para GitHub Actions Job Summary.

        O summary aparece na página do workflow run.
        Salve o output em $GITHUB_STEP_SUMMARY.

        Args:
            report: Relatório de análise

        Returns:
            String markdown para Job Summary
        """
        lines = [
            "# FastAPI Validator Report",
            "",
            "## Summary",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| Routes Analyzed | {report.analyzed_routes} |",
            f"| Errors | {report.error_count} |",
            f"| Warnings | {report.warning_count} |",
            f"| Info | {report.info_count} |",
            "",
        ]

        if report.issues:
            lines.extend([
                "## Issues",
                "",
            ])

            errors = [i for i in report.issues if i.severity == Severity.ERROR]
            warnings = [i for i in report.issues if i.severity == Severity.WARNING]
            infos = [i for i in report.issues if i.severity == Severity.INFO]

            if errors:
                lines.append("### Errors")
                lines.append("")
                for issue in errors:
                    lines.append(self._format_issue_markdown(issue))
                lines.append("")

            if warnings:
                lines.append("### Warnings")
                lines.append("")
                for issue in warnings:
                    lines.append(self._format_issue_markdown(issue))
                lines.append("")

            if infos:
                lines.append("### Info")
                lines.append("")
                for issue in infos:
                    lines.append(self._format_issue_markdown(issue))
                lines.append("")
        else:
            lines.extend([
                "## All checks passed!",
                "",
                "No issues found. Your API follows best practices.",
            ])

        lines.extend([
            "",
            "---",
            "*Generated by FastAPI Validator*",
        ])

        return "\n".join(lines)

    def _issue_to_annotation(self, issue: Issue) -> GitHubAnnotation:
        """Converte Issue para GitHubAnnotation."""
        level = self.SEVERITY_MAP.get(issue.severity, "notice")

        message_parts = [issue.message]
        if issue.path:
            message_parts.append(f"Path: {issue.path}")
        if issue.method:
            message_parts.append(f"Method: {issue.method}")
        if issue.suggestion:
            message_parts.append(f"Suggestion: {issue.suggestion}")

        return GitHubAnnotation(
            level=level,
            message=" | ".join(message_parts),
            file=self.source_file,
            title=issue.rule_id,
        )

    def _format_issue_markdown(self, issue: Issue) -> str:
        """Formata issue como item markdown."""
        parts = [f"- **`{issue.rule_id}`**: {issue.message}"]

        if issue.path:
            parts.append(f"  - Path: `{issue.path}`")
        if issue.method:
            parts.append(f"  - Method: `{issue.method}`")
        if issue.suggestion:
            parts.append(f"  - Suggestion: {issue.suggestion}")

        return "\n".join(parts)

    def save_json(
        self,
        report: AnalysisReport,
        output_path: str | Path,
    ) -> Path:
        """
        Salva anotações em formato JSON.

        Útil para upload via GitHub Checks API.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)

        annotations = []
        for issue in report.issues:
            annotation = self._issue_to_annotation(issue)
            annotations.append({
                "annotation_level": annotation.level,
                "message": annotation.message,
                "title": annotation.title,
                "path": annotation.file or "",
                "start_line": annotation.line or 1,
                "end_line": annotation.end_line or annotation.line or 1,
            })

        data = {
            "title": "FastAPI Validator",
            "summary": f"Found {len(report.issues)} issues in {report.analyzed_routes} routes",
            "annotations": annotations,
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path

    def save_summary(
        self,
        report: AnalysisReport,
        output_path: str | Path,
    ) -> Path:
        """
        Salva summary markdown.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)
        output_path.write_text(self.generate_summary(report), encoding="utf-8")
        return output_path