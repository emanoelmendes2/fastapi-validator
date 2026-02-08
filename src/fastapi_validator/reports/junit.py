"""Gerador de relatórios JUnit XML."""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from ..analyzer.base import AnalysisReport, Issue, Severity


class JUnitReporter:
    """
    Gera relatórios em formato JUnit XML.

    O formato JUnit é suportado pela maioria das ferramentas de CI/CD
    (Jenkins, GitLab CI, Azure DevOps, CircleCI, etc).

    Example:
        from fastapi_validator import APIAnalyzer
        from fastapi_validator.reports import JUnitReporter

        analyzer = APIAnalyzer()
        report = analyzer.analyze(app)

        junit = JUnitReporter()
        junit.save(report, "test-results.xml")

    No CI/CD, configure para ler o arquivo XML como resultado de testes.
    """

    def generate(
        self,
        report: AnalysisReport,
        testsuite_name: str = "fastapi-validator",
    ) -> str:
        """
        Gera XML no formato JUnit.

        Args:
            report: Relatório de análise
            testsuite_name: Nome do test suite

        Returns:
            String XML
        """
        root = self._build_xml(report, testsuite_name)
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _build_xml(
        self,
        report: AnalysisReport,
        testsuite_name: str,
    ) -> ET.Element:
        """Constrói a árvore XML."""
        # Agrupa issues por regra
        issues_by_rule: dict[str, list[Issue]] = {}
        for issue in report.issues:
            if issue.rule_id not in issues_by_rule:
                issues_by_rule[issue.rule_id] = []
            issues_by_rule[issue.rule_id].append(issue)

        # Conta resultados
        total_tests = len(issues_by_rule) if issues_by_rule else 1
        failures = sum(
            1 for issues in issues_by_rule.values()
            if any(i.severity == Severity.ERROR for i in issues)
        )
        errors = 0
        skipped = 0

        # Root element
        testsuites = ET.Element("testsuites")
        testsuites.set("name", testsuite_name)
        testsuites.set("tests", str(total_tests))
        testsuites.set("failures", str(failures))
        testsuites.set("errors", str(errors))
        testsuites.set("time", "0")

        # Test suite
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", testsuite_name)
        testsuite.set("tests", str(total_tests))
        testsuite.set("failures", str(failures))
        testsuite.set("errors", str(errors))
        testsuite.set("skipped", str(skipped))
        testsuite.set("timestamp", datetime.now().isoformat())
        testsuite.set("time", "0")

        # Properties
        properties = ET.SubElement(testsuite, "properties")

        prop_routes = ET.SubElement(properties, "property")
        prop_routes.set("name", "analyzed_routes")
        prop_routes.set("value", str(report.analyzed_routes))

        prop_issues = ET.SubElement(properties, "property")
        prop_issues.set("name", "total_issues")
        prop_issues.set("value", str(len(report.issues)))

        # Se não há issues, adiciona um test case de sucesso
        if not issues_by_rule:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", "api-validation")
            testcase.set("classname", testsuite_name)
            testcase.set("time", "0")
        else:
            # Test cases para cada regra
            for rule_id, issues in issues_by_rule.items():
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", rule_id)
                testcase.set("classname", f"{testsuite_name}.{self._get_category(rule_id)}")
                testcase.set("time", "0")

                # Determina severidade mais alta
                max_severity = max(i.severity for i in issues)

                if max_severity == Severity.ERROR:
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", f"{len(issues)} violation(s) found")
                    failure.set("type", "ValidationError")
                    failure.text = self._format_issues_text(issues)
                elif max_severity == Severity.WARNING:
                    # Warnings como system-out (não falha o build)
                    system_out = ET.SubElement(testcase, "system-out")
                    system_out.text = self._format_issues_text(issues)

        return testsuites

    def _get_category(self, rule_id: str) -> str:
        """Extrai categoria do rule_id."""
        if "-" in rule_id:
            return rule_id.split("-")[0]
        return "general"

    def _format_issues_text(self, issues: list[Issue]) -> str:
        """Formata lista de issues como texto."""
        lines = []
        for issue in issues:
            parts = [issue.message]
            if issue.path:
                parts.append(f"Path: {issue.path}")
            if issue.method:
                parts.append(f"Method: {issue.method}")
            if issue.suggestion:
                parts.append(f"Suggestion: {issue.suggestion}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def save(
        self,
        report: AnalysisReport,
        output_path: str | Path,
        testsuite_name: str = "fastapi-validator",
    ) -> Path:
        """
        Salva relatório em arquivo XML.

        Args:
            report: Relatório de análise
            output_path: Caminho do arquivo de saída
            testsuite_name: Nome do test suite

        Returns:
            Path do arquivo salvo
        """
        output_path = Path(output_path)
        xml_content = self.generate(report, testsuite_name)
        output_path.write_text(xml_content, encoding="utf-8")
        return output_path