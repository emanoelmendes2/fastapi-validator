"""Gerador de relatórios CSV."""

import csv
import io
from pathlib import Path

from ..analyzer.base import AnalysisReport


class CSVReporter:
    """
    Gera relatórios CSV para análise de API.

    O formato CSV facilita importação em ferramentas de análise
    (Excel, pandas, Google Sheets, etc).

    Example:
        from fastapi_validator import APIAnalyzer
        from fastapi_validator.reports import CSVReporter

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        csv_reporter = CSVReporter()
        csv_reporter.save(report, "issues.csv")
        csv_reporter.save_metrics(report, "metrics.csv")
    """

    ISSUE_HEADERS = ["rule_id", "severity", "path", "method", "message", "suggestion"]
    METRICS_HEADERS = ["metric", "value"]

    def generate(self, report: AnalysisReport) -> str:
        """
        Gera CSV de issues.

        Args:
            report: Relatório de análise

        Returns:
            String CSV com os issues
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.ISSUE_HEADERS)

        for issue in report.issues:
            writer.writerow([
                issue.rule_id,
                str(issue.severity),
                issue.path or "",
                issue.method or "",
                issue.message,
                issue.suggestion or "",
            ])

        return output.getvalue()

    def generate_metrics(self, report: AnalysisReport) -> str:
        """
        Gera CSV de métricas.

        Args:
            report: Relatório de análise

        Returns:
            String CSV com as métricas
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.METRICS_HEADERS)

        if report.metrics:
            metrics_dict = report.metrics.to_dict()
            for key, value in metrics_dict.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"{key}.{sub_key}", sub_value])
                else:
                    writer.writerow([key, value])

        return output.getvalue()

    def save(
        self,
        report: AnalysisReport,
        output_path: str | Path,
    ) -> Path:
        """
        Salva o relatório CSV de issues em arquivo.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)
        content = self.generate(report)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def save_metrics(
        self,
        report: AnalysisReport,
        output_path: str | Path,
    ) -> Path:
        """
        Salva o relatório CSV de métricas em arquivo.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)
        content = self.generate_metrics(report)
        output_path.write_text(content, encoding="utf-8")
        return output_path
