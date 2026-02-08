"""
Script para testar todas as funcionalidades do fastapi-validator.

Execute com: python examples/test_all_features.py
"""

import sys
from pathlib import Path

# Adiciona o src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from demo_app import app, good_app

from fastapi_validator import (
    # Core Analyzer
    APIAnalyzer,
    AnalysisReport,
    # Scoring
    APIScorer,
    # Breaking Changes
    BreakingChangesDetector,
    # Dependencies
    DependencyAnalyzer,
    # Auto-fix
    AutoFixer,
)
from fastapi_validator.reports import (
    HTMLReporter,
    BadgeGenerator,
    GitHubAnnotationsReporter,
    JUnitReporter,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_basic_analysis():
    """Testa análise básica."""
    print_header("1. ANÁLISE BÁSICA")

    analyzer = APIAnalyzer()
    report = analyzer.analyze(app)

    print(f"\nRotas analisadas: {report.analyzed_routes}")
    print(f"Total de issues: {len(report.issues)}")
    print(f"  - Erros: {report.error_count}")
    print(f"  - Warnings: {report.warning_count}")
    print(f"  - Info: {report.info_count}")

    print("\nIssues encontrados:")
    for issue in report.issues[:5]:  # Mostra só os 5 primeiros
        print(f"  [{issue.severity.value}] {issue.rule_id}")
        print(f"    Path: {issue.path}")
        print(f"    {issue.message}")

    if len(report.issues) > 5:
        print(f"  ... e mais {len(report.issues) - 5} issues")

    return report


def test_scoring(report: AnalysisReport):
    """Testa sistema de scoring."""
    print_header("2. SISTEMA DE SCORING")

    scorer = APIScorer()
    score = scorer.calculate(report)

    print(f"\nScore Total: {score.total_score}/100")
    print(f"Grade: {score.grade.value}")

    print("\nPor categoria:")
    for category, cat_data in score.categories.items():
        cat_score = int(cat_data.score)
        bar = "#" * (cat_score // 5) + "-" * (20 - cat_score // 5)
        print(f"  {category:15} [{bar}] {cat_score}%")

    return score


def test_breaking_changes():
    """Testa detecção de breaking changes."""
    print_header("3. BREAKING CHANGES DETECTOR")

    detector = BreakingChangesDetector()

    # Compara app com problemas vs app boa
    changes_report = detector.compare(app, good_app)

    print(f"\nBreaking changes: {changes_report.breaking_count}")
    print(f"Non-breaking: {changes_report.non_breaking_count}")
    print(f"É compatível? {'Sim' if changes_report.is_compatible else 'Não'}")

    if changes_report.changes:
        print("\nMudanças detectadas:")
        for change in changes_report.changes[:5]:
            status = "[BREAKING]" if change.is_breaking else "[OK]"
            print(f"  {status} [{change.change_type.value}] {change.path}")

    return changes_report


def test_dependency_analysis():
    """Testa análise de dependências."""
    print_header("4. ANÁLISE DE DEPENDÊNCIAS")

    analyzer = DependencyAnalyzer()
    dep_report = analyzer.analyze(app)

    print(f"\nDependências encontradas: {len(dep_report.dependencies)}")
    print(f"Rotas analisadas: {dep_report.total_routes}")
    print(f"Cobertura de segurança: {dep_report.security_coverage:.1f}%")
    print(f"  - Com segurança: {dep_report.routes_with_security}")
    print(f"  - Sem segurança: {dep_report.routes_without_security}")

    if dep_report.issues:
        print("\nIssues de dependência:")
        for issue in dep_report.issues[:3]:
            print(f"  [{issue.issue_type.value}] {issue.message}")

    return dep_report


def test_autofix(report: AnalysisReport):
    """Testa geração de sugestões de código."""
    print_header("5. AUTO-FIX / SUGESTÕES")

    fixer = AutoFixer()
    fix_report = fixer.generate_suggestions(app, report.issues)

    print(f"\nTotal de sugestões: {len(fix_report.suggestions)}")
    print(f"Auto-fixáveis: {fix_report.fixable_count}")
    print(f"Correção manual: {fix_report.manual_count}")

    print("\nExemplos de sugestões:")
    for suggestion in fix_report.suggestions[:3]:
        tag = "[AUTO]" if suggestion.can_auto_fix else "[MANUAL]"
        print(f"\n  {tag} {suggestion.issue.rule_id}")
        print(f"  {suggestion.explanation}")
        if suggestion.original_code and suggestion.suggested_code:
            print(f"  Antes: {suggestion.original_code.split(chr(10))[0]}")
            print(f"  Depois: {suggestion.suggested_code.split(chr(10))[0]}")

    return fix_report


def test_html_report(report: AnalysisReport, score):
    """Testa geração de relatório HTML."""
    print_header("6. RELATÓRIO HTML")

    reporter = HTMLReporter()
    output_path = Path(__file__).parent / "output" / "report.html"
    output_path.parent.mkdir(exist_ok=True)

    reporter.save(report, output_path, score, app_title="Demo API")
    print(f"\nRelatório HTML salvo em: {output_path}")
    print("Abra no navegador para visualizar!")


def test_badges(score):
    """Testa geração de badges."""
    print_header("7. BADGES SVG")

    generator = BadgeGenerator()
    output_dir = Path(__file__).parent / "output" / "badges"
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = generator.save_all_badges(
        score,
        output_dir,
        error_count=5,
        warning_count=10,
    )

    print(f"\nBadges salvos em: {output_dir}")
    for path in saved:
        print(f"  - {path.name}")


def test_github_annotations(report: AnalysisReport):
    """Testa GitHub annotations."""
    print_header("8. GITHUB ANNOTATIONS")

    reporter = GitHubAnnotationsReporter()

    # Mostra preview das anotações
    output = reporter.generate(report)
    lines = output.split("\n")

    print("\nPreview das anotações (primeiras 10 linhas):")
    for line in lines[:10]:
        print(f"  {line}")
    if len(lines) > 10:
        print(f"  ... e mais {len(lines) - 10} linhas")

    # Salva summary
    output_path = Path(__file__).parent / "output" / "github-summary.md"
    reporter.save_summary(report, output_path)
    print(f"\nSummary salvo em: {output_path}")


def test_junit_report(report: AnalysisReport):
    """Testa relatório JUnit."""
    print_header("9. RELATÓRIO JUNIT XML")

    reporter = JUnitReporter()
    output_path = Path(__file__).parent / "output" / "junit-results.xml"

    reporter.save(report, output_path)
    print(f"\nRelatório JUnit salvo em: {output_path}")
    print("Use em Jenkins, GitLab CI, Azure DevOps, etc.")


def test_good_app():
    """Testa app bem estruturada."""
    print_header("10. COMPARAÇÃO: APP BEM ESTRUTURADA")

    analyzer = APIAnalyzer()
    report = analyzer.analyze(good_app)

    scorer = APIScorer()
    score = scorer.calculate(report)

    print(f"\nRotas analisadas: {report.analyzed_routes}")
    print(f"Issues: {len(report.issues)}")
    print(f"Score: {score.total_score}/100 ({score.grade.value})")

    if report.issues:
        print("\nIssues restantes:")
        for issue in report.issues:
            print(f"  [{issue.severity.value}] {issue.rule_id}: {issue.message}")
    else:
        print("\n✅ Nenhum issue encontrado! API em conformidade.")


def main():
    print("\n" + "=" * 60)
    print("  FASTAPI-VALIDATOR - DEMONSTRAÇÃO COMPLETA")
    print("=" * 60)

    # 1. Análise básica
    report = test_basic_analysis()

    # 2. Scoring
    score = test_scoring(report)

    # 3. Breaking changes
    test_breaking_changes()

    # 4. Dependências
    test_dependency_analysis()

    # 5. Auto-fix
    test_autofix(report)

    # 6. HTML Report
    test_html_report(report, score)

    # 7. Badges
    test_badges(score)

    # 8. GitHub Annotations
    test_github_annotations(report)

    # 9. JUnit
    test_junit_report(report)

    # 10. App boa
    test_good_app()

    print_header("DEMONSTRAÇÃO CONCLUÍDA")
    print("\nArquivos gerados em: examples/output/")
    print("  - report.html      (abra no navegador)")
    print("  - badges/*.svg     (use no README)")
    print("  - github-summary.md")
    print("  - junit-results.xml")


if __name__ == "__main__":
    main()